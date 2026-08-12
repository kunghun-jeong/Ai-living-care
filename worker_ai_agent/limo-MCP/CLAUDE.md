# limo-MCP — LIMO Worker 구현체 (원본 보존)

> **역할** LIMO Worker 구현체 — MCP 서버 · Worker 함수 · Gazebo 브링업
> **상태** Phase 0 · **동작** · 원본 보존 `D-14` · Nav2 대안으로 A* pathplanning/moving_path 추가(Gazebo 없이 이동 검증 가능)
> **읽을 절** spec **§10.1** · **§10.2**(시뮬 환경) — 그 외 절은 열지 않는다
> **정본** 구조 `SOT.md` · spec §10.1 · ⛔ **코드는 담당 연구원 소유 (D-17)**

> **⚠️ 이 디렉터리는 원본을 그대로 보존한다 (D-14).** 내부 구조·파일명·경로를 바꾸지 않는다 (내용 수정은 D-17 범위 — 결정 기록 조건부 허용).
> 최초 커밋 `27b0f30` 시점과 **더 이상 byte-identical이 아니다** — `Actions.py`·`Reasonings.py`·
> `MCP_server.py` 내용을 고치고 `Worker_functions/Visualization.py`를 새로 추가했다 (2026-08-10,
> D-17 범위 내용 수정). 2026-08-11 에 `Perceptions.py`·`Scenarios/run_scenario.py`·
> `Scenarios/turn_on_air_conditioner.json` 도 고치고 `Scenarios/check_grandma*.json` 을 추가했다.
> 구조·파일명·경로는 그대로다. 근거: `docs/decisions/2026-08-10-astar-kinematic-sim.md`
> · `docs/decisions/2026-08-10-worker-side-kg-lookup-phase0.md`.
> (2026-08-12) `Scenarios/scenario_dsl.py`·`variate_scenario.py`·`validate_variant.py` 추가 —
> `check_grandma.json` 류 시나리오의 변형기/검증기, 원본에 없던 파일. 근거:
> `docs/decisions/2026-08-12-scenario-variator-rules.md`.
> (2026-08-12) `Scenarios/object_bindings.json` 추가 + `check_grandma.json`·
> `check_grandma_bedroom_first.json`·`check_obj_state.json`의 `input.object`를
> 의미적 라벨로, `input.target_class`를 실제 탐지 class 대조용으로 분리. 근거:
> `docs/decisions/2026-08-12-object-target-class-split.md`.
> (2026-08-12) PR 전 정리 — 데모 산출물 `check_obj_state_v1~v5.json` 삭제
> (`variate_scenario.py`로 재생성 가능). 근거:
> `docs/decisions/2026-08-12-pre-pr-cleanup-variator.md`.
> 옛 트리는 `tree/27b0f30/limo-MCP` 에서 볼 수 있다.

## 왜 여기 있는가

`limo-MCP`는 프레임워크 컴포넌트가 아니라 **LIMO라는 특정 디바이스의 Worker 실현체**다.
Worker AI Agent의 구현이므로 `worker_ai_agent/` 안에 둔다. 다중 Worker로 확장하면 형제로 늘어난다:

```
worker_ai_agent/
  limo-MCP/          ← LIMO (현재 유일)
  refrigerator/      ← 향후
  smart_tv/          ← 향후
```

## 내부 구조 (원본)

| 경로 | SOT 컴포넌트 대응 |
|---|---|
| `Worker_functions/Perceptions.py` | Perception Function (PF) → `../perception/` |
| `Worker_functions/Reasonings.py` | Reasoning Function (RF) → `../reasoning/` |
| `Worker_functions/Actions.py` | Action Function (AF) → `../action/` |
| `Worker_functions/Visualization.py` | (신규, 2026-08-10) RViz2 실시간 시각화 — `patrol_viz.py`와 같은 토픽 재사용, 원본 목록엔 없던 파일 |
| `Worker_functions/Perceptions.py` | Perception Function (PF). (2026-08-11) `SimCameraPerception` 추가 — `SIM_PERSON` 환경변수가 있을 때만 동작하는 기하 카메라 시뮬 |
| `MCP_server/MCP_server.py` | A2A Server + Agent Executor → `../mcp_server/` |
| `Simulation/` | 시뮬레이션 (비컴포넌트) |
| `Scenarios/` | 검증 클라이언트 (비컴포넌트) |
| `requirements.txt` | 의존성 |
| `SESSION_HANDOFF.md` | 개발 기록 |

각 컴포넌트 디렉터리(`../perception/` 등)의 `CLAUDE.md`에 **설계 규범과 알려진 갭**이 있다.
**구현을 고칠 때는 그 문서를 먼저 읽을 것.**

## 실행 (원본 그대로)

```bash
source /opt/ros/jazzy/setup.bash
./Simulation/fetch_meshes.sh                      # 최초 1회, AWS 메시 ~55MB
ros2 launch Simulation/sim_bringup.launch.py
python3 Scenarios/send_goal.py 1.0 0.0            # 이 디렉터리에서 실행
python3 Scenarios/capture_and_detect.py out.jpg
```

## 알려진 크리티컬 갭

| ID | 갭 | 파일 |
|---|---|---|
| **G-1** | 프레임 pinning 부재 — 최신 1장만 캐시, 과거 `frame_id` 조회 불가 | `Worker_functions/Perceptions.py` |
| **G-2** | `pose`가 항상 `None` | 〃 |
| ~~G-3~~ | ~~person-scan API 5종이 MCP tool로 미노출~~ → **부분 해소 (2026-08-11)**: `check_object_state` 노출. `start/wait/status/stop_person_scan` 4종은 여전히 미노출 (시나리오가 `detect_objects` 폴링으로 대체) | `MCP_server/MCP_server.py` |
| ~~G-4~~ | ~~`look_around` / patrol 미구현~~ → **해소 (2026-08-11)**: `look_around` · `is_looking_around` · `interrupt_look_around` 구현·노출. patrol 은 코드가 아니라 시나리오 JSON 의 `branch` 로 표현한다 | `Worker_functions/Actions.py` |
| **G-5** | stale 콜백 가드 없음 | 〃 |

**G-1과 G-2는 시나리오 1의 핵심 경로를 끊는다.** 상세는 `../perception/CLAUDE.md`.

## 주의

- **`Simulation/`의 RTF가 0.04~0.06**이다. 6.3분 시나리오가 벽시계 2시간. 반복 검증은
  `tools/limo-patrol-viz/`로 하고 여기는 최종 확인용으로 쓴다 (U-14).
- **small_house 카메라는 미검증**이다. 검증 실적은 `turtlebot3_world` 기준 (작업 0-0).
- 개발 경위와 함정은 `SESSION_HANDOFF.md`에 누적 기록돼 있다. 새로 합류하면 그것부터 읽을 것.
