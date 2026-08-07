# Agent Registry

> **역할** Agent Card 보관·조회 — **후보만 제공한다.** 선택은 `worker_selector/`
> **상태** Phase 0 · 미착수
> **읽을 절** spec **§6.4**(Worker MCP 인터페이스) · **§7.2** — 그 외 절은 열지 않는다
> **정본** 구조 `SOT.md` · spec §7.2

Worker의 접속 정보와 능력을 보관·조회한다. A2A Agent Card의 수집처. IF-3·IF-7 경유.

```
register(agent_id, agent_card) -> None
lookup(required_skills: list[str]) -> list[AgentRef]
update_resources(agent_id, resources) -> None   # IF-7, Phase 2
```

## 주의

**Registry는 후보를 제공할 뿐 최종 선택을 하지 않는다.** 선택은 `worker_selector/`의 책임이다 (A2A 명세 경계).
Phase 0에서는 Worker 주소를 고정 설정으로 둬도 된다.
