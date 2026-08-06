# Manager AI Analyzer (MAA)

> **SOT**: `docs/spec/AI-Care_Unified_Architecture_Spec_v0.2.md`
> **상위**: `manager/` · **Phase**: 0 · **구현 상태**: 미착수

Worker Report를 해석해 **임무가 달성됐는지 판정**하고, 재시도·Worker 전환·에스컬레이션을 결정한다.
Intent Assurance 폐루프의 상태 전이 함수다.

slide 21은 이 컴포넌트를 `Edge AI Analyzer`로 표기한다 — **`Manager AI Analyzer`가 정식 명칭**이다.
`Edge`는 배치 위치일 뿐 컴포넌트 이름이 아니다 (spec §2.1, D-1).

## 하위

| 하위 | 책임 |
|---|---|
| `report_interpreter/` | Report의 `status`·`observation`·`confidence`를 해석 |
| `assurance_loop/` | 상태 전이 결정 — Assured / Retry / Reselect / Escalated / 잔여 정책 재발행 |

## 인터페이스

- **IF-2** (Analytics) ↔ MAC — 해석 결과와 판정 전달
- **IF-1** (Database) ↔ IAD — 모든 전이를 감사 기록 (P-5)
- IF-8 (Analyzer-Facing) ↔ WAA — 상세 진단 (Phase 2)

## 주의

**A2A TaskState와 report.status는 다른 축이다.** TaskState는 전송 계층의 작업 수명주기,
report.status는 임무의 의미론적 결과다. `COMPLETED` ≠ 정상 — Task가 성공적으로 끝나도 관측 결과는
`abnormal`일 수 있다. 이 분리를 흐리면 **"할머니가 쓰러졌는데 성공으로 보고"** 같은 서술 오류가 난다.
