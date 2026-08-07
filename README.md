# AI Living Care

독거 어르신 돌봄 로봇. **"할머니 괜찮은지 확인해 줘"** 한 마디로 로봇이 집 안을
순찰하고, 사람을 찾고, 상태를 판단해 보고하는 시스템.

전체 구조는 **Manager AI Agent → A2A → Worker AI Agent** 폐루프다. 계층·인터페이스·
정책 계층(L0~L4)의 정의는 설계 정본 `docs/spec/AI-Care_Unified_Architecture_Spec_v0.2.md`
§1~§6 에 있고, 그림은 [`docs/architecture.md`](docs/architecture.md) 에 있다.

아래는 그중 **Worker 측 시나리오 1**(현재 코드가 실제로 하는 일)이다. Worker 안에서
LLM이 하는 일은 두 가지뿐 — **①어디부터 갈지 정하기**, **②찾은 사람의 사진을 보고
상태 판단하기**. 나머지(순찰 루프, 1Hz 촬영, 경로 추종)는 전부 코드가 한다.

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
| `manager_ai_agent/` | Manager 측 컴포넌트 (MAC · MAA · MAMS · KG · IAD · A2A Client) — 규범만, 코드 미착수 |
| `worker_ai_agent/` | Worker 측 컴포넌트 + **`limo-MCP/`** — MCP 서버, Worker 함수, Gazebo·Nav2 브링업 |
| `interfaces/` | IF-1 ~ IF-8 인터페이스 카탈로그 |
| `contracts/` | L1~L3 · Report 페이로드 스키마 (미작성) |
| `tools/` | **`limo-patrol-viz/`** — Gazebo·Nav2·YOLO 없이 순찰 로직을 검증하고 커버리지를 잰다 |
| `docs/` | 설계 정본 · 상태 · 하네스 · 결정 기록 |

> `limo-MCP/` 와 `limo-patrol-viz/` 는 **원본을 그대로 보존**한다 (D-14). 각 트리의 코드는
> 담당 연구원 소유이며, 구조·파일명·경로를 바꾸지 않는다.

### 새로 합류했다면

[`CLAUDE.md`](CLAUDE.md) 하나만 읽는다. 나머지는 거기서 라우팅된다.

문서는 세 계층이다 — **`@` 표시는 매 세션 자동 로딩**(루트 + doc-map + harness + status),
**무표는 gateway 뒤 lazy**(필요할 때만 연다). 설계 정본은 **통독하지 않는다** —
각 컴포넌트 `CLAUDE.md` 헤더가 지목한 절만 읽는다. **자동 로딩 실측치는 `make status` 맨 아래에 나온다**
— 문서에 숫자를 적지 않는다. `@` 는 재귀 import 라(최대 5홉) 루트 밖에서 쓰면 눈덩이가 된다.

- **브랜치·PR·소유 경계**: [`CONTRIBUTING.md`](CONTRIBUTING.md)
- 작업 시작점(하려는 일 → 열 문서): [`docs/doc-map.md`](docs/doc-map.md)
- 작업 절차: [`docs/harness.md`](docs/harness.md)
- 지금 무엇이 깨져 있는지: [`docs/status.md`](docs/status.md)
- 옛 경로를 찾는 중이라면: [`MIGRATION.md`](MIGRATION.md)
- 전체 계층 그림: [`docs/architecture.md`](docs/architecture.md)
  — ⚠️ 그림의 IF-4·IF-5 종단점에 알려진 불일치가 있다 (F-62, `docs/status.md`)
- 개발 경위: [`docs/handoff/`](docs/handoff/) — **참고 원본, 정본 아님**

---

## 빠른 시작

### 순찰 로직만 먼저 보기 (가벼움, 권장)

Gazebo도 Nav2도 필요 없다. RViz2와 Python만 있으면 된다.

```bash
# 최초 1회 — 커밋할 때 앵커 검사가 자동으로 돈다
make hooks                                    # make 가 없으면 아래 한 줄로 대체
# git config core.hooksPath .githooks && chmod +x .githooks/*

cd tools/limo-patrol-viz
./run_coverage.sh     # GUI 없이 커버리지 수치 + patrol_sim.png
./run_patrol.sh       # RViz2에서 로봇이 실제로 순찰하는 것 + 카메라 스트리밍
```

현재 결과: **경로점 7개 · 6.3분 · 커버리지 93.6% · 2m² 이상 사각지대 0개**

### 전체 시뮬레이션 (Gazebo + Nav2)

```bash
# 대용량 메시는 저장소에 없다. 먼저 받는다 (약 55MB)
./worker_ai_agent/limo-MCP/Simulation/fetch_meshes.sh

source /opt/ros/jazzy/setup.bash
cd worker_ai_agent/limo-MCP && ros2 launch Simulation/sim_bringup.launch.py
```

필요 패키지: `ros-jazzy-navigation2 ros-jazzy-nav2-bringup ros-jazzy-turtlebot3-gazebo
ros-jazzy-slam-toolbox ros-jazzy-ros-gz`

---

## 저장소에 없는 것

용량·라이선스 때문에 제외했다. 스크립트나 최초 실행 시 자동으로 받는다.

| 자산 | 크기 | 받는 법 |
|---|---|---|
| AWS 가구 메시·텍스처 | ~55 MB | `worker_ai_agent/limo-MCP/Simulation/fetch_meshes.sh` |
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
`docs/handoff/limo-MCP_SESSION_HANDOFF.md`에 "`/dev/dri`가 없어 EGL 오프스크린 불가"로 적힌 진단은
이 발견으로 정정된다.

### RViz2는 반대로 소프트웨어 렌더링이 필요하다

RViz2의 Ogre는 d3d12 경로에서 `D3D12: Removing Device`로 3D 뷰가 검게 죽는다.
`LIBGL_ALWAYS_SOFTWARE=1`로 우회한다 (`run_patrol.sh`가 자동 설정).

### RViz2 Map 디스플레이는 이 Mesa에서 동작하지 않는다

`indexed_8bit_image` 셰이더 링크 실패 (RViz2 자체 버그). 그래서 `tools/limo-patrol-viz`는
`OccupancyGrid` 대신 벽/바닥을 `CUBE_LIST` 마커로 직접 그린다.
**Nav2 costmap 시각화도 같은 이유로 실패할 것**이니 미리 알아두자.

### Gazebo small_house.world는 RTF 0.04~0.06

로봇도 렌더링도 없이 headless로 돌려도 그렇다 (실시간의 1/20~1/26).
6분짜리 시나리오가 벽시계로 2시간이 된다. 개선하려면 가구 collision 메시를
단순 박스로 바꾸거나 `<collision>`을 빼는 게 효과가 클 것으로 본다.
**그 전까지는 `tools/limo-patrol-viz`로 반복 검증하고 Gazebo는 최종 확인용으로 쓰는 게 낫다.**

---

## 남은 과제

- [ ] Gazebo RTF 개선 (가구 collision 단순화)
- [ ] `CAM_RANGE` 실측 — YOLO가 사람을 몇 m까지 안정적으로 잡는지. 커버리지 93.6%가
      이 값에 크게 좌우된다
- [ ] **수직 FOV 반영** — 현재 커버리지 계산은 2D 가정이라, 4m 거리 바닥에 누운 사람이
      화면 아래로 벗어나는 경우를 못 잡는다. 쓰러진 상황이 가장 위험한데 그 부분이 미검증
- [ ] 실제 LIMO 모델로 교체 — URDF는 변환돼 있으나(`tools/limo-patrol-viz/limo/limo.urdf`)
      **가제보 플러그인은 0개다.** `make_urdf.sh`가 의도적으로 제거했고 남은 3블록은 색상
      지정이다. 차동 구동·센서 플러그인을 새로 써야 하므로 일정 산정 시 주의 (F-16)
- [ ] YOLO 오탐 검증 — 벽의 액자 속 인물을 사람으로 잡는지 (small_house에 액자가 있다)
- [ ] 전 구역 순회 후에도 못 찾았을 때의 처리 (보호자 알림?)

## 출처

- 월드/맵: [aws-robotics/aws-robomaker-small-house-world](https://github.com/aws-robotics/aws-robomaker-small-house-world) (Apache-2.0, 아카이브됨)
- LIMO 로봇 기술서: [WeGo-Robotics/limo_gazebo](https://github.com/WeGo-Robotics/limo_gazebo)
