# Worker AI Core (WAC)

> **SOT**: `docs/spec/AI-Care_Unified_Architecture_Spec_v0.2.md`
> **상위**: `worker/` · **Phase**: 0 · **구현 상태**: 미착수

**Policy Translator + Session Key Handler.** L2 고수준 정책을 받아 L3 저수준 정책으로 번역하고
SF에 IF-5로 내린다.

## 하위

| 하위 | 책임 |
|---|---|
| `policy_translator/` | L2 → L3 번역 |
| `agent_executor/` | A2A Message에서 정책을 꺼내 Core에 전달 |
| `session_key_handler/` | MAC이 발급한 세션 키 검증 |

## 지금 없는 것

현재 `a2a/server/MCP_server.py`가 노출하는 tool 6종은 **전부 L4(함수 호출) 수준**이다.
A2A 종단점이 되려면 그 위에 **L2 정책을 통째로 받는 `execute_policy`** 가 얹혀야 하고,
그 정책을 L3로 번역하는 것이 이 컴포넌트의 일이다. 두 층위는 공존한다 — 아래층은 디버깅용으로 남긴다.

## 작업 (Phase 0)

- [ ] 0-5 `execute_policy` / `get_task_report` / `cancel_task`
- [ ] 0-6 Policy Translator (L2→L3)
