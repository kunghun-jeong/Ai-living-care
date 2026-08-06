# KG Mapping

> **구조 정본**: `SOT.md` · **설계 정본**: `docs/spec/AI-Care_Unified_Architecture_Spec_v0.2.md`
> **상위**: `manager_ai_core/` · **Phase**: 0 · **구현 상태**: 미착수

추출된 어구를 KG에 조회해 `element = value` 바인딩으로 해소한다. **IF-1 경유** (`interfaces/if01_database/`).

```
resolve(phrase: str, context: dict) -> list[Binding]
Binding = {"element": str, "value": any, "confidence": float, "source": str}
```

slide 21의 KG mapping 표:

| PHRASE | ELEMENT → RETRIEVED VALUE |
|---|---|
| "Grandma" | `target = elder`, `place = living_room` |
| "check" | `task = safety_check`, `mobile = [LIMO_1, LIMO_2]` |
| "is okay" | `condition = realtime`, `sensor = camera` |

## 주의

- **KG를 직접 파일로 읽지 말 것.** IF-1 계약으로만 접근해야 후일 그래프DB로 무중단 교체할 수 있다 (D-6).
- `confidence`를 반드시 채운다. 낮은 신뢰도 바인딩은 사용자 확인(MRTR)으로 승격될 수 있다.
