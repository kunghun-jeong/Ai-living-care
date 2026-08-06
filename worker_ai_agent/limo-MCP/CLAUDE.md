# limo-MCP — LIMO Worker 구현체 (원본 보존)

> **구조 정본**: `SOT.md` · **설계 정본**: `docs/spec/AI-Care_Unified_Architecture_Spec_v0.2.md`
> **상위**: `worker_ai_agent/` · **Phase**: 0 · **구현 상태**: 동작 — 원본 그대로 보존

> **⚠️ 이 디렉터리는 원본을 그대로 보존한다 (D-14).** 내부 구조·파일명·경로를 바꾸지 않는다 (내용 수정은 D-17 범위 — 결정 기록 조건부 허용).
> `github.com/kunghun-jeong/-Ai-living-care` 의 `main/limo-MCP` 와 **내용이 동일**하다.

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
| **G-3** | person-scan API 5종이 MCP tool로 미노출 | `MCP_server/MCP_server.py` |
| **G-4** | `look_around` / patrol 미구현 | `Worker_functions/Actions.py` |
| **G-5** | stale 콜백 가드 없음 | 〃 |

**G-1과 G-2는 시나리오 1의 핵심 경로를 끊는다.** 상세는 `../perception/CLAUDE.md`.

## 주의

- **`Simulation/`의 RTF가 0.04~0.06**이다. 6.3분 시나리오가 벽시계 2시간. 반복 검증은
  `tools/limo-patrol-viz/`로 하고 여기는 최종 확인용으로 쓴다 (U-14).
- **small_house 카메라는 미검증**이다. 검증 실적은 `turtlebot3_world` 기준 (작업 0-0).
- 개발 경위와 함정은 `SESSION_HANDOFF.md`에 누적 기록돼 있다. 새로 합류하면 그것부터 읽을 것.
