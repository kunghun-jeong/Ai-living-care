# Report Interpreter

> **역할** Report 를 읽어 status 를 판정한다
> **상태** Phase 0 · 미착수
> **읽을 절** spec **§5.1**(스키마) · **§5.2**(status 7종) — 그 외 절은 열지 않는다
> **정본** 구조 `SOT.md` · spec §5.1 · §5.2

Worker Report(JSON)를 읽어 임무 결과를 판정한다. 스키마: `contracts/worker_report/`

| status | 의미 | 기본 처리 |
|---|---|---|
| `completed` | 정상 수행, 이상 없음 | 사용자에게 정상 피드백 |
| `abnormal` | 수행 성공, **관측 결과가 이상** | `request[]` 에스컬레이션 |
| `not_found` | 수행했으나 대상 미발견 | 다른 Worker 전환 → 소진 시 에스컬레이션 |
| `failed` | SF 오류·하드웨어 실패 | 재시도 → 임계 초과 시 다른 Worker |
| `partial` | 일부만 수행 | 잔여분 후속 정책 발행 |
| `rejected` | Worker가 수락 거부 | 즉시 재선택 |
| `timeout` | `deadline-sec` 초과 | Task cancel 후 재선택 |

## 주의

`not_found`는 docx의 열린 질문("4곳을 다 봐도 못 찾으면?")을 닫는 값이다.
`request: [caregiver_notify]`를 붙여 `abnormal`과 같은 경로를 타게 한다.
