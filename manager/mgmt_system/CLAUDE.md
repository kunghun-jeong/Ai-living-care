# Manager AI Management System (MAMS)

> **SOT**: `docs/spec/AI-Care_Unified_Architecture_Spec_v0.2.md`
> **상위**: `manager/` · **Phase**: 0 · **구현 상태**: 미착수

Worker의 등록·상태·수명주기를 관리하고, **Agent Registry 역할을 겸한다.**

slide 21은 `Edge AI's Mgmt System`으로 표기 — 정식 명칭은 `Manager AI Management System` (D-1).

## 하위

| 하위 | 책임 | Phase |
|---|---|---|
| `agent_registry/` | Worker 주소·Skill·자원 상태 보관 및 조회 | 0 (고정 설정) → 2 (동적) |
| `worker_selector/` | `required-skill` 기준 후보 필터링·점수화·선택 | 2 |

## 왜 이게 표준화 항목인가 (S-3)

A2A는 Agent Discovery 방식은 제시하지만 **레지스트리 데이터 모델과 Worker 선택 로직은 구현자 몫**으로 남긴다.
게다가 Agent Card만으로는 CPU·메모리·대역폭 등 **실시간 자원 상태를 반영하기 어렵다**
(Duan & Lu, arXiv:2508.15819). **MAMS + IF-7이 정확히 그 공백을 메운다.**

## 주의

Phase 0에서는 Worker 주소를 고정 설정으로 둬도 된다. Worker 수가 늘면 그때 동적 레지스트리로 승격한다.
