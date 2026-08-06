# doc-map — 정본 소유권과 전파 경로

> **이 문서는 "어떤 사실을 누가 소유하고, 그것이 바뀌면 어디를 함께 고쳐야 하는가"를 정한다.**
> 문서 목록이 아니다. 문서를 찾는 것은 루트 `CLAUDE.md`, 작업 절차는 @docs/harness.md.
>
> 하네스 4단계(기록·리스크)에서 **전파 대상을 여기서 찾는다.**

## 왜 필요한가

포렌식 감사에서 확인된 결함의 상당수가 **같은 사실이 여러 곳에 복제돼 갈라진 것**이었다.

- Report 스키마가 spec §5.1과 `worker_ai_analyzer/CLAUDE.md` 두 곳
- TaskState 정렬표가 spec §6.3 · `if04_secure_a2a_channel/CLAUDE.md` · MAA 세 곳
- 이중 세션 키 검증을 `S-4`라 부른 spec §9의 오기가 **CLAUDE.md 3개로 그대로 전파**
- `D-9~D-13 미반영`이라 적혀 있었으나 이미 반영됐고, 진짜 미반영인 `D-14`는 목록에서 누락

**어느 것이 정본인지 선언한 곳이 없어서** 생긴 문제다. 이 문서가 그 선언이다.

---

## 1. 정본 소유권 (Single Owner)

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
| 포렌식 결함 `F-*` | **`docs/status.md`** | `docs/audit/forensic-*.md` | audit은 기록, status는 추적 |
| 설계 결정 `D-1~D-8` | spec §0.2 | `docs/decisions.md` (색인만) | |
| 구조 결정 `D-9~D-14` | `SOT.md` §6 | spec §0.2, `docs/decisions.md` (색인만) | **양쪽 동시 갱신** |
| 미결정 `U-*` | spec §12 | `docs/status.md` | ID 중복 정의 금지 |
| 표준화 항목 `S-*` | spec §11.1 | `interfaces/*/CLAUDE.md` | S-4=A2A-over-MCP 바인딩, S-7=세션 키. **혼동 이력 있음** (F-15, 해소) |
| Phase 0 작업 번호 `0-*` | spec §10.4 | `docs/status.md`, 컴포넌트 `CLAUDE.md` | |
| 설계 원칙 `P-1~P-6` | spec §1.2 | 루트 `CLAUDE.md`, `docs/conventions.md` | `SOT.md` §4는 `SP-*`로 분리 완료 (F-14 해소) |
| 배치 규칙 `SP-1~SP-6` | `SOT.md` §4 | `docs/harness/docs-and-structure.md` | |
| 감사 규칙 `AR-1~AR-10` | `SOT.md` §5 | **`sot_audit.py`** | **표와 구현이 집합 일치해야 함** |
| 문서 정합성 장치 `DA-*` | **`doc_audit.py`** | `docs/doc-map.md` §3, `harness/docs-and-structure.md` | 코드가 정본 |
| 하네스 체크 `HM/HW/HG/HS/HD-*` | 각 하네스 파일 | 없음 (복제 금지) | 접두 `H`로 전역 네임스페이스와 분리 |
| 코딩 규약 | `docs/conventions.md` | 컴포넌트 `CLAUDE.md`의 ⚠️ 항목 | 코드에서 관찰된 것만 |
| 수치 (커버리지·지연·rate) | **실행 출력** | spec §10.1, `tools/*/CLAUDE.md`, `docs/status.md` | **출처·한정어 없이 인용 금지** |
| 실행 명령 | 해당 디렉터리 `CLAUDE.md` | 루트 `CLAUDE.md`, `README.md` | `cd` 기준을 명시 |
| 시뮬 환경 구성·함정 | `Simulation/sim_bringup.launch.py` docstring + spec §10.2 | `docs/harness/simulation.md`, `limo-MCP/CLAUDE.md` | |
| 원본 보존 대상 | `SOT.md` D-14 | `MIGRATION.md`, `sot_audit.py` `PRESERVED` | |

---

## 2. 변경 유형별 전파 체크리스트 (게이트웨이 라우팅)

**무엇을 바꿨는지 찾아 그 행의 대상을 전부 갱신한다.** 하나라도 빠뜨리면 그 사실이 갈라진다.

### 구조

| 바꾼 것 | 반드시 함께 갱신 | 등급 |
|---|---|---|
| **하위 컴포넌트 추가·삭제** | ① 부모 `CLAUDE.md`의 구성 표 ② `SOT.md` §2 트리 ③ `SOT.md` §2.1 대응표 ④ `sot_audit.py`의 `COMPONENTS`/`CHILDREN` ⑤ **`docs/architecture.md` 다이어그램 + 컴포넌트 표** ⑥ 새 디렉터리에 `CLAUDE.md` 생성 ⑦ `docs/decisions.md` | **R2** |
| 디렉터리 이동·개명 | 위 전부 + `MIGRATION.md` 대응표 + 경로를 언급하는 모든 `.md`(하네스 D-1 검사) | **R2** |
| 원본 보존 대상 내부 변경 | `SOT.md` D-14 · `sot_audit.py` `PRESERVED`/R10 · `MIGRATION.md` | **R2** |

### 인터페이스·계약

| 바꾼 것 | 반드시 함께 갱신 | 등급 |
|---|---|---|
| **MCP tool 추가·개명·시그니처** | ① **`docs/api-spec.md`** ② `worker_ai_agent/mcp_server/CLAUDE.md` ③ `limo-MCP/Scenarios/*.json`의 tool 이름·인자 ④ **`docs/architecture.md`의 데이터 흐름** ⑤ 호출하는 클라이언트 전부 ⑥ `docs/decisions.md` | **R1** |
| IF-* 계약 정의·변경 | ① spec §3 표 ② `SOT.md` §3 ③ `interfaces/if*/CLAUDE.md` ④ 양 종단 컴포넌트 `CLAUDE.md` ⑤ `docs/architecture.md` | **R1~R3** |
| L1~L3·Report 스키마 | ① `contracts/<계층>/` ② spec §4 또는 §5 ③ 생산자·소비자 컴포넌트 `CLAUDE.md` ④ 검증기 | **R3** |
| **상태 열거값 추가·변경** | ① 정의처 ② **그 값을 읽는 모든 소비자**(V-4) ③ `docs/api-spec.md` ④ 판정 로직(MAA) | **R1** |
| 주입 시그니처(`DetectFn` 등) | ① `docs/conventions.md` §2 ② 주입하는 쪽·받는 쪽 ③ 해당 컴포넌트 `CLAUDE.md` | **R1** |

### 상태·품질

| 바꾼 것 | 반드시 함께 갱신 | 등급 |
|---|---|---|
| 갭 `G-*` 해소 | ① `docs/status.md` 해당 행 ② spec §10.3 ③ 해당 컴포넌트 `CLAUDE.md`의 ⚠️ ④ `docs/decisions.md` | R1 |
| 새 결함 발견 | ① `docs/status.md`에 `F-*` 부여 ② 해당 컴포넌트 `CLAUDE.md` ⚠️ ③ 재현 조건 명시 | R0~R4 |
| 의존성 추가·고정 | ① `requirements.txt` ② `docs/harness/<해당>.md` 사전 점검 ③ `docs/status.md` TODO ④ `docs/decisions.md` | **R1** |
| 수치 갱신(커버리지 등) | ① 산출 코드 ② 인용하는 모든 문서 **한정어 포함** ③ 실행 명령·조건 명시 | R1 |
| 새 코딩 패턴 확립 | ① `docs/conventions.md` ② 적용 대상 컴포넌트 `CLAUDE.md` | R0 |

### 규범·문서

| 바꾼 것 | 반드시 함께 갱신 | 등급 |
|---|---|---|
| `SOT.md` 규칙(N/SP/R) 추가·변경 | ① `SOT.md` 해당 절 ② **`sot_audit.py` 구현** ③ `docs/harness/docs-and-structure.md` | **R2** |
| 결정 `D-*` 추가 | ① 정본(spec §0.2 또는 `SOT.md` §6) ② `docs/decisions.md` 색인 ③ **구조 결정이면 양쪽 모두** | R1~R3 |
| 실행 명령 변경 | ① 해당 디렉터리 `CLAUDE.md` ② 루트 `CLAUDE.md` ③ `README.md` ④ 하네스 사전 점검 | R1 |
| 설계 정본(spec) 수정 | ① spec ② 그 절을 인용하는 모든 `CLAUDE.md` ③ `docs/` 파생 문서 ④ **팀 합의** | **R3** |

---

## 3. 기계 검사 — `doc_audit.py`

**전파 누락은 사람이 못 잡는다.** 이 절은 원래 "넣을 후보" 목록이었다.
후보로 남겨 둔 동안 `SOT.md` §2 트리에서 두 디렉터리가 사라졌고 아무도 몰랐다 (F-20).
**지금은 전부 `doc_audit.py`에 구현돼 있고, 하네스 2단계·V-5에서 실행된다.**

```bash
python3 sot_audit.py      # 구조      — AR-1~AR-10
python3 doc_audit.py      # 문서 정합성 — DA-1~DA-10
python3 doc_audit.py DA-3 # 장치 하나만
```

| 원래 후보 | 구현 | 무엇을 강제하나 |
|---|---|---|
| DM-1 | **DA-1** | `@mcp.tool()` 집합 = `docs/api-spec.md` · `mcp_server/CLAUDE.md` (§1 「코드가 정본」) |
| DM-2 | **DA-3** | `SOT.md` §2 트리 = `sot_audit.py` 검사 대상 = 실제 디렉터리 **3자 집합 일치** |
| DM-3 | **DA-3** | §2.1 대응표의 경로가 전부 실재 |
| DM-4 | **DA-5** | `F/G/U/S/D/N/SP/AR/P/V/IF-*` 참조가 전부 정의처에 존재 |
| DM-5 | **DA-10** | `architecture.md`의 다이어그램·표 = 실제 컴포넌트 집합 |
| DM-6 | **DA-7** | 문서가 적은 경로 실재. **인라인 코드와 `cd` 상대경로까지 해석한다** |
| DM-7 | **DA-7** | 금지 경로는 실재하지 않으므로 같은 장치가 잡는다 |
| — | **DA-2** | **부모 `CLAUDE.md` ⊇ 실제 자식 디렉터리** ← 하위 작업 시 상위 노후화 방지 |
| — | **DA-4** | 「tool 6종」류 개수 리터럴 = 정본 개수 |
| — | **DA-6** | 보존 대상(D-14) blob = `27b0f30`. **작업 트리를 본다** — 커밋 전에 걸린다 |
| — | **DA-8** | 폐기 생성기가 `ROOT_PY_ALLOW`로 되살아나지 않음 |
| — | **DA-9** | `CLAUDE.md` 헤더 규약 · `@`참조 실재 · 루트 50줄 |

### 기계가 못 잡는 것 (사람이 해야 한다)

- **수치의 한정어** — "93.6%"가 기하 시뮬 결과인지 실측인지 (HD-1)
- **상태 열거값의 소비자 전수** — 값을 읽는 코드가 아직 없어 대조 대상이 없다 (V-4)
- **구조 결정의 양쪽 기록** — spec §0.2 ↔ `SOT.md` §6 (D-14에서 실제로 누락됐다)
- **`Scenarios/*.json`의 tool 이름** — DSL 실행기가 없어 정본이 정해지지 않았다 (HM-6)

> **장치를 하나 추가할 때마다 이 표에 행을 넣는다.** 표에 없는 검사는 아무도 실행하지 않는다.

---

## 4. 복제를 줄이는 것이 먼저다

전파 규칙은 **복제가 이미 있다는 전제**의 차선책이다. 근본 해법은 복제를 없애는 것이다.

현재 알려진 중복 (포렌식 확인):

| 중복된 사실 | 위치 | 조치 |
|---|---|---|
| Report 스키마 | spec §5.1, `worker_ai_analyzer/CLAUDE.md` | `contracts/worker_report/` 작성 시 그쪽으로 단일화 |
| `status` 열거값 | spec §5.2, `report_interpreter/CLAUDE.md`, `docs/api-spec.md` | 〃 |
| A2A↔MCP 객체 매핑 | spec §6.2, `if04/CLAUDE.md` | `if04/`를 정본으로, spec은 요약+링크 |
| TaskState 정렬 | spec §6.3, `if04/CLAUDE.md`, MAA `CLAUDE.md` | 〃 |
| dispatch-mode 5종 | spec §7.3, `worker_selector/CLAUDE.md` | spec 유지, CLAUDE.md는 링크. 개수는 DA-4가 감시 |
| IF-1~IF-8 표 | spec §3, `SOT.md` §3, `interfaces/CLAUDE.md`, `architecture.md` | **4중 복제.** spec을 정본으로 나머지는 요약 |
| G-1~G-6 | spec §10.3, `docs/status.md`, 루트 `CLAUDE.md`, 각 컴포넌트 | status.md를 추적처로, 루트는 링크만 |

> **새 문서를 쓸 때 이 표를 먼저 본다.** 여기 있는 사실을 또 적으면 중복이 하나 늘어난다.
> 적어야 한다면 이 표에 행을 추가하고 정본을 선언한다.
