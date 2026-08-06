#!/usr/bin/env python3
"""AI-Care SOT 재구조화 스크립트.

AI-Care_Unified_Architecture_Spec_v0.2.md §2(정규화된 컴포넌트) / §3(인터페이스 카탈로그)
를 그대로 디렉터리 구조로 옮기고, 각 컴포넌트에 CLAUDE.md를 생성한다.

단계별로 실행한다 (각 단계가 개별 커밋):
    python3 sot_restructure.py tree    # 디렉터리 + CLAUDE.md 생성
    python3 sot_restructure.py move    # git mv + 경로 참조 수정
    python3 sot_restructure.py docs    # 루트 문서를 docs/로 정리
    python3 sot_restructure.py verify  # 결과 점검 (커밋 없음)

저장소 루트에서 실행할 것. 각 단계는 멱등(idempotent)하다.
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SPEC = "docs/spec/AI-Care_Unified_Architecture_Spec_v0.2.md"


def sh(cmd, check=True):
    r = subprocess.run(cmd, shell=True, cwd=ROOT, capture_output=True, text=True)
    if check and r.returncode != 0:
        print(f"  ! {cmd}\n    {r.stderr.strip()}")
    return r


def tracked(path):
    return sh(f'git ls-files --error-unmatch "{path}"', check=False).returncode == 0


def gmv(src, dst):
    """git mv (추적 중이면) 또는 일반 mv. 이미 옮겨졌으면 조용히 넘어간다."""
    if not os.path.exists(os.path.join(ROOT, src)):
        print(f"  - skip (없음): {src}")
        return
    os.makedirs(os.path.join(ROOT, os.path.dirname(dst)), exist_ok=True)
    if tracked(src):
        r = sh(f'git mv -k "{src}" "{dst}"')
        if r.returncode == 0:
            print(f"  git mv  {src} -> {dst}")
    else:
        sh(f'mv "{src}" "{dst}"')
        print(f"  mv      {src} -> {dst}")


# ─────────────────────────────────────────────────────────────────────────────
# CLAUDE.md 본문
#   key   : 디렉터리 경로 ("" = 저장소 루트)
#   title : 제목
#   meta  : 헤더 인용 블록에 들어갈 (상위, Phase, 상태)
#   body  : 본문
# ─────────────────────────────────────────────────────────────────────────────

C = {}


def comp(path, title, parent, phase, state, body):
    C[path] = f"""# {title}

> **SOT**: `{SPEC}`
> **상위**: {parent} · **Phase**: {phase} · **구현 상태**: {state}

{body.strip()}
"""


# ── 루트 ─────────────────────────────────────────────────────────────────────
C[""] = f"""# AI-Care Edge System

스마트홈 거주자의 **자연어 의도**를 기계 판독 가능한 **고수준 정책**으로 번역하고,
A2A로 이기종 IoT **Worker AI Agent**에 배포해 각자 독립 실행·보고하게 하며,
그 보고를 해석해 재시도·전환·에스컬레이션을 결정하는 **의도 기반 폐루프 리빙케어 프레임워크**.

> **이 저장소의 SOT(Single Source of Truth)는 `{SPEC}` 이다.**
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
| `worker/service_functions/{{perception,reasoning,action}}/` | Perception / Reasoning / Action Function | PF/RF/AF |
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
"""

# ── docs ─────────────────────────────────────────────────────────────────────
C["docs"] = f"""# docs — 문서 저장소

## 무엇이 어디에

| 경로 | 내용 | 신뢰도 |
|---|---|---|
| `spec/AI-Care_Unified_Architecture_Spec_v0.2.md` | **SOT.** 정규화 용어, IF-1~IF-8, L0~L4 정책 계층, A2A-over-MCP 바인딩, 로드맵, 표준화 항목 | **정본** |
| `context/` | 배경 컨텍스트 — A2A 개념 매핑, RCP/MCP 결정 기록, ViLaR-IMO 연계, 연구 자료 계보 | 참고 |
| `handoff/` | 세션 인수인계 — 왜 그렇게 했는지, 다시 겪지 않아도 될 함정 | 참고 |
| `audit/` | IETF-125/126 승계 판정 | **참고 전용, 결정 아님** |
| `slides/` | UKC2026 발표 덱 (42MB, git 제외) | 원본 |

## 읽는 순서

처음 합류하면:

1. 루트 `CLAUDE.md` — 전체 그림과 현재 Phase
2. `spec/` §1~§5 — 설계 원칙, 컴포넌트, 인터페이스, 정책 계층, Report
3. `spec/` §10 — 기존 자산, 시뮬 환경, 크리티컬 갭, Phase 계획
4. `handoff/` — 실제로 겪은 함정 (재발 방지)
5. 담당할 컴포넌트 디렉터리의 `CLAUDE.md`

## 주의

- **`spec/`이 정본이다.** 다른 문서와 어긋나면 spec을 따르고, spec이 틀렸으면 spec을 고친다.
- **`audit/IETF승계issue.md`는 참고 자료다.** 판정이 스펙에 반영되지 않았다. 채택하기로 하면 그때 옮긴다.
- **슬라이드와 UKC 논문에는 용어 불일치가 있다.** spec §2.4와 부록 B의 대조표를 먼저 볼 것.
- `slides/*.pptx`는 `.gitignore` 대상이다 (42MB). 로컬에만 둔다.
"""

# ── manager ──────────────────────────────────────────────────────────────────
comp("manager", "Manager AI Agent", "저장소 루트", "0", "부분 (Core만 착수 예정)", """
사용자의 자연어 의도를 해석해 **고수준 정책(L2)** 을 만들고, 적절한 Worker를 선택해 A2A로 배포하며,
돌아온 Report를 해석해 재시도·전환·에스컬레이션을 결정한다.

## 구성 (P-1 대칭성)

| 하위 | 정규화 명칭 | 책임 |
|---|---|---|
| `core/` | Manager AI Core (MAC) | Intent Translator + Session Key Manager. L0→L1→L2 변환의 주체 |
| `analyzer/` | Manager AI Analyzer (MAA) | Report 해석, 임무 완료 판정, 재시도/Worker 전환 결정 |
| `mgmt_system/` | Manager AI Management System (MAMS) | Worker 등록·상태·수명주기. **Agent Registry 역할 겸함** |
| `knowledge_graph/` | Knowledge Graph (KG) | 사용자·공간·디바이스의 관계와 능력 (누가 무엇을 할 수 있는가) |
| `intent_audit_db/` | Intent Audit Database (IAD) | intent/policy 이력, 스키마 프롬프트, 검증 규칙 |

> **KG와 IAD는 별개다.** 원 자료(slide 16·17·21, 논문 Fig.1)에서 이 자리에 박스가 하나만 그려져 있고
> 자료마다 이름이 다르지만, 접근 패턴과 수명이 달라 두 저장소로 분리했다. spec §2.3 참조.

## 인터페이스

| ID | 상대 | 내용 |
|---|---|---|
| IF-1 | KG / IAD | KG 조회, intent·policy 감사 레코드, KB audit |
| IF-2 | MAA | 해석된 report, 완료/재시도/전환 판정 |
| IF-3 | MAMS | Worker 등록·조회·상태 |
| **IF-4** | **WAC (Secure A2A Channel)** | **L2 고수준 정책, Task 상태, Artifact** |
| IF-7 | WAMS | Worker 능력·자원·가용성 공시 (Phase 2) |
| IF-8 | WAA | 상세 진단·이상 이벤트 (Phase 2) |

## 주의

docx는 Manager를 "우리 스코프 아님"으로 두었으나 **2026-08-06 사용자 결정으로 구현 범위에 포함**됐다.
단 KG는 그래프DB가 아니라 JSON 룩업으로 간소 구현한다 (D-6).
""")

comp("manager/core", "Manager AI Core (MAC)", "`manager/`", "0", "미착수", """
**Intent Translator + Session Key Manager.** L0(자연어) → L1(Intent Query) → L2(High-level Policy) 변환의 주체.

논문 Fig.1과 slide 17의 표는 이 컴포넌트를 `Manager Controller`로 표기한다 — **별칭으로만 인정**하고
정식 명칭은 `Manager AI Core`다 (spec §2.1).

## 파이프라인

```
"Check if Grandma is okay"
  → intent_extraction/     ["Grandma", "check", "is okay"]
  → kg_mapping/            IF-1로 KG 조회 → phrase별 element=value 바인딩
  → query_composing/       L1 Intent Query JSON
  → policy_generation/     LLM + Schema Prompt → L2 ECA XML
```

`session_key_manager/`는 이 흐름과 직교하며 IF-4의 세션 키를 발급·갱신한다.

## 반드시 지킬 것

- **L2에 디바이스 이름을 넣지 않는다.** L2는 device-agnostic이어야 다중 Worker fan-out이 성립한다.
  어느 Worker가 수행할지는 MAMS의 배포 결정이다 (spec §4.3).
- **`bindings`를 반드시 남긴다.** 어느 어구가 어떤 값으로 해소됐는지 없으면 오역 디버깅이 불가능하다 (P-5).
- **LLM 실패 경로를 설계에 포함한다.** P-4. 정상 파싱 → 필드 정규화 → 규칙 기반 폴백 3단 구조를 권장한다.

## 작업 (Phase 0)

- [ ] 0-3 L0→L2 파이프라인 전체
- [ ] LLM 선택 확정 (U-3: Claude API vs Ollama Llama 3.1 vs 로컬 소형)
- [ ] L2 직렬화 형식 확정 (U-2: 내부 JSON / 표준 문서 XML 양방향 변환 권고)
""")

comp("manager/core/intent_extraction", "Intent Extraction", "`manager/core/`", "0", "미착수", """
자연어 발화에서 의미 어구를 뽑는다. 여기서 **의미를 해소하지 않는다** — 해소는 `kg_mapping/`의 일이다.

## 계약

```
extract(utterance: str) -> list[str]
# "Check if Grandma is okay" -> ["Grandma", "check", "is okay"]
```

## 주의

- 어구 경계는 KG의 `phrase_bindings` 키와 맞아야 매핑이 성립한다. 두 컴포넌트를 함께 바꿀 것.
- 추출 결과는 L1의 `bindings[].phrase`로 그대로 흘러간다 (P-5).
""")

comp("manager/core/kg_mapping", "KG Mapping", "`manager/core/`", "0", "미착수", """
추출된 어구를 KG에 조회해 `element = value` 바인딩으로 해소한다. **IF-1(Database Interface)** 경유.

## 계약

```
resolve(phrase: str, context: dict) -> list[Binding]
Binding = {"element": str, "value": any, "confidence": float, "source": str}
```

slide 21의 KG mapping 표를 그대로 직렬화한 형태:

| PHRASE | ELEMENT → RETRIEVED VALUE |
|---|---|
| "Grandma" | `target = elder`, `place = living_room` |
| "check" | `task = safety_check`, `mobile = [LIMO_1, LIMO_2]` |
| "is okay" | `condition = realtime`, `sensor = camera` |

## 주의

- **KG를 직접 파일로 읽지 말 것.** IF-1 계약을 통해서만 접근해야 후일 그래프DB로 무중단 교체할 수 있다 (D-6).
- `confidence`를 반드시 채운다. 낮은 신뢰도 바인딩은 L2 생성 시 사용자 확인(MRTR)으로 승격될 수 있다.
""")

comp("manager/core/query_composing", "Intent Query Composing", "`manager/core/`", "0", "미착수", """
바인딩을 모아 **L1 Intent Query(JSON)** 를 만든다. 아직 정책이 아니다 — 구조화된 의도다.

스키마: `contracts/intent_query/`

## 필드 출처

| 필드 | 출처 |
|---|---|
| `intent`, `target`, `task`, `condition`, `place`, `devices` | slide 21 원본 |
| `sensors` | KG 매핑표에는 있으나 원본 composed JSON에서 누락된 것을 복원 |
| `intent_id`, `raw_utterance`, `issued_by`, `issued_at`, `bindings` | 이 스펙이 추가 (P-5 감사 가능성) |

## 주의

`devices`는 **후보 힌트**일 뿐이다. 확정은 MAMS의 Worker 선택이 한다 (spec §7.2).
여기서 정한 디바이스가 L2로 넘어가면 안 된다.
""")

comp("manager/core/policy_generation", "High-level Policy Generation", "`manager/core/`", "0", "미착수", """
L1 Intent Query + Schema Prompt를 LLM에 넣어 **L2 High-level Policy (ECA XML)** 를 생성한다.

스키마: `contracts/high_level_policy/`

## 생성 결과 형태

```xml
<living-care-policy>
  <policy-id/> <intent-id/> <policy-name/> <issued-by/> <issued-at/>
  <rule>
    <rule-name/>
    <event><event-type/><trigger/></event>
    <condition><target-role/><place/><modality/></condition>
    <action><action-type/><required-skill/>…<dispatch-mode/></action>
  </rule>
  <assurance><deadline-sec/><report-mode/><escalation-on/></assurance>
</living-care-policy>
```

## 반드시 지킬 것

- **디바이스 이름 금지** (P-2). `<required-skill>`이 Worker 선택의 유일한 기준이다.
- **`<assurance>`를 비우지 않는다.** `not_found`·`timeout` 후속 액션이 여기서 선언적으로 정해진다.
- **스키마 검증을 통과하지 못한 출력은 정책으로 승격하지 않는다** (P-4).
  검증 실패 → 재생성 → 그래도 실패 → 규칙 기반 폴백 또는 사용자 확인.

## 주의

Ollama를 쓸 경우 호출에 `format: "json"`을 걸어 출력 형식을 강제할 수 있다.
LLM 실패 시 폴백 설계는 `docs/audit/IETF승계issue.md` §4.1 참조 (참고 자료).
""")

comp("manager/core/session_key_manager", "Session Key Manager", "`manager/core/`", "1", "미착수", """
IF-4(Secure A2A Channel)의 세션 키를 발급·검증·갱신한다. Worker 측 대응은 `worker/core/session_key_handler/`.

## Phase별 범위

| Phase | 내용 |
|---|---|
| 0 | stdio 로컬 통신 — OS 프로세스 격리에 의존. 키 발급만 인메모리로 |
| 1+ | mTLS over Streamable HTTP, rekeying 주기 정책화 |
| 2+ | Skill 단위 권한, `AUTH_REQUIRED` TaskState 활용 |

## 주의

slide 16·18은 **Action Function이 실제 액추에이션 직전에 Session Key Check를 한 번 더** 수행하도록
명시한다. 즉 키 검증이 Core에만 있지 않은 **이중 검증 구조**다. 이 설계를 유지할 것 (표준화 항목 S-4의 근거).
""")

comp("manager/analyzer", "Manager AI Analyzer (MAA)", "`manager/`", "0", "미착수", """
Worker Report를 해석해 **임무가 달성됐는지 판정**하고, 재시도·Worker 전환·에스컬레이션을 결정한다.
Intent Assurance 폐루프의 상태 전이 함수다.

slide 21은 이 컴포넌트를 `Edge AI Analyzer`로 표기한다 — **`Manager AI Analyzer`가 정식 명칭**이다.
`Edge`는 배치 위치일 뿐 컴포넌트 이름이 아니다 (spec §2.1, D-1).

## 하위

| 하위 | 책임 |
|---|---|
| `report_interpreter/` | Report의 `status`·`observation`·`confidence`를 해석 |
| `assurance_loop/` | 상태 전이 결정 — Assured / Retry / Reselect / Escalated / 잔여 정책 재발행 |

## 인터페이스

- **IF-2** (Analytics) ↔ MAC — 해석 결과와 판정 전달
- **IF-1** (Database) ↔ IAD — 모든 전이를 감사 기록 (P-5)
- IF-8 (Analyzer-Facing) ↔ WAA — 상세 진단 (Phase 2)

## 주의

**A2A TaskState와 report.status는 다른 축이다.** TaskState는 전송 계층의 작업 수명주기,
report.status는 임무의 의미론적 결과다. `COMPLETED` ≠ 정상 — Task가 성공적으로 끝나도 관측 결과는
`abnormal`일 수 있다. 이 분리를 흐리면 **"할머니가 쓰러졌는데 성공으로 보고"** 같은 서술 오류가 난다.
""")

comp("manager/analyzer/report_interpreter", "Report Interpreter", "`manager/analyzer/`", "0", "미착수", """
Worker Report(JSON)를 읽어 임무 결과를 판정한다. 스키마: `contracts/worker_report/`

## `status` 열거값과 기본 처리

| status | 의미 | 기본 처리 |
|---|---|---|
| `completed` | 정상 수행, 이상 없음 | 사용자에게 정상 피드백 |
| `abnormal` | 수행 성공, **관측 결과가 이상** | `request[]` 에스컬레이션 |
| `not_found` | 수행했으나 대상 미발견 | 다른 Worker 전환 / 탐색 확대 → 소진 시 에스컬레이션 |
| `failed` | SF 오류·하드웨어 실패 | 재시도 → 임계 초과 시 다른 Worker |
| `partial` | 일부만 수행 | 잔여분에 대해 후속 정책 발행 |
| `rejected` | Worker가 정책 수락 거부 | 즉시 다른 Worker 재선택 |
| `timeout` | `deadline-sec` 초과, report 없음 | Task cancel 후 재선택 |

## 주의

`not_found`는 docx의 열린 질문("4곳을 다 봐도 못 찾으면?")을 닫는 값이다.
`request: [caregiver_notify]`를 붙여 `abnormal`과 같은 에스컬레이션 경로를 타게 한다.
""")

comp("manager/analyzer/assurance_loop", "Intent Assurance Loop", "`manager/analyzer/`", "0", "미착수", """
판정 결과에 따라 다음 행동을 결정하는 상태기계. 모든 전이는 IAD에 기록된다 (P-5).

```
IntentReceived → PolicyGenerated → WorkerSelected → Dispatched → Executing → Reported
Reported ─ completed ──────────────→ Assured
         ├ abnormal / not_found(소진) → Escalated
         ├ failed / timeout ─────────→ Retry ─ (<N) → Dispatched
         │                                   └ (≥N) → Reselect
         ├ rejected / not_found(잔존) → Reselect ─ 후보 잔존 → WorkerSelected
         │                                        └ 소진   → Escalated
         └ partial ──────────────────→ PolicyGenerated (잔여 정책 재생성)
```

## 주의

**루프가 수렴하는지 반드시 확인할 것.** 재시도 횟수 상한과 후보 소진 조건이 없으면
`failed → Retry → Dispatched → failed`가 무한히 돈다. Phase 0부터 상한을 넣는다.
""")

comp("manager/mgmt_system", "Manager AI Management System (MAMS)", "`manager/`", "0", "미착수", """
Worker의 등록·상태·수명주기를 관리하고, **Agent Registry 역할을 겸한다.**

slide 21은 `Edge AI's Mgmt System`으로 표기 — 정식 명칭은 `Manager AI Management System` (D-1).

## 하위

| 하위 | 책임 | Phase |
|---|---|---|
| `agent_registry/` | Worker 주소·Skill·자원 상태 보관 및 조회 | 0 (고정 설정) → 2 (동적) |
| `worker_selector/` | `required-skill` 기준 후보 필터링·점수화·선택 | 2 |

## 왜 이게 표준화 항목인가 (S-3)

A2A는 Agent Discovery 방식은 제시하지만 **레지스트리 데이터 모델과 Worker 선택 로직은 구현자 몫**으로 남긴다.
게다가 Agent Card만으로는 CPU·메모리·대역폭 등 **실시간 자원 상태를 반영하기 어렵다**
(Duan & Lu, arXiv:2508.15819). **MAMS + IF-7이 정확히 그 공백을 메운다.**

## 주의

Phase 0에서는 Worker 주소를 고정 설정으로 둬도 된다. Worker 수가 늘면 그때 동적 레지스트리로 승격한다.
""")

comp("manager/mgmt_system/agent_registry", "Agent Registry", "`manager/mgmt_system/`", "0", "미착수", """
Worker의 접속 정보와 능력을 보관·조회한다. A2A Agent Card의 수집처.

## 계약 (초안)

```
register(agent_id, agent_card) -> None
lookup(required_skills: list[str]) -> list[AgentRef]
update_resources(agent_id, resources) -> None   # IF-7, Phase 2
```

## 주의

**Registry는 후보를 제공할 뿐 최종 선택을 하지 않는다.** 선택은 `worker_selector/`의 책임이다 (A2A 명세 경계).
""")

comp("manager/mgmt_system/worker_selector", "Worker Selector", "`manager/mgmt_system/`", "2", "미착수", """
L2 정책의 `<required-skill>`을 만족하는 Worker를 골라 배포 대상을 확정한다.

## 알고리즘 초안 (spec §7.2)

```
1. Registry 조회: required-skill 전부를 공시한 Worker 집합 C
2. 필터: 가용(alive) ∧ 자원 충족 ∧ 세션 유효
3. 점수화: score(w) = α·capability_match + β·proximity(place)
                    + γ·availability − δ·recent_failure_rate
4. dispatch-mode에 따라 상위 1개(or-fallback) 또는 상위 k개(or-race, k ≤ max-parallel)
5. rejected 수신 시 해당 Worker 제외하고 재선택
```

## dispatch-mode 5종

| 모드 | 완료 조건 | 예 |
|---|---|---|
| `and-all` | 전부 `completed` | "전등 다 끄고 문 잠가줘" |
| `or-race` | 최초 성공. **나머지 취소** | **시나리오 1** — LIMO_1/LIMO_2 중 먼저 찾는 쪽 |
| `or-fallback` | 순차 시도, 최초 성공 or 후보 소진 | 동시 기동 자원이 부족할 때 |
| `sequential` | 마지막 단계 완료 | "찾아서 확인하고, 이상하면 디스펜서 열어" |
| `split` | 모든 파티션 완료 | "1층 LIMO_1, 2층 LIMO_2" |

## 주의

α·β·γ·δ 가중치는 미정 (U-4). Phase 2에서 실측으로 정한다.
""")

comp("manager/knowledge_graph", "Knowledge Graph (KG)", "`manager/`", "0", "미착수 — G-6", """
사용자·공간·디바이스의 **관계와 능력**을 보유한다 — 누가 무엇을 할 수 있는가.
`intent_audit_db/`(감사 이력)와는 별개다 (spec §2.3).

## Phase 0: JSON 룩업으로 간소 구현 (D-6)

인터페이스 계약을 아래로 **고정**하여 후일 그래프DB로 무중단 교체한다.

```
resolve(phrase: str, context: dict) -> list[Binding]
```

`kg.json` 형태:

```json
{
  "entities": {
    "grandma":     {"type": "person", "role": "elder", "usual_place": "living_room"},
    "living_room": {"type": "space", "map_frame": "map", "pose": {"x":…, "y":…, "yaw":…}},
    "LIMO_1":      {"type": "device", "skills": ["navigate","person-scan","state-check"],
                    "sensors": ["camera","lidar"], "agent_uri": "stdio://limo_1"}
  },
  "phrase_bindings": { "grandma": [...], "check": [...], "is okay": [...] }
}
```

## G-6 — 이 컴포넌트가 채워야 할 공백

현재 코드에 `list_locations` / `locations.json`이 **없다.** `plan_and_navigate`는 좌표만 받는다.
따라서 L2 정책의 `<location-label>living_room`을 좌표로 해소할 경로가 없다.

**좌표 ↔ 방 이름 매핑을 만드는 것이 곧 G-6 해소이자 `entities.<space>` 채우기다** (작업 0-10).

## 주의 (중요)

- 저장소에서 좌표에 **의미 있는 이름이 붙은 것은 두 개뿐**이다:
  `(8.10, 1.71)`="식탁 구역", `(-7.77, 0.56)`="좌상단 방" (`tools/patrol_viz/`).
  **나머지 5개 순찰 좌표에는 방 이름이 부여된 바 없다.** 임의로 붙이지 말 것.
- docx의 `locations.json`(`living_room = (1.2, 0.4)`)은 **별개 출처이며 small_house 좌표계와 무관하다.**
  두 좌표계를 섞지 말 것.
- `phrase_bindings`는 데모용 지름길이다. Phase 1에서 `entities` 그래프 순회 + 임베딩 유사도로 대체하고,
  이 표는 회귀 테스트의 정답셋으로 전환한다.
""")

comp("manager/intent_audit_db", "Intent Audit Database (IAD)", "`manager/`", "1", "미착수", """
intent·policy 이력, 스키마 프롬프트, 검증 규칙을 보관한다. **Intent Validator 기능을 포함**한다.
`knowledge_graph/`(도메인 지식)와는 접근 패턴과 수명이 다르다.

| | Knowledge Graph | **Intent Audit Database** |
|---|---|---|
| 담는 것 | elder는 보통 living_room에 있다 | 14:03 intent#a1b2 → policy#p7 → LIMO_1 → status=abnormal |
| 접근 | KG Mapping 단계, 읽기 위주 | 전 계층, **쓰기 위주** + 정책 생성 시 스키마/프롬프트 읽기 |
| 표준화 관점 | 도메인 데이터 모델 | **감사·보증(assurance) 데이터 모델 (S-5)** |

## P-5를 실현하는 곳

L0~L4 전 계층의 변환 결과와 모든 A2A 메시지가 `intent_id`로 상관되어 여기에 기록된다.
**end-to-end 블랙박스 정책 대비 이 프레임워크의 핵심 장점**이므로 논문·제안서의 논거이기도 하다.

## 승계할 인터페이스 계약

조직 선행 구현(IETF-125 `k8s_server.py`)의 엔드포인트를 **계약 그대로 승계**하는 것을 검토 중이다:

- `POST /inference` — JSON + base64 이미지 → `logs/json/`, `logs/images/`
- `POST /receive_policy` — YAML 정책 수신

**ViLaR-IMO 트랙이 지금도 `/inference`를 쓰므로, 계약을 유지하면 두 트랙이 같은 감사 저장소를 공유한다.**
자세한 판정은 `docs/audit/IETF승계issue.md` §5 (참고 자료, 미채택).
""")

# ── worker ───────────────────────────────────────────────────────────────────
comp("worker", "Worker AI Agent", "저장소 루트", "0", "부분 구현 — SF 3종 동작", """
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
""")

comp("worker/core", "Worker AI Core (WAC)", "`worker/`", "0", "미착수", """
**Policy Translator + Session Key Handler.** L2 고수준 정책을 받아 L3 저수준 정책으로 번역하고
SF에 IF-5로 내린다.

## 하위

| 하위 | 책임 |
|---|---|
| `policy_translator/` | L2 → L3 번역 |
| `agent_executor/` | A2A Message에서 정책을 꺼내 Core에 전달 |
| `session_key_handler/` | MAC이 발급한 세션 키 검증 |

## 지금 없는 것

현재 `a2a/server/MCP_server.py`가 노출하는 tool 6종은 **전부 L4(함수 호출) 수준**이다.
A2A 종단점이 되려면 그 위에 **L2 정책을 통째로 받는 `execute_policy`** 가 얹혀야 하고,
그 정책을 L3로 번역하는 것이 이 컴포넌트의 일이다. 두 층위는 공존한다 — 아래층은 디버깅용으로 남긴다.

## 작업 (Phase 0)

- [ ] 0-5 `execute_policy` / `get_task_report` / `cancel_task`
- [ ] 0-6 Policy Translator (L2→L3)
""")

comp("worker/core/policy_translator", "Policy Translator", "`worker/core/`", "0", "미착수", """
L2 `<living-care-policy>` → L3 `<limo-agent-policy>` 번역. 스키마는 `contracts/`.

## 번역 시 해소해야 할 것

| L2 | → L3 | 해소 주체 |
|---|---|---|
| `<place>living_room` | `<waypoint><x/><y/>` | KG 조회 (G-6) |
| `<required-skill>person-scan` | `<perception>` 블록 (model·rate·min-confidence) | 디바이스 능력 |
| `<action-type>inspect-and-report` | 실행 시퀀스 | 시나리오 선택 |
| `<assurance><deadline-sec>` | `<report><timeout-sec>` | 그대로 전달 |

## Phase 3 — RL의 위치 (오독 주의)

docx의 강화학습은 **정책 생성이 아니라, 사전 저장된 시나리오 배열 중 정책에 맞는 것을 고르는 선택 문제**다.
즉 **이 컴포넌트 내부의 선택 모듈**이며, L2→L3 번역을 규칙 기반에서 학습 기반으로 대체하는 것이다.
논문에서 이 위치를 흐리면 "정책 생성을 RL로 한다"로 오독된다. (Search-R1, arXiv:2503.09516)
""")

comp("worker/core/agent_executor", "Agent Executor", "`worker/core/`", "0", "미착수", """
A2A Message에서 정책을 꺼내 Worker AI Core로 넘기는 얇은 어댑터.
**A2A 통신 계층과 실행 로직을 잇는 지점**이다 — 이게 없으면 A2A 서버만 있고 기기는 움직이지 않는다.

```
A2A Message 수신 → Agent Executor → Policy Translator
                 → Perception / Reasoning / Action → Task Status / Artifact 반환
```

## 주의

정책을 **해석하지 않는다.** 꺼내서 넘기고, 수락/거부(`rejected`)만 판정한다.
능력 불일치·자원 부족으로 거부할 때 이유를 반드시 채운다 — MAMS의 재선택 입력이 된다.
""")

comp("worker/core/session_key_handler", "Session Key Handler", "`worker/core/`", "1", "미착수", """
MAC의 `session_key_manager/`가 발급한 세션 키를 검증한다.

## 주의

**Action Function이 실제 액추에이션 직전에 한 번 더 검증한다** (slide 16·18 명시).
Core에서 통과했다고 AF의 검증을 생략하지 말 것 — 이중 검증이 설계 의도다 (표준화 항목 S-4).
""")

comp("worker/analyzer", "Worker AI Analyzer (WAA)", "`worker/`", "0", "미착수", """
SF 실행 상태를 IF-6로 수집해 **Worker Report**를 만들고, A2A Task Status / Artifact로 변환해 상향 보고한다.
자가진단도 담당한다.

## 만들어야 할 Report

스키마: `contracts/worker_report/`

```json
{
  "report_id", "task_id", "policy_id", "intent_id", "agent_id", "reported_at",
  "status": "abnormal",
  "observation": {"found", "place", "posture", "motion": {"state","duration_sec"},
                  "frame_id", "pose"},
  "confidence": 0.86,
  "evidence": {"type": "image/jpeg", "ref": "iad://evidence/f_47", "bbox": [...]},
  "request": ["emergency_call", "audio_check"],
  "diagnostics": {"elapsed_sec", "rooms_visited", "sf_errors"}
}
```

## 지금 못 채우는 필드

- **`observation.pose`** — PF가 pose를 채우지 않는다 (G-2). "어느 방에서 발견했는지" 보고 불가.
- **`evidence`** — 프레임 pinning이 없어 증거 이미지를 확보할 수 없다 (G-1).

**두 갭이 Report의 핵심 필드를 비운다.** Phase 0의 0-7·0-8이 이것을 푼다.
""")

comp("worker/mgmt_system", "Worker AI Management System (WAMS)", "`worker/`", "1", "미착수", """
자기 등록(registration)과 SF 컨테이너 수명주기를 담당한다.

## 하위

- `agent_card/` — Worker의 접속 정보와 Skill을 외부에 공개

## 인터페이스

- IF-3 (Registration) ↔ WAC
- **IF-7 (AMS-Facing) ↔ MAMS** — 능력·자원·가용성 공시 (Phase 2)

## 주의

**IF-7이 이 프레임워크의 차별점이다.** A2A의 Agent Card는 정적 능력만 공시해 실시간 자원 상태를
반영하지 못한다. WAMS가 주기적으로 자원 상태를 MAMS에 갱신하는 경로가 그 공백을 메운다 (S-3).

SF를 Kubernetes 컨테이너로 관리하는 것은 UKC 논문이 제시한 방향이나, Phase 0에서는 단일 프로세스
내 모듈로 두고 컨테이너화는 Phase 2 이후로 미룬다.
""")

comp("worker/mgmt_system/agent_card", "Agent Card", "`worker/mgmt_system/`", "1", "미착수", """
Worker가 공개하는 디지털 명함. Manager는 여기서 이름·주소·지원 통신 방식·제공 Skill을 확인한다.

## A2A-over-MCP 매핑

| A2A | MCP 대응 |
|---|---|
| AgentCard 코어 | `server/discover` 결과 |
| 확장 필드 (자원 상태·배터리·위치) | MCP resource `agentcard://self` |
| AgentSkill | `tools/list` 항목 1개 = Skill 1개 |

권장 Skill 명명: `skill.<domain>.<verb>` (예: `skill.livingcare.person-scan`)

## 주의

**Skill은 내부 함수 목록이 아니다.** Manager가 작업을 맡길 때 이해할 수 있는 **고수준 능력**이어야 한다.
`start_person_scan`은 함수이고, `person-scan`이 Skill이다.
""")

comp("worker/service_functions", "Service Functions (PF / RF / AF)", "`worker/`", "0", "구현됨", """
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
""")

comp("worker/service_functions/perception", "Perception Function (PF)", "`worker/service_functions/`", "0",
     "구현됨 — **크리티컬 결함 2건**", """
디바이스 데이터 획득과 상태 모델링. 현재는 `/camera/image_raw`를 구독해 최신 프레임을 캐시한다.

**파일**: `Perceptions.py` — `PerceptionModule(node, topic="/camera/image_raw")`
`ReasoningModule`이 기대하는 `FrameSource` 시그니처를 만족한다:
`(frame_id=None) -> {"frame_id", "frame", "stamp", "pose"}`

## ⚠️ G-1 — 프레임 pinning 부재 (크리티컬)

```python
self._latest: Optional[dict] = None          # 슬롯 1개뿐
...
if frame_id is not None and item["frame_id"] != frame_id:
    return None                              # 과거 프레임 조회 불가
```

`PersonScan`이 `f_47`에서 사람을 잡아도, LLM이 `check_object_state(frame_id="f_47")`를 부를 때쯤엔
최신이 `f_53`이라 **증거 이미지를 얻을 수 없다.** 시나리오 1의 결론부가 끊긴다.

**0-7**: N프레임 링버퍼 + `pin(frame_id)` 추가.
단 pin만으로는 부족하다 — `check_object_state`가 pin된 프레임에도 YOLO를 **다시 돌리므로**,
`PersonScan`이 이미 확보한 `hit["bbox"]`를 전달하는 경로도 함께 뚫어야 한다.

## ⚠️ G-2 — `pose`가 항상 `None`

`_on_image`가 `"pose": None`을 하드코딩한다. Report의 `observation.pose`를 채울 수 없다.
**0-8**: TF(`map` ← `base_link`) 조회를 프레임에 스탬프.

## ⚠️ 인코딩 검사 없음 (실물 LIMO 이행 시)

```python
frame = np.frombuffer(msg.data, dtype=np.uint8).reshape(msg.height, msg.width, 3)
```

`msg.encoding`을 보지 않는다. 시뮬 카메라 SDF가 `R8G8B8`(rgb8)인 가정이다.
실물 LIMO는 Orbbec 계열이라 보통 **bgr8**이고, 그러면 `yolo_detect`의 `frame[:, :, ::-1]`과 겹쳐
**YOLO가 RGB를 보게 되어 정확도가 떨어진다**(크래시는 아님).
depth(16UC1)나 mono8이면 **reshape에서 크래시하거나 조용히 쓰레기 배열**이 된다.

## 주의

프레임 rate가 자료마다 다르다 — 스펙 30 Hz / d3d12 설정 시 10 Hz / **실측 ~2·~3.8 Hz**.
**작업 0-0에서 실제 rate를 먼저 측정할 것.** G-1의 위험도가 여기에 좌우된다.
""")

comp("worker/service_functions/reasoning", "Reasoning Function (RF)", "`worker/service_functions/`", "0",
     "**구현 완성도 최고**", """
관측으로부터 상태를 판단한다. 정책 규칙·컨텍스트·디바이스 지식을 다룬다.

**파일**: `Reasonings.py` — `ReasoningModule` + `PersonScan` + `yolo_detect`

## 왜 이 파일이 기준인가

**ROS2에 의존하지 않는 순수 로직**이다. 백엔드(YOLO·Nav2·크롭)를 생성자로 주입받고
미주입 시 no-op으로 동작하므로 **로봇 없이 단독 테스트가 가능하다.**
이 저장소에서 가장 잘 분리된 설계이므로 다른 컴포넌트를 만들 때 이 패턴을 따를 것.

```python
DetectFn    = Callable[[object], list]          # frame -> [{"class","conf","bbox"}]
PlanFn      = Callable[[dict, dict], list]      # start, goal -> [{"x","y","yaw"}]
CropFn      = Callable[[object, list], bytes]   # frame, bbox -> jpeg bytes
FrameSource = Callable[..., Optional[dict]]
```

## `PersonScan` — P-3의 "코드 자율 구간"

1 Hz로 최신 프레임에 YOLO를 돌려 **사람 유무(O/X)만** 판별한다. **상태 판정은 하지 않는다.**
사람이 잡히면 그 시점의 frame_id·pose·bbox만 기록하고, "괜찮은지"는 상위 LLM이 크롭 이미지를 보고 정한다.

**이 분리가 P-3(판단 위치 최소화)의 실체다.** 픽셀이 LLM에 올라가는 유일한 순간은
`check_object_state`가 크롭 1장을 돌려줄 때다. 컨텍스트 보호와 비용 절감이 동시에 된다.

## ⚠️ G-3 — API 5종이 MCP tool로 미노출

`start_person_scan` · `wait_for_person` · `check_object_state` · `stop_person_scan` · `get_scan_status`가
**구현돼 있으나** `a2a/server/MCP_server.py`에 tool 데코레이터가 없다.
시나리오 1의 탐색·판정 경로를 외부에서 호출할 수 없다. **구현이 아니라 노출만 하면 되는 저비용 작업 (0-9).**

## 주의

`yolo_detect`는 `ultralytics`를 **함수 안에서만 import**한다 — 이 모듈을 그냥 import했을 때
torch 등 무거운 의존성을 물지 않게 하기 위함이다. 이 lazy import를 최상단으로 올리지 말 것.
""")

comp("worker/service_functions/action", "Action Function (AF)", "`worker/service_functions/`", "0",
     "구현됨 — 단일 웨이포인트만 검증", """
결정에 따른 물리 행동. 세션 키 검증 후 디바이스를 제어한다.

**파일**: `Actions.py` — `ActionModule(node, nav_action="navigate_to_pose")`
Nav2 `NavigateToPose` 액션 클라이언트를 감싸 웨이포인트 리스트를 백그라운드 스레드로 순차 전송한다.

## ROS2 의존 표면 (전부)

```python
from action_msgs.msg  import GoalStatus
from geometry_msgs.msg import PoseStamped
from nav2_msgs.action  import NavigateToPose
```

**로봇 비의존이다.** Nav2만 돌면 turtlebot3든 실물 LIMO든 수정 없이 동작한다.

## 검증 실적 (과신 금지)

기록된 검증은 `plan_and_navigate(x=1.0, y=0.0)` **단일 웨이포인트 1회**뿐이다
(`sequence_result: {"completed": 1, "total": 1}`, `/odom` `(0,0)` → `(0.764, 0.009)`).
**다중 웨이포인트 순차 이동 · `cancel_goal_sequence` · `cancel`은 실행 기록이 없다.**
게다가 이 검증은 `turtlebot3_world`에서 이뤄졌고 **small_house 재검증은 없다.**

## ⚠️ G-5 — stale 콜백 가드 없음

- `_on_result`가 토큰 검사 없이 `self.status`를 덮어쓴다
- `cancel_goal`이 Nav2 취소 승인을 안 기다리고 낙관적으로 `"cancelled"`로 쓴다
- `_on_feedback`도 무조건 `"navigating"`을 쓴다 → stale feedback이 대기 루프를 풀 수 있다

**0-12**: `_goal_token` 도입 + 취소 승인 대기. (limo_slam이 같은 버그를 고친 전례가 있다)

## ⚠️ G-4 — `look_around` / patrol 미구현

`tools/scenarios/check_obj_state.json`이 `look_around`·`is_looking_around`·`interrupt_look_around`를
참조하지만 여기에 없다. **해당 시나리오는 실행 불가.**
(두 번째 실행 불가 사유도 있다 — `check_object_state`에 `detections` 인자를 넘기는데 RF가 받지 않는다)

## 주의

첫 웨이포인트는 `prev_xy`가 없어 `yaw_deg = 0.0`으로 떨어진다.
**현재 로봇 자세를 읽지 않으므로** 필요하면 명시적으로 줄 것.
""")

# ── a2a ──────────────────────────────────────────────────────────────────────
comp("a2a", "Secure A2A Channel (IF-4) — A2A-over-MCP 바인딩", "저장소 루트", "0",
     "부분 — MCP 서버 동작, A2A 의미론 미구현", """
Manager AI Core ↔ Worker AI Core 간 **고수준 정책·Task 상태·Artifact** 전달 계층.
**A2A 의미론을 유지하면서 전송·직렬화는 MCP를 재사용한다.**

## 하위

| 하위 | 책임 | 상태 |
|---|---|---|
| `server/` | Worker 측 A2A/MCP 종단점 | **동작** (`MCP_server.py`) |
| `client/` | Manager 측 A2A 클라이언트 | 미착수 |
| `binding/` | A2A ↔ MCP 객체 매핑 정의 | 미착수 |

## 왜 이 바인딩인가 (★핵심 기여 — 표준화 항목 S-4)

업계 통념은 "MCP는 agent↔tool, A2A는 agent↔agent"로 역할이 갈린다는 것이다. 이 프로젝트가
A2A 의미론을 MCP 위에 얹는 근거:

1. **엣지 로컬성** — Manager와 Worker가 같은 엣지에 있는 배치가 다수. stdio 로컬 IPC가 지연·전력에서 유리
2. **툴체인 단일화** — Worker 내부 SF 호출(L4)이 이미 MCP tool이다. 외부까지 MCP로 통일하면
   Worker는 **서버 구현 하나**만 가진다
3. **2026-07-28 MCP 개정이 격차를 없앰** — A2A 핵심 객체 전부가 현행 MCP에 대응물을 갖게 됨

> **포지셔닝**: "A2A를 MCP로 대체한다"가 아니라 **"A2A 의미론의 MCP 전송 바인딩을 정의한다"**.
> A2A 명세가 이미 JSON-RPC / gRPC / HTTP+JSON 3종 바인딩을 인정하므로
> **제4의 바인딩을 제안하는 형태**가 표준화 트랙에서 가장 방어 가능하다.

## 주의

**A2A TaskState와 report.status를 혼동하지 말 것.** 전자는 전송 계층의 작업 수명주기,
후자는 임무의 의미론적 결과다. `COMPLETED` ≠ 정상.
""")

comp("a2a/server", "A2A Server (Worker 측 종단점)", "`a2a/`", "0", "동작 — L4만 노출", """
**파일**: `MCP_server.py` — `LimoGatewayNode` + MCP tool. stdio 트랜스포트.

## 현재 노출된 tool 6종 (전부 L4 수준)

| tool | 계층 | Phase 0 처리 |
|---|---|---|
| `plan_and_navigate`, `navigate_waypoints`, `cancel` | L4 Action | 유지. `execute_policy` 내부에서 호출 |
| `get_camera_snapshot`, `detect_objects` | L4 Perception/Reasoning | 유지 |
| `get_status` | L4 상태 | `get_task_report`로 승격 (task_id 상관 추가) |
| — | **L2** | **`execute_policy` 신설** ← 0-5 |
| — | L4 | **person-scan 5종 노출** ← 0-9 (G-3) |

## Phase 0 최소 A2A 집합

```
server/discover                  → 프로토콜 버전·능력·정체성 (= Agent Card 코어)
tools/list                       → 공개 Skill 목록
resources/read agentcard://self  → 확장 Agent Card

tools/call execute_policy        → L2 정책 수락. 즉시 task handle 반환
  args:   {policy_xml | policy_json, policy_id, deadline_sec, session_ref}
  result: {task_id, accepted, reject_reason?}
tools/call get_task_report       → 상태·최종 Report 조회
tools/call cancel_task           → 취소
```

## ⚠️ MCP SDK 버전 (U-1)

`from mcp.server.mcpserver import Image, MCPServer` — 구 `fastmcp.FastMCP`가 아닌 새 이름이지만
**이것만으로 최신 SDK라고 판단할 수 없다.** 반대 증거:

- `tools/scenarios/*.py`가 **`await session.initialize()`를 호출한다** — 2026-07-28이 제거했다는 그 핸드셰이크가 살아 있다
- `requirements.txt`가 `mcp[cli]`로 **버전 미고정**
- 이 import는 limo_slam에서 **그대로 복사한 패턴**이라 의도적 채택 흔적이 아니다

**작업 0-0에서 설치된 `mcp` 패키지 버전을 직접 확인할 것.**

## 주의

**stdout을 오염시키지 말 것.** stdio 트랜스포트는 stdout을 JSON-RPC 전용으로 쓴다.
초기화 중 stdout에 쓰는 라이브러리가 있으면 프로토콜이 깨진다
(YOLO 가중치 다운로드 진행표시줄이 실제로 이 문제를 일으켰고, `contextlib.redirect_stdout(sys.stderr)`로
감싼 warm-up으로 해결했다 — 그 코드를 제거하지 말 것).
""")

comp("a2a/client", "A2A Client (Manager 측)", "`a2a/`", "0", "미착수", """
Manager AI Core가 Worker의 Agent Card를 조회하고, L2 정책을 `SendMessage`로 전달하며,
Task 상태와 Artifact를 수신한다.

## 흐름

```
MAMS 조회 (required-skill)      → Worker 후보
server/discover + agentcard://self → Agent Card 확인
tools/call execute_policy(L2)   → {task_id, accepted}
tasks/get(task_id) 폴링          → COMPLETED + Artifact(Report + 증거 이미지)
```

## 주의

**Worker 선택은 Client의 책임이 아니다.** MAMS의 `worker_selector/`가 정한다.
Client는 정해진 상대에게 보내고 받는 것만 한다.

Task 상태 전달 방식(폴링 vs `notifications/progress` 스트리밍)은 미정 (U-5).
Phase 0은 폴링으로 간다.
""")

comp("a2a/binding", "A2A ↔ MCP 바인딩 정의", "`a2a/`", "0", "미착수 — 문서만 존재", """
A2A v1.0 객체를 MCP 2026-07-28 위에 어떻게 실현하는지의 **규범적 매핑**.
표준화 항목 **S-4**의 실체이며, 정의는 스펙 §6.2에 있다.

## 매핑 요약

| A2A v1.0 | MCP 2026-07-28 |
|---|---|
| AgentCard | `server/discover` 결과 + resource `agentcard://self` |
| AgentSkill | `tools/list` 항목 1개 |
| Message / `message/send` | `tools/call` |
| Task + TaskState | `io.modelcontextprotocol/tasks` **공식 확장** |
| `tasks/get` | `tasks/get` (이름까지 동일) |
| Artifact | tool result의 `content` / `structuredContent` |
| `TASK_STATE_INPUT_REQUIRED` | **MRTR** `InputRequiredResult` |
| `message/stream` (SSE) | 요청 범위 `notifications/progress` |
| push notification config | `subscriptions/listen` |
| Agent Registry | **MAMS** (MCP 밖 — AI-Care 고유 확장) |

## TaskState ↔ report.status 정렬

| A2A TaskState | 대응 report.status |
|---|---|
| `SUBMITTED` / `WORKING` / `INPUT_REQUIRED` | (미발행) |
| `COMPLETED` | `completed` / `abnormal` / `not_found` / `partial` |
| `FAILED` | `failed` |
| `REJECTED` | `rejected` |
| `CANCELED` | `timeout` |

## 주의

**제안서·논문 제출 전 MCP 명세 최신판을 재확인할 것** (U-1).
이 매핑 전체가 2026-07-28 개정판에 의존한다.
""")

# ── contracts ────────────────────────────────────────────────────────────────
C["contracts"] = f"""# contracts — 계층 간 스키마

> **SOT**: `{SPEC}` §4(정책 계층) · §5(Report)
> **Phase**: 0 · **구현 상태**: 미착수 (작업 0-4)

컴포넌트 사이의 **유일한 계약**이다. P-2(정책 계층 분리)에 따라 각 계층은 바로 아래 계층만 알고,
그 앎은 전부 여기 있는 스키마로만 이뤄진다.

## 구성

| 경로 | 계층 | 형식 |
|---|---|---|
| `intent_query/` | **L1** Intent Query | JSON |
| `high_level_policy/` | **L2** High-level Policy (ECA) | XML (내부는 JSON 병용 검토 — U-2) |
| `low_level_policy/` | **L3** Low-level Policy (디바이스 특화) | XML |
| `worker_report/` | Worker Report | JSON |

## 규칙

1. **스키마를 바꾸면 여기부터 고치고 스펙에 반영한다.** 코드가 스펙을 앞서면 SOT가 깨진다.
2. **L2에 디바이스 이름을 넣지 않는다.** device-agnostic이어야 다중 Worker fan-out이 성립한다.
3. **검증기를 함께 둔다.** 스키마만 있고 검증이 없으면 P-4(실패 안전)가 성립하지 않는다.
4. L3의 요소명은 SF가 실제로 받는 자료구조와 1:1로 맞춘다
   (예: `<waypoint>` ↔ `Actions._goal_xy_yaw()`가 받는 `{{"x","y","frame"?,"yaw_deg"?}}`).

## 원본 자료의 알려진 오류 (수정해서 쓸 것)

- slide 21의 `<goal>37.5665, 126.9781</goal>`은 **WGS84 위경도(서울시청)** 다.
  실내 Nav2 로봇은 `map` 프레임 x/y/yaw를 쓴다. GPS 좌표를 목표로 줄 수 없다.
- slide 21의 `<rate>10Hz`는 **순찰 시나리오에 잘못 붙은 값**이다.
  구현은 1 Hz이고, 10 Hz는 I2ICF의 주행 중 장애물 회피 값이다.
- slide 21의 XML은 닫는 태그가 없는 **표현용 의사코드**다. 논문·제안서에는 정규화안을 쓸 것.

## 미결정

- **U-2**: L2 직렬화 — XML(YANG/NETCONF 정합) vs JSON(LLM 생성 정확도·MCP 친화).
  현재 권고는 **내부 JSON, 표준 문서·전시 XML, 양방향 변환**.
"""

# ── sim / tools ──────────────────────────────────────────────────────────────
C["sim"] = f"""# sim — 시뮬레이션 환경

> **SOT**: `{SPEC}` §10.2
> **컴포넌트가 아니다.** 여기에 비즈니스 로직을 두지 않는다.

Gazebo + Nav2 + slam_toolbox 브링업. `sim_bringup.launch.py`가 진입점이다.

```bash
source /opt/ros/jazzy/setup.bash
./fetch_meshes.sh                        # 최초 1회 — AWS 메시 ~55MB
ros2 launch sim/sim_bringup.launch.py
```

## 구성

| 항목 | 현재 |
|---|---|
| ROS2 | **Jazzy** (WSL2 Ubuntu 24.04) — **팀 내 배포판이 갈려 있음, 통일 필요 (U-12)** |
| 로봇 | **turtlebot3 waffle** (LIMO 아님) — 카메라 센서·브리지가 이미 완성돼 있어 선택 |
| 월드 | **AWS RoboMaker small_house** — 실제 주거 공간이라 리빙케어에 적합 |
| 측위 | **`slam_toolbox` (`slam:=True`)** — AMCL 아님. 초기 pose TF 레이스를 원천 회피 |
| 카메라 | `/camera/image_raw` — rate가 자료마다 다름 (30 / 10 / 실측 2~3.8 Hz) |
| **RTF** | **0.04 ~ 0.06** — **최대 리스크** |

## ⚠️ 두 가지 큰 문제

**1. RTF 0.04~0.06 (U-14)** — headless·무로봇 상태에서도 그렇다.
6.3분 시나리오가 **벽시계 2시간**이 된다. 반복 검증이 불가능하므로 `tools/patrol_viz/`로 논리를 검증하고
여기는 최종 확인용으로 쓰는 이원화가 현재 유일한 실행 가능안이다.
개선하려면 가구 collision을 단순 박스로 바꾸거나 `<collision>`을 빼는 게 효과가 클 것으로 본다.

**2. small_house 카메라 미검증 (작업 0-0)** — 카메라·YOLO 검증 실적은 전부 `turtlebot3_world` 기준이다.
small_house 전환 후 비대화형 세션에서 양 경로가 막혔다:
헤드리스 오프스크린은 100초 넘게 프레임 0장(`/dev/dri` 부재 추정), GUI는 `qt.qpa.xcb: could not connect to display :0`.
저장소는 이를 **비대화형 세션(WSLg 소켓 접근 불가)의 제약으로 추정**하며 대화형 재검증을 못 했다고 명시한다.
**사람이 자기 WSL 터미널에서 직접 돌려 확인하는 것이 Phase 0의 사실상 첫 작업이다.**

## 해결된 함정 (재발 방지)

- **`cmd_vel` 타입 불일치** — 스톡 브리지 yaml은 `TwistStamped`, Nav2 `collision_monitor`는 `Twist` 발행 →
  ROS2가 별개 토픽으로 취급해 **로봇이 영영 안 움직였다.** `waffle_bridge_fixed.yaml`로 `Twist` 통일.
- **RViz2 Map 디스플레이 미동작** — `indexed_8bit_image` 셰이더 링크 실패(RViz2 자체 버그).
  **Nav2 costmap 시각화도 같은 이유로 실패할 것.**
- **RViz2 ↔ Gazebo 렌더링 요구가 반대** — Gazebo는 `GALLIUM_DRIVER=d3d12`(하드웨어),
  RViz2는 `LIBGL_ALWAYS_SOFTWARE=1`(소프트웨어).
- **WSL2 GPU** — `/dev/dri`가 아니라 **`/dev/dxg`** 를 쓴다. `GALLIUM_DRIVER=d3d12` +
  `LD_LIBRARY_PATH=/usr/lib/wsl/lib`로 하드웨어 가속이 살아난다.
- **numpy ABI 충돌** — `ultralytics`가 numpy 2.x를 깔면 apt matplotlib과 충돌. `numpy==1.26.4` 고정.

## 실물 LIMO 이행 시 없는 것

이 디렉터리에는 **실로봇용 bringup이 없다** (`amcl`·`map_server`·`limo_base`·`ydlidar` 참조 0건).
`sim_bringup.launch.py`는 Gazebo에 완전히 묶여 있다 — gz_sim, ros_gz_bridge, turtlebot3 스폰, `use_sim_time:=true`.
실로봇용 `real_bringup.launch.py`를 별도로 작성해야 한다.
"""

C["tools"] = f"""# tools — 검증·시연 도구

> **SOT**: `{SPEC}` §10.1
> **컴포넌트가 아니다.** 여기에 비즈니스 로직을 두지 않는다.

| 경로 | 용도 |
|---|---|
| `patrol_viz/` | Gazebo·Nav2·YOLO **없이** 순찰 로직을 검증·시연 |
| `scenarios/` | MCP 왕복 CLI 클라이언트 + 시나리오 DSL. **정책 실행 회귀 테스트 하네스로 승격 예정** |

## patrol_viz — 왜 존재하는가

Gazebo RTF가 0.04~0.06이라 6.3분 시나리오가 벽시계 2시간이 된다. **반복 검증이 불가능해 만든 대체 수단**이다.
AWS small_house 맵 위에서 A*로 경로를 뽑고 운동학만 적분해 로봇을 움직이며, 카메라 1인칭 뷰까지 합성한다.

```bash
cd tools/patrol_viz
./run_coverage.sh    # GUI 없이 커버리지 수치 + patrol_sim.png
./run_patrol.sh      # RViz2에서 순찰 애니메이션 + 카메라 스트리밍
```

### 결과: 경로점 7개 · 375초 · 스캔 376회 · 주행 50 m · **커버리지 93.6%** · 사각지대 0

**⚠️ 이 수치는 "실측"이 아니라 기하 시뮬레이션 결과다.** 논문·제안서에 반드시 이렇게 표기할 것:

- 물리(바퀴 미끄러짐·충돌)와 Nav2 실제 재계획 없음 → **실소요는 20~30% 더 걸릴 것**
- **YOLO를 돌리지 않음** — "FOV 안 + 시야 확보 = 발견"으로 처리
- `CAM_RANGE = 4.0 m`는 **미측정 가정**이며 커버리지가 여기에 가장 민감
- **수직 FOV 미반영 (U-13)** — 2D 가정이라 4 m 거리에서 **바닥에 누운 사람이 화면 아래로 벗어나는 경우**를
  못 잡는다. 쓰러진 상황이 리빙케어에서 가장 위험한데 바로 그 부분이 미검증이다

## scenarios

```bash
python3 tools/scenarios/send_goal.py 1.0 0.0        # plan_and_navigate 왕복
python3 tools/scenarios/capture_and_detect.py out.jpg  # 스냅샷 + YOLO
```

**`check_obj_state.json`은 현재 실행 불가**다 — 참조하는 `look_around`·`is_looking_around`·
`interrupt_look_around`가 AF에 없고(G-4), `check_object_state`도 tool로 노출되지 않았으며(G-3),
게다가 RF의 `check_object_state`는 JSON이 넘기는 `detections` 인자를 받지 않는다.

## 자산 메모

`patrol_viz/limo/limo.urdf` — WeGo `limo_gazebo`(ROS1 xacro)에서 변환한 **실제 LIMO 모델**.
Jazzy 파싱은 통과한다. **Gazebo 플러그인 3블록만 Harmonic 문법으로 재작성하면 시뮬에 투입 가능**하다.
"""

# ─────────────────────────────────────────────────────────────────────────────


def stage_tree():
    print("[tree] 디렉터리 + CLAUDE.md 생성")
    for path in sorted(C):
        d = os.path.join(ROOT, path) if path else ROOT
        os.makedirs(d, exist_ok=True)
        f = os.path.join(d, "CLAUDE.md")
        with open(f, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(C[path])
        print(f"  + {os.path.join(path, 'CLAUDE.md') if path else 'CLAUDE.md'}")
    # 코드가 들어올 빈 디렉터리도 미리 만든다
    for extra in ("contracts/intent_query", "contracts/high_level_policy",
                  "contracts/low_level_policy", "contracts/worker_report",
                  "docs/spec", "docs/context", "docs/handoff", "docs/audit", "docs/slides"):
        os.makedirs(os.path.join(ROOT, extra), exist_ok=True)
        gk = os.path.join(ROOT, extra, ".gitkeep")
        if not os.path.exists(gk):
            open(gk, "w").close()
    print(f"[tree] CLAUDE.md {len(C)}개 생성 완료")


def stage_move():
    print("[move] git mv + 경로 참조 수정")

    gmv("limo-MCP/Worker_functions/Perceptions.py", "worker/service_functions/perception/Perceptions.py")
    gmv("limo-MCP/Worker_functions/Reasonings.py",  "worker/service_functions/reasoning/Reasonings.py")
    gmv("limo-MCP/Worker_functions/Actions.py",     "worker/service_functions/action/Actions.py")
    gmv("limo-MCP/MCP_server/MCP_server.py",        "a2a/server/MCP_server.py")
    gmv("limo-MCP/requirements.txt",                "requirements.txt")

    for n in ("sim_bringup.launch.py", "waffle_bridge_fixed.yaml", "fetch_meshes.sh"):
        gmv(f"limo-MCP/Simulation/{n}", f"sim/{n}")
    gmv("limo-MCP/Simulation/aws_small_house", "sim/aws_small_house")

    for n in ("send_goal.py", "capture_and_detect.py", "check_obj_state.json"):
        gmv(f"limo-MCP/Scenarios/{n}", f"tools/scenarios/{n}")

    for n in ("patrol_sim.py", "patrol_viz.py", "patrol.rviz", "README.md",
              "run_coverage.sh", "run_patrol.sh", "limo", "maps", "tools"):
        gmv(f"limo-patrol-viz/{n}", f"tools/patrol_viz/{n}")

    gmv("limo-MCP/SESSION_HANDOFF.md", "docs/handoff/limo-MCP_SESSION_HANDOFF.md")

    # ── 경로 참조 수정 ──
    print("[move] 경로 참조 수정")

    p = os.path.join(ROOT, "a2a/server/MCP_server.py")
    if os.path.exists(p):
        s = open(p, encoding="utf-8").read()
        old = 'sys.path.append(os.path.join(os.path.dirname(__file__), "..", "Worker_functions"))'
        new = ('# SF는 worker/service_functions/ 아래 세 디렉터리로 분리돼 있다.\n'
               '# 모듈명(Perceptions/Reasonings/Actions)은 그대로라 import는 바뀌지 않는다.\n'
               '_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))\n'
               'for _sf in ("perception", "reasoning", "action"):\n'
               '    sys.path.append(os.path.join(_ROOT, "worker", "service_functions", _sf))')
        if old in s:
            s = s.replace(old, new)
            open(p, "w", encoding="utf-8", newline="\n").write(s)
            print("  fix a2a/server/MCP_server.py : sys.path -> worker/service_functions/*")
        else:
            print("  - a2a/server/MCP_server.py : sys.path 이미 수정됨")

    for n in ("send_goal.py", "capture_and_detect.py"):
        p = os.path.join(ROOT, "tools/scenarios", n)
        if not os.path.exists(p):
            continue
        s = open(p, encoding="utf-8").read()
        old = 'os.path.join(os.path.dirname(__file__), "..", "MCP_server", "MCP_server.py")'
        new = 'os.path.join(os.path.dirname(__file__), "..", "..", "a2a", "server", "MCP_server.py")'
        changed = False
        if old in s:
            s = s.replace(old, new); changed = True
        if "    cd limo-MCP\n" in s:
            s = s.replace("    cd limo-MCP\n", "    cd <repo root>\n"); changed = True
        s = s.replace("python3 Scenarios/", "python3 tools/scenarios/")
        if changed or "tools/scenarios/" in s:
            open(p, "w", encoding="utf-8", newline="\n").write(s)
            print(f"  fix tools/scenarios/{n} : SERVER_PATH -> a2a/server/MCP_server.py")

    print("[move] 완료. sim/ 과 tools/patrol_viz/ 는 디렉터리 단위 이동이라 내부 상대경로가 그대로 유효하다.")


def stage_docs():
    print("[docs] 루트 문서 정리")
    mapping = {
        "AI-Care_Unified_Architecture_Spec_v0.2.md": "docs/spec/",
        "AI-Care_A2A_Core_Context(2).md":            "docs/context/",
        "RCP_MCP_NOTES.md":                          "docs/context/",
        "I2ICF_ViLaR_IMO_LLM_CONTEXT_KR.md":         "docs/context/",
        "RESEARCH_HANDOFF.md":                       "docs/context/",
        "SESSION_HANDOFF.md":                        "docs/handoff/",
        "IETF승계issue.md":                          "docs/audit/",
    }
    parent = os.path.dirname(ROOT)
    for name, dest in mapping.items():
        src = os.path.join(parent, name)
        if not os.path.exists(src):
            print(f"  - skip (없음): {name}")
            continue
        os.makedirs(os.path.join(ROOT, dest), exist_ok=True)
        os.replace(src, os.path.join(ROOT, dest, name))
        print(f"  mv  ../{name} -> {dest}{name}")

    for f in os.listdir(parent):
        if f.lower().endswith((".pptx", ".pdf")):
            os.makedirs(os.path.join(ROOT, "docs/slides"), exist_ok=True)
            os.replace(os.path.join(parent, f), os.path.join(ROOT, "docs/slides", f))
            print(f"  mv  ../{f} -> docs/slides/{f}  (git 제외)")

    gi = os.path.join(ROOT, ".gitignore")
    s = open(gi, encoding="utf-8").read() if os.path.exists(gi) else ""
    block = "\n####################\n# 대용량 발표 자료 (로컬 전용)\n####################\ndocs/slides/\n"
    if "docs/slides/" not in s:
        open(gi, "a", encoding="utf-8", newline="\n").write(block)
        print("  + .gitignore : docs/slides/")


def stage_verify():
    print("[verify]")
    ok = True
    must = ["CLAUDE.md", "docs/CLAUDE.md", "docs/spec/AI-Care_Unified_Architecture_Spec_v0.2.md",
            "worker/service_functions/perception/Perceptions.py",
            "worker/service_functions/reasoning/Reasonings.py",
            "worker/service_functions/action/Actions.py",
            "a2a/server/MCP_server.py", "sim/sim_bringup.launch.py",
            "sim/aws_small_house/worlds/small_house.world",
            "tools/patrol_viz/patrol_viz.py", "tools/patrol_viz/maps/map.pgm",
            "tools/scenarios/send_goal.py", "requirements.txt"]
    for m in must:
        e = os.path.exists(os.path.join(ROOT, m))
        print(f"  {'OK ' if e else 'MISS'}  {m}")
        ok &= e

    n = sum(1 for _, _, fs in os.walk(ROOT) for f in fs
            if f == "CLAUDE.md" and ".git" not in _)
    print(f"  CLAUDE.md 총 {n}개")

    p = os.path.join(ROOT, "a2a/server/MCP_server.py")
    if os.path.exists(p):
        s = open(p, encoding="utf-8").read()
        print(f"  {'OK ' if 'worker' in s and 'service_functions' in s else 'MISS'}  MCP_server.py sys.path 수정")
    p = os.path.join(ROOT, "tools/scenarios/send_goal.py")
    if os.path.exists(p):
        s = open(p, encoding="utf-8").read()
        needle = '"a2a", "server"'
        print(f"  {'OK ' if needle in s else 'MISS'}  send_goal.py SERVER_PATH 수정")

    leftovers = [d for d in ("limo-MCP", "limo-patrol-viz") if os.path.exists(os.path.join(ROOT, d))]
    if leftovers:
        print(f"  ! 잔여 디렉터리: {leftovers} (비어 있으면 수동 삭제)")
    print("  " + ("모두 정상" if ok else "누락 있음 — 위 MISS 확인"))


if __name__ == "__main__":
    stages = {"tree": stage_tree, "move": stage_move, "docs": stage_docs, "verify": stage_verify}
    a = sys.argv[1] if len(sys.argv) > 1 else ""
    if a not in stages:
        print(__doc__)
        sys.exit(1)
    stages[a]()
