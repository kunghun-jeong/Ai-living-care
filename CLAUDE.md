# AI-Care Edge System

스마트홈 거주자의 **자연어 의도**를 기계 판독 가능한 **고수준 정책**으로 번역하고,
A2A로 이기종 IoT **Worker AI Agent**에 배포해 각자 독립 실행·보고하게 하며,
그 보고를 해석해 재시도·전환·에스컬레이션을 결정하는 **의도 기반 폐루프 리빙케어 프레임워크**.

> | 문서 | 관할 |
> |---|---|
> | `docs/spec/AI-Care_Unified_Architecture_Spec_v0.2.md` | **설계** — 무엇을 만드는가, 용어, 스키마, 인터페이스 의미 |
> | **`SOT.md`** | **구조** — 어디에 두는가, 디렉터리 이름, 배치 규칙 |
> | `sot_audit.py` | **집행** — `python3 sot_audit.py` 로 기계 검사 |
>
> 우선순위는 **spec > SOT > 코드**. 코드가 앞서면 SOT를 고치고, SOT가 앞서면 spec에 반영한다.

## 상위 과제

IITP RS-2024-00398199 「AI 에이전트 기반 능동형 생활지원을 위한 지능형 리빙케어 프레임워크」 (SKKU 정재훈)
산출물 3종: **프로토타입** · **IITP 표준화 과제 제안서** · **매거진 논문**

## 디렉터리 = 컴포넌트 (스펙 §2)

| 디렉터리 | 정규화 명칭 | 약칭 |
|---|---|---|
| `manager_ai_agent/manager_ai_core/` | Manager AI Core | MAC |
| `manager_ai_agent/manager_ai_analyzer/` | Manager AI Analyzer | MAA |
| `manager_ai_agent/manager_ai_management_system/` | Manager AI Management System | MAMS |
| `manager_ai_agent/knowledge_graph/` | Knowledge Graph | KG |
| `manager_ai_agent/intent_audit_database/` | Intent Audit Database | IAD |
| `manager_ai_agent/mcp_client/` | A2A Client (IF-4 Manager 측) | — |
| `worker_ai_agent/worker_ai_core/` | Worker AI Core | WAC |
| `worker_ai_agent/worker_ai_analyzer/` | Worker AI Analyzer | WAA |
| `worker_ai_agent/worker_ai_management_system/` | Worker AI Management System | WAMS |
| `worker_ai_agent/perception/` | Perception Function | PF |
| `worker_ai_agent/reasoning/` | Reasoning Function | RF |
| `worker_ai_agent/action/` | Action Function | AF |
| `worker_ai_agent/mcp_server/` | A2A Server + Agent Executor (IF-4 Worker 측) | — |
| `interfaces/if01…if08/` | 인터페이스 카탈로그 IF-1~IF-8 | — |
| `contracts/` | L1~L3 · Report 페이로드 스키마 | — |
| `sim/` `tools/` `docs/` | 비컴포넌트 | — |

## Intent-Policy Continuum (L0~L4)

```
L0 Intent (자연어)     "할머니 괜찮은지 확인해줘"
   ↓ Extraction + KG Mapping + Composing      [manager_ai_agent/manager_ai_core/]
L1 Intent Query (JSON)                        [contracts/intent_query/]
   ↓ LLM + Schema Prompt                      [manager_ai_agent/manager_ai_core/policy_generation/]
L2 High-level Policy (ECA XML)                [contracts/high_level_policy/]
   ↓ IF-4 Secure A2A Channel                  [interfaces/if04_secure_a2a_channel/]
   ↓ Policy Translation                       [worker_ai_agent/worker_ai_core/policy_translator/]
L3 Low-level Policy                           [contracts/low_level_policy/]
   ↓ IF-5 SF-Facing
L4 Function Call                              [worker_ai_agent/{perception,reasoning,action}/]
```

## 설계 원칙 (스펙 §1.2)

- **P-1 대칭성** — Manager와 Worker는 동일한 3원 구조(Core + Analyzer + Management System)
- **P-2 정책 계층 분리** — 각 계층은 바로 아래 계층만 안다. 계층 간 계약은 스키마로만
- **P-3 판단 위치 최소화** — LLM/VLM은 ①의도 해석 ②최종 상태 판정 ③장애물 차단 시 대체 경로 선택 **세 지점에만**
- **P-4 실패 안전** — 유효한 정책·경로·응답이 없으면 정지 상태를 유지
- **P-5 감사 가능성** — L0~L4 전 계층 변환과 모든 A2A 메시지를 `intent_id`로 상관해 IAD에 기록
- **P-6 전송 독립성** — A2A 의미론은 고정, 전송(stdio / Streamable HTTP)은 배치에 따라 선택

## 현재 Phase: **0 — 단일 Worker 왕복**

최종 목표는 다중 Worker 병렬 + Worker↔Worker 통신이나, 지금은 Manager 1 + Worker 1 + Skill 1 왕복을 닫는 것이 목표다.

### 착수 전 반드시 확인할 것

| # | 항목 | 왜 |
|---|---|---|
| **0-0** | 대화형 WSL 터미널에서 **small_house 카메라 재검증** + 실제 프레임 rate 측정 | 검증 실적은 `turtlebot3_world` 기준. 현재 월드에서 프레임 확보 자체가 미검증 |
| **U-1** | 설치된 `mcp` SDK 프로토콜 리비전 확인 | 클라이언트가 `session.initialize()` 호출 중 → 구 핸드셰이크 잔존 가능성 |
| **U-12** | ROS2 배포판 통일 | 코드·문서 전부 Jazzy 기준. 실물 LIMO는 통상 Foxy/Humble이고 **ROS2는 배포판 간 통신을 보장하지 않음** |
| **U-14** | Gazebo RTF 0.04~0.06 대응 전략 합의 | 6.3분 시나리오가 벽시계 2시간 |

### 크리티컬 갭 (스펙 §10.3)

| ID | 갭 | 위치 |
|---|---|---|
| **G-1** | 프레임 pinning 부재 — 최신 1장만 캐시. 과거 `frame_id` 조회 불가 | `worker_ai_agent/perception/` |
| **G-2** | `pose`가 항상 `None` | `worker_ai_agent/perception/` |
| **G-3** | person-scan API 5종이 MCP tool로 미노출 | `worker_ai_agent/mcp_server/` |
| **G-4** | `look_around` / patrol 미구현 | `worker_ai_agent/action/` |
| **G-5** | stale 콜백 가드 없음 | `worker_ai_agent/action/` |
| **G-6** | 장소 룩업(KG 연결점) 부재 | `manager_ai_agent/knowledge_graph/` |

**G-1과 G-2는 시나리오 1의 핵심 경로를 끊는다.**

## 작업 규칙

1. **용어는 스펙 §2, 배치는 SOT를 따른다.** 축약 디렉터리(`core/` `analyzer/`)를 만들지 않는다.
2. **컴포넌트 경계를 넘는 직접 호출을 만들지 않는다.** 반드시 `interfaces/`의 IF-1~IF-8을 경유한다.
3. **스키마를 바꾸면 `contracts/` 먼저 고치고 스펙에 반영한다.**
4. **`sim/` `tools/`는 컴포넌트가 아니다.** 비즈니스 로직을 두지 않는다.
5. 구조를 바꾸면 `python3 sot_audit.py`를 돌려 통과시킨다.

## 실행

```bash
source /opt/ros/jazzy/setup.bash
ros2 launch sim/sim_bringup.launch.py
python3 tools/scenarios/send_goal.py 1.0 0.0
cd tools/patrol_viz && ./run_coverage.sh
python3 sot_audit.py
```
