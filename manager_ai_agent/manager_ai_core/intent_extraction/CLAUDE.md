# Intent Extraction

> **역할** L0 자연어를 어구로 분해한다 — **의미 해소는 하지 않는다**
> **상태** Phase 0 · 미착수
> **읽을 절** spec **§4.2**(L1 스키마) · **부록 A**(전 계층 트레이스) — 그 외 절은 열지 않는다
> **정본** 구조 `SOT.md` · spec §4.2

자연어 발화에서 의미 어구를 뽑는다. **여기서 의미를 해소하지 않는다** — 해소는 `kg_mapping/`의 일이다.

```
extract(utterance: str) -> list[str]
# "Check if Grandma is okay" -> ["Grandma", "check", "is okay"]
```

## 주의

- 어구 경계는 KG의 `phrase_bindings` 키와 맞아야 매핑이 성립한다. 두 컴포넌트를 함께 바꿀 것.
- 추출 결과는 L1의 `bindings[].phrase`로 그대로 흘러간다 (P-5).
