# A2A Server + Agent Executor (IF-4 Worker 측 종단점)

> **구조 정본**: `SOT.md` · **설계 정본**: `docs/spec/AI-Care_Unified_Architecture_Spec_v0.2.md`
> **상위**: `worker_ai_agent/` · **Phase**: 0 · **구현 상태**: 동작 — L4만 노출

**파일**: `MCP_server.py` — `LimoGatewayNode` + MCP tool. stdio 트랜스포트.
바인딩 정의는 `interfaces/if04_secure_a2a_channel/`에 있다.

> **배치 근거 (D-9)**: `docs/context/AI-Care_A2A_Core_Context(2).md` §4가 **A2A Server와 Agent Executor를
> Worker AI Agent 레벨**에 배정한다. 스펙 §10.1도 `MCP_server.py`를 "Worker AI Core / A2A 종단점"으로 매핑.
> **최상위 `a2a/` 디렉터리는 두 문서 어디에도 근거가 없어 폐기했다.**


## 구현 위치 (D-14)

원본 보존 원칙에 따라 실제 코드는 **`worker_ai_agent/limo-MCP/MCP_server/MCP_server.py`** 에 있다.
이 디렉터리는 **규범(설계·인터페이스·갭)** 을 보유하고, 코드는 두지 않는다.

**구현을 고치기 전에 이 문서의 갭·주의사항을 먼저 읽을 것.**

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

`sys.path`로 `worker_ai_agent/{perception,reasoning,action}`을 추가해 모듈명(`Perceptions`/`Reasonings`/`Actions`)
그대로 import한다. 패키지화는 Phase 1 정리 항목이다.
