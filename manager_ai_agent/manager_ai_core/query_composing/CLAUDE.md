# Intent Query Composing

> **역할** 바인딩 → L1 Intent Query JSON
> **상태** Phase 0 · 미착수
> **읽을 절** spec **§4.2**(27줄) — 그 외 절은 열지 않는다
> **정본** 구조 `SOT.md` · spec §4.2 · 스키마 `contracts/intent_query/`

바인딩을 모아 **L1 Intent Query(JSON)** 를 만든다. 아직 정책이 아니다 — 구조화된 의도다.

스키마: `contracts/intent_query/`

| 필드 | 출처 |
|---|---|
| `intent`·`target`·`task`·`condition`·`place`·`devices` | slide 21 원본 |
| `sensors` | KG 매핑표엔 있으나 composed JSON에서 누락된 것을 복원 |
| `intent_id`·`raw_utterance`·`issued_by`·`issued_at`·`bindings` | 스펙이 추가 (P-5) |

## 주의

`devices`는 **후보 힌트**일 뿐이다. 확정은 MAMS의 Worker 선택이 한다 (spec §7.2).
여기서 정한 디바이스가 L2로 넘어가면 안 된다.
