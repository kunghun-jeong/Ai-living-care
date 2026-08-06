# IF-3 — Registration Interface

> **구조 정본**: `SOT.md` §3 · **설계 정본**: `docs/spec/AI-Care_Unified_Architecture_Spec_v0.2.md` §3
> **종단점**: MAC ↔ MAMS, WAC ↔ WAMS · **Phase**: 0 · **구현 상태**: 미착수

Worker 등록·조회·상태를 주고받는다. Manager와 Worker 양쪽에 대칭으로 존재한다 (P-1).

| 방향 | 내용 |
|---|---|
| MAC → MAMS | `required-skill`로 Worker 후보 조회 |
| WAC → WAMS | 자기 등록, SF 수명주기 상태 |

## 주의

**Registry는 후보만 제공하고 최종 선택은 MAMS의 `worker_selector/`가 한다.**
A2A 명세는 Worker 자동 선택을 하지 않으며, 선택 로직은 Manager의 책임이라고 명시한다.
Phase 0에서는 Worker 주소를 고정 설정으로 둬도 된다.
