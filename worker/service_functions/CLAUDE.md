# Service Functions (PF / RF / AF)

> **SOT**: `docs/spec/AI-Care_Unified_Architecture_Spec_v0.2.md`
> **상위**: `worker/` · **Phase**: 0 · **구현 상태**: 구현됨

WAC이 IF-5로 내린 **L3 저수준 정책**을 실제로 수행하는 3종 기능.

| 하위 | 명칭 | 파일 | 상태 |
|---|---|---|---|
| `perception/` | Perception Function (PF) | `Perceptions.py` | 동작. **G-1·G-2 결함** |
| `reasoning/` | Reasoning Function (RF) | `Reasonings.py` | 순수 로직 완성 |
| `action/` | Action Function (AF) | `Actions.py` | 동작. 단일 웨이포인트만 검증, **G-5 결함** |

## 인터페이스

- IF-5 (SF-Facing) ← WAC — 저수준 정책 수신
- IF-6 (Agent Monitoring) → WAA — 실행 상태·관측값

## import 규칙 (이동 후)

세 파일은 각각 다른 디렉터리에 있지만 **모듈명은 그대로**다 (`Perceptions`, `Reasonings`, `Actions`).
`a2a/server/MCP_server.py`가 세 디렉터리를 `sys.path`에 추가하므로 기존 import가 그대로 동작한다.
패키지화(`__init__.py` + 상대 import)는 Phase 1의 정리 항목이다.

## 주의

**SF는 로봇 비의존이어야 한다.** `Actions.py`는 Nav2 액션만, `Reasonings.py`는 아무 ROS2 인터페이스도
말하지 않는다. 덕분에 turtlebot3 → 실물 LIMO 교체 시 이 디렉터리는 손대지 않아도 된다.
이 성질을 깨는 코드를 넣지 말 것.
