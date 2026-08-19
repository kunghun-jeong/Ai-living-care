# A2A Server + Agent Executor (IF-4 Worker 측 종단점)

> **역할** IF-4 Worker 측 종단점 + Agent Executor
> **상태** Phase 0 · 동작 — **L4 tool 만 노출**, L2 를 받는 층이 없다 · 갭 `G-3` ·
> **표준 A2A 실험 코드 있음(`a2a_server.py`+`worker_mcp_server.py`, 실험·미승인, D-21)**
> **읽을 절** spec **§6.4** · **§6.5** — 그 외 절은 열지 않는다
> **정본** 구조 `SOT.md` · tool 시그니처는 **코드** · spec §6

**파일**: `MCP_server.py` — `LimoGatewayNode` + MCP tool. stdio 트랜스포트.
바인딩 정의는 `interfaces/if04_secure_a2a_channel/`에 있다.

> **배치 근거 (D-9)**: `docs/context/AI-Care_A2A_Core_Context(2).md` §4가 **A2A Server와 Agent Executor를
> Worker AI Agent 레벨**에 배정한다. 스펙 §10.1도 `MCP_server.py`를 "Worker AI Core / A2A 종단점"으로 매핑.
> **최상위 `a2a/` 디렉터리는 두 문서 어디에도 근거가 없어 폐기했다.**


## 구현 위치 (D-14)

원본 보존 원칙에 따라 실제 코드는 **`worker_ai_agent/limo-MCP/MCP_server/MCP_server.py`** 에 있다.
이 디렉터리는 규범을 보유한다 — `MCP_server.py`는 손대지 않는다.

**구현을 고치기 전에 이 문서의 갭·주의사항을 먼저 읽을 것.**

## 실험 코드 — `worker_mcp_server.py` + `a2a_server.py` (실험 · 미승인 · 상급자 승인 대기)

`MCP_server.py`(위, 정본·원본 보존)는 손대지 않는다. 대신 **별도 프로세스** 둘을 새로 뒀다 —
`docs/decisions/2026-08-19-worker-functions-and-a2a-store.md` 참조.

### `worker_mcp_server.py` — 두 번째 stdio MCP 서버

`action/nav2_move.py`·`perception/camera_stream.py`·`reasoning/yolo_reasoning.py`(각 디렉터리의
새 wrapper — `worker_functions.py` 하나가 아니라 셋으로 나눔)를 `sys.path`로 가져와
`ActionModule`/`PerceptionModule`/`ReasoningModule` 인스턴스와 함께 호출한다. 노드 이름
`limo_worker_functions_gateway`, 서버 이름 `"limo-worker-fn"` — 둘 다 원본(`limo_mcp_gateway`·
`"limo-worker"`)과 달라 **`MCP_server.py`와 동시에 띄울 수 있다.** `@mcp.tool()`로
`nav2_move`·`nav2_move_waypoints`·`nav2_cancel`·`nav2_status`·`camera_stream`·`yolo_reasoning`을
노출한다 — 위 6종과는 별개 tool 집합이다(anchor.py A2는 `MCP_server.py`만 검사하므로 이 6개는
자동 대조 대상이 아니다).

### `a2a_server.py` — 표준 A2A HTTP 서버, 수신+저장만

`manager_ai_agent/a2a_client/dev_mock_worker_agent.py`(가짜 스텁)의 **실제 대체품**이다.
`manager_ai_agent/a2a_client/CLAUDE.md`가 공개한 "Worker A2A 서버가 맞춰야 할 계약"
(`message/send`·`tasks/get`·`tasks/cancel`, JSON-RPC 2.0, 포트 9000)을 그대로 구현한다.
**스코프는 수신 즉시 `task_store.py`로 저장하는 것까지다 — L2→L3 번역·실행(`execute_policy`)은
하지 않는다**(위 갭 `G-3`, 작업 0-5·0-6, WAC의 몫). `message/send`는 저장 성공 시 바로
`completed`로 응답한다 — `a2a_client.py`가 `state == "completed"`만 성공으로 보기 때문이고,
실제로는 미실행이라는 사실은 응답의 `artifacts` 텍스트에 남긴다.

`rclpy`·`ultralytics`를 import하지 않는다 — ROS2/WSL 없이 Windows에서 단독으로 뜬다
(`worker_mcp_server.py`와 별개 프로세스인 이유).

### `task_store.py` · `data/`

`a2a_server.py`가 받은 task를 `data/{task_id}.json` 파일로 원자적 저장한다(task_id별
`RLock`). `data/`는 런타임 전용 — `.gitignore` 등재, 커밋 안 함, 자기 `CLAUDE.md` 보유(SP-5).

## 현재 노출된 tool 6종 (전부 L4)

| tool | 계층 | Phase 0 처리 |
|---|---|---|
| `plan_and_navigate`·`navigate_waypoints`·`cancel` | L4 Action | 유지. `execute_policy` 내부에서 호출 |
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

`MCP_server.py`는 `sys.path`로 `limo-MCP/Worker_functions`를 추가해 모듈명(`Perceptions`/`Reasonings`/`Actions`)
그대로 import한다. 패키지화는 Phase 1 정리 항목이다 — 아직 이뤄지지 않았다.
`worker_mcp_server.py`(위 실험 코드)도 같은 `Actions`/`Perceptions`/`Reasonings`를 그대로 가져오되,
**추가로** `worker_ai_agent/{action,perception,reasoning}`도 `sys.path`에 얹어 `nav2_move`/
`camera_stream`/`yolo_reasoning` wrapper를 가져온다 — `Actions.py` 등 원본 자체를 옮긴 게 아니다.
