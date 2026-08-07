# IF-4 — Secure A2A Channel

> **역할** A2A-over-MCP 바인딩 — **이 프로젝트의 핵심 기여** (`S-4`)
> **상태** Phase 0 · **부분** — MCP 서버는 동작, A2A 의미론 미구현
> **읽을 절** spec **§6.2**(객체 매핑, 18줄) · **§6.3**(TaskState, 17줄) · **§9**(보안, 16줄) — 그 외 절은 열지 않는다
> **정본** 구조 `SOT.md` · spec §6

**L2 고수준 정책, Task 상태, Artifact**를 전달하는 에이전트 간 채널.
**A2A 의미론을 유지하면서 전송·직렬화는 MCP를 재사용한다.**

종단점 구현: Manager 측 `manager_ai_agent/mcp_client/` · Worker 측 `worker_ai_agent/mcp_server/`
이 디렉터리에는 **바인딩 정의**(어느 쪽 소유도 아닌 공유 자산)를 둔다.

## 왜 이 바인딩인가 (★핵심 기여 — 표준화 항목 S-4)

업계 통념은 "MCP는 agent↔tool, A2A는 agent↔agent"로 역할이 갈린다는 것이다. 근거:

1. **엣지 로컬성** — 같은 엣지 배치가 다수. stdio 로컬 IPC가 지연·전력에서 유리
2. **툴체인 단일화** — Worker 내부 SF 호출(L4)이 이미 MCP tool. 외부까지 통일하면 **서버 구현 하나**
3. **2026-07-28 MCP 개정이 격차를 없앰** — A2A 핵심 객체 전부가 현행 MCP에 대응물을 가짐

> **포지셔닝**: "A2A를 MCP로 대체한다"가 아니라 **"A2A 의미론의 MCP 전송 바인딩을 정의한다"**.
> A2A 명세가 이미 JSON-RPC / gRPC / HTTP+JSON 3종 바인딩을 인정하므로
> **제4의 바인딩을 제안하는 형태**가 표준화 트랙에서 가장 방어 가능하다.

## 객체 매핑 (스펙 §6.2)

| A2A v1.0 | MCP 2026-07-28 |
|---|---|
| AgentCard | `server/discover` + resource `agentcard://self` |
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

## 보안

mTLS/IPsec + Session Key (slide 13). Phase 0은 stdio 로컬로 OS 프로세스 격리에 의존한다.
**Action Function이 액추에이션 직전에 키를 한 번 더 검증하는 이중 구조를 유지할 것** (S-7).
> 이 문서 위쪽의 S-4는 바인딩 프로파일을 가리킨다 — **두 항목은 다르다** (F-15).

## 주의

**제안서·논문 제출 전 MCP 명세 최신판을 재확인할 것** (U-1). 이 매핑 전체가 2026-07-28 개정판에 의존한다.
