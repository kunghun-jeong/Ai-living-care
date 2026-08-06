#!/usr/bin/env python3
"""SOT.md 규범으로 저장소를 이행한다.

    python3 sot_migrate.py move      # git mv + interfaces/ 신설 + 폐기 디렉터리 격리
    python3 sot_migrate.py claudemd  # CLAUDE.md 전면 재생성 (SOT 기준 경로)
    python3 sot_migrate.py fixpath   # 경로 참조 수정
    python3 sot_migrate.py spec      # D-9~D-13을 스펙 §0.2 결정표에 반영

저장소 루트에서 실행. 각 단계는 멱등하다.
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SPEC = "docs/spec/AI-Care_Unified_Architecture_Spec_v0.2.md"
MA, WA = "manager_ai_agent", "worker_ai_agent"
TRASH = "_to_delete/obsolete"


def sh(cmd, check=False):
    return subprocess.run(cmd, shell=True, cwd=ROOT, capture_output=True, text=True)


def clr():
    for f in (".git/index.lock", ".git/HEAD.lock", ".git/objects/maintenance.lock"):
        p = os.path.join(ROOT, f)
        if os.path.exists(p):
            os.makedirs(os.path.join(ROOT, "_to_delete/gitlocks"), exist_ok=True)
            try:
                os.replace(p, os.path.join(ROOT, "_to_delete/gitlocks",
                                           os.path.basename(f) + f".{os.getpid()}"))
            except OSError:
                pass


def gmv(src, dst):
    s, d = os.path.join(ROOT, src), os.path.join(ROOT, dst)
    if not os.path.exists(s):
        return print(f"  - skip {src}")
    if os.path.exists(d):
        return print(f"  - skip {src} (대상 존재)")
    os.makedirs(os.path.dirname(d), exist_ok=True)
    r = sh(f'git mv "{src}" "{dst}"')
    clr()
    if r.returncode == 0:
        print(f"  git mv  {src} -> {dst}")
    else:
        os.replace(s, d)
        print(f"  mv      {src} -> {dst}")


def trash(rel):
    s = os.path.join(ROOT, rel)
    if not os.path.exists(s):
        return
    t = os.path.join(ROOT, TRASH)
    os.makedirs(t, exist_ok=True)
    os.replace(s, os.path.join(t, rel.replace("/", "__")))
    print(f"  폐기    {rel} -> {TRASH}/")


MOVES = [
    ("manager/core",                        f"{MA}/manager_ai_core"),
    ("manager/analyzer",                    f"{MA}/manager_ai_analyzer"),
    ("manager/mgmt_system",                 f"{MA}/manager_ai_management_system"),
    ("manager/knowledge_graph",             f"{MA}/knowledge_graph"),
    ("manager/intent_audit_db",             f"{MA}/intent_audit_database"),
    ("manager/CLAUDE.md",                   f"{MA}/CLAUDE.md"),
    ("worker/core",                         f"{WA}/worker_ai_core"),
    ("worker/analyzer",                     f"{WA}/worker_ai_analyzer"),
    ("worker/mgmt_system",                  f"{WA}/worker_ai_management_system"),
    ("worker/service_functions/perception", f"{WA}/perception"),
    ("worker/service_functions/reasoning",  f"{WA}/reasoning"),
    ("worker/service_functions/action",     f"{WA}/action"),
    ("worker/CLAUDE.md",                    f"{WA}/CLAUDE.md"),
    ("a2a/server",                          f"{WA}/mcp_server"),
    ("a2a/client",                          f"{MA}/mcp_client"),
    ("a2a/binding",                         "interfaces/if04_secure_a2a_channel"),
]

IFDIRS = ["if01_database", "if02_analytics", "if03_registration", "if04_secure_a2a_channel",
          "if05_sf_facing", "if06_agent_monitoring", "if07_ams_facing", "if08_analyzer_facing"]


def stage_move():
    print("[move] SOT 정규 경로로 이동")
    clr()
    for s, d in MOVES:
        gmv(s, d)
    # Agent Executor는 SOT §2.2에서 mcp_server 소속 -> 별도 디렉터리 폐기
    trash(f"{WA}/worker_ai_core/agent_executor")
    # 폐기 디렉터리
    for rel in ("worker/service_functions/CLAUDE.md", "a2a/CLAUDE.md"):
        trash(rel)
    for rel in ("worker/service_functions", "worker", "manager", "a2a"):
        p = os.path.join(ROOT, rel)
        if os.path.isdir(p) and not os.listdir(p):
            trash(rel)
        elif os.path.isdir(p):
            print(f"  ! {rel}/ 비어있지 않음: {os.listdir(p)[:5]}")
    for d in IFDIRS:
        os.makedirs(os.path.join(ROOT, "interfaces", d), exist_ok=True)
    print(f"  + interfaces/ {len(IFDIRS)}개 확보")
    clr()


# ─────────────────────────────────────────────────────────────────────────────
C = {}


def comp(path, title, parent, phase, state, body):
    C[path] = (f"# {title}\n\n"
               f"> **구조 정본**: `SOT.md` · **설계 정본**: `{SPEC}`\n"
               f"> **상위**: {parent} · **Phase**: {phase} · **구현 상태**: {state}\n\n"
               f"{body.strip()}\n")


def iface(d, ifid, name, ends, phase, state, body):
    C[f"interfaces/{d}"] = (
        f"# {ifid} — {name}\n\n"
        f"> **구조 정본**: `SOT.md` §3 · **설계 정본**: `{SPEC}` §3\n"
        f"> **종단점**: {ends} · **Phase**: {phase} · **구현 상태**: {state}\n\n"
        f"{body.strip()}\n")


C[""] = f"""# AI-Care Edge System

스마트홈 거주자의 **자연어 의도**를 기계 판독 가능한 **고수준 정책**으로 번역하고,
A2A로 이기종 IoT **Worker AI Agent**에 배포해 각자 독립 실행·보고하게 하며,
그 보고를 해석해 재시도·전환·에스컬레이션을 결정하는 **의도 기반 폐루프 리빙케어 프레임워크**.

> | 문서 | 관할 |
> |---|---|
> | `{SPEC}` | **설계** — 무엇을 만드는가, 용어, 스키마, 인터페이스 의미 |
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
| `{MA}/manager_ai_core/` | Manager AI Core | MAC |
| `{MA}/manager_ai_analyzer/` | Manager AI Analyzer | MAA |
| `{MA}/manager_ai_management_system/` | Manager AI Management System | MAMS |
| `{MA}/knowledge_graph/` | Knowledge Graph | KG |
| `{MA}/intent_audit_database/` | Intent Audit Database | IAD |
| `{MA}/mcp_client/` | A2A Client (IF-4 Manager 측) | — |
| `{WA}/worker_ai_core/` | Worker AI Core | WAC |
| `{WA}/worker_ai_analyzer/` | Worker AI Analyzer | WAA |
| `{WA}/worker_ai_management_system/` | Worker AI Management System | WAMS |
| `{WA}/perception/` | Perception Function | PF |
| `{WA}/reasoning/` | Reasoning Function | RF |
| `{WA}/action/` | Action Function | AF |
| `{WA}/mcp_server/` | A2A Server + Agent Executor (IF-4 Worker 측) | — |
| `interfaces/if01…if08/` | 인터페이스 카탈로그 IF-1~IF-8 | — |
| `contracts/` | L1~L3 · Report 페이로드 스키마 | — |
| `sim/` `tools/` `docs/` | 비컴포넌트 | — |

## Intent-Policy Continuum (L0~L4)

```
L0 Intent (자연어)     "할머니 괜찮은지 확인해줘"
   ↓ Extraction + KG Mapping + Composing      [{MA}/manager_ai_core/]
L1 Intent Query (JSON)                        [contracts/intent_query/]
   ↓ LLM + Schema Prompt                      [{MA}/manager_ai_core/policy_generation/]
L2 High-level Policy (ECA XML)                [contracts/high_level_policy/]
   ↓ IF-4 Secure A2A Channel                  [interfaces/if04_secure_a2a_channel/]
   ↓ Policy Translation                       [{WA}/worker_ai_core/policy_translator/]
L3 Low-level Policy                           [contracts/low_level_policy/]
   ↓ IF-5 SF-Facing
L4 Function Call                              [{WA}/{{perception,reasoning,action}}/]
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
| **G-1** | 프레임 pinning 부재 — 최신 1장만 캐시. 과거 `frame_id` 조회 불가 | `{WA}/perception/` |
| **G-2** | `pose`가 항상 `None` | `{WA}/perception/` |
| **G-3** | person-scan API 5종이 MCP tool로 미노출 | `{WA}/mcp_server/` |
| **G-4** | `look_around` / patrol 미구현 | `{WA}/action/` |
| **G-5** | stale 콜백 가드 없음 | `{WA}/action/` |
| **G-6** | 장소 룩업(KG 연결점) 부재 | `{MA}/knowledge_graph/` |

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
"""

C["docs"] = f"""# docs — 문서 저장소

> **구조 정본**: `SOT.md` · **설계 정본**: `spec/AI-Care_Unified_Architecture_Spec_v0.2.md`

| 경로 | 내용 | 신뢰도 |
|---|---|---|
| `spec/` | **설계 정본.** 정규화 용어, IF-1~IF-8, L0~L4, A2A-over-MCP 바인딩, 로드맵, 표준화 항목 | **정본** |
| `context/` | 배경 — A2A 개념 매핑, RCP/MCP 결정 기록, ViLaR-IMO 연계, 연구 자료 계보 | 참고 |
| `handoff/` | 세션 인수인계 — 왜 그렇게 했는지, 다시 겪지 않아도 될 함정 | 참고 |
| `audit/` | IETF-125/126 승계 판정 | **참고 전용, 결정 아님** |
| `slides/` | UKC2026 발표 덱 (42MB, git 제외) | 원본 |

## 읽는 순서

1. 루트 `CLAUDE.md` — 전체 그림과 현재 Phase
2. `../SOT.md` — 구조·명명 규범
3. `spec/` §1~§5 — 설계 원칙, 컴포넌트, 인터페이스, 정책 계층, Report
4. `spec/` §10 — 기존 자산, 시뮬 환경, 크리티컬 갭, Phase 계획
5. `handoff/` — 실제로 겪은 함정
6. 담당 컴포넌트의 `CLAUDE.md`

## 주의

- **`spec/`이 설계 정본이다.** 어긋나면 spec을 따르고, spec이 틀렸으면 spec을 고친다.
- **`audit/IETF승계issue.md`는 참고 자료다.** 판정이 스펙에 반영되지 않았다.
- **슬라이드와 UKC 논문에는 용어 불일치가 있다.** spec §2.4와 부록 B 대조표를 먼저 볼 것.
"""

# ── Manager ──────────────────────────────────────────────────────────────────
comp(MA, "Manager AI Agent", "저장소 루트", "0", "미착수", f"""
사용자의 자연어 의도를 해석해 **고수준 정책(L2)** 을 만들고, 적절한 Worker를 선택해 A2A로 배포하며,
돌아온 Report를 해석해 재시도·전환·에스컬레이션을 결정한다.

## 구성 (P-1 대칭성)

| 디렉터리 | 정규화 명칭 | 약칭 |
|---|---|---|
| `manager_ai_core/` | Manager AI Core | MAC |
| `manager_ai_analyzer/` | Manager AI Analyzer | MAA |
| `manager_ai_management_system/` | Manager AI Management System | MAMS |
| `knowledge_graph/` | Knowledge Graph | KG |
| `intent_audit_database/` | Intent Audit Database | IAD |
| `mcp_client/` | A2A Client — IF-4 Manager 측 종단점 | — |

> **KG와 IAD는 별개다.** 원 자료(slide 16·17·21, 논문 Fig.1)에서 이 자리에 박스가 하나만 그려져 있고
> 자료마다 이름이 다르지만, 접근 패턴과 수명이 달라 두 저장소로 분리했다 (spec §2.3).

## 인터페이스

IF-1(→KG/IAD) · IF-2(↔MAA) · IF-3(↔MAMS) · **IF-4**(↔WAC) · IF-7(↔WAMS, P2) · IF-8(↔WAA, P2)
정의는 `interfaces/`에 있다.

## 주의

docx는 Manager를 "우리 스코프 아님"으로 두었으나 **2026-08-06 결정으로 구현 범위에 포함**됐다.
KG는 그래프DB가 아니라 JSON 룩업으로 간소 구현한다 (D-6).
""")

comp(f"{MA}/manager_ai_core", "Manager AI Core (MAC)", f"`{MA}/`", "0", "미착수", f"""
**Intent Translator + Session Key Manager.** L0(자연어) → L1(Intent Query) → L2(High-level Policy) 변환의 주체.

논문 Fig.1과 slide 17의 표는 `Manager Controller`로 표기 — **별칭으로만 인정**한다 (spec §2.1).

## 파이프라인

```
"Check if Grandma is okay"
  → intent_extraction/     ["Grandma", "check", "is okay"]
  → kg_mapping/            IF-1로 KG 조회 → phrase별 element=value 바인딩
  → query_composing/       L1 Intent Query JSON
  → policy_generation/     LLM + Schema Prompt → L2 ECA XML
```

`session_key_manager/`는 직교하며 IF-4의 세션 키를 발급·갱신한다.
생성된 L2는 `../mcp_client/`가 IF-4로 실어 보낸다.

## 반드시 지킬 것

- **L2에 디바이스 이름을 넣지 않는다.** device-agnostic이어야 다중 Worker fan-out이 성립한다 (spec §4.3).
- **`bindings`를 반드시 남긴다.** 어느 어구가 어떤 값으로 해소됐는지 없으면 오역 디버깅이 불가능하다 (P-5).
- **LLM 실패 경로를 설계에 포함한다** (P-4). 정상 파싱 → 필드 정규화 → 규칙 기반 폴백 3단 구조 권장.

## 작업 (Phase 0)

- [ ] 0-3 L0→L2 파이프라인 전체
- [ ] LLM 선택 확정 (U-3)
- [ ] L2 직렬화 형식 확정 (U-2 — 내부 JSON / 표준 문서 XML 양방향 변환 권고)
""")

comp(f"{MA}/manager_ai_core/intent_extraction", "Intent Extraction", "`manager_ai_core/`", "0", "미착수", """
자연어 발화에서 의미 어구를 뽑는다. **여기서 의미를 해소하지 않는다** — 해소는 `kg_mapping/`의 일이다.

```
extract(utterance: str) -> list[str]
# "Check if Grandma is okay" -> ["Grandma", "check", "is okay"]
```

## 주의

- 어구 경계는 KG의 `phrase_bindings` 키와 맞아야 매핑이 성립한다. 두 컴포넌트를 함께 바꿀 것.
- 추출 결과는 L1의 `bindings[].phrase`로 그대로 흘러간다 (P-5).
""")

comp(f"{MA}/manager_ai_core/kg_mapping", "KG Mapping", "`manager_ai_core/`", "0", "미착수", """
추출된 어구를 KG에 조회해 `element = value` 바인딩으로 해소한다. **IF-1 경유** (`interfaces/if01_database/`).

```
resolve(phrase: str, context: dict) -> list[Binding]
Binding = {"element": str, "value": any, "confidence": float, "source": str}
```

slide 21의 KG mapping 표:

| PHRASE | ELEMENT → RETRIEVED VALUE |
|---|---|
| "Grandma" | `target = elder`, `place = living_room` |
| "check" | `task = safety_check`, `mobile = [LIMO_1, LIMO_2]` |
| "is okay" | `condition = realtime`, `sensor = camera` |

## 주의

- **KG를 직접 파일로 읽지 말 것.** IF-1 계약으로만 접근해야 후일 그래프DB로 무중단 교체할 수 있다 (D-6).
- `confidence`를 반드시 채운다. 낮은 신뢰도 바인딩은 사용자 확인(MRTR)으로 승격될 수 있다.
""")

comp(f"{MA}/manager_ai_core/query_composing", "Intent Query Composing", "`manager_ai_core/`", "0", "미착수", """
바인딩을 모아 **L1 Intent Query(JSON)** 를 만든다. 아직 정책이 아니다 — 구조화된 의도다.

스키마: `contracts/intent_query/`

| 필드 | 출처 |
|---|---|
| `intent`·`target`·`task`·`condition`·`place`·`devices` | slide 21 원본 |
| `sensors` | KG 매핑표엔 있으나 composed JSON에서 누락된 것을 복원 |
| `intent_id`·`raw_utterance`·`issued_by`·`issued_at`·`bindings` | 스펙이 추가 (P-5) |

## 주의

`devices`는 **후보 힌트**일 뿐이다. 확정은 MAMS의 Worker 선택이 한다 (spec §7.2).
여기서 정한 디바이스가 L2로 넘어가면 안 된다.
""")

comp(f"{MA}/manager_ai_core/policy_generation", "High-level Policy Generation", "`manager_ai_core/`", "0", "미착수", """
L1 + Schema Prompt를 LLM에 넣어 **L2 High-level Policy (ECA XML)** 를 생성한다.

스키마: `contracts/high_level_policy/`

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
- **스키마 검증 실패 출력은 정책으로 승격하지 않는다** (P-4). 재생성 → 폴백 → 사용자 확인 순.

## 주의

Ollama를 쓸 경우 `format: "json"`으로 출력 형식을 강제할 수 있다.
LLM 실패 폴백 설계는 `docs/audit/IETF승계issue.md` §4.1 참조 (참고 자료, 미채택).
""")

comp(f"{MA}/manager_ai_core/session_key_manager", "Session Key Manager", "`manager_ai_core/`", "1", "미착수", f"""
IF-4의 세션 키를 발급·검증·갱신한다. Worker 측 대응은 `{WA}/worker_ai_core/session_key_handler/`.

| Phase | 범위 |
|---|---|
| 0 | stdio 로컬 — OS 프로세스 격리에 의존. 키 발급만 인메모리 |
| 1+ | mTLS over Streamable HTTP, rekeying 주기 정책화 |
| 2+ | Skill 단위 권한, `AUTH_REQUIRED` TaskState 활용 |

## 주의

slide 16·18은 **Action Function이 실제 액추에이션 직전에 Session Key Check를 한 번 더** 수행하도록
명시한다. 키 검증이 Core에만 있지 않은 **이중 검증 구조**다. 유지할 것 (표준화 항목 S-4의 근거).
""")

comp(f"{MA}/manager_ai_analyzer", "Manager AI Analyzer (MAA)", f"`{MA}/`", "0", "미착수", """
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
""")

comp(f"{MA}/manager_ai_analyzer/report_interpreter", "Report Interpreter", "`manager_ai_analyzer/`", "0", "미착수", """
Worker Report(JSON)를 읽어 임무 결과를 판정한다. 스키마: `contracts/worker_report/`

| status | 의미 | 기본 처리 |
|---|---|---|
| `completed` | 정상 수행, 이상 없음 | 사용자에게 정상 피드백 |
| `abnormal` | 수행 성공, **관측 결과가 이상** | `request[]` 에스컬레이션 |
| `not_found` | 수행했으나 대상 미발견 | 다른 Worker 전환 → 소진 시 에스컬레이션 |
| `failed` | SF 오류·하드웨어 실패 | 재시도 → 임계 초과 시 다른 Worker |
| `partial` | 일부만 수행 | 잔여분 후속 정책 발행 |
| `rejected` | Worker가 수락 거부 | 즉시 재선택 |
| `timeout` | `deadline-sec` 초과 | Task cancel 후 재선택 |

## 주의

`not_found`는 docx의 열린 질문("4곳을 다 봐도 못 찾으면?")을 닫는 값이다.
`request: [caregiver_notify]`를 붙여 `abnormal`과 같은 경로를 타게 한다.
""")

comp(f"{MA}/manager_ai_analyzer/assurance_loop", "Intent Assurance Loop", "`manager_ai_analyzer/`", "0", "미착수", """
판정에 따라 다음 행동을 결정하는 상태기계. 모든 전이는 IF-1로 IAD에 기록된다 (P-5).

```
IntentReceived → PolicyGenerated → WorkerSelected → Dispatched → Executing → Reported
Reported ─ completed ──────────────→ Assured
         ├ abnormal / not_found(소진) → Escalated
         ├ failed / timeout ─────────→ Retry ─ (<N) → Dispatched
         │                                   └ (≥N) → Reselect
         ├ rejected / not_found(잔존) → Reselect ─ 잔존 → WorkerSelected
         │                                        └ 소진 → Escalated
         └ partial ──────────────────→ PolicyGenerated (잔여 정책 재생성)
```

## 주의

**루프 수렴을 반드시 확인할 것.** 재시도 상한과 후보 소진 조건이 없으면
`failed → Retry → Dispatched → failed`가 무한히 돈다. Phase 0부터 상한을 넣는다.
""")

comp(f"{MA}/manager_ai_management_system", "Manager AI Management System (MAMS)", f"`{MA}/`", "0", "미착수", """
Worker의 등록·상태·수명주기를 관리하고 **Agent Registry 역할을 겸한다.**

slide 21은 `Edge AI's Mgmt System`으로 표기 — 정식 명칭은 `Manager AI Management System` (D-1).

| 하위 | 책임 | Phase |
|---|---|---|
| `agent_registry/` | Worker 주소·Skill·자원 상태 보관·조회 | 0(고정) → 2(동적) |
| `worker_selector/` | `required-skill` 기준 필터링·점수화·선택 | 2 |

## 왜 표준화 항목인가 (S-3)

A2A는 Agent Discovery 방식은 제시하지만 **레지스트리 데이터 모델과 Worker 선택 로직은 구현자 몫**으로 남긴다.
게다가 Agent Card만으로는 CPU·메모리·대역폭 등 **실시간 자원 상태를 반영하기 어렵다**
(Duan & Lu, arXiv:2508.15819). **MAMS + IF-7이 정확히 그 공백을 메운다.**
""")

comp(f"{MA}/manager_ai_management_system/agent_registry", "Agent Registry", "`manager_ai_management_system/`", "0", "미착수", """
Worker의 접속 정보와 능력을 보관·조회한다. A2A Agent Card의 수집처. IF-3·IF-7 경유.

```
register(agent_id, agent_card) -> None
lookup(required_skills: list[str]) -> list[AgentRef]
update_resources(agent_id, resources) -> None   # IF-7, Phase 2
```

## 주의

**Registry는 후보를 제공할 뿐 최종 선택을 하지 않는다.** 선택은 `worker_selector/`의 책임이다 (A2A 명세 경계).
Phase 0에서는 Worker 주소를 고정 설정으로 둬도 된다.
""")

comp(f"{MA}/manager_ai_management_system/worker_selector", "Worker Selector", "`manager_ai_management_system/`", "2", "미착수", """
L2 정책의 `<required-skill>`을 만족하는 Worker를 골라 배포 대상을 확정한다.

```
1. Registry 조회: required-skill 전부를 공시한 Worker 집합 C
2. 필터: 가용(alive) ∧ 자원 충족 ∧ 세션 유효
3. 점수화: score(w) = α·capability_match + β·proximity(place)
                    + γ·availability − δ·recent_failure_rate
4. dispatch-mode에 따라 상위 1개(or-fallback) 또는 상위 k개(or-race, k ≤ max-parallel)
5. rejected 수신 시 해당 Worker 제외하고 재선택
```

| dispatch-mode | 완료 조건 | 예 |
|---|---|---|
| `and-all` | 전부 `completed` | "전등 다 끄고 문 잠가줘" |
| `or-race` | 최초 성공. **나머지 취소** | **시나리오 1** — LIMO_1/LIMO_2 |
| `or-fallback` | 순차 시도 | 동시 기동 자원 부족 시 |
| `sequential` | 마지막 단계 완료 | "찾아서 확인하고 이상하면 디스펜서 열어" |
| `split` | 모든 파티션 완료 | "1층 LIMO_1, 2층 LIMO_2" |

## 주의

α·β·γ·δ 가중치는 미정 (U-4). Phase 2에서 실측으로 정한다.
""")

comp(f"{MA}/knowledge_graph", "Knowledge Graph (KG)", f"`{MA}/`", "0", "미착수 — **G-6**", """
사용자·공간·디바이스의 **관계와 능력**을 보유한다 — 누가 무엇을 할 수 있는가.
`intent_audit_database/`(감사 이력)와는 별개다 (spec §2.3). 접근은 **IF-1 경유**.

## Phase 0: JSON 룩업으로 간소 구현 (D-6)

인터페이스 계약을 **고정**해 후일 그래프DB로 무중단 교체한다.

```json
{
  "entities": {
    "grandma":     {"type":"person","role":"elder","usual_place":"living_room"},
    "living_room": {"type":"space","map_frame":"map","pose":{"x":…,"y":…,"yaw":…}},
    "LIMO_1":      {"type":"device","skills":["navigate","person-scan","state-check"],
                    "sensors":["camera","lidar"],"agent_uri":"stdio://limo_1"}
  },
  "phrase_bindings": { "grandma": [...], "check": [...], "is okay": [...] }
}
```

## G-6 — 채워야 할 공백

현재 코드에 `list_locations` / `locations.json`이 **없다.** `plan_and_navigate`는 좌표만 받는다.
L2의 `<location-label>living_room`을 좌표로 해소할 경로가 없다.
**좌표 ↔ 방 이름 매핑을 만드는 것이 곧 G-6 해소이자 `entities.<space>` 채우기다** (작업 0-10).

## 주의 (중요)

- 저장소에서 좌표에 **의미 있는 이름이 붙은 것은 두 개뿐**이다:
  `(8.10, 1.71)`="식탁 구역", `(-7.77, 0.56)`="좌상단 방" (`tools/patrol_viz/`).
  **나머지 5개 순찰 좌표에는 방 이름이 부여된 바 없다. 임의로 붙이지 말 것.**
- docx의 `locations.json`(`living_room = (1.2, 0.4)`)은 **별개 출처이며 small_house 좌표계와 무관하다.**
- `phrase_bindings`는 데모용 지름길이다. Phase 1에서 그래프 순회 + 임베딩 유사도로 대체하고
  이 표는 회귀 테스트 정답셋으로 전환한다.
""")

comp(f"{MA}/intent_audit_database", "Intent Audit Database (IAD)", f"`{MA}/`", "1", "미착수", """
intent·policy 이력, 스키마 프롬프트, 검증 규칙을 보관한다. **Intent Validator 기능을 포함**한다.

| | Knowledge Graph | **Intent Audit Database** |
|---|---|---|
| 담는 것 | elder는 보통 living_room에 있다 | 14:03 intent#a1b2 → policy#p7 → LIMO_1 → abnormal |
| 접근 | KG Mapping, 읽기 위주 | 전 계층, **쓰기 위주** + 스키마/프롬프트 읽기 |
| 표준화 | 도메인 데이터 모델 | **감사·보증 데이터 모델 (S-5)** |

## P-5를 실현하는 곳

L0~L4 전 계층 변환과 모든 A2A 메시지가 `intent_id`로 상관되어 기록된다.
**end-to-end 블랙박스 정책 대비 이 프레임워크의 핵심 장점**이므로 논문·제안서의 논거이기도 하다.

## 승계 검토 중인 계약

IETF-125 `k8s_server.py`의 엔드포인트를 계약 그대로 승계하는 안:
`POST /inference` (JSON+base64 이미지 → `logs/json/`, `logs/images/`) · `POST /receive_policy` (YAML)

**ViLaR-IMO 트랙이 지금도 `/inference`를 쓰므로, 유지하면 두 트랙이 같은 감사 저장소를 공유한다.**
판정은 `docs/audit/IETF승계issue.md` §5 (참고 자료, 미채택).
""")

comp(f"{MA}/mcp_client", "A2A Client (IF-4 Manager 측 종단점)", f"`{MA}/`", "0", "미착수", f"""
MAC이 만든 L2 정책을 Worker에 전달하고 Task 상태·Artifact를 수신한다.
`{WA}/mcp_server/`의 대응 짝이며, 바인딩 정의는 `interfaces/if04_secure_a2a_channel/`에 있다.

## 흐름

```
MAMS 조회 (required-skill)          → Worker 후보
server/discover + agentcard://self  → Agent Card 확인
tools/call execute_policy(L2)       → {{task_id, accepted}}
tasks/get(task_id) 폴링              → COMPLETED + Artifact(Report + 증거 이미지)
```

## 주의

- **Worker 선택은 Client의 책임이 아니다.** MAMS의 `worker_selector/`가 정한다.
  Client는 정해진 상대에게 보내고 받는 것만 한다.
- Task 상태 전달 방식(폴링 vs `notifications/progress`)은 미정 (U-5). Phase 0은 폴링.
- 배치 근거: `docs/context/AI-Care_A2A_Core_Context(2).md` §4가 A2A Client를 **Manager AI Agent**에 배정 (D-9).
""")

# ── Worker ───────────────────────────────────────────────────────────────────
comp(WA, "Worker AI Agent", "저장소 루트", "0", "부분 구현 — SF 3종 동작", """
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
""")

comp(f"{WA}/worker_ai_core", "Worker AI Core (WAC)", f"`{WA}/`", "0", "미착수", f"""
**Policy Translator + Session Key Handler.** L2를 받아 L3로 번역하고 SF에 IF-5로 내린다.

| 하위 | 책임 |
|---|---|
| `policy_translator/` | L2 → L3 번역 (A2A 문서의 Policy Handler) |
| `session_key_handler/` | MAC이 발급한 세션 키 검증 |

> **Agent Executor는 여기 없다.** A2A 문서 §4가 Agent Executor를 **Worker AI Agent** 레벨에 배정하므로
> `../mcp_server/`에 둔다 (D-9).

## 지금 없는 것

현재 `../mcp_server/`가 노출하는 tool 6종은 **전부 L4(함수 호출) 수준**이다.
A2A 종단점이 되려면 그 위에 **L2 정책을 통째로 받는 `execute_policy`** 가 얹혀야 하고,
그 정책을 L3로 번역하는 것이 이 컴포넌트의 일이다. 두 층위는 공존한다 — 아래층은 디버깅용으로 남긴다.

## 작업 (Phase 0)

- [ ] 0-5 `execute_policy` / `get_task_report` / `cancel_task`
- [ ] 0-6 Policy Translator (L2→L3)
""")

comp(f"{WA}/worker_ai_core/policy_translator", "Policy Translator", "`worker_ai_core/`", "0", "미착수", """
L2 `<living-care-policy>` → L3 `<limo-agent-policy>` 번역. 스키마는 `contracts/`.

| L2 | → L3 | 해소 주체 |
|---|---|---|
| `<place>living_room` | `<waypoint><x/><y/>` | KG 조회 (G-6) |
| `<required-skill>person-scan` | `<perception>` 블록 | 디바이스 능력 |
| `<action-type>inspect-and-report` | 실행 시퀀스 | 시나리오 선택 |
| `<assurance><deadline-sec>` | `<report><timeout-sec>` | 그대로 전달 |

## Phase 3 — RL의 위치 (오독 주의)

docx의 강화학습은 **정책 생성이 아니라, 사전 저장된 시나리오 배열 중 정책에 맞는 것을 고르는 선택 문제**다.
즉 **이 컴포넌트 내부의 선택 모듈**이며, L2→L3 번역을 규칙 기반에서 학습 기반으로 대체하는 것이다.
논문에서 이 위치를 흐리면 "정책 생성을 RL로 한다"로 오독된다. (Search-R1, arXiv:2503.09516)
""")

comp(f"{WA}/worker_ai_core/session_key_handler", "Session Key Handler", "`worker_ai_core/`", "1", "미착수", """
MAC의 `session_key_manager/`가 발급한 세션 키를 검증한다.

## 주의

**Action Function이 실제 액추에이션 직전에 한 번 더 검증한다** (slide 16·18 명시).
Core에서 통과했다고 AF의 검증을 생략하지 말 것 — 이중 검증이 설계 의도다 (S-4).
""")

comp(f"{WA}/worker_ai_analyzer", "Worker AI Analyzer (WAA)", f"`{WA}/`", "0", "미착수", """
SF 실행 상태를 **IF-6**로 수집해 **Worker Report**를 만들고, A2A Task Status / Artifact로 변환해 상향 보고한다.
자가진단도 담당한다. 스키마: `contracts/worker_report/`

```json
{
  "report_id","task_id","policy_id","intent_id","agent_id","reported_at",
  "status":"abnormal",
  "observation":{"found","place","posture","motion":{"state","duration_sec"},"frame_id","pose"},
  "confidence":0.86,
  "evidence":{"type":"image/jpeg","ref":"iad://evidence/f_47","bbox":[...]},
  "request":["emergency_call","audio_check"],
  "diagnostics":{"elapsed_sec","rooms_visited","sf_errors"}
}
```

## 지금 못 채우는 필드

- **`observation.pose`** — PF가 pose를 채우지 않는다 (G-2). "어느 방에서 발견했는지" 보고 불가.
- **`evidence`** — 프레임 pinning이 없어 증거 이미지를 확보할 수 없다 (G-1).

**두 갭이 Report의 핵심 필드를 비운다.** Phase 0의 0-7·0-8이 이것을 푼다.
""")

comp(f"{WA}/worker_ai_management_system", "Worker AI Management System (WAMS)", f"`{WA}/`", "1", "미착수", """
자기 등록(registration)과 SF 컨테이너 수명주기를 담당한다. IF-3(↔WAC) · **IF-7(↔MAMS)**.

- `agent_card/` — Worker의 접속 정보와 Skill을 외부에 공개

## 주의

**IF-7이 이 프레임워크의 차별점이다.** A2A의 Agent Card는 정적 능력만 공시해 실시간 자원 상태를
반영하지 못한다. WAMS가 주기적으로 자원 상태를 MAMS에 갱신하는 경로가 그 공백을 메운다 (S-3).

SF의 Kubernetes 컨테이너화는 UKC 논문이 제시한 방향이나, Phase 0에서는 단일 프로세스 내 모듈로 두고
컨테이너화는 Phase 2 이후로 미룬다.
""")

comp(f"{WA}/worker_ai_management_system/agent_card", "Agent Card", "`worker_ai_management_system/`", "1", "미착수", """
Worker가 공개하는 디지털 명함. Manager는 여기서 이름·주소·지원 통신 방식·제공 Skill을 확인한다.

| A2A | MCP 대응 |
|---|---|
| AgentCard 코어 | `server/discover` 결과 |
| 확장 필드 (자원 상태·배터리·위치) | MCP resource `agentcard://self` |
| AgentSkill | `tools/list` 항목 1개 = Skill 1개 |

권장 명명: `skill.<domain>.<verb>` (예: `skill.livingcare.person-scan`)

## 주의

**Skill은 내부 함수 목록이 아니다.** Manager가 작업을 맡길 때 이해할 수 있는 **고수준 능력**이어야 한다.
`start_person_scan`은 함수이고, `person-scan`이 Skill이다.
""")

comp(f"{WA}/perception", "Perception Function (PF)", f"`{WA}/`", "0",
     "구현됨 — **크리티컬 결함 2건**", f"""
디바이스 데이터 획득과 상태 모델링. `/camera/image_raw`를 구독해 최신 프레임을 캐시한다.
IF-5(←WAC) · IF-6(→WAA).

**파일**: `Perceptions.py` — `PerceptionModule(node, topic="/camera/image_raw")`
`ReasoningModule`이 기대하는 `FrameSource` 시그니처를 만족한다:
`(frame_id=None) -> {{"frame_id","frame","stamp","pose"}}`

## ⚠️ G-1 — 프레임 pinning 부재 (크리티컬)

```python
self._latest: Optional[dict] = None          # 슬롯 1개뿐
...
if frame_id is not None and item["frame_id"] != frame_id:
    return None                              # 과거 프레임 조회 불가
```

`PersonScan`이 `f_47`에서 사람을 잡아도, LLM이 `check_object_state(frame_id="f_47")`를 부를 때쯤엔
최신이 `f_53`이라 **증거 이미지를 얻을 수 없다.** 시나리오 1의 결론부가 끊긴다.

**0-7**: N프레임 링버퍼 + `pin(frame_id)`.
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
실물 LIMO는 Orbbec 계열이라 보통 **bgr8**이고, `yolo_detect`의 `frame[:, :, ::-1]`과 겹쳐
**YOLO가 RGB를 보게 되어 정확도가 떨어진다**. depth(16UC1)나 mono8이면 **크래시하거나 쓰레기 배열**이 된다.

## 주의

프레임 rate가 자료마다 다르다 — 스펙 30 Hz / d3d12 시 10 Hz / **실측 ~2·~3.8 Hz**.
**작업 0-0에서 실제 rate를 먼저 측정할 것.** G-1의 위험도가 여기에 좌우된다.
""")

comp(f"{WA}/reasoning", "Reasoning Function (RF)", f"`{WA}/`", "0",
     "**구현 완성도 최고**", f"""
관측으로부터 상태를 판단한다. 정책 규칙·컨텍스트·디바이스 지식을 다룬다. IF-5 · IF-6.

**파일**: `Reasonings.py` — `ReasoningModule` + `PersonScan` + `yolo_detect`

## 왜 이 파일이 기준인가

**ROS2에 의존하지 않는 순수 로직**이다. 백엔드(YOLO·Nav2·크롭)를 생성자로 주입받고
미주입 시 no-op으로 동작하므로 **로봇 없이 단독 테스트가 가능하다.**
이 저장소에서 가장 잘 분리된 설계이므로 다른 컴포넌트를 만들 때 이 패턴을 따를 것.

```python
DetectFn    = Callable[[object], list]          # frame -> [{{"class","conf","bbox"}}]
PlanFn      = Callable[[dict, dict], list]      # start, goal -> [{{"x","y","yaw"}}]
CropFn      = Callable[[object, list], bytes]   # frame, bbox -> jpeg bytes
FrameSource = Callable[..., Optional[dict]]
```

## `PersonScan` — P-3의 "코드 자율 구간"

1 Hz로 최신 프레임에 YOLO를 돌려 **사람 유무(O/X)만** 판별한다. **상태 판정은 하지 않는다.**
사람이 잡히면 frame_id·pose·bbox만 기록하고, "괜찮은지"는 상위 LLM이 크롭 이미지를 보고 정한다.

**이 분리가 P-3의 실체다.** 픽셀이 LLM에 올라가는 유일한 순간은 `check_object_state`가 크롭 1장을
돌려줄 때다. 컨텍스트 보호와 비용 절감이 동시에 된다.

## ⚠️ G-3 — API 5종이 MCP tool로 미노출

`start_person_scan` · `wait_for_person` · `check_object_state` · `stop_person_scan` · `get_scan_status`가
**구현돼 있으나** `../mcp_server/MCP_server.py`에 tool 데코레이터가 없다.
시나리오 1의 탐색·판정 경로를 외부에서 호출할 수 없다. **구현이 아니라 노출만 하면 되는 저비용 작업 (0-9).**

## 주의

`yolo_detect`는 `ultralytics`를 **함수 안에서만 import**한다 — 이 모듈을 그냥 import했을 때
torch 등 무거운 의존성을 물지 않게 하기 위함이다. 이 lazy import를 최상단으로 올리지 말 것.
""")

comp(f"{WA}/action", "Action Function (AF)", f"`{WA}/`", "0",
     "구현됨 — 단일 웨이포인트만 검증", f"""
결정에 따른 물리 행동. 세션 키 검증 후 디바이스를 제어한다. IF-5 · IF-6.

**파일**: `Actions.py` — `ActionModule(node, nav_action="navigate_to_pose")`

## ROS2 의존 표면 (전부)

```python
from action_msgs.msg   import GoalStatus
from geometry_msgs.msg import PoseStamped
from nav2_msgs.action  import NavigateToPose
```

**로봇 비의존이다.** Nav2만 돌면 turtlebot3든 실물 LIMO든 수정 없이 동작한다.

## 검증 실적 (과신 금지)

기록된 검증은 `plan_and_navigate(x=1.0, y=0.0)` **단일 웨이포인트 1회**뿐이다
(`sequence_result: {{"completed":1,"total":1}}`, `/odom` `(0,0)` → `(0.764, 0.009)`).
**다중 웨이포인트 순차 이동 · `cancel_goal_sequence` · `cancel`은 실행 기록이 없다.**
게다가 이 검증은 `turtlebot3_world`에서 이뤄졌고 **small_house 재검증은 없다.**

## ⚠️ G-5 — stale 콜백 가드 없음

- `_on_result`가 토큰 검사 없이 `self.status`를 덮어쓴다
- `cancel_goal`이 Nav2 취소 승인을 안 기다리고 낙관적으로 `"cancelled"`로 쓴다
- `_on_feedback`도 무조건 `"navigating"`을 쓴다 → stale feedback이 대기 루프를 풀 수 있다

**0-12**: `_goal_token` 도입 + 취소 승인 대기.

## ⚠️ G-4 — `look_around` / patrol 미구현

`tools/scenarios/check_obj_state.json`이 `look_around`·`is_looking_around`·`interrupt_look_around`를
참조하지만 여기에 없다. **해당 시나리오는 실행 불가.**
(두 번째 사유도 있다 — `check_object_state`에 `detections` 인자를 넘기는데 RF가 받지 않는다)

## 주의

첫 웨이포인트는 `prev_xy`가 없어 `yaw_deg = 0.0`으로 떨어진다.
**현재 로봇 자세를 읽지 않으므로** 필요하면 명시적으로 줄 것.
""")

comp(f"{WA}/mcp_server", "A2A Server + Agent Executor (IF-4 Worker 측 종단점)", f"`{WA}/`", "0",
     "동작 — L4만 노출", f"""
**파일**: `MCP_server.py` — `LimoGatewayNode` + MCP tool. stdio 트랜스포트.
바인딩 정의는 `interfaces/if04_secure_a2a_channel/`에 있다.

> **배치 근거 (D-9)**: `docs/context/AI-Care_A2A_Core_Context(2).md` §4가 **A2A Server와 Agent Executor를
> Worker AI Agent 레벨**에 배정한다. 스펙 §10.1도 `MCP_server.py`를 "Worker AI Core / A2A 종단점"으로 매핑.
> **최상위 `a2a/` 디렉터리는 두 문서 어디에도 근거가 없어 폐기했다.**

## 현재 노출된 tool 6종 (전부 L4)

| tool | 계층 | Phase 0 처리 |
|---|---|---|
| `plan_and_navigate`·`navigate_waypoints`·`cancel` | L4 Action | 유지. `execute_policy` 내부에서 호출 |
| `get_camera_snapshot`·`detect_objects` | L4 Perception/Reasoning | 유지 |
| `get_status` | L4 상태 | `get_task_report`로 승격 (task_id 상관 추가) |
| — | **L2** | **`execute_policy` 신설** ← 0-5 |
| — | L4 | **person-scan 5종 노출** ← 0-9 (G-3) |

## Phase 0 최소 A2A 집합

```
server/discover                  → 프로토콜 버전·능력·정체성 (= Agent Card 코어)
tools/list                       → 공개 Skill 목록
resources/read agentcard://self  → 확장 Agent Card
tools/call execute_policy        → L2 수락. {{task_id, accepted, reject_reason?}}
tools/call get_task_report       → 상태·최종 Report
tools/call cancel_task           → 취소
```

## ⚠️ MCP SDK 버전 (U-1)

`from mcp.server.mcpserver import Image, MCPServer` — 구 `fastmcp.FastMCP`가 아닌 새 이름이지만
**이것만으로 최신 SDK라고 판단할 수 없다.** 반대 증거:

- `tools/scenarios/*.py`가 **`await session.initialize()`를 호출한다** — 2026-07-28이 제거했다는 핸드셰이크가 살아 있다
- `requirements.txt`가 `mcp[cli]`로 **버전 미고정**
- 이 import는 limo_slam에서 **그대로 복사한 패턴**이라 의도적 채택 흔적이 아니다

**작업 0-0에서 설치된 `mcp` 패키지 버전을 직접 확인할 것.**

## 주의

**stdout을 오염시키지 말 것.** stdio 트랜스포트는 stdout을 JSON-RPC 전용으로 쓴다.
YOLO 가중치 다운로드 진행표시줄이 실제로 프로토콜을 깼고, `contextlib.redirect_stdout(sys.stderr)`로
감싼 warm-up으로 해결했다 — **그 코드를 제거하지 말 것.**

`sys.path`로 `{WA}/{{perception,reasoning,action}}`을 추가해 모듈명(`Perceptions`/`Reasonings`/`Actions`)
그대로 import한다. 패키지화는 Phase 1 정리 항목이다.
""")

# ── interfaces ───────────────────────────────────────────────────────────────
C["interfaces"] = f"""# interfaces — 인터페이스 카탈로그 (IF-1 ~ IF-8)

> **구조 정본**: `SOT.md` §3 · **설계 정본**: `{SPEC}` §3

스펙 §3은 *"각 인터페이스가 곧 표준화 문서의 한 절이 된다"* 고 적는다.
**IF-1~IF-8은 표준화 산출물(S-6)이므로 1급 디렉터리를 갖는다** (D-10).

| 디렉터리 | 인터페이스 | 종단점 | Phase |
|---|---|---|---|
| `if01_database/` | Database Interface | MAC ↔ KG/IAD, MAA ↔ IAD | 0 |
| `if02_analytics/` | Analytics Interface | MAC ↔ MAA, WAC ↔ WAA | 0 |
| `if03_registration/` | Registration Interface | MAC ↔ MAMS, WAC ↔ WAMS | 0 |
| `if04_secure_a2a_channel/` | **Secure A2A Channel** | MAC ↔ WAC | 0 |
| `if05_sf_facing/` | SF-Facing Interface | WAC → PF/RF/AF | 0 |
| `if06_agent_monitoring/` | Agent Monitoring Interface | PF/RF/AF → WAA | 0 |
| `if07_ams_facing/` | AMS-Facing Interface | MAMS ↔ WAMS | 2 |
| `if08_analyzer_facing/` | Analyzer-Facing Interface | MAA ↔ WAA | 2 |

## `interfaces/` 와 `contracts/` 의 차이

- **`interfaces/`** = **누가 누구에게 어떻게 말하는가.** 종단점·호출 규약·전송·수명주기.
- **`contracts/`** = **무엇을 말하는가.** 그 위를 흐르는 페이로드 스키마(L1·L2·L3·Report).

예: IF-4는 "MAC이 WAC에 `tools/call execute_policy`로 보내고 `tasks/get`으로 폴링한다"를 정하고,
`contracts/high_level_policy/`는 "그 안에 실리는 `<living-care-policy>`가 어떤 필드를 갖는가"를 정한다.

## 규칙

**컴포넌트 경계를 넘는 직접 호출을 만들지 않는다** (P-2). 필요하면 인터페이스를 새로 정의하고
스펙 §3 표에 추가한 뒤 여기에 디렉터리를 만든다.
"""

iface("if01_database", "IF-1", "Database Interface",
      "MAC ↔ KG/IAD, MAA ↔ IAD", "0", "미착수", """
KG 조회, intent·policy 감사 레코드 쓰기, KB audit을 담당한다.

## 계약 (초안)

```
resolve(phrase: str, context: dict) -> list[Binding]     # KG 읽기
audit(record: AuditRecord) -> None                        # IAD 쓰기
prompt(schema_id: str) -> str                             # IAD 스키마 프롬프트 읽기
```

## 왜 하나의 인터페이스인가

KG와 IAD는 별개 저장소지만 접근 계층은 같다. 하나로 두면 **MAC이 저장소 구현을 몰라도 된다** —
KG를 JSON 룩업에서 그래프DB로 바꿔도 이 계약이 고정이면 무중단 교체가 된다 (D-6).

## 주의

**P-5(감사 가능성)를 실현하는 인터페이스다.** L0~L4 전 계층의 변환 결과가 여기를 통해 기록된다.
어느 한 계층이라도 감사 레코드를 빠뜨리면 end-to-end 상관이 끊긴다.
""")

iface("if02_analytics", "IF-2", "Analytics Interface",
      "MAC ↔ MAA, WAC ↔ WAA", "0", "미착수", """
해석된 report와 완료/재시도/전환 판정을 주고받는다. **Manager와 Worker 양쪽에 대칭으로 존재한다** (P-1).

| 방향 | 내용 |
|---|---|
| MAA → MAC | 임무 판정 (Assured / Retry / Reselect / Escalated / 잔여 정책) |
| WAA → WAC | SF 실행 요약, 자가진단 결과 |

## 주의

**IF-8(Analyzer-Facing)과 혼동하지 말 것.**
IF-2는 **같은 에이전트 안**의 Core↔Analyzer, IF-8은 **에이전트를 넘는** MAA↔WAA다.
IF-8은 제어 평면과 분리된 관측 평면이며 Phase 2다.
""")

iface("if03_registration", "IF-3", "Registration Interface",
      "MAC ↔ MAMS, WAC ↔ WAMS", "0", "미착수", """
Worker 등록·조회·상태를 주고받는다. Manager와 Worker 양쪽에 대칭으로 존재한다 (P-1).

| 방향 | 내용 |
|---|---|
| MAC → MAMS | `required-skill`로 Worker 후보 조회 |
| WAC → WAMS | 자기 등록, SF 수명주기 상태 |

## 주의

**Registry는 후보만 제공하고 최종 선택은 MAMS의 `worker_selector/`가 한다.**
A2A 명세는 Worker 자동 선택을 하지 않으며, 선택 로직은 Manager의 책임이라고 명시한다.
Phase 0에서는 Worker 주소를 고정 설정으로 둬도 된다.
""")

iface("if04_secure_a2a_channel", "IF-4", "Secure A2A Channel",
      "MAC ↔ WAC", "0", "부분 — MCP 서버 동작, A2A 의미론 미구현", f"""
**L2 고수준 정책, Task 상태, Artifact**를 전달하는 에이전트 간 채널.
**A2A 의미론을 유지하면서 전송·직렬화는 MCP를 재사용한다.**

종단점 구현: Manager 측 `{MA}/mcp_client/` · Worker 측 `{WA}/mcp_server/`
이 디렉터리에는 **바인딩 정의**(어느 쪽 소유도 아닌 공유 자산)를 둔다.

## 왜 이 바인딩인가 (★핵심 기여 — 표준화 항목 S-4)

업계 통념은 "MCP는 agent↔tool, A2A는 agent↔agent"로 역할이 갈린다는 것이다. 근거:

1. **엣지 로컬성** — 같은 엣지 배치가 다수. stdio 로컬 IPC가 지연·전력에서 유리
2. **툴체인 단일화** — Worker 내부 SF 호출(L4)이 이미 MCP tool. 외부까지 통일하면 **서버 구현 하나**
3. **2026-07-28 MCP 개정이 격차를 없앰** — A2A 핵심 객체 전부가 현행 MCP에 대응물을 가짐

> **포지셔닝**: "A2A를 MCP로 대체한다"가 아니라 **"A2A 의미론의 MCP 전송 바인딩을 정의한다"**.
> A2A 명세가 이미 JSON-RPC / gRPC / HTTP+JSON 3종 바인딩을 인정하므로
> **제4의 바인딩을 제안하는 형태**가 표준화 트랙에서 가장 방어 가능하다.

## 객체 매핑 (스펙 §6.2)

| A2A v1.0 | MCP 2026-07-28 |
|---|---|
| AgentCard | `server/discover` + resource `agentcard://self` |
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

## 보안

mTLS/IPsec + Session Key (slide 13). Phase 0은 stdio 로컬로 OS 프로세스 격리에 의존한다.
**Action Function이 액추에이션 직전에 키를 한 번 더 검증하는 이중 구조를 유지할 것** (S-4).

## 주의

**제안서·논문 제출 전 MCP 명세 최신판을 재확인할 것** (U-1). 이 매핑 전체가 2026-07-28 개정판에 의존한다.
""")

iface("if05_sf_facing", "IF-5", "SF-Facing Interface",
      "WAC → PF/RF/AF", "0", "부분 — 현재는 함수 직접 호출", f"""
Worker AI Core가 **L3 저수준 정책**을 Service Function에 내리는 인터페이스.
IETF I2NSF의 **NSF-Facing Interface**에 대응하는 이름이며, 이 대응이 표준화 논거다 (S-2).

## 전달 대상

`{WA}/perception/` · `{WA}/reasoning/` · `{WA}/action/`
페이로드 스키마는 `contracts/low_level_policy/`.

## 요소명 규칙

L3 요소명은 SF가 실제로 받는 자료구조와 **1:1**로 맞춘다.
예: `<waypoint>` ↔ `Actions._goal_xy_yaw()`가 받는 `{{"x","y","frame"?,"yaw_deg"?}}`.
어긋나면 Policy Translator에 변환 로직이 쌓여 계층 분리(P-2)가 무너진다.

## 현재 상태

`MCP_server.py`가 `LimoGatewayNode`에서 세 모듈을 직접 생성·주입한다.
즉 **인터페이스가 아직 코드 경계로만 존재하고 규약으로 형식화되지 않았다.**
0-6(Policy Translator) 착수 시 이 계약을 먼저 정의할 것.
""")

iface("if06_agent_monitoring", "IF-6", "Agent Monitoring Interface",
      "PF/RF/AF → WAA", "0", "미착수", """
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
""")

iface("if07_ams_facing", "IF-7", "AMS-Facing Interface",
      "MAMS ↔ WAMS", "2", "미착수", """
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
""")

iface("if08_analyzer_facing", "IF-8", "Analyzer-Facing Interface",
      "MAA ↔ WAA", "2", "미착수", """
상세 진단과 이상 이벤트를 에이전트 간에 주고받는다. **제어 평면과 분리된 관측 평면**이다.

## IF-4와의 분리 이유

IF-4(제어)는 정책·Task·Artifact를 나른다. IF-8(관측)은 그와 별도로 진단·이상 이벤트를 나른다.
분리하면 **제어 채널이 막혀도 진단은 흐르고**, 관측 트래픽이 제어 지연에 영향을 주지 않는다.

## 주의

Phase 2 항목이다. Phase 0에서는 진단이 Report의 `diagnostics` 필드에 실려 IF-4로 함께 올라간다.
IF-8을 도입할 때 그 필드를 이쪽으로 옮길지 결정해야 한다 (미결정).
""")

# ── 비컴포넌트 ───────────────────────────────────────────────────────────────
C["contracts"] = f"""# contracts — 계층 간 페이로드 스키마

> **구조 정본**: `SOT.md` · **설계 정본**: `{SPEC}` §4·§5
> **Phase**: 0 · **구현 상태**: 미착수 (작업 0-4)

컴포넌트 사이의 **유일한 계약**이다. P-2에 따라 각 계층은 바로 아래 계층만 알고, 그 앎은 전부 여기 있는 스키마로만 이뤄진다.

| 경로 | 계층 | 형식 | 흐르는 인터페이스 |
|---|---|---|---|
| `intent_query/` | **L1** Intent Query | JSON | (MAC 내부) |
| `high_level_policy/` | **L2** High-level Policy (ECA) | XML (내부 JSON 병용 검토 — U-2) | **IF-4** |
| `low_level_policy/` | **L3** Low-level Policy | XML | **IF-5** |
| `worker_report/` | Worker Report | JSON | IF-6 → IF-4 |

## `interfaces/` 와의 차이

`interfaces/`는 **누가 누구에게 어떻게 말하는가**, `contracts/`는 **무엇을 말하는가**이다.

## 규칙

1. **스키마를 바꾸면 여기부터 고치고 스펙에 반영한다.** 코드가 스펙을 앞서면 SOT가 깨진다.
2. **L2에 디바이스 이름을 넣지 않는다.** device-agnostic이어야 다중 Worker fan-out이 성립한다.
3. **검증기를 함께 둔다.** 스키마만 있고 검증이 없으면 P-4가 성립하지 않는다.
4. L3 요소명은 SF가 실제로 받는 자료구조와 1:1로 맞춘다.

## 원본 자료의 알려진 오류 (수정해서 쓸 것)

- slide 21의 `<goal>37.5665, 126.9781</goal>`은 **WGS84 위경도(서울시청)** 다. 실내 Nav2 로봇은 `map` 프레임 x/y/yaw를 쓴다.
- slide 21의 `<rate>10Hz`는 **순찰 시나리오에 잘못 붙은 값**이다. 구현은 1 Hz이고 10 Hz는 I2ICF의 주행 중 회피 값이다.
- slide 21의 XML은 닫는 태그가 없는 **표현용 의사코드**다. 논문·제안서에는 정규화안을 쓸 것.

## 미결정

**U-2**: L2 직렬화 — XML(YANG/NETCONF 정합) vs JSON(LLM 생성 정확도·MCP 친화).
현재 권고는 **내부 JSON, 표준 문서·전시 XML, 양방향 변환**.
"""

C["sim"] = f"""# sim — 시뮬레이션 환경

> **구조 정본**: `SOT.md` · **설계 정본**: `{SPEC}` §10.2
> **컴포넌트가 아니다.** 비즈니스 로직을 두지 않는다 (P-3).

```bash
source /opt/ros/jazzy/setup.bash
./fetch_meshes.sh                     # 최초 1회 — AWS 메시 ~55MB
ros2 launch sim/sim_bringup.launch.py
```

| 항목 | 현재 |
|---|---|
| ROS2 | **Jazzy** (WSL2 Ubuntu 24.04) — **팀 내 배포판이 갈려 있음, 통일 필요 (U-12)** |
| 로봇 | **turtlebot3 waffle** (LIMO 아님) — 카메라 센서·브리지가 이미 완성돼 있어 선택 |
| 월드 | **AWS RoboMaker small_house** — 실제 주거 공간이라 리빙케어에 적합 |
| 측위 | **`slam_toolbox` (`slam:=True`)** — AMCL 아님. 초기 pose TF 레이스 원천 회피 |
| 카메라 | `/camera/image_raw` — rate가 자료마다 다름 (30 / 10 / 실측 2~3.8 Hz) |
| **RTF** | **0.04 ~ 0.06** — **최대 리스크** |

## ⚠️ 두 가지 큰 문제

**1. RTF 0.04~0.06 (U-14)** — headless·무로봇에서도 그렇다. 6.3분 시나리오가 **벽시계 2시간**이 된다.
반복 검증이 불가능하므로 `tools/patrol_viz/`로 논리를 검증하고 여기는 최종 확인용으로 쓰는 이원화가
현재 유일한 실행 가능안이다. 개선하려면 가구 collision을 단순 박스로 바꾸거나 `<collision>`을 빼는 게 효과가 클 것이다.

**2. small_house 카메라 미검증 (작업 0-0)** — 카메라·YOLO 검증 실적은 전부 `turtlebot3_world` 기준이다.
small_house 전환 후 비대화형 세션에서 양 경로가 막혔다: 헤드리스는 100초 넘게 프레임 0장(`/dev/dri` 부재 추정),
GUI는 `qt.qpa.xcb: could not connect to display :0`. 저장소는 이를 **비대화형 세션(WSLg 소켓 접근 불가)의
제약으로 추정**하며 대화형 재검증을 못 했다고 명시한다.
**사람이 자기 WSL 터미널에서 직접 돌려 확인하는 것이 Phase 0의 사실상 첫 작업이다.**

## 해결된 함정 (재발 방지)

- **`cmd_vel` 타입 불일치** — 스톡 브리지 yaml은 `TwistStamped`, Nav2 `collision_monitor`는 `Twist` 발행 →
  ROS2가 별개 토픽으로 취급해 **로봇이 영영 안 움직였다.** `waffle_bridge_fixed.yaml`로 `Twist` 통일.
- **RViz2 Map 디스플레이 미동작** — `indexed_8bit_image` 셰이더 링크 실패. **Nav2 costmap 시각화도 같은 이유로 실패할 것.**
- **RViz2 ↔ Gazebo 렌더링 요구가 반대** — Gazebo는 `GALLIUM_DRIVER=d3d12`, RViz2는 `LIBGL_ALWAYS_SOFTWARE=1`.
- **WSL2 GPU** — `/dev/dri`가 아니라 **`/dev/dxg`**. `GALLIUM_DRIVER=d3d12` + `LD_LIBRARY_PATH=/usr/lib/wsl/lib`.
- **numpy ABI 충돌** — `ultralytics`가 numpy 2.x를 깔면 apt matplotlib과 충돌. `numpy==1.26.4` 고정.

## 실물 LIMO 이행 시 없는 것

**실로봇용 bringup이 없다** (`amcl`·`map_server`·`limo_base`·`ydlidar` 참조 0건).
`sim_bringup.launch.py`는 Gazebo에 완전히 묶여 있다. `real_bringup.launch.py`를 별도로 작성해야 한다.
"""

C["tools"] = f"""# tools — 검증·시연 도구

> **구조 정본**: `SOT.md` · **설계 정본**: `{SPEC}` §10.1
> **컴포넌트가 아니다.** 비즈니스 로직을 두지 않는다 (P-3).

| 경로 | 용도 |
|---|---|
| `patrol_viz/` | Gazebo·Nav2·YOLO **없이** 순찰 로직 검증·시연 |
| `scenarios/` | MCP 왕복 CLI 클라이언트 + 시나리오 DSL |

## patrol_viz — 왜 존재하는가

Gazebo RTF가 0.04~0.06이라 6.3분 시나리오가 벽시계 2시간이 된다. **반복 검증이 불가능해 만든 대체 수단**이다.

```bash
cd tools/patrol_viz
./run_coverage.sh    # GUI 없이 커버리지 수치 + patrol_sim.png
./run_patrol.sh      # RViz2 순찰 애니메이션 + 카메라 스트리밍
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
python3 tools/scenarios/send_goal.py 1.0 0.0
python3 tools/scenarios/capture_and_detect.py out.jpg
```

**`check_obj_state.json`은 현재 실행 불가**다 — 참조하는 `look_around`·`is_looking_around`·
`interrupt_look_around`가 AF에 없고(G-4), `check_object_state`도 tool로 노출되지 않았으며(G-3),
RF의 `check_object_state`는 JSON이 넘기는 `detections` 인자를 받지 않는다.

## 자산 메모

`patrol_viz/limo/limo.urdf` — WeGo `limo_gazebo`(ROS1 xacro)에서 변환한 **실제 LIMO 모델**.
Jazzy 파싱은 통과한다. **Gazebo 플러그인 3블록만 Harmonic 문법으로 재작성하면 시뮬에 투입 가능**하다.
"""


def stage_claudemd():
    print("[claudemd] CLAUDE.md 재생성")
    for path in sorted(C):
        d = os.path.join(ROOT, path) if path else ROOT
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "CLAUDE.md"), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(C[path])
    print(f"  {len(C)}개 생성")
    # 폐기 위치에 남은 CLAUDE.md 정리
    for stale in (f"{WA}/service_functions", "a2a", "manager", "worker"):
        p = os.path.join(ROOT, stale, "CLAUDE.md")
        if os.path.exists(p):
            trash(f"{stale}/CLAUDE.md")


def stage_fixpath():
    print("[fixpath] 경로 참조 수정")
    p = os.path.join(ROOT, WA, "mcp_server", "MCP_server.py")
    if os.path.exists(p):
        s = open(p, encoding="utf-8").read()
        s2 = s.replace('"worker", "service_functions", _sf', f'"{WA}", _sf')
        if s2 != s:
            open(p, "w", encoding="utf-8", newline="\n").write(s2)
            print(f"  fix MCP_server.py sys.path -> {WA}/{{perception,reasoning,action}}")
        else:
            print("  - MCP_server.py sys.path 이미 정상")
    for n in ("send_goal.py", "capture_and_detect.py"):
        p = os.path.join(ROOT, "tools", "scenarios", n)
        if not os.path.exists(p):
            continue
        s = open(p, encoding="utf-8").read()
        s2 = s.replace('"..", "..", "a2a", "server", "MCP_server.py"',
                       f'"..", "..", "{WA}", "mcp_server", "MCP_server.py"')
        if s2 != s:
            open(p, "w", encoding="utf-8", newline="\n").write(s2)
            print(f"  fix tools/scenarios/{n} SERVER_PATH -> {WA}/mcp_server/")
        else:
            print(f"  - tools/scenarios/{n} 이미 정상")


DECISIONS = """| **D-9** *(SOT)* | A2A 종단점을 **최상위가 아니라 각 에이전트 안에** 둔다 — `manager_ai_agent/mcp_client/`, `worker_ai_agent/mcp_server/` | `AI-Care_A2A_Core_Context` §4가 A2A Client를 Manager AI Agent에, A2A Server·Agent Executor를 Worker AI Agent에 배정. §10.1도 `MCP_server.py`를 WAC/A2A 종단점으로 매핑. **최상위 `a2a/`는 근거 없음** |
| **D-10** *(SOT)* | `interfaces/`를 **1급 디렉터리**로 두고 IF-1~IF-8에 각각 디렉터리를 준다 | §3 *"각 인터페이스가 곧 표준화 문서의 한 절이 된다"*. 표준화 항목 S-6의 실체 |
| **D-11** *(SOT)* | PF/RF/AF 디렉터리에서 `_function` 접미사를 뺀다 (`perception/` 등) | 명명 규칙 N-1의 명시적 예외. 상위 `worker_ai_agent/`가 문맥을 준다 |
| **D-12** *(SOT)* | `service_functions/` 중간 계층을 **두지 않는다** | §2.2에서 "Service Functions"는 컴포넌트가 아니라 **행 레이블**. 실제 컴포넌트는 PF/RF/AF 셋 |
| **D-13** *(SOT)* | 컴포넌트 디렉터리에 정식 명칭 전체를 쓴다 (`manager_ai_core`, `core` 아님) | 파일 하나만 열려 있어도 소속이 드러나야 하고, 축약형은 Manager/Worker 양쪽에서 충돌한다 |"""


def stage_spec():
    print("[spec] D-9~D-13을 §0.2 결정표에 반영")
    p = os.path.join(ROOT, SPEC)
    if not os.path.exists(p):
        return print(f"  ! 스펙 없음: {SPEC}")
    s = open(p, encoding="utf-8").read()
    if "**D-9**" in s:
        return print("  - 이미 반영됨")
    anchor = "| **D-8** *(v0.2)*"
    i = s.find(anchor)
    if i < 0:
        return print("  ! D-8 행을 못 찾음 — 수동 반영 필요")
    j = s.find("\n", i)
    s = s[:j + 1] + DECISIONS + "\n" + s[j + 1:]
    note = ("\n> **D-9 ~ D-13은 저장소 구조 정본 `SOT.md`에서 온 결정이다.** "
            "구조 규범과 기계 검사는 `SOT.md` / `sot_audit.py`가 관할한다.\n")
    k = s.find("\n---", j)
    s = s[:k] + "\n" + note + s[k:]
    open(p, "w", encoding="utf-8", newline="\n").write(s)
    print("  + D-9 ~ D-13 5건 추가")


if __name__ == "__main__":
    st = {"move": stage_move, "claudemd": stage_claudemd,
          "fixpath": stage_fixpath, "spec": stage_spec}
    a = sys.argv[1] if len(sys.argv) > 1 else ""
    if a not in st:
        print(__doc__)
        sys.exit(1)
    st[a]()
