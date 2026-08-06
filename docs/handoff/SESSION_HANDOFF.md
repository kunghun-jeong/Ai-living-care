# 2026-08-03~04 세션 요약 (LIMO 시뮬레이션 + mcp_gateway 확장)

다른 AI/사람이 이어서 작업할 때 참고하는 문서. "왜 이렇게 했는지"와 "다시 겪지 않아도 될 함정"을 남기는 게 목적이라, 코드 자체는 각 파일을 직접 읽는 게 정확함.

## 1. mcp_gateway/action.py — patrol/dock/interrupt 추가

기존에는 `send_goal`(1회성 이동), `look_around`, `cancel_goal`만 있었고 `mode`(idle/patrol/dock)는 라벨만 있고 실제 동작이 없었음.

**추가된 것:**
- `start_patrol(waypoints, loop)` / `cancel_patrol()` / `is_patrolling()` — 웨이포인트 리스트를 순차 이동, `loop=True`면 반복. 백그라운드 스레드 + `threading.Event` 인터럽트 패턴.
- `start_dock(x, y, frame, yaw_deg)` / `cancel_dock()` / `is_docking()` — 단일 지점 이동 + `is_docked` 상태 플래그. patrol과 같은 패턴 재사용.
- `interrupt()` — 현재 뭘 하고 있든(수동 목표/patrol/dock/look_around) 상태 몰라도 호출하면 전부 멈추고 idle로. **주의**: 그냥 `set_mode("idle")`만 부르면 백그라운드 스레드가 실제로 멈추기 전에 리턴해버려서(비동기 취소) 호출자가 바로 다음 동작을 시도하면 "in progress"로 거부당함 — 그래서 `interrupt()`는 관련 스레드를 최대 8초까지 `join()`해서 실제로 멈춘 뒤 리턴하도록 만들었음. (patrol/dock의 첫 leg가 `_send_goal_internal`의 블로킹 대기(`wait_for_server` 최대 2초 + accept 대기 최대 5초) 안에 있으면 인터럽트 이벤트를 그 시점엔 못 보기 때문에 최악의 경우 몇 초 걸림.)
- **상호 배제**: `send_goal`/`look_around`/`start_patrol`/`start_dock` 넷이 서로 겹쳐 실행되지 않도록 서로의 `is_*ing()`과 `self._goal_handle`을 체크. 특히 `look_around`가 활성 nav goal 여부를 체크 안 하던 게 원래 버그였음(직접 cmd_vel 쏘는 look_around와 Nav2 controller가 동시에 cmd_vel을 쏠 수 있었음) — 고쳐짐.
- **`cancel_goal`의 레이스 컨디션 수정**: 취소 후 도착한 stale `_on_result` 콜백이 상태를 다시 덮어쓰는 문제가 있어서 `_goal_token`을 도입해 취소/재전송 시마다 증가시키고, 콜백은 자기 토큰이 현재 토큰과 다르면 무시하도록 함.
- **`_on_pose` 구독 QoS 버그 수정**: AMCL은 `/amcl_pose`를 `TRANSIENT_LOCAL`로 발행하는데 기존 구독은 기본(`VOLATILE`) QoS라서, 로봇이 멈춰있는 동안(AMCL이 재발행 안 함) 늦게 붙은 구독자는 pose를 영영 못 받는 문제가 있었음. `QoSDurabilityPolicy.TRANSIENT_LOCAL`로 명시.
- `_make_pose`에 `header.stamp` 채우도록 수정 (원래 비어있었음).

**아직 안 고친 것 (알고 있는 한계, 우선순위 낮다고 판단):**
- `cancel_goal()`이 Nav2의 실제 취소 승인을 기다리지 않고 낙관적으로 `status="cancelled"`로 씀.
- 여러 MCP 툴 호출이 동시에 들어오는 경우의 스레드 안전성은 GIL에 의존 (락 없음).

## 2. mcp_gateway/limo_mcp_server.py

`start_patrol`/`cancel_patrol`/`is_patrolling`/`start_dock`/`cancel_dock`/`is_docking`/`interrupt` MCP 툴 추가. `get_status`에 `is_docked` 추가. `set_mode` 설명을 patrol/dock은 각각 전용 툴로 진입해야 한다고 갱신.

## 3. mcp_gateway/yolo_detector.py — lazy import

`from ultralytics import YOLO` / `from cv_bridge import CvBridge`가 모듈 최상단에 있어서 `limo_mcp_server.py`를 import만 해도 (실제 YOLO 안 써도) 저 무거운 의존성이 필요했음. `make_yolo_detector()`가 리턴하는 `detect()` 클로저 안으로 이 import들을 옮겨서, 실제로 `detect_objects` 툴이 처음 호출될 때만 로드되도록 함. **`ultralytics`는 현재 미설치** (확인함 — WSL python3/pip list/venv/Windows Python 어디에도 없음). 카메라 토픽도 시뮬레이션에 없어서(`/image_raw` 없음) `check_obj_human.json` 시나리오는 지금 못 돌림.

## 4. ROS2 시뮬레이션 환경 (WSL2 Ubuntu 24.04)

**설치:** ROS2 **Jazzy** (24.04 네이티브 배포판), `ros-jazzy-desktop`, `ros-jazzy-navigation2`, `ros-jazzy-nav2-bringup`, `ros-jazzy-turtlebot3-gazebo`, Gazebo는 새 버전(gz-sim8, "Harmonic" 계열) — Gazebo Classic 아님. 설치 스크립트: `scenarios/install_ros2_jazzy_nav2_sim.sh`.

매번 새 WSL 터미널에서: `source /opt/ros/jazzy/setup.bash` 필요 (비대화형 세션에선 `.bashrc` 자동 소싱이 안 될 수 있음).

### 4.1 turtlebot3 기반 시뮬레이션 — `scenarios/sim_bringup.launch.py`

`nav2_bringup`의 공식 `tb3_simulation_launch.py`를 감싼 래퍼. 기본 로봇은 turtlebot3 waffle.

```
ros2 launch scenarios/sim_bringup.launch.py
# 다른 지도(월드 세트로 같이 바꿔야 함, 아래 4.3 참고):
ros2 launch scenarios/sim_bringup.launch.py \
  map:=/opt/ros/jazzy/share/nav2_bringup/maps/depot.yaml \
  world:=/opt/ros/jazzy/share/nav2_minimal_tb4_sim/worlds/depot.sdf
```

`headless`/`use_rviz` 인자는 **대문자** `True`/`False`로 줘야 함 (`nav2_bringup`이 내부적으로 `PythonExpression`/`eval`로 처리해서 소문자 `true`는 `NameError`).

### 4.2 `scenarios/nav2_params_sim.yaml` — AMCL 자동 초기화

`nav2_bringup`의 기본 `nav2_params.yaml`을 복사해서 `amcl.set_initial_pose: true` + `initial_pose: {x: -2.0, y: -0.5, z: 0, yaw: 0}` 추가한 버전. **이유**: `global_costmap`이 activate될 때 `base_link→map` TF가 필요한데, 사람이 RViz에서 "2D Pose Estimate"를 누르는 속도가 이 activation 타임아웃보다 느려서 매번 `bt_navigator`/`planner_server`/`global_costmap`이 `inactive`에 멈추는 레이스가 있었음. AMCL이 시작할 때 스스로 초기 pose를 넣게 하면 이 레이스 자체가 사라짐. (스폰 위치 -2.0, -0.5는 `tb3_simulation_launch.py`의 기본 스폰 좌표와 일치시킨 것.)

### 4.3 지도(map) 바꾸기 — 월드(world)도 같이 바꿔야 함

`nav2_bringup/maps/`에 `depot.yaml`/`warehouse.yaml`도 번들돼 있지만, 이건 turtlebot **4**용 데모(`nav2_minimal_tb4_sim`)의 맵이라 대응하는 Gazebo 월드가 `nav2_minimal_tb4_sim/worlds/depot.sdf` 쪽에 있음 (`nav2_minimal_tb3_sim` 쪽엔 `tb3_sandbox` 월드 하나뿐). **map만 바꾸고 world는 그대로 두면 AMCL이 로컬라이즈 못 함** (지도와 실제 물리 환경이 다른 공간이라).

- **depot**: turtlebot3/LIMO 둘 다 기본 스폰 좌표(-2.0,-0.5)가 비어있어서 그대로 작동 확인함.
- **warehouse**: 지도상 스폰 좌표는 비어있다고 나오는데(픽셀 값 확인함) 실제로는 30초+ 기다려도 AMCL이 위치를 못 잡음 — 원인 미해결. 아마 그 월드의 실제 로봇 시작 위치가 tb3 기본 스폰 좌표(-2.0,-0.5)와 안 맞는 것으로 추정. 쓰려면 추가 조사 필요.

### 4.4 LIMO 로봇 — `scenarios/limo_robot/` + `scenarios/sim_bringup_limo.launch.py`

실제 AgileX LIMO(4륜 diff drive) 치수를 `agilexrobotics/limo_ros2`(ROS2 Humble, Gazebo Classic 플러그인)에서 가져와서 new Gazebo(gz-sim) 플러그인으로 포팅한 것. WeGo 로봇 자체의 URDF/SDF는 이 프로젝트(`wego` 패키지)에 없어서 AgileX 것으로 대체.

**구성 파일:**
- `limo_robot/urdf/gz_limo.sdf.xacro` — Gazebo 스폰용. `gz::sim::systems::DiffDrive`(2개 wheel pair 지원, front/rear 각각 left/right) + `JointStatePublisher` + `gpu_lidar` + `imu` 센서. 참고 템플릿: `/opt/ros/jazzy/share/nav2_minimal_tb3_sim/urdf/gz_waffle.sdf.xacro`.
- `limo_robot/urdf/limo.urdf` — `robot_state_publisher`용 플랫 URDF. **SDF와 링크/조인트 이름이 정확히 같아야 TF가 맞음** — 손으로 동기화해야 함 (한쪽 고치면 다른 쪽도).
- `limo_robot/configs/limo_bridge.yaml` — `ros_gz_bridge` 토픽 매핑. `nav2_minimal_tb3_sim`의 `turtlebot3_waffle_bridge.yaml`과 토픽 이름 구조가 같아서 그대로 참고해 만듦.
- `limo_robot/launch/spawn_limo.launch.py` — 스폰 + 브리지. `nav2_minimal_tb3_sim/launch/spawn_tb3.launch.py` 구조 복제.
- `limo_robot/meshes/` — 실제 LIMO 메시(limo_base.dae, limo_wheel.dae, agilexrobotics 저장소에서 다운로드). **현재 SDF/URDF에서는 안 씀** (아래 함정 참고). 남겨는 두되 참조는 안 됨.

**실제 치수** (agilexrobotics `limo_four_diff.xacro`/`.gazebo`에서 그대로 가져옴): wheelbase 0.2m, track 0.13m, wheel_radius 0.045m, laser 위치 (0.103, 0, -0.034), imu 위치 (0, 0, -0.1) (base_link 기준). `wheel_separation`(0.172, DiffDrive 플러그인용)은 AgileX가 실측 튜닝한 값이라 track 폭에서 그냥 계산한 값이 아님. **`max_linear_velocity`(0.6m/s) 등 속도/가속도 파라미터는 실제 AgileX 스펙이 아니라 보수적인 추정값** — 실물 로봇 스펙 문서 있으면 나중에 맞출 것.

`sim_bringup_limo.launch.py`는 `tb3_simulation_launch.py`를 그대로 재사용 못 해서 (아래 함정 참고) 그 구조를 통째로 복제해 새로 작성함. 인자 구성은 `sim_bringup.launch.py`와 거의 동일 (`map`, `world`, `headless`, `use_rviz`, `params_file` 등) + LIMO 전용 `robot_name`/`robot_sdf`/`mesh_dir`.

```
ros2 launch scenarios/sim_bringup_limo.launch.py
# depot 지도로:
ros2 launch scenarios/sim_bringup_limo.launch.py \
  map:=/opt/ros/jazzy/share/nav2_bringup/maps/depot.yaml \
  world:=/opt/ros/jazzy/share/nav2_minimal_tb4_sim/worlds/depot.sdf
```

tb3_sandbox와 depot 둘 다 헤드리스로 검증 완료(AMCL 로컬라이즈 + 실제 navigate_to_pose 성공). warehouse는 미시도.

## 5. 오늘 겪은 삽질/함정 (재발 방지용)

이 순서대로 겪었음 — 비슷한 걸 다시 만들 때 참고.

1. **`headless`/`use_rviz` 인자는 대문자 `True`/`False`**. `nav2_bringup`이 일부 인자를 `PythonExpression`(=`eval`)로 처리해서 소문자 `true`를 주면 `NameError: name 'true' is not defined`.
2. **`bt_navigator`/`planner_server`/`global_costmap`이 `inactive`에 멈추는 문제** — `global_costmap` activate가 `base_link→map` TF를 기다리는데, 사람이 RViz에서 pose 찍는 게 그 타임아웃보다 느림. → `amcl.set_initial_pose`로 해결 (4.2).
3. **MCP stdio 클라이언트는 자식 프로세스에 최소한의 환경변수만 물려줌** (`mcp` 파이썬 SDK의 `DEFAULT_INHERITED_ENV_VARS`는 POSIX에서 `HOME/LOGNAME/PATH/SHELL/TERM/USER`뿐 — `PYTHONPATH`/ROS 환경변수 전부 제외). `scenario_runner.py`가 `limo_mcp_server.py`를 띄울 때 이거 때문에 `rclpy` 못 찾는 에러 남 → `StdioServerParameters(..., env=dict(os.environ))`로 명시적으로 전체 환경 전달해서 해결.
4. **`tb3_simulation_launch.py`는 `robot_sdf` 인자로 Gazebo 스폰 로봇은 바꿀 수 있지만, `robot_state_publisher`에 넘기는 URDF는 `turtlebot3_waffle.urdf`로 하드코딩돼 있어서 로봇을 통째로 바꿀 수 없음**. LIMO 넣으려면 이 launch 파일 자체를 통째로 복제해서 새로 써야 했음 (`sim_bringup_limo.launch.py`).
5. **월드가 참조하는 `model://` 리소스는 `GZ_SIM_RESOURCE_PATH`가 설정돼야 풀림** — `spawn_tb3.launch.py`는 `AppendEnvironmentVariable`로 이걸 설정해주는데, 직접 짠 `spawn_limo.launch.py`엔 없어서 처음에 월드 로딩 자체가 실패함 (`Unable to find uri[model://turtlebot3_world]`). `sim_bringup_limo.launch.py`에 같은 env var 액션 추가해서 해결.
6. **`ROS_DOMAIN_ID`는 ROS2 DDS만 격리하고 Gazebo Transport(gz-transport)는 격리 안 됨.** 격리 테스트한다고 `ROS_DOMAIN_ID`만 다르게 줬더니, 이미 켜져 있던 다른 시뮬레이션 인스턴스와 gz-transport가 섞여서 AMCL이 완전히 엉뚱한 위치로 튀는 버그처럼 보였음. **`GZ_PARTITION` 환경변수도 고유하게 설정해야 진짜 격리됨.**
7. **Gazebo가 `file://` URI 안의 비ASCII(한글) 경로를 못 읽음** (`Could not resolve file`). 프로젝트 경로 자체가 `산학협력`이라 메시 파일을 못 불러왔음. → 메시를 한글 없는 경로(`~/limo_sim_assets/meshes`)로 복사해서 임시로 해결했었으나, 그 다음 문제(8) 때문에 결국 메시 자체를 안 쓰게 됨.
8. **실제 다운로드한 LIMO 메시(limo_base.dae 52MB, limo_wheel.dae 11MB)가 너무 커서 WSLg 렌더링이 사실상 멈춤** (14분+ CPU 100%, 창 자체가 안 뜸). → 시각적 정밀도 포기하고 collision과 같은 크기의 박스/실린더로 대체 (`gz_limo.sdf.xacro`/`limo.urdf` 둘 다 primitive geometry, 색만 구분: 몸체 주황, 바퀴 진회색). 메시 파일 자체는 `limo_robot/meshes/`에 남아있지만 참조 안 됨 — 나중에 저폴리로 디메이션하면 다시 쓸 수 있음.
9. **WSLg 자체가 가끔 맛이 감** (특히 GUI 프로세스를 `kill -9`로 여러 번 강제 종료한 뒤): 프로세스는 다 정상 실행 중이고 X서버에 창도 실제로 등록되는데(`xwininfo`로 확인) 작업표시줄 클릭해도 화면이 안 그려짐. `wsl --shutdown` (Windows PowerShell에서, WSL 안에서는 안 됨) 후 재시작하면 해결됨.
10. (프로세스 정리할 때 `ROS_DOMAIN_ID` 환경변수로 프로세스를 걸러서 죽이려다가, **한 번은 실제로 사용자가 띄워둔 세션을 잘못 죽인 적 있음** — `pgrep -f`로 명령줄만 매칭하고 env var 필터링이 부정확했음. 프로세스 강제종료할 땐 PID를 명확히 확인하고 최소 단위로 죽일 것.)

## 6. 시나리오 실행 (MCP 파이프라인)

`scenarios/scenario_runner.py`가 `limo_mcp_server.py`를 MCP stdio 서버로 띄우고 JSON 시나리오의 `steps`를 순서대로 실행. step type: `call`(툴 1개 호출), `poll_until_match`(리스트에서 클래스 매칭될 때까지 반복 폴링 — 원래 perception 시나리오용으로 설계됨), `branch`(조건 분기), `sleep`(오늘 추가함, 그냥 대기).

```
source /opt/ros/jazzy/setup.bash
python3 scenarios/scenario_runner.py scenarios/patrol_dock_demo.json
```

시뮬레이터가 먼저 떠 있어야 함. 결과는 `scenarios/logs/`에 JSON으로 쌓임.

`patrol_dock_demo.json`의 좌표는 **tb3_sandbox 지도 기준으로 실측 확인한 free space**임 (지도 pgm을 직접 파싱해서 찾음). 다른 지도(depot 등)로 시나리오 돌리려면 그 지도용으로 좌표를 새로 찾아야 함 — pgm 파싱 스크립트 패턴은 이 세션 대화 기록에 있음 (origin/resolution은 각 지도의 `.yaml`에 있고, pgm은 `negate:0` 기준으로 픽셀값이 255에 가까울수록 free).

`test_action_module.py`는 MCP 계층 없이 `ActionModule`을 직접 물고 도는 스모크 테스트 (patrol/dock/interrupt/look_around 순차 실행) — 의존성 가볍게 로직만 빠르게 검증하고 싶을 때 씀.

## 7. 안 끝난 것들

- `ultralytics`(YOLO) 미설치, 카메라 브리지(`/image_raw`) 없음 → `check_obj_human.json` 시나리오 못 돌림.
- warehouse 지도 로컬라이즈 실패 원인 미해결.
- LIMO 시각 모델이 primitive(박스/실린더)로 대체됨 — 메시 다시 쓰려면 저폴리 버전으로 교체 필요.
- LIMO의 속도/가속도 파라미터가 추정치 (실물 스펙 확인 필요).
- depot용 patrol/dock 시나리오 좌표는 아직 안 만듦 (요청 시 pgm 파싱해서 만들 것).
