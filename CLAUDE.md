# AI-Care Edge System

스마트홈 거주자의 **자연어 의도**를 기계 판독 가능한 **고수준 정책**으로 번역하고,
A2A로 이기종 IoT **Worker AI Agent**에 배포해 각자 독립 실행·보고하게 하며,
그 보고를 해석해 재시도·전환·에스컬레이션을 결정하는 **의도 기반 폐루프 리빙케어 프레임워크**.

> **이 저장소의 SOT(Single Source of Truth)는 `docs/spec/AI-Care_Unified_Architecture_Spec_v0.2.md` 이다.**
> 용어·스키마·인터페이스에 이견이 생기면 그 문서를 따른다. 이 디렉터리 구조는 그 문서의 §2·§3를 그대로 옮긴 것이다.

## 상위 과제

IITP RS-2024-00398199 「AI 에이전트 기반 능동형 생활지원을 위한 지능형 리빙케어 프레임워크」 (SKKU 정재훈)
산출물 3종: **프로토타입** · **IITP 표준화 과제 제안서** · **매거진 논문**

## 디렉터리 = 컴포넌트

| 경로 | 정규화 명칭 | 약칭 |
|---|---|---|
| `manager/core/` | Manager AI Core | MAC |
| `manager/analyzer/` | Manager AI Analyzer | MAA |
| `manager/mgmt_system/` | Manager AI Management System | MAMS |
| `manager/knowledge_graph/` | Knowledge Graph | KG |
| `manager/intent_audit_db/` | Intent Audit Database | IAD |
| `worker/core/` | Worker AI Core | WAC |
| `worker/analyzer/` | Worker AI Analyzer | WAA |
| `worker/mgmt_system/` | Worker AI Management System | WAMS |
| `worker/service_functions/{perception,reasoning,action}/` | Perception / Reasoning / Action Function | PF/RF/AF |
| `a2a/` | Secure A2A Channel (IF-4) 바인딩 | — |
| `contracts/` | L1~L3 · Report 스키마 | — |
| `sim/` · `tools/` | 시뮬레이션 · 검증 도구 (컴포넌트 아님) | — |

## Intent-Policy Continuum (L0~L4)

```
L0 Intent (자연어)        "할머니 괜찮은지 확인해줘"
   ↓ Intent Extraction + KG Mapping + Query Composing   [manager/core/]
L1 Intent Query (JSON)    구조화된 의도. 아직 정책 아님   [contracts/intent_query/]
   ↓ LLM + Schema Prompt                                [manager/core/policy_generation/]
L2 High-level Policy      ECA XML. 디바이스 비의존        [contracts/high_level_policy/]
   ↓ A2A (IF-4)                                         [a2a/]
   ↓ Policy Translation                                 [worker/core/policy_translator/]
L3 Low-level Policy       디바이스 특화                   [contracts/low_level_policy/]
   ↓ SF-Facing (IF-5)
L4 Function Call          MCP tool / ROS2 액션            [worker/service_functions/]
```

## 설계 원칙 (스펙 §1.2)

- **P-1 대칭성** — Manager와 Worker는 동일한 3원 구조(Core + Analyzer + Mgmt System)
- **P-2 정책 계층 분리** — 각 계층은 바로 아래 계층만 안다. 계층 간 계약은 스키마로만
- **P-3 판단 위치 최소화** — LLM/VLM은 ①의도 해석 ②최종 상태 판정 ③장애물 차단 시 대체 경로 선택 **세 지점에만** 개입
- **P-4 실패 안전** — 유효한 정책·경로·응답이 없으면 정지 상태를 유지
- **P-5 감사 가능성** — L0~L4 전 계층 변환과 모든 A2A 메시지를 `intent_id`로 상관해 IAD에 기록
- **P-6 전송 독립성** — A2A 의미론은 고정, 전송(stdio / Streamable HTTP)은 배치에 따라 선택

## 현재 Phase: **0 — 단일 Worker 왕복**

최종 목표는 다중 Worker 병렬 + Worker↔Worker 통신이나, 지금은 Manager 1 + Worker 1 + Skill 1 왕복을 닫는 것이 목표다.

### 착수 전 반드시 확인할 것

| # | 항목 | 왜 |
|---|---|---|
| **0-0** | 대화형 WSL 터미널에서 **small_house 카메라 재검증** + 실제 프레임 rate 측정 | 검증 실적은 `turtlebot3_world` 기준. 현재 월드에서 프레임 확보 자체가 미검증 — 여기서 안 나오면 시나리오 1 전체가 성립 안 함 |
| **U-1** | 설치된 `mcp` SDK 프로토콜 리비전 확인 | 클라이언트가 `session.initialize()`를 호출 중 → 구 핸드셰이크가 살아 있을 가능성 |
| **U-12** | ROS2 배포판 통일 | 코드·문서 전부 Jazzy 기준. 실물 LIMO는 통상 Foxy/Humble 출하이고 **ROS2는 배포판 간 통신을 보장하지 않음** |
| **U-14** | Gazebo RTF 0.04~0.06 대응 전략 합의 | 6.3분 시나리오가 벽시계 2시간. `tools/patrol_viz/` 이원화가 현재 유일한 실행안 |

### 크리티컬 갭 (스펙 §10.3)

| ID | 갭 | 위치 |
|---|---|---|
| **G-1** | 프레임 pinning 부재 — 최신 1장만 캐시. 과거 `frame_id` 조회 불가 | `worker/service_functions/perception/` |
| **G-2** | `pose`가 항상 `None` | `worker/service_functions/perception/` |
| **G-3** | person-scan API 5종이 MCP tool로 미노출 | `a2a/server/` |
| **G-4** | `look_around` / patrol 미구현 | `worker/service_functions/action/` |
| **G-5** | stale 콜백 가드 없음 | `worker/service_functions/action/` |
| **G-6** | 장소 룩업(KG 연결점) 부재 | `manager/knowledge_graph/` |

**G-1과 G-2는 시나리오 1의 핵심 경로를 끊는다.**

## 작업 규칙

1. **용어는 스펙 §2를 따른다.** `Edge AI Analyzer`(X) → `Manager AI Analyzer`(O). 슬라이드·논문의 이표기는 §부록 B 대조표 참조.
2. **컴포넌트 경계를 넘는 직접 호출을 만들지 않는다.** 반드시 §3의 인터페이스(IF-1~IF-8)를 경유한다.
3. **스키마를 바꾸면 `contracts/` 먼저 고치고 스펙에 반영한다.** 코드가 스펙을 앞서면 SOT가 깨진다.
4. **`sim/`과 `tools/`는 컴포넌트가 아니다.** 여기에 비즈니스 로직을 두지 않는다.
5. 새 결정을 내리면 스펙의 §0.2(결정 표) 또는 §12(미결정 사항)에 반영한다.

## 실행

```bash
source /opt/ros/jazzy/setup.bash
ros2 launch sim/sim_bringup.launch.py        # Gazebo + Nav2 + slam_toolbox
python3 tools/scenarios/send_goal.py 1.0 0.0 # MCP 왕복 확인
cd tools/patrol_viz && ./run_coverage.sh     # 순찰 로직 경량 검증
```
