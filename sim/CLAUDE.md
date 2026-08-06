# sim — 시뮬레이션 환경

> **SOT**: `docs/spec/AI-Care_Unified_Architecture_Spec_v0.2.md` §10.2
> **컴포넌트가 아니다.** 여기에 비즈니스 로직을 두지 않는다.

Gazebo + Nav2 + slam_toolbox 브링업. `sim_bringup.launch.py`가 진입점이다.

```bash
source /opt/ros/jazzy/setup.bash
./fetch_meshes.sh                        # 최초 1회 — AWS 메시 ~55MB
ros2 launch sim/sim_bringup.launch.py
```

## 구성

| 항목 | 현재 |
|---|---|
| ROS2 | **Jazzy** (WSL2 Ubuntu 24.04) — **팀 내 배포판이 갈려 있음, 통일 필요 (U-12)** |
| 로봇 | **turtlebot3 waffle** (LIMO 아님) — 카메라 센서·브리지가 이미 완성돼 있어 선택 |
| 월드 | **AWS RoboMaker small_house** — 실제 주거 공간이라 리빙케어에 적합 |
| 측위 | **`slam_toolbox` (`slam:=True`)** — AMCL 아님. 초기 pose TF 레이스를 원천 회피 |
| 카메라 | `/camera/image_raw` — rate가 자료마다 다름 (30 / 10 / 실측 2~3.8 Hz) |
| **RTF** | **0.04 ~ 0.06** — **최대 리스크** |

## ⚠️ 두 가지 큰 문제

**1. RTF 0.04~0.06 (U-14)** — headless·무로봇 상태에서도 그렇다.
6.3분 시나리오가 **벽시계 2시간**이 된다. 반복 검증이 불가능하므로 `tools/patrol_viz/`로 논리를 검증하고
여기는 최종 확인용으로 쓰는 이원화가 현재 유일한 실행 가능안이다.
개선하려면 가구 collision을 단순 박스로 바꾸거나 `<collision>`을 빼는 게 효과가 클 것으로 본다.

**2. small_house 카메라 미검증 (작업 0-0)** — 카메라·YOLO 검증 실적은 전부 `turtlebot3_world` 기준이다.
small_house 전환 후 비대화형 세션에서 양 경로가 막혔다:
헤드리스 오프스크린은 100초 넘게 프레임 0장(`/dev/dri` 부재 추정), GUI는 `qt.qpa.xcb: could not connect to display :0`.
저장소는 이를 **비대화형 세션(WSLg 소켓 접근 불가)의 제약으로 추정**하며 대화형 재검증을 못 했다고 명시한다.
**사람이 자기 WSL 터미널에서 직접 돌려 확인하는 것이 Phase 0의 사실상 첫 작업이다.**

## 해결된 함정 (재발 방지)

- **`cmd_vel` 타입 불일치** — 스톡 브리지 yaml은 `TwistStamped`, Nav2 `collision_monitor`는 `Twist` 발행 →
  ROS2가 별개 토픽으로 취급해 **로봇이 영영 안 움직였다.** `waffle_bridge_fixed.yaml`로 `Twist` 통일.
- **RViz2 Map 디스플레이 미동작** — `indexed_8bit_image` 셰이더 링크 실패(RViz2 자체 버그).
  **Nav2 costmap 시각화도 같은 이유로 실패할 것.**
- **RViz2 ↔ Gazebo 렌더링 요구가 반대** — Gazebo는 `GALLIUM_DRIVER=d3d12`(하드웨어),
  RViz2는 `LIBGL_ALWAYS_SOFTWARE=1`(소프트웨어).
- **WSL2 GPU** — `/dev/dri`가 아니라 **`/dev/dxg`** 를 쓴다. `GALLIUM_DRIVER=d3d12` +
  `LD_LIBRARY_PATH=/usr/lib/wsl/lib`로 하드웨어 가속이 살아난다.
- **numpy ABI 충돌** — `ultralytics`가 numpy 2.x를 깔면 apt matplotlib과 충돌. `numpy==1.26.4` 고정.

## 실물 LIMO 이행 시 없는 것

이 디렉터리에는 **실로봇용 bringup이 없다** (`amcl`·`map_server`·`limo_base`·`ydlidar` 참조 0건).
`sim_bringup.launch.py`는 Gazebo에 완전히 묶여 있다 — gz_sim, ros_gz_bridge, turtlebot3 스폰, `use_sim_time:=true`.
실로봇용 `real_bringup.launch.py`를 별도로 작성해야 한다.
