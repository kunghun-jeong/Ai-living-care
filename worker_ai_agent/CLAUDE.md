# Worker AI Agent

> **구조 정본**: `SOT.md` · **설계 정본**: `docs/spec/AI-Care_Unified_Architecture_Spec_v0.2.md`
> **상위**: 저장소 루트 · **Phase**: 0 · **구현 상태**: 부분 구현 — SF 3종 동작

Manager가 만든 **고수준 정책(L2)** 을 받아 디바이스별 **저수준 정책(L3)** 으로 번역하고,
실제로 수행한 뒤 결과를 Report로 되돌린다.

## 구성 (P-1 대칭성)

| 디렉터리 | 정규화 명칭 | 상태 |
|---|---|---|
| `worker_ai_core/` | Worker AI Core (WAC) | 미착수 — Policy Translator 없음 |
| `worker_ai_analyzer/` | Worker AI Analyzer (WAA) | 미착수 |
| `worker_ai_management_system/` | Worker AI Management System (WAMS) | 미착수 |
| `perception/` | Perception Function (PF) | **구현됨** (G-1·G-2) |
| `reasoning/` | Reasoning Function (RF) | **구현 완성도 최고** |
| `action/` | Action Function (AF) | **구현됨** (G-5, 단일 웨이포인트만 검증) |
| `mcp_server/` | A2A Server + Agent Executor | **동작** — L4만 노출 (G-3) |

논문 Fig.1과 slide 18 표는 Core를 `Worker Controller (Policy Translator)`,
RF를 `Reasoning Function (Rule Based)`로 표기 — 별칭으로만 인정한다.
`(Rule Based)`는 Phase 3에서 RL 기반 선택으로 대체될 예정이라 정식 명칭에서 뺐다.

## 인터페이스

**IF-4**(↔MAC, `mcp_server/`) · **IF-5**(→PF/RF/AF) · **IF-6**(←PF/RF/AF) · IF-3(↔WAMS) · IF-7(↔MAMS, P2)

## 현재 실행 경로

```
mcp_server/MCP_server.py  (LimoGatewayNode)
  ├─ PerceptionModule   → /camera/image_raw 구독
  ├─ ReasoningModule    → detect / plan / person-scan / check_object_state
  └─ ActionModule       → Nav2 NavigateToPose
```

## 주의

**`ReasoningModule`은 ROS2에 의존하지 않는다.** 백엔드를 생성자로 주입받고 미주입 시 no-op으로 동작해
로봇 없이 단독 테스트가 가능하다. **이 저장소에서 가장 잘 분리된 설계이므로 훼손하지 말 것.**
