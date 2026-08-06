# Worker AI Analyzer (WAA)

> **SOT**: `docs/spec/AI-Care_Unified_Architecture_Spec_v0.2.md`
> **상위**: `worker/` · **Phase**: 0 · **구현 상태**: 미착수

SF 실행 상태를 IF-6로 수집해 **Worker Report**를 만들고, A2A Task Status / Artifact로 변환해 상향 보고한다.
자가진단도 담당한다.

## 만들어야 할 Report

스키마: `contracts/worker_report/`

```json
{
  "report_id", "task_id", "policy_id", "intent_id", "agent_id", "reported_at",
  "status": "abnormal",
  "observation": {"found", "place", "posture", "motion": {"state","duration_sec"},
                  "frame_id", "pose"},
  "confidence": 0.86,
  "evidence": {"type": "image/jpeg", "ref": "iad://evidence/f_47", "bbox": [...]},
  "request": ["emergency_call", "audio_check"],
  "diagnostics": {"elapsed_sec", "rooms_visited", "sf_errors"}
}
```

## 지금 못 채우는 필드

- **`observation.pose`** — PF가 pose를 채우지 않는다 (G-2). "어느 방에서 발견했는지" 보고 불가.
- **`evidence`** — 프레임 pinning이 없어 증거 이미지를 확보할 수 없다 (G-1).

**두 갭이 Report의 핵심 필드를 비운다.** Phase 0의 0-7·0-8이 이것을 푼다.
