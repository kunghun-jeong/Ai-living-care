# IF-7 — AMS-Facing Interface

> **역할** WAMS → MAMS 실시간 자원 갱신 — **A2A 의 공백을 메우는 부분** (`S-3`)
> **상태** Phase 2 · 미착수
> **읽을 절** spec **§7.2** — 그 외 절은 열지 않는다
> **정본** 구조 `SOT.md` · spec §3

Worker의 능력·자원·가용성을 Manager 측 Registry에 공시·갱신한다. Agent Card 갱신 경로.

## 왜 이게 차별점인가 (표준화 항목 S-3)

A2A의 Agent Card는 **정적 능력만** 공시한다. 선행 연구가 지적하듯
*"Agent Card만으로는 CPU, Memory, Bandwidth 같은 현재 자원 상태를 충분히 반영하기 어렵다"*
(Duan & Lu, arXiv:2508.15819).

**IF-7은 WAMS가 주기적으로 실시간 자원 상태를 MAMS에 갱신하는 경로**이며,
이것이 `worker_selector/`의 점수 함수에 `availability`·`recent_failure_rate`를 공급한다.
**A2A가 비워둔 자리를 메우는 인터페이스**이므로 제안서의 핵심 논거다.

## 주의

Phase 2 항목이다. Phase 0에서는 Worker 주소·Skill을 고정 설정으로 둔다.
