# Agent Registry

> **구조 정본**: `SOT.md` · **설계 정본**: `docs/spec/AI-Care_Unified_Architecture_Spec_v0.2.md`
> **상위**: `manager_ai_management_system/` · **Phase**: 0 · **구현 상태**: 미착수

Worker의 접속 정보와 능력을 보관·조회한다. A2A Agent Card의 수집처. IF-3·IF-7 경유.

```
register(agent_id, agent_card) -> None
lookup(required_skills: list[str]) -> list[AgentRef]
update_resources(agent_id, resources) -> None   # IF-7, Phase 2
```

## 주의

**Registry는 후보를 제공할 뿐 최종 선택을 하지 않는다.** 선택은 `worker_selector/`의 책임이다 (A2A 명세 경계).
Phase 0에서는 Worker 주소를 고정 설정으로 둬도 된다.
