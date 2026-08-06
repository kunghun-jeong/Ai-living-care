# 정본 소유권

> **어떤 사실을 어느 문서가 소유하는가.** 참고용 표다 — 관문이 아니다.
> 전파 체크리스트와 기계 검사 목록은 폐기했다. 대신 **앵커 갱신**(@docs/harness.md §3) 하나만 지킨다.

## 표

**규칙: 사실 하나에 정본은 하나다.** 복제본은 정본을 인용하고, 정본이 바뀌면 전부 따라 바꾼다.
복제가 불가피한 경우만 "복제 허용"에 적었다 — 그 외 위치에 같은 사실을 쓰면 위반이다.

| 사실 유형 | **정본** | 복제 허용 위치 | 비고 |
|---|---|---|---|
| 컴포넌트 정식 명칭·약칭 | spec §2.1 / §2.2 | `SOT.md` §2.1, 각 컴포넌트 `CLAUDE.md` 제목 | 별칭(`Manager Controller` 등)은 spec §2.1 각주에만 |
| 디렉터리 배치·명명 규칙 | **`SOT.md`** §1·§2 | `docs/architecture.md`, `sot_audit.py`, `MIGRATION.md` | 트리와 `sot_audit.py` 검사 대상이 **집합 일치**해야 함 |
| 인터페이스 IF-1~IF-8 | spec §3 | `SOT.md` §3, `interfaces/*/CLAUDE.md`, `architecture.md` | 종단점·전달 내용·Phase |
| **MCP tool 시그니처** | **코드** (`MCP_server.py`의 `@mcp.tool()`) | `docs/api-spec.md`, `mcp_server/CLAUDE.md` | **코드가 정본이다.** 문서가 코드를 따라간다 |
| L1·L2·L3·Report 스키마 | **`contracts/`** | spec §4·§5, 관련 `CLAUDE.md` | 미작성 상태 — 작성 즉시 정본이 `contracts/`로 이동 |
| 갭 `G-*` | spec §10.3 | `docs/status.md`, 해당 컴포넌트 `CLAUDE.md` | 루트 `CLAUDE.md`에는 두지 않는다 (status.md 링크로) |
| 포렌식 결함 `F-*` | **`docs/status.md`** | 없음 | 감사 보고서를 따로 만들지 않는다 |
| 설계 결정 `D-1~D-8` | spec §0.2 | `docs/decisions.md` (색인만) | |
| 구조 결정 `D-9~D-14` | `SOT.md` §6 | spec §0.2, `docs/decisions.md` (색인만) | **양쪽 동시 갱신** |
| 미결정 `U-*` | spec §12 | `docs/status.md` | ID 중복 정의 금지 |
| 표준화 항목 `S-*` | spec §11.1 | `interfaces/*/CLAUDE.md` | S-4=A2A-over-MCP 바인딩, S-7=세션 키. **혼동 이력 있음** (F-15, 해소) |
| Phase 0 작업 번호 `0-*` | spec §10.4 | `docs/status.md`, 컴포넌트 `CLAUDE.md` | |
| 설계 원칙 `P-1~P-6` | spec §1.2 | 루트 `CLAUDE.md`, `docs/conventions.md` | `SOT.md` §4는 `SP-*`로 분리 완료 (F-14 해소) |
| 배치 규칙 `SP-1~SP-6` | `SOT.md` §4 | `docs/harness/docs-and-structure.md` | |
| 감사 규칙 `AR-1~AR-10` | `SOT.md` §5 | **`sot_audit.py`** | **표와 구현이 집합 일치해야 함** |
| 문서 정합성 장치 `DA-*` | **`anchor.py`** | `docs/doc-map.md` §3, `harness/docs-and-structure.md` | 코드가 정본 |
| 하네스 체크 `HM/HW/HG/HS/HD-*` | 각 하네스 파일 | 없음 (복제 금지) | 접두 `H`로 전역 네임스페이스와 분리 |
| 코딩 규약 | `docs/conventions.md` | 컴포넌트 `CLAUDE.md`의 ⚠️ 항목 | 코드에서 관찰된 것만 |
| 수치 (커버리지·지연·rate) | **실행 출력** | spec §10.1, `tools/*/CLAUDE.md`, `docs/status.md` | **출처·한정어 없이 인용 금지** |
| 실행 명령 | 해당 디렉터리 `CLAUDE.md` | 루트 `CLAUDE.md`, `README.md` | `cd` 기준을 명시 |
| 시뮬 환경 구성·함정 | `Simulation/sim_bringup.launch.py` docstring + spec §10.2 | `docs/harness/simulation.md`, `limo-MCP/CLAUDE.md` | |
| 원본 보존 대상 | `SOT.md` D-14 | `MIGRATION.md`, `sot_audit.py` `PRESERVED` | |

---
