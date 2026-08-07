# doc-map — 문서 라우팅 정본

> **작업 시작점.** 하려는 일을 아래 표에서 찾아 **거기 적힌 것만** 연다.
> 표에 없으면 @docs/harness.md 의 공통 절차만 따른다 (fail-closed — 모르면 더 안 연다).

## 1. 하려는 일 → 열 문서

| 하려는 일 | 열 문서 | 안 여는 것 |
|---|---|---|
| **MCP tool 추가·수정** | `docs/harness/mcp.md` · `docs/api-spec.md` · `worker_ai_agent/mcp_server/CLAUDE.md` | spec 전체 (필요한 절은 §6) |
| **Manager 컴포넌트 신규 구현** | 그 컴포넌트 `CLAUDE.md` → 헤더가 지목한 spec 절 · `docs/harness/manager-ai.md` | spec 전체 · `SOT.md` |
| **Perception · Reasoning · Action 코드** | ⛔ **담당 연구원 영역 (D-17).** 결함을 찾았으면 `docs/status.md` 에 기록만 | 전부 |
| **순찰 · 시뮬 · 맵 · 좌표** | `docs/harness/simulation.md` · `tools/limo-patrol-viz/CLAUDE.md` | spec |
| **문서 · 디렉터리 구조 변경** | `docs/harness/docs-and-structure.md` · `SOT.md` §1·§2·§4 | spec |
| **논문 · IITP 제안서 작성** | **아래 §2 팀장 문서** · spec **§11**(표준화 항목 36줄) · `docs/status.md`(수치와 한정어) | 컴포넌트 `CLAUDE.md` · 코드 |
| **인터페이스 계약 정의** | `interfaces/if0N_*/CLAUDE.md` · spec **§3**(51줄) | spec 전체 |
| **스키마(L1~L3·Report)** | `contracts/*/CLAUDE.md` · spec **§4**(L1·L2) 또는 **§5**(Report) | 나머지 절 |
| **브랜치를 파거나 PR 을 연다** | `CONTRIBUTING.md` | 나머지 전부 |
| 위에 없음 | @docs/harness.md 공통 절차 | 나머지 전부 |

> **수치를 인용할 때는 반드시 한정어를 함께 가져온다.** 「사각지대 0」이 아니라
> 「**2 m² 이상** 사각지대 0」이고, 93.6%는 **기하 시뮬레이션 결과**이지 실측이 아니다 (F-17).

## 2. 팀장 문서 — 각 영역 현황

**한 화면에서 전 영역 현황을 보려면:**

```bash
make status          # = python3 anchor.py --status
```

48개 `CLAUDE.md` 헤더의 `> **상태**` 줄을 **읽는 시점에** 모아 보여준다.
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

## 3. 정본 소유권

**사실 하나에 정본은 하나다.** 복제본은 정본을 인용하고, 정본이 바뀌면 전부 따라 바꾼다.
복제가 불가피한 경우만 「복제 허용」에 적었다 — 그 외 위치에 같은 사실을 쓰면 위반이다.

| 사실 유형 | **정본** | 복제 허용 위치 | 비고 |
|---|---|---|---|
| 컴포넌트 정식 명칭·약칭 | spec §2.1 / §2.2 | `SOT.md` §2.1, 각 컴포넌트 `CLAUDE.md` 제목 | 별칭은 spec §2.1 각주에만 |
| 디렉터리 배치·명명 규칙 | **`SOT.md`** §1·§2 | `docs/architecture.md`, `sot_audit.py`, `MIGRATION.md` | 트리와 검사 대상이 **집합 일치**해야 함 |
| 인터페이스 IF-1~IF-8 | spec §3 | `SOT.md` §3, `interfaces/*/CLAUDE.md`, `architecture.md` | 종단점·전달 내용·Phase |
| **MCP tool 시그니처** | **코드** (`MCP_server.py`의 `@mcp.tool()`) | `docs/api-spec.md`, `mcp_server/CLAUDE.md` | **코드가 정본이다.** `anchor.py` 가 이름 집합을 강제 |
| L1·L2·L3·Report 스키마 | **`contracts/`** | spec §4·§5, 관련 `CLAUDE.md` | 미작성 — 작성 즉시 정본이 `contracts/`로 |
| 갭 `G-*` | spec §10.3 | `docs/status.md`, 해당 컴포넌트 `CLAUDE.md` | 루트에는 두지 않는다 |
| 포렌식 결함 `F-*` | **`docs/status.md`** | 없음 | 감사 보고서를 따로 만들지 않는다 |
| 설계 결정 `D-1~D-8` | spec §0.2 | `docs/decisions.md` (색인만) | |
| 구조 결정 `D-9~D-17` | `SOT.md` §6 | spec §0.2, `docs/decisions.md` (색인만) | **양쪽 동시 갱신** |
| 미결정 `U-*` | spec §12 | `docs/status.md` | ID 중복 정의 금지 |
| 표준화 항목 `S-*` | spec §11.1 | `interfaces/*/CLAUDE.md` | S-4=A2A-over-MCP 바인딩, S-7=세션 키 |
| Phase 0 작업 번호 `0-*` | spec §10.4 | `docs/status.md`, 컴포넌트 `CLAUDE.md` | |
| 설계 원칙 `P-1~P-6` | spec §1.2 | 루트 `CLAUDE.md`, `docs/conventions.md` | `SOT.md` §4는 `SP-*` |
| 배치 규칙 `SP-*` · 감사 규칙 `AR-*` | `SOT.md` §4 · §5 | `sot_audit.py` | 표와 구현이 집합 일치 |
| 하네스 체크 `HM/HW/HG/HS/HD-*` | 각 하네스 파일 | 없음 (복제 금지) | 접두 `H`로 전역과 분리 |
| 코딩 규약 | `docs/conventions.md` | 컴포넌트 `CLAUDE.md`의 ⚠️ | 코드에서 관찰된 것만 |
| 수치 (커버리지·지연·rate) | **실행 출력** | spec §10.1, `tools/*/CLAUDE.md`, `docs/status.md` | **출처·한정어 없이 인용 금지** |
| 실행 명령 | 해당 디렉터리 `CLAUDE.md` | 루트 `CLAUDE.md`, `README.md` | `cd` 기준을 명시 |
| 시뮬 환경 구성·함정 | `Simulation/sim_bringup.launch.py` docstring + spec §10.2 | `docs/harness/simulation.md`, `limo-MCP/CLAUDE.md` | |
| 원본 보존·소유 경계 | `SOT.md` D-14 · D-17 | `MIGRATION.md`, `sot_audit.py` `PRESERVED`, 루트 `CLAUDE.md` | |
