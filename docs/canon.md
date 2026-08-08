# 정본 소유권 — 어느 사실이 어디에 사는가

> **참조표다. 매 세션 열지 않는다.** `docs/doc-map.md` §1 이 「무엇을 열까」를 정하고,
> 여기는 **「이 사실을 어디에 쓸까」**를 정한다 — 새 사실을 기록하기 직전에 한 번 연다.
> 라우팅은 `docs/doc-map.md`, 절차는 `docs/harness.md`.

## 정본 소유권

**사실 하나에 정본은 하나다.** 복제본은 정본을 인용하고, 정본이 바뀌면 전부 따라 바꾼다.
복제가 불가피한 경우만 「복제 허용」에 적었다 — 그 외 위치에 같은 사실을 쓰면 위반이다.

| 사실 유형 | **정본** | 복제 허용 위치 | 비고 |
|---|---|---|---|
| 컴포넌트 정식 명칭·약칭 | spec §2.1 / §2.2 | `SOT.md` §2.1, 각 컴포넌트 `CLAUDE.md` 제목 | 별칭은 spec §2.1 각주에만 |
| 디렉터리 배치·명명 규칙 | **`SOT.md`** §1·§2 | `docs/architecture.md`, `sot_audit.py`, `MIGRATION.md` | 트리와 검사 대상이 **집합 일치**해야 함 |
| 인터페이스 IF-1~IF-8 | spec §3 | `SOT.md` §3, `interfaces/*/CLAUDE.md`, `architecture.md` | 종단점·전달 내용·Phase |
| **MCP tool 시그니처** | **코드** (`MCP_server.py`의 `@mcp.tool()`) | `docs/api-spec.md`, `mcp_server/CLAUDE.md` | **코드가 정본이다.** `A2` 가 이름은 **막고** 파라미터 목록 불일치는 **알린다** (반환 타입은 비교 안 함) |
| L1·L2·L3·Report 스키마 | **`contracts/`** | spec §4·§5, 관련 `CLAUDE.md` | 미작성 — 작성 즉시 정본이 `contracts/`로 |
| 갭 `G-*` | spec §10.3 | `docs/status.md`, 해당 컴포넌트 `CLAUDE.md` | 루트에는 두지 않는다 |
| 포렌식 결함 `F-*` | **`docs/safety/`**(미해소 안전, 하나가 파일 하나) · **`docs/status-defects.md`**(그 외 전문) | 귀속 컴포넌트 `상태` 줄의 ID (A5 가 양방향 강제) | `status.md` 에는 **절차만** 남는다 — 목록은 `make status` 맨 위 · 채번 충돌은 `A10` |
| **그 밖의 결정** | **`docs/decisions/`** — 결정 하나가 **파일 하나** | 없음 | `decisions.md` 는 2026-08-08 까지의 **동결 이력**. 새 행을 넣지 않는다 |
| 수치 표기 규약 (한정어 4분류) | `docs/harness/docs-and-structure.md` `HD-1` | `docs/papers/CLAUDE.md` | 원고 쓰는 사람이 하네스 노트를 열지 않아 복제를 허용 |
| 설계 결정 `D-1~D-8` | spec §0.2 | `docs/decisions/` (색인만) | |
| 구조 결정 `D-9~D-18` | `SOT.md` §6 | spec §0.2, `docs/decisions/` (색인만) | **양쪽 동시 갱신** |
| 미결정 `U-*` | spec §12 | `docs/status.md` | ID 중복 정의 금지 |
| 표준화 항목 `S-*` | spec §11.1 | `interfaces/*/CLAUDE.md` | S-4=A2A-over-MCP 바인딩, S-7=세션 키 |
| 논문·표준 **원고** | `docs/papers/` · `docs/standards/` | 없음 | **정의는 spec §11.1, 원고는 여기.** 반대 방향으로 고치지 않는다 |
| Phase 0 작업 번호 `0-*` | spec §10.4 | `docs/status.md`, 컴포넌트 `CLAUDE.md` | |
| 설계 원칙 `P-1~P-6` | spec §1.2 | 루트 `CLAUDE.md`, `docs/conventions.md` | `SOT.md` §4는 `SP-*` |
| 배치 규칙 `SP-*` · 감사 규칙 `AR-*` | `SOT.md` §4 · §5 | `sot_audit.py` | 표와 구현이 집합 일치 |
| 하네스 체크 `HM/HW/HG/HS/HD-*` | 각 하네스 파일 | 없음 (복제 금지) | 접두 `H`로 전역과 분리 |
| 코딩 규약 | `docs/conventions.md` | 컴포넌트 `CLAUDE.md`의 ⚠️ | 코드에서 관찰된 것만 |
| 수치 (커버리지·지연·rate) | **실행 출력** | spec §10.1, `tools/*/CLAUDE.md`, `docs/status.md` | **출처·한정어 없이 인용 금지** |
| 실행 명령 | 해당 디렉터리 `CLAUDE.md` | 루트 `CLAUDE.md`, `README.md` | `cd` 기준을 명시 |
| 시뮬 환경 구성·함정 | `Simulation/sim_bringup.launch.py` docstring + spec §10.2 | `docs/harness/simulation.md`, `limo-MCP/CLAUDE.md` | |
| 원본 보존·소유 경계 | `SOT.md` D-14 · D-17 | `MIGRATION.md`, `sot_audit.py` `PRESERVED`, 루트 `CLAUDE.md` | |
