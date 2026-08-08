# AI Living Care

> **팀에 합류하셨다면 → [팀 온보딩](#팀-온보딩--이-한-장이면-시작한다).** 그 한 장이면 일을 시작할 수 있습니다.
> 이 문서의 나머지는 시스템이 무엇을 하는지 설명합니다.

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

---

## 팀 온보딩 — 이 한 장이면 시작한다

> **규칙은 안내지 통제가 아니다.** 커밋을 막는 것은 넷뿐이고 전부 「한 줄 빠뜨림」이다.
> 나머지는 PR 에서 알리거나, 한 줄 말하고 그냥 통과시킨다.

### 1. 최초 1회

```bash
make hooks     # make 가 없으면: git config core.hooksPath .githooks && chmod +x .githooks/*
git config --global user.email "<GitHub 계정에 인증된 주소>"
```

두 번째 줄을 빠뜨리면 **커밋이 아무에게도 귀속되지 않는다** — 이 저장소에서 실제로 28개가 그랬다.
자세한 건 [`CONTRIBUTING.md`](CONTRIBUTING.md) 「커밋 신원」.

### 2. 세션마다 한 번 — 일 시작 전에

```bash
make status    # make 가 없으면: python anchor.py --status
```

한 화면에 다섯이 나온다 — **미해소 안전 결함 · 전 영역 상태 · 최근 커밋 · 최근 결정 · 커밋 안 된 변경.**
매 세션 자동으로 열리는 문서들은 **남이 일해도 변하지 않는다.** 갱신을 보는 창구는 여기뿐이다.

### 3. 일할 때 — 다섯 줄

1. **건드릴 디렉터리의 `CLAUDE.md` 만 읽는다.** 무엇을 열지는 [`docs/doc-map.md`](docs/doc-map.md) §1 이 정한다.
2. **설계 정본을 통독하지 않는다** — 그 헤더의 `읽을 절` 이 지목한 절만 연다.
3. 파일·디렉터리가 생기면 **그 자리 `CLAUDE.md` 에 한 줄.** 새 디렉터리엔 `CLAUDE.md` 를 만든다.
4. 결정은 [`docs/decisions/`](docs/decisions/) 에 **파일 하나** — 표에 줄을 넣지 않는다.
   그 파일의 `정본 반영` 줄에 **따라 고쳐야 할 문서**를 적는다. CI 가 실제로 고쳐졌는지 본다.
5. **`상태` 줄에 「지금 무엇으로」를 넣는다.** 논문·표준 담당자는 그 한 줄로 구현 절을 쓴다.

```
✅  Phase 1 · 구현 중 · LM encoder(BERT-base, LSTM 에서 전환) · 작업 0-5
❌  Phase 1 · 진행 중
```

### 4. 병렬로 일할 때 — 부딪히지 않는 법

- **자기 디렉터리 안에서는 마음껏 병렬로.** 6인 동시 작업 병합 실측에서 충돌 0.
- 결정·안전 결함은 **각자 파일 하나**라 절대 부딪히지 않는다.
- **부딪히는 곳은 하나뿐 — 같은 부모 밑에 둘이 동시에 새 디렉터리를 만들 때.** 순서를 정한다.
  (부딪혀도 git 이 멈추고, 잘못 풀면 커밋이 막힌다. 조용히 사라지지 않는다.)

### 5. ⛔ 남의 트리

```
worker_ai_agent/limo-MCP/**      코드는 담당 연구원 소유
tools/limo-patrol-viz/**         코드는 담당 연구원 소유
```

**읽고 결함만 남긴다.** 안전 경로(정지·취소 / 사람 판정 / 프레임 신선도 / 세션 키)면
[`docs/safety/`](docs/safety/) 에 파일 하나 + 귀속 컴포넌트의 `상태` 줄에 같은 ID,
그 외는 [`docs/status-defects.md`](docs/status-defects.md). 훅이 커밋 때 알려준다(막지는 않는다).
담당자 본인이면 `OWNER=1`.

### 6. 브랜치

`master` 가 협업자가 일하는 곳이다. **작은 변경은 바로 커밋한다.** `main` 은 소유자가 승격한다.
같은 영역에 둘이 붙거나 리뷰가 필요하면 `<영역>/<하려는 일>` 로 브랜치를 판다 (base = `master`).

### 7. 그 밖에 열 문서

| 하려는 일 | 열 문서 |
|---|---|
| 무엇을 열지 모르겠다 | [`docs/doc-map.md`](docs/doc-map.md) §1 |
| 작업 절차 전체 | [`docs/harness.md`](docs/harness.md) |
| 브랜치 · PR · 소유 경계 | [`CONTRIBUTING.md`](CONTRIBUTING.md) |
| 지금 무엇이 깨져 있나 | [`docs/status.md`](docs/status.md) |
| 이 사실을 어디에 쓰지 | [`docs/canon.md`](docs/canon.md) |
| 전체 계층 그림 | [`docs/architecture.md`](docs/architecture.md) — ⚠️ IF-4·IF-5 종단점 불일치 (`F-62`) |
| 옛 경로를 찾는 중 | [`MIGRATION.md`](MIGRATION.md) |
| 개발 경위 | [`docs/handoff/`](docs/handoff/) — **참고 원본, 인용하지 않는다** |

---

## 빠른 시작

### 순찰 로직만 먼저 보기 (가벼움, 권장)

Gazebo도 Nav2도 필요 없다. RViz2와 Python만 있으면 된다.

```bash
cd tools/limo-patrol-viz
./run_coverage.sh     # GUI 없이 커버리지 수치 + patrol_sim.png
./run_patrol.sh       # RViz2에서 로봇이 실제로 순찰하는 것 + 카메라 스트리밍
```

현재 결과: **경로점 7개 · 6.3분 · 커버리지 93.6% · 2m² 이상 사각지대 0개**
— **기하 시뮬레이션 결과이지 실측이 아니다.** 한정어를 떼고 인용하지 않는다 (`F-17`).

> 코드·문서를 만질 거라면 위 [팀 온보딩](#팀-온보딩--이-한-장이면-시작한다) 의 「최초 1회」를 먼저 한다.

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
