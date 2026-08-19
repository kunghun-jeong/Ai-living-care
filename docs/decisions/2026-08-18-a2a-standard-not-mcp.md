# 2026-08-18 · Manager 쪽 A2A는 MCP가 아니라 표준(HTTP+JSON-RPC 2.0)으로 만든다

> **정본 반영** 없음 — `SOT.md`·spec §6·`interfaces/if04_secure_a2a_channel/`는 이 변경에서
> 바꾸지 않았다. 대신 `manager_ai_agent/mcp_client/CLAUDE.md`에 실험 코드로 캐비어트를 남겼다.

## 왜

`manager_ai_agent/mcp_client/send_to_worker.py`(HTTP POST 스텁, 2026-08-18 오전에 추가)를
"진짜 A2A 프로토콜"로 바꾸는 작업을 시작하며, 이 저장소가 이미 정의해둔 A2A 설계
(`interfaces/if04_secure_a2a_channel/`, spec §6)를 확인했다. 그 문서는 A2A를 **MCP 위에
얹는(A2A-over-MCP, stdio, `tools/call execute_policy(L2)`)** 방식으로 정의하고 있었다.

이건 **표준이 아니라 이 프로젝트만의 선택**이다. 실제 A2A(Agent2Agent, Google이 만들고
Linux Foundation에 기증한 프로토콜)는 원래 **HTTP(S) + JSON-RPC 2.0**을 쓰고, `AgentCard`·
`Task`·`TaskState`·`Message`·`Artifact` 같은 개념도 이 저장소 문서가 그대로 인용해온
바로 그 표준 A2A의 용어다 — MCP는 애초에 "에이전트↔도구" 프로토콜이고 A2A는
"에이전트↔에이전트" 프로토콜이라 목적이 다르다.

사용자(팀장)가 확인 후 **MCP 위에 얹는 방식을 버리고 표준 A2A(HTTP+JSON-RPC 2.0, Agent
Card, Task 생명주기)를 그대로 구현하기로** 결정했다.

## 무엇이 달라지나

| | `interfaces/if04_secure_a2a_channel/`·spec §6 (정본, 미착수) | 이번에 만든 것 (실험·미승인) |
|---|---|---|
| 전송 | MCP over stdio | HTTP(S) + JSON-RPC 2.0 |
| Agent Card | `agentcard://self` (MCP 리소스) | `GET /.well-known/agent-card.json` |
| 정책 전달 | `tools/call execute_policy(L2)` | `message/send` (JSON-RPC 메서드) |
| 상태 조회 | `tasks/get(task_id)` (MCP 확장) | `tasks/get` (JSON-RPC 메서드) — 이름은 같지만 전송이 다르다 |
| TaskState | 8종(SUBMITTED 등) | 동일 8종 — 여기는 원래 표준과 일치했다 |

## 왜 MCP를 실제로 안 썼는지 (검토 결과)

로컬에 설치된 `mcp` 패키지(2.0.0)를 직접 열어봤다 — `discover()`·`Task`/`TaskStatus`/
`GetTaskRequest` 타입은 SDK에 존재하지만, `ClientSession`에 그걸 실제로 호출하는 편의
메서드가 없어 raw JSON-RPC 요청을 직접 구성해야 했다(검증 안 된 표면). 반면 이 저장소의
실제로 동작하는 Worker MCP 코드(`plan_and_navigate`+`get_status` 비동기 폴링 패턴,
`Scenarios/send_goal.py`)는 전부 **평범한 `@mcp.tool()` 함수**만 쓴다 — spec §6.4도
"`get_task_report` (또는 `tasks/get`)"라고 이미 이 fallback을 예정해뒀었다. 이번 결정으로
그 갈림길 자체가 없어졌다: MCP를 아예 안 쓰므로 U-1(SDK 버전 모호성)도 이 실험 코드에는
더 이상 해당하지 않는다.

## 무엇을 추가했나

| 경로 | 역할 |
|---|---|
| `manager_ai_agent/mcp_client/a2a_client.py` | `send_to_worker.py` 대체. discover→message/send→tasks/get 폴링을 전부 캡슐화 |
| `manager_ai_agent/mcp_client/dev_mock_worker_agent.py` | **실제 Worker 아님.** 로컬에서 위 클라이언트를 시험하기 위한 가짜 A2A 서버 |

`manager_ai_agent/manager_ai_core/api_server.py`는 import 한 줄만 바꿨다
(`send_to_worker.py` → `a2a_client.py`, 함수 시그니처 동일).

## 검증 (1회 실측)

`dev_mock_worker_agent.py`(9000)·`api_server.py`(8000)·`frontend`(5173)를 모두 로컬에 띄우고,
`a2a_client.py`를 단독 실행해 discover→message/send→폴링이 콘솔에서 도는 것을 확인했다.
이어서 브라우저(Claude in Chrome)로 "할머니 괜찮은지 확인해줘"를 입력해 WellBeing 판단·
intent·"Worker 전달됨 — dev-mock-worker (가짜) task ... -> completed" 배지까지 화면에서
확인했다. mock을 끈 상태에서 "Worker 전달 실패"로 정상적으로 표시되는 것도 확인했다.
