# Worker AI Core (WAC)

> **역할** L2 → L3 번역 + 세션 키 검증. Worker 측 진입점
> **상태** Phase 0 · 미착수
> **읽을 절** spec **§2.2**(13줄) · **§4.4**(L3, 80줄) — 그 외 절은 열지 않는다
> **정본** 구조 `SOT.md` · spec §4.4

**Policy Translator + Session Key Handler.** L2를 받아 L3로 번역하고 SF에 IF-5로 내린다.

| 하위 | 책임 |
|---|---|
| `policy_translator/` | L2 → L3 번역 (A2A 문서의 Policy Handler) |
| `session_key_handler/` | MAC이 발급한 세션 키 검증 |

> **Agent Executor는 여기 없다.** A2A 문서 §4가 Agent Executor를 **Worker AI Agent** 레벨에 배정하므로
> `../mcp_server/`에 둔다 (D-9).

## 지금 없는 것

현재 `../mcp_server/`가 노출하는 tool 6종은 **전부 L4(함수 호출) 수준**이다.
A2A 종단점이 되려면 그 위에 **L2 정책을 통째로 받는 `execute_policy`** 가 얹혀야 하고,
그 정책을 L3로 번역하는 것이 이 컴포넌트의 일이다. 두 층위는 공존한다 — 아래층은 디버깅용으로 남긴다.

## 작업 (Phase 0)

- [ ] 0-5 `execute_policy` / `get_task_report` / `cancel_task`
- [ ] 0-6 Policy Translator (L2→L3)
