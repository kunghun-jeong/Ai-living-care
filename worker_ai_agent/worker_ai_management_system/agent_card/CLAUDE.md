# Agent Card

> **구조 정본**: `SOT.md` · **설계 정본**: `docs/spec/AI-Care_Unified_Architecture_Spec_v0.2.md`
> **상위**: `worker_ai_management_system/` · **Phase**: 1 · **구현 상태**: 미착수

Worker가 공개하는 디지털 명함. Manager는 여기서 이름·주소·지원 통신 방식·제공 Skill을 확인한다.

| A2A | MCP 대응 |
|---|---|
| AgentCard 코어 | `server/discover` 결과 |
| 확장 필드 (자원 상태·배터리·위치) | MCP resource `agentcard://self` |
| AgentSkill | `tools/list` 항목 1개 = Skill 1개 |

권장 명명: `skill.<domain>.<verb>` (예: `skill.livingcare.person-scan`)

## 주의

**Skill은 내부 함수 목록이 아니다.** Manager가 작업을 맡길 때 이해할 수 있는 **고수준 능력**이어야 한다.
`start_person_scan`은 함수이고, `person-scan`이 Skill이다.
