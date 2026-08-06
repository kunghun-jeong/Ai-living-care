# IF-2 — Analytics Interface

> **구조 정본**: `SOT.md` §3 · **설계 정본**: `docs/spec/AI-Care_Unified_Architecture_Spec_v0.2.md` §3
> **종단점**: MAC ↔ MAA, WAC ↔ WAA · **Phase**: 0 · **구현 상태**: 미착수

해석된 report와 완료/재시도/전환 판정을 주고받는다. **Manager와 Worker 양쪽에 대칭으로 존재한다** (P-1).

| 방향 | 내용 |
|---|---|
| MAA → MAC | 임무 판정 (Assured / Retry / Reselect / Escalated / 잔여 정책) |
| WAA → WAC | SF 실행 요약, 자가진단 결과 |

## 주의

**IF-8(Analyzer-Facing)과 혼동하지 말 것.**
IF-2는 **같은 에이전트 안**의 Core↔Analyzer, IF-8은 **에이전트를 넘는** MAA↔WAA다.
IF-8은 제어 평면과 분리된 관측 평면이며 Phase 2다.
