# A2A ↔ MCP 바인딩 정의

> **SOT**: `docs/spec/AI-Care_Unified_Architecture_Spec_v0.2.md`
> **상위**: `a2a/` · **Phase**: 0 · **구현 상태**: 미착수 — 문서만 존재

A2A v1.0 객체를 MCP 2026-07-28 위에 어떻게 실현하는지의 **규범적 매핑**.
표준화 항목 **S-4**의 실체이며, 정의는 스펙 §6.2에 있다.

## 매핑 요약

| A2A v1.0 | MCP 2026-07-28 |
|---|---|
| AgentCard | `server/discover` 결과 + resource `agentcard://self` |
| AgentSkill | `tools/list` 항목 1개 |
| Message / `message/send` | `tools/call` |
| Task + TaskState | `io.modelcontextprotocol/tasks` **공식 확장** |
| `tasks/get` | `tasks/get` (이름까지 동일) |
| Artifact | tool result의 `content` / `structuredContent` |
| `TASK_STATE_INPUT_REQUIRED` | **MRTR** `InputRequiredResult` |
| `message/stream` (SSE) | 요청 범위 `notifications/progress` |
| push notification config | `subscriptions/listen` |
| Agent Registry | **MAMS** (MCP 밖 — AI-Care 고유 확장) |

## TaskState ↔ report.status 정렬

| A2A TaskState | 대응 report.status |
|---|---|
| `SUBMITTED` / `WORKING` / `INPUT_REQUIRED` | (미발행) |
| `COMPLETED` | `completed` / `abnormal` / `not_found` / `partial` |
| `FAILED` | `failed` |
| `REJECTED` | `rejected` |
| `CANCELED` | `timeout` |

## 주의

**제안서·논문 제출 전 MCP 명세 최신판을 재확인할 것** (U-1).
이 매핑 전체가 2026-07-28 개정판에 의존한다.
