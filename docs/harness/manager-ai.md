# 하네스 — Manager AI Agent

> 대상: `manager_ai_agent/**` (MAC · MAA · MAMS · KG · IAD · mcp_client)
>
> 공통 절차는 @docs/harness.md.

## 0. 먼저 알아야 할 것

**Manager AI Agent는 코드가 0줄이다.** 전 디렉터리가 규범만 갖고 있다.
따라서 이 하네스는 "고칠 때"가 아니라 **"처음 만들 때"** 의 하네스다.

무엇을 만들든 **가장 먼저 `contracts/`의 스키마를 정한다.** 스키마 없이 코드를 쓰면
계층 분리(P-2)가 무너지고 나중에 전부 다시 써야 한다.

## 1. 읽을 것

1. `manager_ai_agent/<대상>/CLAUDE.md` — 그 컴포넌트의 책임과 계약 초안
2. @docs/architecture.md §계층 구조 — L0~L4가 어디서 무엇으로 바뀌는지
3. 설계 정본의 **해당 절만**:
   - MAC → §4 (Intent-Policy Continuum, L1/L2 스키마)
   - MAA → §5 (Report 스키마, status 열거, 폐루프)
   - MAMS → §7 (정책 분해, Worker 선택, dispatch-mode)
   - KG/IAD → §3.1 (IF-1 계약), §2.3 (KG vs IAD 구분)
   - mcp_client → §6 (A2A-over-MCP 바인딩)
4. @docs/conventions.md §2 — **의존성 주입 패턴을 그대로 따른다**

## 2. 사전 점검

```bash
# 만들려는 컴포넌트가 의존하는 인터페이스와 스키마가 먼저 정의됐는지
ls interfaces/if01_database/ interfaces/if02_analytics/ interfaces/if04_secure_a2a_channel/
ls contracts/intent_query/ contracts/high_level_policy/ contracts/worker_report/
```

비어 있으면 **거기부터 채운다.** 코드가 스키마를 앞서면 SOT가 깨진다 (SP-4).

## 3. 컴포넌트별 필수 검증

### (a) Manager AI Core — L0 → L1 → L2

| # | 검증 |
|---|---|
| C-1 | **L2에 디바이스 이름이 들어가지 않는가.** L1의 `devices`는 후보 힌트일 뿐이고 확정은 MAMS가 한다. L2가 device-agnostic이어야 다중 Worker fan-out이 성립한다 |
| C-2 | **`bindings`를 남기는가.** 어느 어구가 어떤 값으로 해소됐는지 없으면 오역 디버깅이 불가능하다 (P-5 감사) |
| C-3 | **LLM 실패 경로를 실행했는가.** 타임아웃·스키마 위반 출력·JSON 파싱 실패 각각에서 **규칙 기반 폴백**으로 내려앉는지. 정상 파싱 → 필드 정규화 → 폴백 3단 구조를 권장 |
| C-4 | **스키마 검증을 통과 못 한 출력이 정책으로 승격되지 않는가.** 재생성 → 폴백 → 사용자 확인 순 (P-4 실패 안전) |
| C-5 | **KG를 직접 파일로 읽지 않는가.** IF-1 계약(`resolve()`)으로만 접근해야 후일 그래프DB로 무중단 교체된다 |
| C-6 | `<assurance>` 블록이 비어 있지 않은가. `not_found`·`timeout` 후속 액션이 여기서 선언적으로 정해진다 |

### (b) Manager AI Analyzer — Report 해석 · 폐루프

| # | 검증 |
|---|---|
| A-1 | **`status` 7종을 전부 처리하는가.** `completed`/`abnormal`/`not_found`/`failed`/`partial`/`rejected`/`timeout`. 처리되지 않는 값이 있으면 폐루프가 멈춘다 |
| A-2 | **루프가 수렴하는가.** 재시도 상한과 후보 소진 조건 없이는 `failed → Retry → Dispatched → failed`가 무한히 돈다. **Phase 0부터 상한을 넣는다** |
| A-3 | **A2A TaskState와 report.status를 혼동하지 않는가.** `COMPLETED` ≠ 정상. Task가 성공해도 관측은 `abnormal`일 수 있다 |
| A-4 | 모든 상태 전이가 IF-1로 IAD에 기록되는가 (P-5) |

> **A-3을 흐리면 "할머니가 쓰러졌는데 성공으로 보고"가 된다. 이건 R4다.**

### (c) MAMS — Registry · Worker 선택

| # | 검증 |
|---|---|
| M-1 | Registry가 **후보만 제공**하고 최종 선택은 `worker_selector/`가 하는가 (A2A 명세 경계) |
| M-2 | `rejected` 수신 시 해당 Worker를 제외하고 재선택하는가 |
| M-3 | dispatch-mode 5종(`and-all`/`or-race`/`or-fallback`/`sequential`/`split`)의 완료 조건이 각각 구현됐는가 (Phase 2) |
| M-4 | `or-race`에서 **첫 성공 시 나머지를 실제로 취소**하는가 |

### (d) KG — 장소 룩업 (G-6)

| # | 검증 |
|---|---|
| K-1 | **좌표계를 섞지 않는가.** docx의 `locations.json`(`living_room=(1.2,0.4)`)은 small_house 좌표계와 **무관한 별개 출처**다. 설계 정본 §3.1의 예시 값도 이 문제를 갖고 있다 |
| K-2 | **방 이름을 임의로 붙이지 않는가.** 저장소에서 의미 있는 이름이 붙은 좌표는 **2개뿐**이다 — `(8.10, 1.71)`="식탁 구역", `(-7.77, 0.56)`="좌상단 방" |
| K-3 | 좌표가 맵 범위 안인가. A* `snap()`은 범위 검사가 없어 **음수 인덱스면 numpy가 조용히 반대편 끝을 읽는다** |
| K-4 | `confidence`를 채우는가. 낮은 신뢰도 바인딩은 사용자 확인(MRTR)으로 승격될 수 있다 |

### (e) mcp_client — IF-4 Manager 측

@docs/harness/mcp.md 를 함께 읽는다. 추가로:

| # | 검증 |
|---|---|
| L-1 | **Worker 선택을 클라이언트가 하지 않는가.** MAMS의 책임이다. 클라이언트는 정해진 상대에게 보내고 받는 것만 한다 |
| L-2 | Task 폴링에 **상한**이 있는가. `deadline-sec` 초과 시 `timeout`으로 전이하고 cancel을 보내는가 |

## 4. 결정 기록

Manager는 전부 신규 구현이므로 **거의 모든 작업이 기록 대상**이다. 특히:

- L1/L2 스키마 필드 확정 → **R3** (contracts + spec 동시 갱신)
- LLM 선택 (U-3: Claude API vs Ollama vs 로컬) → **R3**
- L2 직렬화 형식 확정 (U-2: XML vs JSON) → **R3**
- KG 저장 형식·`resolve()` 시그니처 → **R1**
- Worker 선택 점수 함수 가중치 (U-4) → **R2**
- 재시도 상한·에스컬레이션 정책 → **R4**

## 5. 아키텍처 리스크

| 변경 | 등급 |
|---|---|
| 컴포넌트 내부 로직 | R0 |
| IF-1/IF-2/IF-3 계약 정의·변경 | R1 |
| L1/L2 스키마 | **R3** — 모든 하위 계층이 여기에 걸린다 |
| 폐루프 상태기계 전이 규칙 | **R4** — 에스컬레이션이 안 되면 사람이 방치된다 |
| `abnormal`/`not_found` 판정 기준 | **R4** |
| dispatch-mode 추가 | R2 |

> **Manager를 만들 때 가장 흔한 실수는 "일단 동작하게" 만들면서 L2에 디바이스 이름을 넣는 것이다.**
> 그러면 Phase 2의 다중 Worker fan-out이 통째로 불가능해진다. 이건 나중에 못 고친다.
