# 2026-08-18 · frontend↔Manager HTTP 게이트웨이를 실험·미승인으로 추가한다

> **정본 반영** 없음 — `SOT.md`·root `CLAUDE.md`·`docs/api-spec.md`는 이 변경에서 바꾸지 않았다.
> 대신 `frontend/CLAUDE.md` · `manager_ai_agent/manager_ai_core/CLAUDE.md` ·
> `manager_ai_agent/mcp_client/CLAUDE.md`에 실험 코드로 캐비어트를 남겼다.

## 왜

`manager_ai_core/pipeline.py`(2026-08-18에 `graph_inference/`에서 분배한 Neo4j 추론
파이프라인)를 콘솔 데모가 아니라 실제로 눌러볼 수 있는 창구가 필요했다. React 프론트엔드가
자연어를 POST하면 Manager가 처리해 화면에 판단·intent를 보여주고, 동시에 Worker로도
전달한다.

## 원칙 충돌 — 의도적으로 미해소

root `CLAUDE.md`·`docs/api-spec.md` 둘 다 "**HTTP API 없음 — 외부 인터페이스는 MCP tool
6종뿐**"이라고 명시한다. 이번 추가(`frontend/` → `manager_ai_core/api_server.py` POST)는
그 원칙을 정면으로 어긴다.

**팀원 간에는 합의했으나 상급자 보고·승인 전**이다. `graph_inference` 때와 같은 방식으로
처리한다:
- `SOT.md` §2 트리·root `CLAUDE.md`·`docs/api-spec.md`는 건드리지 않았다 — "HTTP API 없음"을
  뒤집는 것은 승인 이후의 별도 절차다.
- 새로 만든 코드는 전부 자기 위치의 `CLAUDE.md`에 "실험·미승인·상급자 승인 대기"로 표시했다.
- 별도 브랜치에서만 존재하고 승인 전에는 `main`에 머지하지 않는다 (브랜치는 팀장이 직접 판다).

## 추가한 것

| 경로 | 역할 |
|---|---|
| `frontend/` (신규 최상위) | React(Vite). 입력창 → 결과 표시. `SOT.md` §2 밖 |
| `manager_ai_agent/manager_ai_core/api_server.py` | FastAPI. `POST /api/query`가 `pipeline.run()`을 호출하고 결과에 `worker_delivery`를 붙여 반환 |
| `manager_ai_agent/mcp_client/send_to_worker.py` | 이 폴더의 첫 코드. `WORKER_ENDPOINT_URL`로 HTTP POST — 정식 A2A(`execute_policy(L2)`)가 아니라 얇은 스텁 |

## 범위를 의도적으로 좁힌 것

- **Worker 전달은 "보내는 것만 확인되면 됨"** — Worker AI Agent는 다른 팀원이 별도 설계
  중이라, 실제 좌표 기반 로봇 제어(`plan_and_navigate` 등)나 MCP stdio 세션 연결은 이번
  범위에 넣지 않았다. `send_to_worker()`가 실패해도 Manager API는 안 죽고 프론트엔드에
  "Worker 전달 실패"만 표시한다 — 받는 쪽이 아직 없어도 정상 동작이다.
- 좌표 매핑 갭(G-6, 방 이름 2개만 좌표 있음)은 그대로 둔다. 이번 변경과 무관하다.

## 검증 (1회 실측)

Neo4j·frontend·Manager API·더미 Worker 리시버(`python -m http.server`류)를 모두 로컬에
띄우고 브라우저(Claude in Chrome)로 "할머니 괜찮은지 확인해줘"를 입력 → WellBeing 판단·
intent·"Worker 전달됨(200)" 배지까지 화면에서 확인했다. 더미 Worker를 끄면 "Worker 전달
실패"로 정상적으로 표시되는 것도 확인했다.
