# Manager AI Core (MAC)

> **역할** L0(자연어) → L1(Intent Query) → L2(High-level Policy)
> **상태** Phase 0 · 미착수 · 작업 `0-3`
> **읽을 절** spec **§4.1**(계층 정의) · **§4.2**(L1) · **§4.3**(L2 ECA) — 그 외 절은 열지 않는다
> **정본** 구조 `SOT.md` · spec §4

**Intent Translator + Session Key Manager.** L0(자연어) → L1(Intent Query) → L2(High-level Policy) 변환의 주체.

논문 Fig.1과 slide 17의 표는 `Manager Controller`로 표기 — **별칭으로만 인정**한다 (spec §2.1).

## 구성

| 디렉터리 | 책임 |
|---|---|
| `intent_extraction/` | L0 자연어 → 어구 분해 |
| `kg_mapping/` | 어구 → KG element=value 바인딩 (IF-1) |
| `query_composing/` | 바인딩 → L1 Intent Query JSON |
| `policy_generation/` | L1 → L2 High-level Policy (ECA) |
| `session_key_manager/` | IF-4 세션 키 발급·갱신 (파이프라인과 직교) |

## 파이프라인

```
"Check if Grandma is okay"
  → intent_extraction/     ["Grandma", "check", "is okay"]
  → kg_mapping/            IF-1로 KG 조회 → phrase별 element=value 바인딩
  → query_composing/       L1 Intent Query JSON
  → policy_generation/     LLM + Schema Prompt → L2 ECA XML
```

`session_key_manager/`는 직교하며 IF-4의 세션 키를 발급·갱신한다.
생성된 L2는 `../mcp_client/`가 IF-4로 실어 보낸다.

## 반드시 지킬 것

- **L2에 디바이스 이름을 넣지 않는다.** device-agnostic이어야 다중 Worker fan-out이 성립한다 (spec §4.3).
- **`bindings`를 반드시 남긴다.** 어느 어구가 어떤 값으로 해소됐는지 없으면 오역 디버깅이 불가능하다 (P-5).
- **LLM 실패 경로를 설계에 포함한다** (P-4). 정상 파싱 → 필드 정규화 → 규칙 기반 폴백 3단 구조 권장.

## 작업 (Phase 0)

- [ ] 0-3 L0→L2 파이프라인 전체
- [ ] LLM 선택 확정 (U-3)
- [ ] L2 직렬화 형식 확정 (U-2 — 내부 JSON / 표준 문서 XML 양방향 변환 권고)
