# IF-8 — Analyzer-Facing Interface

> **구조 정본**: `SOT.md` §3 · **설계 정본**: `docs/spec/AI-Care_Unified_Architecture_Spec_v0.2.md` §3
> **종단점**: MAA ↔ WAA · **Phase**: 2 · **구현 상태**: 미착수

상세 진단과 이상 이벤트를 에이전트 간에 주고받는다. **제어 평면과 분리된 관측 평면**이다.

## IF-4와의 분리 이유

IF-4(제어)는 정책·Task·Artifact를 나른다. IF-8(관측)은 그와 별도로 진단·이상 이벤트를 나른다.
분리하면 **제어 채널이 막혀도 진단은 흐르고**, 관측 트래픽이 제어 지연에 영향을 주지 않는다.

## 주의

Phase 2 항목이다. Phase 0에서는 진단이 Report의 `diagnostics` 필드에 실려 IF-4로 함께 올라간다.
IF-8을 도입할 때 그 필드를 이쪽으로 옮길지 결정해야 한다 (미결정).
