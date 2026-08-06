# Worker AI Agent

> **SOT**: `docs/spec/AI-Care_Unified_Architecture_Spec_v0.2.md`
> **상위**: 저장소 루트 · **Phase**: 0 · **구현 상태**: 부분 구현 — SF 3종 동작

Manager가 만든 **고수준 정책(L2)** 을 받아 디바이스별 **저수준 정책(L3)** 으로 번역하고,
실제로 수행한 뒤 결과를 Report로 되돌린다.

## 구성 (P-1 대칭성 — Manager와 같은 3원 구조)

| 하위 | 정규화 명칭 | 상태 |
|---|---|---|
| `core/` | Worker AI Core (WAC) | 미착수 — Policy Translator가 없다 |
| `analyzer/` | Worker AI Analyzer (WAA) | 미착수 |
| `mgmt_system/` | Worker AI Management System (WAMS) | 미착수 |
| `service_functions/perception/` | Perception Function (PF) | **구현됨** (G-1·G-2 결함) |
| `service_functions/reasoning/` | Reasoning Function (RF) | **구현 완성도 최고** |
| `service_functions/action/` | Action Function (AF) | **구현됨** (단일 웨이포인트만 검증, G-5 결함) |

논문 Fig.1과 slide 18 표는 Core를 `Worker Controller (Policy Translator)`,
RF를 `Reasoning Function (Rule Based)`로 표기한다 — 별칭으로만 인정한다.
`(Rule Based)` 한정어는 Phase 3에서 RL 기반 선택으로 대체될 예정이라 정식 명칭에서 뺐다.

## 인터페이스

| ID | 상대 | 내용 |
|---|---|---|
| **IF-4** | MAC (Secure A2A Channel) | L2 정책 수신, Task 상태·Artifact 반환 |
| **IF-5** | PF / RF / AF (SF-Facing) | **L3 저수준 정책** |
| **IF-6** | WAA (Agent Monitoring) | SF 실행 상태·관측값 |
| IF-3 | WAMS (Registration) | 자기 등록 |

## 현재 실행 경로

```
a2a/server/MCP_server.py  (LimoGatewayNode)
  ├─ PerceptionModule   → /camera/image_raw 구독
  ├─ ReasoningModule    → detect / plan / person-scan / check_object_state
  └─ ActionModule       → Nav2 NavigateToPose
```

## 주의

**`ReasoningModule`은 ROS2에 의존하지 않는다.** 백엔드를 생성자로 주입받고 미주입 시 no-op으로 동작해
로봇 없이 단독 테스트가 가능하다. **이 저장소에서 가장 잘 분리된 설계이므로 훼손하지 말 것.**
