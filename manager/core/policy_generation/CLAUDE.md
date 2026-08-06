# High-level Policy Generation

> **SOT**: `docs/spec/AI-Care_Unified_Architecture_Spec_v0.2.md`
> **상위**: `manager/core/` · **Phase**: 0 · **구현 상태**: 미착수

L1 Intent Query + Schema Prompt를 LLM에 넣어 **L2 High-level Policy (ECA XML)** 를 생성한다.

스키마: `contracts/high_level_policy/`

## 생성 결과 형태

```xml
<living-care-policy>
  <policy-id/> <intent-id/> <policy-name/> <issued-by/> <issued-at/>
  <rule>
    <rule-name/>
    <event><event-type/><trigger/></event>
    <condition><target-role/><place/><modality/></condition>
    <action><action-type/><required-skill/>…<dispatch-mode/></action>
  </rule>
  <assurance><deadline-sec/><report-mode/><escalation-on/></assurance>
</living-care-policy>
```

## 반드시 지킬 것

- **디바이스 이름 금지** (P-2). `<required-skill>`이 Worker 선택의 유일한 기준이다.
- **`<assurance>`를 비우지 않는다.** `not_found`·`timeout` 후속 액션이 여기서 선언적으로 정해진다.
- **스키마 검증을 통과하지 못한 출력은 정책으로 승격하지 않는다** (P-4).
  검증 실패 → 재생성 → 그래도 실패 → 규칙 기반 폴백 또는 사용자 확인.

## 주의

Ollama를 쓸 경우 호출에 `format: "json"`을 걸어 출력 형식을 강제할 수 있다.
LLM 실패 시 폴백 설계는 `docs/audit/IETF승계issue.md` §4.1 참조 (참고 자료).
