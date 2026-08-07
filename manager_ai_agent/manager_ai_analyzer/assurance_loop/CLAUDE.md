# Intent Assurance Loop

> **역할** 폐루프 상태기계 — 수렴하지 않으면 사람이 방치된다
> **상태** Phase 0 · 미착수
> **읽을 절** spec **§5.3**(30줄) — 그 외 절은 열지 않는다
> **정본** 구조 `SOT.md` · spec §5.3

판정에 따라 다음 행동을 결정하는 상태기계. 모든 전이는 IF-1로 IAD에 기록된다 (P-5).

```
IntentReceived → PolicyGenerated → WorkerSelected → Dispatched → Executing → Reported
Reported ─ completed ──────────────→ Assured
         ├ abnormal / not_found(소진) → Escalated
         ├ failed / timeout ─────────→ Retry ─ (<N) → Dispatched
         │                                   └ (≥N) → Reselect
         ├ rejected / not_found(잔존) → Reselect ─ 잔존 → WorkerSelected
         │                                        └ 소진 → Escalated
         └ partial ──────────────────→ PolicyGenerated (잔여 정책 재생성)
```

## 주의

**루프 수렴을 반드시 확인할 것.** 재시도 상한과 후보 소진 조건이 없으면
`failed → Retry → Dispatched → failed`가 무한히 돈다. Phase 0부터 상한을 넣는다.
