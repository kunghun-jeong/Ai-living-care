# doc-map — 문서 라우팅 정본

> **작업 시작점.** 하려는 일을 아래 표에서 찾아 **거기 적힌 것만** 연다.
> 표에 없으면 `docs/harness.md` 의 공통 절차만 따른다 (fail-closed — 모르면 더 안 연다).

## 1. 하려는 일 → 열 문서

| 하려는 일 | 열 문서 | 안 여는 것 |
|---|---|---|
| **무엇이 바뀌었는지 알고 싶다** (세션 시작) | `make status` — 상태 줄 + 최근 커밋·결정을 한 화면에. `make` 없으면 `python anchor.py --status` | 문서를 뒤지지 않는다 — 이건 명령이다 |
| **MCP tool 추가·수정** | `docs/harness/mcp.md` · `docs/api-spec.md` · `worker_ai_agent/mcp_server/CLAUDE.md` | spec 전체 (필요한 절은 §6) |
| **Manager 컴포넌트 신규 구현** | 그 컴포넌트 `CLAUDE.md` → 헤더가 지목한 spec 절 · `docs/harness/manager-ai.md` | spec 전체 · `SOT.md` |
| **Perception · Reasoning · Action 코드** | ⛔ **담당 연구원 영역 (D-17).** 결함을 찾았으면 기록만 — 위 「결함을 발견했다」 행. 훅이 커밋 때 경계를 알린다(막지는 않는다) | 전부 |
| **순찰 · 시뮬 · 맵 · 좌표** | `docs/harness/simulation.md` · `tools/limo-patrol-viz/CLAUDE.md` | spec |
| **문서 · 디렉터리 구조 변경** | `docs/harness/docs-and-structure.md` · `SOT.md` §1·§2·§4 | spec |
| **결함을 발견했다** | 안전 경로(정지·취소 / 사람 판정 / 프레임 신선도 / 세션 키)면 `docs/safety/` 에 **파일 하나** + 귀속 컴포넌트 `상태` 줄, 그 외는 `docs/status-defects.md` | 다른 사람 코드 — 고치지 않는다 (D-17) |
| **표준 기고문 · I-D 작성** | `docs/standards/CLAUDE.md` · spec **§11.1**(`S-*` 정본) · `docs/status.md`(수치와 한정어) | spec 나머지 · 코드 |
| **매거진 논문 작성** | **아래 §2 팀장 문서** · spec **§11**(표준화 항목) · `docs/status.md`(수치와 한정어) | 컴포넌트 `CLAUDE.md` · 코드 |
| **IITP 제안서 작성** | spec **§11.1**(`S-*` 정본) · `docs/status.md`(수치와 한정어) — **spec 은 제안서의 기준 문서가 아니다**(spec 서두). 인용은 §11.1 까지 | spec 나머지 · 컴포넌트 `CLAUDE.md` · 코드 |
| **인터페이스 계약 정의** | `interfaces/if0N_*/CLAUDE.md` · spec **§3** | spec 전체 |
| **스키마(L1~L3·Report)** | `contracts/*/CLAUDE.md` · **그 헤더가 지목한 절만** (`§4.1`~`§4.4` · `§5.1`~`§5.2`, 각 27~80줄) | `§4` 통째(196줄) — 헤더가 더 좁게 지목한다 |
| **스키마 검증기** | `contracts/*/CLAUDE.md` 규칙 3 — **검증기 프레임워크는 미결정**(`U-*` 후보). 정하기 전에는 스키마만 두지 않는다 | spec 나머지 |
| **브랜치를 파거나 PR 을 연다** | `CONTRIBUTING.md` | 나머지 전부 |
| 위에 없음 | `docs/harness.md` 공통 절차 | 나머지 전부 |

> **수치를 인용할 때는 반드시 한정어를 함께 가져온다.** 「사각지대 0」이 아니라
> 「**2 m² 이상** 사각지대 0」이고, 93.6%는 **기하 시뮬레이션 결과**이지 실측이 아니다 (F-17).

## 2. 팀장 문서 — 각 영역 현황

**한 화면에서 전 영역 현황을 보려면:**

```bash
make status          # make 가 없으면: python anchor.py --status
```

각 `CLAUDE.md` 헤더의 `> **상태**` 줄 + **최근 커밋·결정**을 **읽는 시점에** 모아 보여준다.
**파일에 쓰지 않는다** — 생성물을 커밋하면 매 PR 이 그 블록을 건드려 충돌하기 때문이다
(실측: 평면 수확 3/4 충돌 · 계층 수확 1/4 · 미수확 0/4). 파일이 아니라 낡을 수가 없다.

상태를 바꾸려면 **그 디렉터리 `CLAUDE.md` 의 `> **상태**` 줄만** 고친다. 표는 따라온다.

| 영역 | 진입 문서 |
|---|---|
| Manager AI Agent | `manager_ai_agent/CLAUDE.md` |
| Worker AI Agent | `worker_ai_agent/CLAUDE.md` |
| 인터페이스 | `interfaces/CLAUDE.md` |
| 스키마 | `contracts/CLAUDE.md` |
| 검증 도구 | `tools/CLAUDE.md` |
| 문서 | `docs/CLAUDE.md` |

## 3. 정본 소유권 → [`docs/canon.md`](canon.md)

**사실 하나에 정본은 하나다.** 어느 사실의 정본이 어디이고 복제가 어디까지 허용되는지는
[`docs/canon.md`](canon.md) 가 갖는다. **새 사실을 어디에 쓸지 정할 때** 연다 —
22행 참조표라 매 세션 열 이유가 없다. (예전에 이 자리에 있던 표가 그대로 옮겨갔다.)
