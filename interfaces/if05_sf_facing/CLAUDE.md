# IF-5 — SF-Facing Interface

> **역할** WAC → PF/RF/AF 호출 — 저수준 정책이 실제 함수가 되는 지점
> **상태** Phase 0 · **부분** — 현재는 함수 직접 호출
> **읽을 절** spec **§2.2**(Worker 컴포넌트, 13줄) · **§4.4**(L3, 80줄) — 그 외 절은 열지 않는다
> **정본** 구조 `SOT.md` · spec §3

Worker AI Core가 **L3 저수준 정책**을 Service Function에 내리는 인터페이스.
IETF I2NSF의 **NSF-Facing Interface**에 대응하는 이름이며, 이 대응이 표준화 논거다 (S-2).

## 전달 대상

`worker_ai_agent/perception/` · `worker_ai_agent/reasoning/` · `worker_ai_agent/action/`
페이로드 스키마는 `contracts/low_level_policy/`.

## 요소명 규칙

L3 요소명은 SF가 실제로 받는 자료구조와 **1:1**로 맞춘다.
예: `<waypoint>` ↔ `Actions._goal_xy_yaw()`가 받는 `{"x","y","frame"?,"yaw_deg"?}`.
어긋나면 Policy Translator에 변환 로직이 쌓여 계층 분리(P-2)가 무너진다.

## 현재 상태

`MCP_server.py`가 `LimoGatewayNode`에서 세 모듈을 직접 생성·주입한다.
즉 **인터페이스가 아직 코드 경계로만 존재하고 규약으로 형식화되지 않았다.**
0-6(Policy Translator) 착수 시 이 계약을 먼저 정의할 것.
