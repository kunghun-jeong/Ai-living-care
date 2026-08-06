# A2A Server (Worker 측 종단점)

> **SOT**: `docs/spec/AI-Care_Unified_Architecture_Spec_v0.2.md`
> **상위**: `a2a/` · **Phase**: 0 · **구현 상태**: 동작 — L4만 노출

**파일**: `MCP_server.py` — `LimoGatewayNode` + MCP tool. stdio 트랜스포트.

## 현재 노출된 tool 6종 (전부 L4 수준)

| tool | 계층 | Phase 0 처리 |
|---|---|---|
| `plan_and_navigate`, `navigate_waypoints`, `cancel` | L4 Action | 유지. `execute_policy` 내부에서 호출 |
| `get_camera_snapshot`, `detect_objects` | L4 Perception/Reasoning | 유지 |
| `get_status` | L4 상태 | `get_task_report`로 승격 (task_id 상관 추가) |
| — | **L2** | **`execute_policy` 신설** ← 0-5 |
| — | L4 | **person-scan 5종 노출** ← 0-9 (G-3) |

## Phase 0 최소 A2A 집합

```
server/discover                  → 프로토콜 버전·능력·정체성 (= Agent Card 코어)
tools/list                       → 공개 Skill 목록
resources/read agentcard://self  → 확장 Agent Card

tools/call execute_policy        → L2 정책 수락. 즉시 task handle 반환
  args:   {policy_xml | policy_json, policy_id, deadline_sec, session_ref}
  result: {task_id, accepted, reject_reason?}
tools/call get_task_report       → 상태·최종 Report 조회
tools/call cancel_task           → 취소
```

## ⚠️ MCP SDK 버전 (U-1)

`from mcp.server.mcpserver import Image, MCPServer` — 구 `fastmcp.FastMCP`가 아닌 새 이름이지만
**이것만으로 최신 SDK라고 판단할 수 없다.** 반대 증거:

- `tools/scenarios/*.py`가 **`await session.initialize()`를 호출한다** — 2026-07-28이 제거했다는 그 핸드셰이크가 살아 있다
- `requirements.txt`가 `mcp[cli]`로 **버전 미고정**
- 이 import는 limo_slam에서 **그대로 복사한 패턴**이라 의도적 채택 흔적이 아니다

**작업 0-0에서 설치된 `mcp` 패키지 버전을 직접 확인할 것.**

## 주의

**stdout을 오염시키지 말 것.** stdio 트랜스포트는 stdout을 JSON-RPC 전용으로 쓴다.
초기화 중 stdout에 쓰는 라이브러리가 있으면 프로토콜이 깨진다
(YOLO 가중치 다운로드 진행표시줄이 실제로 이 문제를 일으켰고, `contextlib.redirect_stdout(sys.stderr)`로
감싼 warm-up으로 해결했다 — 그 코드를 제거하지 말 것).
