# A2A Client (IF-4 Manager 측 종단점)

> **역할** IF-4 Manager 측 종단점 — 정해진 상대에게 보내고 받는 것만 한다
> **상태** Phase 0 · 정식(spec 원안, MCP 기반) A2A 미착수 · **`a2a_client.py`(실험·미승인, 표준 A2A/HTTP+JSON-RPC 2.0) 있음**
> **경로** 2026-08-18에 `mcp_client/` → `a2a_client/`로 개명(실험·미승인, 상급자 승인 대기) — `docs/decisions/2026-08-18-rename-mcp-client-to-a2a-client.md`
> **읽을 절** spec **§6.4** · **§6.5**(Phase 0 시퀀스) — 그 외 절은 열지 않는다
> **정본** 구조 `SOT.md` · spec §6

MAC이 만든 L2 정책을 Worker에 전달하고 Task 상태·Artifact를 수신한다.
`worker_ai_agent/mcp_server/`의 대응 짝이며, 바인딩 정의는 `interfaces/if04_secure_a2a_channel/`에 있다.

## 흐름

```
MAMS 조회 (required-skill)          → Worker 후보
server/discover + agentcard://self  → Agent Card 확인
tools/call execute_policy(L2)       → {task_id, accepted}
tasks/get(task_id) 폴링              → COMPLETED + Artifact(Report + 증거 이미지)
```

## 주의

- **Worker 선택은 Client의 책임이 아니다.** MAMS의 `worker_selector/`가 정한다.
  Client는 정해진 상대에게 보내고 받는 것만 한다.
- Task 상태 전달 방식(폴링 vs `notifications/progress`)은 미정 (U-5). Phase 0은 폴링.
- 배치 근거: `docs/context/AI-Care_A2A_Core_Context(2).md` §4가 A2A Client를 **Manager AI Agent**에 배정 (D-9).

## 실험 코드 — `a2a_client.py` (실험 · 미승인 · 상급자 승인 대기)

2026-08-18에 `send_to_worker.py`(HTTP POST 스텁)를 **표준 A2A**로 교체했다. **위 「흐름」이
말하는 MCP 기반(`server/discover`+`tools/call`+stdio)이 아니다** — 실제 A2A(Google→Linux
Foundation 기증 표준)는 원래 **HTTP(S) + JSON-RPC 2.0**이고 MCP와는 별개 프로토콜이다.
내용물이 MCP를 전혀 안 쓰게 되면서 폴더 이름도 `mcp_client/` → `a2a_client/`로 같이
바꿨다(`D-9`가 정한 이름이라 SOT.md도 함께 고쳤다 — 아래 참조). 왜 이렇게 바꿨는지는
`docs/decisions/2026-08-18-a2a-standard-not-mcp.md` ·
`docs/decisions/2026-08-18-rename-mcp-client-to-a2a-client.md` 참조.

### 프로토콜 (표준 A2A 그대로)

- **Agent Card**: `GET {WORKER_AGENT_URL}/.well-known/agent-card.json`
- **JSON-RPC 2.0**: `POST {WORKER_AGENT_URL}/` — `{"jsonrpc":"2.0","id":...,"method":...,"params":{...}}`
- **TaskState** 8종: `submitted · working · input-required · completed · failed · canceled · rejected · auth-required`
  (spec §6.3 표와 동일 — 표준 A2A와 이 저장소 문서가 원래 일치해 있었다)

### 팀원이 Worker A2A 서버를 만들 때 맞춰야 할 계약 (이 클라이언트가 실제로 보내는 요청)

| 메서드 | params | result (기대) |
|---|---|---|
| `message/send` | `{"message": {"role": "agent", "messageId": str, "parts": [{"type": "data", "data": {...}}]}}` | Task: `{"id": str, "status": {"state": "submitted"\|...}}` 또는 즉시 완료 Message |
| `tasks/get` | `{"id": task_id}` | Task (위와 같은 모양, `status.state`가 갱신됨) |
| `tasks/cancel` | `{"id": task_id}` | Task, `status.state = "canceled"` |

`parts[0].data`에 실제로 들어가는 페이로드는 `{"axis", "evaluation", "sequence"}` —
`manager_ai_core/pipeline.py`의 결과 원형 그대로다. **L2 ECA XML이 아니다** — 그 스키마는
`contracts/high_level_policy/`가 아직 미정이고 우리 실험 파이프라인도 안 쓰므로, 지금
있는 그대로의 판단·intent JSON을 보낸다.

### 파일

| 파일 | 역할 |
|---|---|
| `a2a_client.py` | `discover`·`send_message`·`get_task`·`cancel_task` + 이 넷을 엮은 `send_to_worker(payload)`(폴링까지 포함, `api_server.py`가 호출) |
| `dev_mock_worker_agent.py` | **실제 Worker 아님** — 로컬에서 `a2a_client.py`를 시험하기 위한 가짜 A2A 서버. `python dev_mock_worker_agent.py`(uvicorn, 포트 9000) 또는 `python -m uvicorn dev_mock_worker_agent:app --port 9000` |

`WORKER_AGENT_URL` 환경변수(기본 `http://localhost:9000`)로 대상을 바꾼다. 연결 실패·타임아웃은
전부 삼키고 `{"ok": false, ...}`를 반환한다 — Worker가 아직 없어도 Manager API는 안 죽는다.
Worker 선택 로직은 넣지 않았다(위 규칙 그대로) — 지금은 `WORKER_AGENT_URL` 하나로 고정.
