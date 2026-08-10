# A2A Server + Agent Executor (IF-4 Worker 측 종단점)

> **역할** IF-4 Worker 측 종단점 + Agent Executor
> **상태** Phase 0 · 동작 — **L4 tool 만 노출**, L2 를 받는 층이 없다 · 갭 `G-3`
> **읽을 절** spec **§6.4** · **§6.5** — 그 외 절은 열지 않는다
> **정본** 구조 `SOT.md` · tool 시그니처는 **코드** · spec §6

**파일**: `MCP_server.py` — `LimoGatewayNode` + MCP tool. stdio 트랜스포트.
바인딩 정의는 `interfaces/if04_secure_a2a_channel/`에 있다.

> **배치 근거 (D-9)**: `docs/context/AI-Care_A2A_Core_Context(2).md` §4가 **A2A Server와 Agent Executor를
> Worker AI Agent 레벨**에 배정한다. 스펙 §10.1도 `MCP_server.py`를 "Worker AI Core / A2A 종단점"으로 매핑.
> **최상위 `a2a/` 디렉터리는 두 문서 어디에도 근거가 없어 폐기했다.**


## 구현 위치 (D-14)

원본 보존 원칙에 따라 실제 코드는 **`worker_ai_agent/limo-MCP/MCP_server/MCP_server.py`** 에 있다.
이 디렉터리는 **규범(설계·인터페이스·갭)** 을 보유하고, 코드는 두지 않는다.

**구현을 고치기 전에 이 문서의 갭·주의사항을 먼저 읽을 것.**

## 현재 노출된 tool 12종 (전부 L4)

| tool | 계층 | Phase 0 처리 |
|---|---|---|
| `plan_and_navigate`·`navigate_waypoints`·`cancel` | L4 Action | Nav2 경유 — Nav2 미기동 환경에서는 `pathplanning`+`moving_path`가 대안 |
| `resolve_location` | L4 Reasoning | KG(`manager_ai_agent/knowledge_graph/`)를 **IF-1 없이 직접 import** — 임시 배선, 근거는 `docs/decisions/2026-08-10-worker-side-kg-lookup-phase0.md` |
| `pathplanning` | L4 Reasoning | **Nav2·Gazebo 불필요** — `tools/limo-patrol-viz/maps/map.pgm` 위에서 A*로 직접 계산 (`patrol_sim.py`와 같은 알고리즘). 근거: `docs/decisions/2026-08-10-astar-kinematic-sim.md` |
| `moving_path`·`get_path_status`·`cancel_path` | L4 Action | **Nav2·Gazebo·실물 오도메트리 불필요** — 운동학만 소프트웨어로 적분하는 시뮬레이션(`patrol_sim.py`의 `advance_to`와 동일 모델). `LimoGatewayNode.viz`가 매 틱 RViz2로 스트리밍(`tools/limo-patrol-viz/patrol.rviz`로 확인) |
| `send_ir_signal` | L4 Action | **(스텁)** 로그만 남긴다 — 실제 IR 하드웨어 미구현 |
| `get_camera_snapshot`·`detect_objects` | L4 Perception/Reasoning | 유지 |
| `get_status` | L4 상태 | `get_task_report`로 승격 (task_id 상관 추가) |
| — | **L2** | **`execute_policy` 신설** ← 0-5 |
| — | L4 | **person-scan 5종 노출** ← 0-9 (G-3) |

## Phase 0 최소 A2A 집합

```
server/discover                  → 프로토콜 버전·능력·정체성 (= Agent Card 코어)
tools/list                       → 공개 Skill 목록
resources/read agentcard://self  → 확장 Agent Card
tools/call execute_policy        → L2 수락. {task_id, accepted, reject_reason?}
tools/call get_task_report       → 상태·최종 Report
tools/call cancel_task           → 취소
```

## ⚠️ MCP SDK 버전 (U-1)

`from mcp.server.mcpserver import Image, MCPServer` — 구 `fastmcp.FastMCP`가 아닌 새 이름이지만
**이것만으로 최신 SDK라고 판단할 수 없다.** 반대 증거:

- `limo-MCP/Scenarios/*.py`가 **`await session.initialize()`를 호출한다** — 2026-07-28이 제거했다는 핸드셰이크가 살아 있다
- `requirements.txt`가 `mcp[cli]`로 **버전 미고정**
- 이 import는 limo_slam에서 **그대로 복사한 패턴**이라 의도적 채택 흔적이 아니다

**작업 0-0에서 설치된 `mcp` 패키지 버전을 직접 확인할 것.**

## 주의

**stdout을 오염시키지 말 것.** stdio 트랜스포트는 stdout을 JSON-RPC 전용으로 쓴다.
YOLO 가중치 다운로드 진행표시줄이 실제로 프로토콜을 깼고, `contextlib.redirect_stdout(sys.stderr)`로
감싼 warm-up으로 해결했다 — **그 코드를 제거하지 말 것.**

`sys.path`로 `worker_ai_agent/{perception,reasoning,action}`을 추가해 모듈명(`Perceptions`/`Reasonings`/`Actions`)
그대로 import한다. 패키지화는 Phase 1 정리 항목이다.
