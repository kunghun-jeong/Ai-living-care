# IF-1 — Database Interface

> **역할** KG·IAD 접근 — MAC/MAA 가 지식과 감사 이력에 닿는 유일한 경로
> **상태** Phase 0 · 미착수
> **읽을 절** spec **§3.1**(IF-1 계약) — 그 외 절은 열지 않는다
> **정본** 구조 `SOT.md` · spec §3.1

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
