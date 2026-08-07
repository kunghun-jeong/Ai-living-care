# Manager AI Analyzer (MAA)

> **역할** Worker Report 를 해석해 재시도·전환·에스컬레이션을 결정한다
> **상태** Phase 0 · 미착수
> **읽을 절** spec **§5.2**(status 열거, 14줄) · **§5.3**(폐루프, 30줄) — 그 외 절은 열지 않는다
> **정본** 구조 `SOT.md` · spec §5

Worker Report를 해석해 **임무 달성 여부를 판정**하고 재시도·Worker 전환·에스컬레이션을 결정한다.
Intent Assurance 폐루프의 상태 전이 함수다.

slide 21은 `Edge AI Analyzer`로 표기 — **`Manager AI Analyzer`가 정식 명칭**이다.
`Edge`는 배치 위치일 뿐 컴포넌트 이름이 아니다 (D-1).

| 하위 | 책임 |
|---|---|
| `report_interpreter/` | Report의 `status`·`observation`·`confidence` 해석 |
| `assurance_loop/` | Assured / Retry / Reselect / Escalated / 잔여 정책 재발행 결정 |

## 인터페이스

IF-2(↔MAC) · IF-1(→IAD, 전이 감사 기록) · IF-8(↔WAA, Phase 2)

## 주의

**A2A TaskState와 report.status는 다른 축이다.** 전자는 전송 계층의 작업 수명주기,
후자는 임무의 의미론적 결과다. `COMPLETED` ≠ 정상 — Task가 성공해도 관측은 `abnormal`일 수 있다.
이 분리를 흐리면 **"할머니가 쓰러졌는데 성공으로 보고"** 같은 서술 오류가 난다.
