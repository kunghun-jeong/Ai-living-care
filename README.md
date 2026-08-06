# AI Living Care

독거 어르신 돌봄 로봇. **"할머니 괜찮은지 확인해 줘"** 한 마디로 로봇이 집 안을
순찰하고, 사람을 찾고, 상태를 판단해 보고하는 시스템.

Worker AI agent(LLM)가 **MCP**를 통해 Perception / Reasoning / Action 세 모듈의
도구를 호출하는 구조다. LLM이 하는 일은 두 가지뿐 — **①어디부터 갈지 정하기**,
**②찾은 사람의 사진을 보고 상태 판단하기**. 나머지(순찰 루프, 1Hz 촬영, 경로 추종)는
전부 코드가 한다.

```
사용자: "할머니 괜찮은지 확인해 줘"
   │
   ├─ ① LLM: 순찰 순서 결정
   │
   ├─ 코드 루프 (LLM 개입 없음)
   │     plan_path → 이동 → 1Hz 사람 스캔 → 도착 시 look_around
   │     발견하면 그 프레임을 붙잡고 정지
   │
   └─ ② LLM: 크롭 사진 1장을 보고 "괜찮으신지" 판단 → 보고
```

핵심 설계: **이미지는 LLM을 통과하지 않는다.** 1Hz 스캔 결과는 사람 유무(O/X)와
`frame_id`만 오가고, 실제 픽셀은 발견 시점에 크롭 1장만 올라간다. 컨텍스트 보호와
비용 절감이 동시에 된다.

---

## 저장소 구성

| 디렉터리 | 내용 |
|---|---|
| **`limo-MCP/`** | 본 프로젝트. MCP 서버 + Worker 함수(Action/Reasoning/Perception) + Gazebo·Nav2 브링업 |
| **`limo-patrol-viz/`** | 순찰 로직 검증·시연 도구. Gazebo·Nav2·YOLO 없이 RViz2에서 로봇을 움직이고 커버리지를 잰다 |

개발 경위와 함정은 [`limo-MCP/SESSION_HANDOFF.md`](limo-MCP/SESSION_HANDOFF.md)에
누적 기록한다. 새로 합류하면 그 문서부터 읽는 게 빠르다.

---

## 빠른 시작

### 순찰 로직만 먼저 보기 (가벼움, 권장)

Gazebo도 Nav2도 필요 없다. RViz2와 Python만 있으면 된다.

```bash
cd limo-patrol-viz
./run_coverage.sh     # GUI 없이 커버리지 수치 + patrol_sim.png
./run_patrol.sh       # RViz2에서 로봇이 실제로 순찰하는 것 + 카메라 스트리밍
```

현재 결과: **경로점 7개 · 6.3분 · 커버리지 93.6% · 2m² 이상 사각지대 0개**

### 전체 시뮬레이션 (Gazebo + Nav2)

```bash
# 대용량 메시는 저장소에 없다. 먼저 받는다 (약 55MB)
./limo-MCP/Simulation/fetch_meshes.sh

source /opt/ros/jazzy/setup.bash
ros2 launch limo-MCP/Simulation/sim_bringup.launch.py
```

필요 패키지: `ros-jazzy-navigation2 ros-jazzy-nav2-bringup ros-jazzy-turtlebot3-gazebo
ros-jazzy-slam-toolbox ros-jazzy-ros-gz`

---

## 저장소에 없는 것

용량·라이선스 때문에 제외했다. 스크립트나 최초 실행 시 자동으로 받는다.

| 자산 | 크기 | 받는 법 |
|---|---|---|
| AWS 가구 메시·텍스처 | ~55 MB | `limo-MCP/Simulation/fetch_meshes.sh` |
| `yolov8n.pt` | 6.3 MB | ultralytics가 최초 추론 시 자동 다운로드 (AGPL-3.0) |

월드 파일과 모든 `model.sdf`는 **우리가 수정한 상태 그대로 포함**되어 있다
(ShoeRack `izz` 오타, furniture 56종 `<static>true</static>`). 메시만 원본에서 받으면 된다.

---

## 환경 관련해서 알아둘 것 (WSL2에서 실제로 겪은 것들)

### WSL2 GPU — `/dev/dri`가 없어도 하드웨어 가속이 된다

WSL2는 `/dev/dri`가 아니라 **`/dev/dxg`**를 쓴다. Mesa가 기본으로 llvmpipe를 고를 뿐이다.

```bash
export GALLIUM_DRIVER=d3d12
export LD_LIBRARY_PATH=/usr/lib/wsl/lib:$LD_LIBRARY_PATH
glxinfo -B | grep "OpenGL renderer"
#  -> D3D12 (Intel(R) Arc(TM) Graphics),  OpenGL 4.6
```

이 설정에서 **Gazebo Harmonic 카메라 센서가 640×480 / 10Hz**로 나온다.
`SESSION_HANDOFF.md`에 "`/dev/dri`가 없어 EGL 오프스크린 불가"로 적힌 진단은
이 발견으로 정정된다.

### RViz2는 반대로 소프트웨어 렌더링이 필요하다

RViz2의 Ogre는 d3d12 경로에서 `D3D12: Removing Device`로 3D 뷰가 검게 죽는다.
`LIBGL_ALWAYS_SOFTWARE=1`로 우회한다 (`run_patrol.sh`가 자동 설정).

### RViz2 Map 디스플레이는 이 Mesa에서 동작하지 않는다

`indexed_8bit_image` 셰이더 링크 실패 (RViz2 자체 버그). 그래서 `limo-patrol-viz`는
`OccupancyGrid` 대신 벽/바닥을 `CUBE_LIST` 마커로 직접 그린다.
**Nav2 costmap 시각화도 같은 이유로 실패할 것**이니 미리 알아두자.

### Gazebo small_house.world는 RTF 0.04~0.06

로봇도 렌더링도 없이 headless로 돌려도 그렇다 (실시간의 1/20~1/26).
6분짜리 시나리오가 벽시계로 2시간이 된다. 개선하려면 가구 collision 메시를
단순 박스로 바꾸거나 `<collision>`을 빼는 게 효과가 클 것으로 본다.
**그 전까지는 `limo-patrol-viz`로 반복 검증하고 Gazebo는 최종 확인용으로 쓰는 게 낫다.**

---

## 남은 과제

- [ ] Gazebo RTF 개선 (가구 collision 단순화)
- [ ] `CAM_RANGE` 실측 — YOLO가 사람을 몇 m까지 안정적으로 잡는지. 커버리지 93.6%가
      이 값에 크게 좌우된다
- [ ] **수직 FOV 반영** — 현재 커버리지 계산은 2D 가정이라, 4m 거리 바닥에 누운 사람이
      화면 아래로 벗어나는 경우를 못 잡는다. 쓰러진 상황이 가장 위험한데 그 부분이 미검증
- [ ] 실제 LIMO 모델로 교체 — URDF는 이미 변환돼 있고(`limo-patrol-viz/limo/limo.urdf`),
      가제보 플러그인 3블록만 Harmonic 문법으로 새로 쓰면 된다
- [ ] YOLO 오탐 검증 — 벽의 액자 속 인물을 사람으로 잡는지 (small_house에 액자가 있다)
- [ ] 전 구역 순회 후에도 못 찾았을 때의 처리 (보호자 알림?)

## 출처

- 월드/맵: [aws-robotics/aws-robomaker-small-house-world](https://github.com/aws-robotics/aws-robomaker-small-house-world) (Apache-2.0, 아카이브됨)
- LIMO 로봇 기술서: [WeGo-Robotics/limo_gazebo](https://github.com/WeGo-Robotics/limo_gazebo)
