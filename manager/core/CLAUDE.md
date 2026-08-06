# Manager AI Core (MAC)

> **SOT**: `docs/spec/AI-Care_Unified_Architecture_Spec_v0.2.md`
> **상위**: `manager/` · **Phase**: 0 · **구현 상태**: 미착수

**Intent Translator + Session Key Manager.** L0(자연어) → L1(Intent Query) → L2(High-level Policy) 변환의 주체.

논문 Fig.1과 slide 17의 표는 이 컴포넌트를 `Manager Controller`로 표기한다 — **별칭으로만 인정**하고
정식 명칭은 `Manager AI Core`다 (spec §2.1).

## 파이프라인

```
"Check if Grandma is okay"
  → intent_extraction/     ["Grandma", "check", "is okay"]
  → kg_mapping/            IF-1로 KG 조회 → phrase별 element=value 바인딩
  → query_composing/       L1 Intent Query JSON
  → policy_generation/     LLM + Schema Prompt → L2 ECA XML
```

`session_key_manager/`는 이 흐름과 직교하며 IF-4의 세션 키를 발급·갱신한다.

## 반드시 지킬 것

- **L2에 디바이스 이름을 넣지 않는다.** L2는 device-agnostic이어야 다중 Worker fan-out이 성립한다.
  어느 Worker가 수행할지는 MAMS의 배포 결정이다 (spec §4.3).
- **`bindings`를 반드시 남긴다.** 어느 어구가 어떤 값으로 해소됐는지 없으면 오역 디버깅이 불가능하다 (P-5).
- **LLM 실패 경로를 설계에 포함한다.** P-4. 정상 파싱 → 필드 정규화 → 규칙 기반 폴백 3단 구조를 권장한다.

## 작업 (Phase 0)

- [ ] 0-3 L0→L2 파이프라인 전체
- [ ] LLM 선택 확정 (U-3: Claude API vs Ollama Llama 3.1 vs 로컬 소형)
- [ ] L2 직렬화 형식 확정 (U-2: 내부 JSON / 표준 문서 XML 양방향 변환 권고)
