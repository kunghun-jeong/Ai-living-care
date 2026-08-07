# Worker Selector

> **역할** 점수 함수로 Worker 를 고른다 — 가중치는 미결정 `U-4`
> **상태** Phase 2 · 미착수
> **읽을 절** spec **§7.1**(분해 모드, 23줄) · **§7.2**(16줄) — 그 외 절은 열지 않는다
> **정본** 구조 `SOT.md` · spec §7.2

L2 정책의 `<required-skill>`을 만족하는 Worker를 골라 배포 대상을 확정한다.

```
1. Registry 조회: required-skill 전부를 공시한 Worker 집합 C
2. 필터: 가용(alive) ∧ 자원 충족 ∧ 세션 유효
3. 점수화: score(w) = α·capability_match + β·proximity(place)
                    + γ·availability − δ·recent_failure_rate
4. dispatch-mode에 따라 상위 1개(or-fallback) 또는 상위 k개(or-race, k ≤ max-parallel)
5. rejected 수신 시 해당 Worker 제외하고 재선택
```

| dispatch-mode | 완료 조건 | 예 |
|---|---|---|
| `and-all` | 전부 `completed` | "전등 다 끄고 문 잠가줘" |
| `or-race` | 최초 성공. **나머지 취소** | **시나리오 1** — LIMO_1/LIMO_2 |
| `or-fallback` | 순차 시도 | 동시 기동 자원 부족 시 |
| `sequential` | 마지막 단계 완료 | "찾아서 확인하고 이상하면 디스펜서 열어" |
| `split` | 모든 파티션 완료 | "1층 LIMO_1, 2층 LIMO_2" |

## 주의

α·β·γ·δ 가중치는 미정 (U-4). Phase 2에서 실측으로 정한다.
