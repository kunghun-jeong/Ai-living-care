# IF-1 — Database Interface

> **구조 정본**: `SOT.md` §3 · **설계 정본**: `docs/spec/AI-Care_Unified_Architecture_Spec_v0.2.md` §3
> **종단점**: MAC ↔ KG/IAD, MAA ↔ IAD · **Phase**: 0 · **구현 상태**: 미착수

KG 조회, intent·policy 감사 레코드 쓰기, KB audit을 담당한다.

## 계약 (초안)

```
resolve(phrase: str, context: dict) -> list[Binding]     # KG 읽기
audit(record: AuditRecord) -> None                        # IAD 쓰기
prompt(schema_id: str) -> str                             # IAD 스키마 프롬프트 읽기
```

## 왜 하나의 인터페이스인가

KG와 IAD는 별개 저장소지만 접근 계층은 같다. 하나로 두면 **MAC이 저장소 구현을 몰라도 된다** —
KG를 JSON 룩업에서 그래프DB로 바꿔도 이 계약이 고정이면 무중단 교체가 된다 (D-6).

## 주의

**P-5(감사 가능성)를 실현하는 인터페이스다.** L0~L4 전 계층의 변환 결과가 여기를 통해 기록된다.
어느 한 계층이라도 감사 레코드를 빠뜨리면 end-to-end 상관이 끊긴다.
