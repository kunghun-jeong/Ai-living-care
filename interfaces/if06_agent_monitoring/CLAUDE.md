# IF-6 — Agent Monitoring Interface

> **역할** PF/RF/AF → WAA 관측 수집 — Report 의 재료가 여기서 온다
> **상태** Phase 0 · 미착수
> **읽을 절** spec **§3** · **§5.1**(Report 스키마) — 그 외 절은 열지 않는다
> **정본** 구조 `SOT.md` · spec §3

Service Function의 실행 상태와 관측값을 Worker AI Analyzer로 올린다.
WAA는 이걸 모아 **Worker Report**를 만든다 (`contracts/worker_report/`).

## 올려야 할 것

| SF | 내용 |
|---|---|
| PF | 프레임 수신 상태, rate, 인코딩, pose |
| RF | 스캔 tick 수, hit 여부, confidence, bbox |
| AF | 웨이포인트 진행, Nav2 goal 상태, 취소·실패 사유 |

## 주의

**G-1·G-2가 이 인터페이스의 출력을 비운다.**
PF가 pose를 안 채우고(G-2) 과거 프레임을 못 꺼내므로(G-1),
Report의 `observation.pose`와 `evidence`가 null이 된다. 0-7·0-8이 선결이다.
