# limo-MCP 개발 기록

다른 AI/사람이 이어서 작업할 때 참고하는 문서. 세션마다 "무엇을 했고 왜 그렇게 했는지"를 이어서 기록한다. 코드 자체의 정확한 동작은 각 파일을 직접 읽는 게 맞음 — 여긴 결정/배경/함정 기록용.

## 프로젝트 위치와 관계

`Desktop\산학협력\limo-MCP` — 같은 폴더의 `limo_slam`(mcp_gateway/action.py, reasoning.py, mcp_server.py + Gazebo/Nav2 시뮬레이션 브링업 이미 검증됨, `limo_slam/SESSION_HANDOFF.md` 참고)과는 **별개의 독립 프로젝트**로 진행하기로 함 (2026-08-06 확정). Gazebo 시뮬레이션 환경도 limo_slam 것을 재사용하지 않고 limo-MCP 안에서 새로 구성하기로 결정.

## 2026-08-06

**구조 파악:**
- `Worker_functions/Actions.py`: 구현 완료. `ActionModule` — Nav2 `NavigateToPose` 액션 클라이언트 래핑. 웨이포인트 리스트를 백그라운드 스레드로 순차 전송(`send_goal_sequence`), 단일 목표 전송/취소, yaw 자동 계산(`_goal_xy_yaw`) 등.
- `Worker_functions/Reasonings.py`: 구현 완료. `ReasoningModule` — YOLO 검출/경로계획/크롭을 생성자 주입 방식으로 받는 ROS2 비의존 순수 로직. `PersonScan`(1Hz 백그라운드 사람 탐지 루프) 포함. `plan_fn`은 아직 no-op 기본값만 있고 실제 구현 없음.
- `MCP_server/MCP_server.py`, `Worker_functions/Perceptions.py`, `Scenarios/check_obj_state.json`: 아직 빈 파일 (스텁만 존재).

**설계 결정 (사용자 확인):**
- Reasoning → Action 연결 시 시뮬레이터는 Gazebo 사용, limo-MCP 안에 독립적으로 새 환경 구성.
- `plan_path`의 역할: **단순 웨이포인트 전달**로 결정. `Actions.py`의 `send_goal_sequence`가 각 웨이포인트마다 Nav2 `NavigateToPose`를 순차 전송하는데, `NavigateToPose` 자체가 Nav2 내부에서 전역 경로계획(global planner)을 다시 수행하기 때문에 `plan_path`가 별도로 `ComputePathToPose`를 호출해 촘촘한 경로를 미리 뽑을 필요는 없다고 판단함. `plan_path`는 목표 지점(들)을 검증/정리해서 `send_goal_sequence`가 바로 쓸 수 있는 웨이포인트 리스트로 넘기는 역할만 함.

**추가 요구사항 확인 (사용자):** 카메라가 실제로 동작해야 하고 시뮬레이션이 원활해야 함.

**시뮬레이션 로봇/월드 선택 (조사 후 결정):** ROS2 Jazzy에 이미 설치된 `turtlebot3_gazebo` 패키지의 waffle 모델 사용. `/opt/ros/jazzy/share/turtlebot3_gazebo/models/turtlebot3_waffle/model.sdf`에 실제 RGB 카메라 센서(`intel_realsense_r200`, `camera/image_raw` 토픽)가 이미 정의돼 있고, `spawn_turtlebot3.launch.py`가 `ros_gz_image image_bridge`로 ROS2 토픽까지 이미 연결해줌 — limo_slam이 못 끝낸 카메라 브리지가 이 패키지엔 이미 완성돼 있음. 메시가 전부 `/opt/ros/jazzy` 밑 ASCII 경로라 limo_slam이 겪은 한글 경로 문제(함정 #7)도 없음. `nav2_bringup`이 제공하는 turtlebot3_world용 사전 제작 지도가 없어서 AMCL 대신 `slam_toolbox`로 실시간 매핑하면서 동시에 내비게이션하는 `slam:=True` 조합 사용 (limo_slam이 겪은 AMCL 초기 pose TF 레이스, 함정 #2를 원천적으로 피함). 커스텀 로봇 모델은 만들지 않음 — `Actions.py`/`Reasonings.py`는 로봇이 무엇이든 동일하게 동작하므로 나중에 실제 LIMO 모델로 교체해도 Worker_functions 코드는 안 건드림.

**구현 완료:**
- `Simulation/sim_bringup.launch.py` (신규) — `TURTLEBOT3_MODEL=waffle` 환경변수 설정 후 `turtlebot3_gazebo`의 `turtlebot3_world.launch.py`(Gazebo+로봇+카메라 브리지)와 `nav2_bringup`의 `bringup_launch.py`(`slam:=True`, `use_sim_time:=true`, `autostart:=true`)를 그대로 include만 해서 엮음. 커스텀 로봇/월드 코드 없음, 공식 배포판 그대로 사용. `ros2 launch ... --show-args`로 파싱 정상 확인함 (WSL2 Ubuntu 24.04, ROS2 Jazzy).
- `MCP_server/MCP_server.py` (신규) — limo_slam의 `mcp_gateway/limo_mcp_server.py`와 동일 패턴(`mcp.server.mcpserver.MCPServer`, rclpy 백그라운드 데몬 스레드 spin + 메인 스레드 `mcp.run(transport="stdio")`)을 limo-MCP의 `ActionModule`/`ReasoningModule` API에 맞춰 작성. `_plan_fn`은 목표 지점 검증만 하고 그대로 웨이포인트로 돌려줌(단순 웨이포인트 전달 — 실제 전역 경로계획은 `send_goal_sequence`가 보내는 각 `NavigateToPose`가 Nav2 내부에서 수행). MCP 툴: `plan_and_navigate`, `navigate_waypoints`, `get_status`, `cancel`. `Actions.py`/`Reasonings.py` import 및 컴파일 확인함.
- `requirements.txt` (신규) — `mcp[cli]` (이번 범위엔 YOLO 불필요해서 ultralytics 제외).

**실제 실행 검증 (WSL2 Ubuntu 24.04, ROS2 Jazzy):**

`ros2 launch Simulation/sim_bringup.launch.py`로 첫 실행 시 Gazebo + Nav2 + slam_toolbox 자체는 정상 기동함 (`/camera/image_raw` ~3.8Hz 발행, `/map` 발행, lifecycle "Managed nodes are active", AMCL TF 레이스 없음 — 예상한 리스크는 발생 안 함). 하지만 실제 목표를 보내보니 로봇이 전혀 움직이지 않는 버그를 발견함:

- **증상**: `NavigateToPose`는 계속 재계획만 반복(`controller_server: Failed to make progress` 반복), `/odom` 위치가 몇 분 동안 완전히 고정.
- **원인**: `turtlebot3_gazebo`의 스톡 `turtlebot3_waffle_bridge.yaml`은 `cmd_vel`을 `geometry_msgs/msg/TwistStamped`로 선언하는데, 이 ROS2 Jazzy + `nav2_bringup` 스톡 `nav2_params.yaml` 조합에서는 Nav2의 `collision_monitor`가 최종 `/cmd_vel`을 `geometry_msgs/msg/Twist`(스탬프 없음)로 발행함. `ros2 topic info /cmd_vel --verbose`로 확인: publisher(`collision_monitor`)는 `Twist`, 유일한 subscriber(`ros_gz_bridge`)는 `TwistStamped` — 타입이 안 맞아 ROS2가 둘을 별개 토픽 인스턴스로 취급, 아무 것도 브리지되지 않음. 그래서 Gazebo의 `DiffDrive` 플러그인은 속도 명령을 영원히 못 받음.
- **수정**: `Simulation/waffle_bridge_fixed.yaml` 신규 — 스톡 브리지 yaml을 그대로 복사하되 `cmd_vel` 타입만 `Twist`로 고침. `sim_bringup.launch.py`를 `turtlebot3_world.launch.py`(스폰까지 통째로 포함, 브리지 yaml 경로를 밖에서 바꿀 방법이 없음)를 그대로 include하는 대신, gzserver/gzclient/robot_state_publisher/spawn/bridge/image_bridge를 각각 직접 풀어서 구성하도록 재작성 — 스폰(`ros_gz_sim create`)과 브리지(`parameter_bridge`)만 우리 파일을 가리키게 하고 나머지는 공식 패키지 그대로 사용.
- **검증 결과**: 수정 후 재기동 → MCP 클라이언트로 `plan_and_navigate(x=1.0, y=0.0)` 호출 → `get_status()` 폴링 결과 `status: "navigating"` → `"succeeded"`로 전이, `sequence_result: {"completed": 1, "total": 1, "interrupted": false}`. `/odom` 위치가 호출 전 `(0,0)`에서 호출 후 `(0.764, 0.009)`로 실제 이동 확인함 (목표 1.0m에서 goal tolerance 이내인 0.764m — Nav2 기본 goal checker 허용 오차, 정상 동작). **Reasoning(plan_path)→Action(send_goal_sequence)→실제 Gazebo 로봇 이동까지 MCP 서버를 통한 전체 연결성 확인 완료.**

테스트에 쓴 MCP 클라이언트 스크립트는 WSL `~/mcp_navigate_test.py`에 있음 (저장소에는 포함 안 함 — 임시 검증용).

**카메라 스트리밍 확인:** `rqt_image_view /camera/image_raw`로 라이브 GUI 창 확인, `PIL`로 프레임 1장 저장해서 실제 turtlebot3_world 장애물이 렌더링되는 것도 확인함 (WSL CPU 부하로 스펙상 30Hz보다 느린 ~2Hz).

**`Scenarios/send_goal.py` (신규):** 사용자가 직접 시뮬레이션을 조작할 수 있는 커맨드라인 MCP 클라이언트. `python3 Scenarios/send_goal.py <x> <y> [yaw_deg]` — `MCP_server.py`를 서브프로세스로 띄워 `plan_and_navigate` 호출 후 `succeeded`/`failed`까지 상태 폴링. 실행 확인함.

## Perception + YOLO 연동

`Worker_functions/Perceptions.py` (신규) — `PerceptionModule(node, topic="/camera/image_raw")`. `/camera/image_raw`를 구독해서 최신 프레임 1장만 캐시(`get_latest_frame`). `Reasonings.py`의 `ReasoningModule`이 기대하는 `FrameSource` 시그니처를 그대로 만족하도록 만듦 (limo_slam의 `FrameStore`와 같은 역할, Actions.py처럼 ROS2 의존).

`MCP_server/MCP_server.py`에 `_detect_fn`(YOLO, ultralytics는 함수 안에서만 import — 안 쓰면 무거운 의존성 안 물게 함), `_crop_fn`/`_encode_jpeg`(PIL 기반 JPEG 인코딩)를 추가하고 `ReasoningModule`에 주입. MCP 툴 `get_camera_snapshot()`(사진 그대로 가져오기), `detect_objects(min_conf)`(YOLO 검출 결과 반환) 추가.

**실행 중 발견하고 고친 문제 2개 (WSL2 Ubuntu 24.04):**
1. **numpy ABI 충돌**: `pip install --user ultralytics`가 numpy 2.5.1을 깔았는데, apt로 깔린 시스템 matplotlib(rclpy 등이 쓰는)은 numpy 1.x용으로 컴파일돼 있어서 `from ultralytics import YOLO`가 matplotlib import 단계에서 `ImportError: numpy.core.multiarray failed to import`로 죽음. `pip install --user --break-system-packages numpy==1.26.4`로 apt 쪽과 맞춰서 해결 (opencv-python이 numpy>=2를 요구한다는 pip 경고가 뜨지만 실제 런타임엔 문제없음, `import cv2`로 확인함).
2. **YOLO 첫 다운로드가 MCP stdio 프로토콜을 깸**: `detect_objects`를 처음 호출하면 `yolov8n.pt` 가중치를 내려받는데 그 진행 표시줄이 stdout으로 나감 — MCP stdio 트랜스포트는 stdout을 JSON-RPC 프로토콜 전용으로 쓰기 때문에 클라이언트가 "Failed to parse JSONRPC message" 에러를 냄 (다행히 치명적이진 않고 그 줄만 무시하고 넘어감, 하지만 근본 수정 필요). `mcp.run()`으로 stdout을 넘기기 전에 더미 프레임으로 한 번 미리 예열(`contextlib.redirect_stdout(sys.stderr)`로 감싸서)하도록 고침 — 다운로드/모델 로딩이 서버 시작 시점에 stderr로만 끝나고, 첫 실제 `detect_objects` 호출은 이미 로딩된 모델을 씀 (타임아웃 문제도 같이 해결됨, 기존 `ReasoningModule.plan_path`/`detect_objects` 기본 5~10초 타임아웃은 그대로 둠).

**검증 결과**: MCP 클라이언트로 `get_camera_snapshot` → 실제 JPEG 저장 확인, `detect_objects` → `{"class": "tv", "conf": 0.35, "bbox": [...]}` 형태로 정상 반환 확인 (turtlebot3_world엔 실제 COCO 클래스 객체가 없어서 벽 텍스처를 tv로 오탐하는 것 — 파이프라인 자체가 정상 동작한다는 증거로는 충분).

**`Scenarios/capture_and_detect.py` (신규):** `send_goal.py`와 같은 패턴의 커맨드라인 클라이언트. `python3 Scenarios/capture_and_detect.py [저장경로.jpg]` — 스냅샷 저장 + 검출 결과 출력. 실행 확인함.

`requirements.txt`에 `ultralytics` 추가함.

**리팩터 (사용자 요청):** YOLO 구현을 `MCP_server.py`의 `_detect_fn`에서 `Reasonings.py`의 `yolo_detect`로 옮김 — `MCP_server.py`는 이제 `from Reasonings import ReasoningModule, yolo_detect`로 가져다 쓰기만 함. `plan_fn`은 여전히 게이트웨이 쪽(`MCP_server.py`)에 남겨둠 — 웨이포인트 전달은 애초에 로직이랄 게 없는 얇은 검증이라 굳이 옮길 이유가 없었음. `ReasoningModule`의 `detect_fn` 기본값은 그대로 `_no_op_detect`로 유지(테스트 편의) — `yolo_detect`는 named export로 두고 명시적으로 주입하는 방식 그대로. 옮긴 후 스냅샷+검출 재검증 완료.

**다음 단계 (미착수):**
- 실제 LIMO 로봇 모델로 교체 (원하면) — Worker_functions/MCP_server 코드는 안 건드려도 됨
- YOLO 오탐(turtlebot3_world 벽을 tv로 인식)은 실제 COCO 객체(사람 모델 등)가 있는 월드로 바꾸면 더 의미있게 테스트 가능
