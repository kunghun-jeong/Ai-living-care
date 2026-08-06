# Manager AI Analyzer (MAA)

> **구조 정본**: `SOT.md` · **설계 정본**: `docs/spec/AI-Care_Unified_Architecture_Spec_v0.2.md`
> **상위**: `manager_ai_agent/` · **Phase**: 0 · **구현 상태**: 미착수

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
