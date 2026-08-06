# Intent Extraction

> **SOT**: `docs/spec/AI-Care_Unified_Architecture_Spec_v0.2.md`
> **상위**: `manager/core/` · **Phase**: 0 · **구현 상태**: 미착수

자연어 발화에서 의미 어구를 뽑는다. 여기서 **의미를 해소하지 않는다** — 해소는 `kg_mapping/`의 일이다.

## 계약

```
extract(utterance: str) -> list[str]
# "Check if Grandma is okay" -> ["Grandma", "check", "is okay"]
```

## 주의

- 어구 경계는 KG의 `phrase_bindings` 키와 맞아야 매핑이 성립한다. 두 컴포넌트를 함께 바꿀 것.
- 추출 결과는 L1의 `bindings[].phrase`로 그대로 흘러간다 (P-5).
