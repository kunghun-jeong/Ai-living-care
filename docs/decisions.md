# 의사결정 기록 (Decision Log)

새 결정은 항상 맨 위에 추가한다.

<!-- 템플릿
## YYYY-MM-DD: 결정 제목
- 변경: 무엇을 바꿨나
- 이유: 왜 바꿨나
- 참고: 관련 파일 / PR
-->

## 2026-08-06: 생태계 재감사 — D-14의 범위를 확정하고 감사기에 자기 감사를 넣음

- 변경: **D-17** 신설 — D-14의 보존 범위는 「구조·파일명·경로」이며 내용 동결이 아니다.
  `doc_audit.py` DA-6을 그에 맞춰 재작성(삭제·개명·무단 추가는 FAIL, 내용 변경은 결정 기록 조건부 허용,
  변경 목록은 `[NOTE]`로 항상 출력). **DA-11** 신설 — 감사기 자기 감사.
  DA-4의 죽어 있던 카운터 2종(`status`·`인터페이스`) 복구. DA-6의 SKIP을 FAIL로.
- 이유: `doc_audit.py`가 D-14를 **내용 동결**로 집행하고 있었고, 규범 문서 셋은 전부 **구조·파일명**이라
  적고 있었다. 그 결과 **Phase 0 작업 0-5·0-7~0-12(7건)가 커밋 불가**였고, 이 7건은 안전 결함
  F-1~F-3과 실행 차단 F-4~F-8의 수정 대상과 겹친다. **보존이 안전 수정을 막으면 보존이 아니다.**
  또한 「N/N 통과」의 분모가 저장소 상태의 함수라 `audit()`을 비우면 **0/0 PASS · exit 0**이었다.
- 검증: `Perceptions.py` 수정 → 기록 없으면 FAIL, 기록 후 PASS, 파일 개명은 여전히 FAIL — 3단 실증.
  DA-11 도입 즉시 6개 문서의 「DA-1~DA-N」 드리프트를 잡았고, 이 결정 기록을 쓰다가 한 번 더 걸렸다.
- 리스크: **R3** — D-14의 해석을 바꾸므로 spec §0.2와 `SOT.md` §6 양쪽에 반영했다.
- 남은 것: 재감사가 확정한 미해소 30건(F-34~F-63)은 `docs/status.md`에 등재. 우선순위는
  F-41(테스트 자리) → F-40(R4 완료 조건) → F-46~F-51(안전 경로 6건) 순.
- 참고: `docs/audit/forensic-2026-08-06-2.md`

## 2026-08-06: 문서 정합성을 사람 절차에서 기계 관문으로 옮김 (`doc_audit.py` 신설)

- 변경: `doc_audit.py` 신설 — 장치 10종(DA-1~DA-11), 398개 검사. 하네스 2단계 사전 점검과
  V-5에 배선했다. `doc-map.md` §3의 미구현 후보 DM-1~DM-7을 전부 구현으로 대체했다.
  하네스의 죽은 셸 검사 2건(구 D-1·D-2)은 폐기했다.
- 이유: 하네스를 포렌식 감사한 결과, **전파 절차 11단계 중 기계로 강제되는 것이 0건**이었고
  (F-21), 그 결과 **하네스 출하 시점에 이미 `SOT.md` §2 트리에서 `worker_ai_agent/mcp_server/`와
  `limo-MCP/`가 소실**돼 있었다 (F-20). 구조 정본이 파생물보다 낡았는데 `sot_audit.py`는
  전항목 PASS를 냈다. 구 D-1은 ` ```bash ` 펜스만 스캔해 루트 `CLAUDE.md`에서 **0개 경로를 검사**했고,
  구 D-2는 `! A | B || echo` 구조라 **항상 exit 0**이었다 (F-22).
  **통과하는 것처럼 보이는 검사는 없는 검사보다 나쁘다.**
- 검증: 장치 10종 각각에 결함을 주입해 **FAIL로 전환되는 것을 실증**했다 —
  하위 컴포넌트 신설 후 부모 미갱신(DA-2/3/10), tool 개명(DA-1), 개수 리터럴 분기(DA-4),
  미정의 ID 인용(DA-5), 보존 대상 변경·개명(DA-6), 인라인 경로 사망(DA-7),
  폐기 생성기 부활(DA-8), 스펙 참조 규약 이탈(DA-9). 무결함 상태에서 398/398 통과.
- 함께 해소: F-13(`sim/` 규범 모순), F-14(`P-*` 네임스페이스 충돌 → `SP-*`/`AR-*`/`H*-`),
  F-15(세션 키 이중 검증 귀속 S-4→S-7), F-19(D-14를 spec §0.2에 반영),
  F-25(리스크 등급 다중 판정 → "최고 등급 우선" 명문화), F-26(dispatch-mode 5종 중 1종 미정의).
- 리스크: **R2** — `SOT.md` §4·§5 규칙 ID 개명, `sot_audit.py` 규칙 라벨 변경.
  spec §7.3에 `sequential` 완료 조건을 추가한 부분만 **R3**(설계 정본 수정)이며,
  이는 이미 3개 문서가 「5종」이라 쓰고 있던 것을 정본에 반영한 것이다.
- 참고: `doc_audit.py`, `docs/doc-map.md` §3, `docs/harness.md`, `docs/status.md` F-20~F-26

## 2026-08-06: 루트 CLAUDE.md를 Lazy Loading 목차로 전환하고 작업 하네스를 신설

- 변경: 루트 `CLAUDE.md` 107줄 → 40줄 목차로 축약. 상세 내용을 `docs/architecture.md`,
  `docs/conventions.md`, `docs/status.md`, `docs/api-spec.md`로 분리. 기존 「작업 규칙」 섹션을
  `docs/harness.md` + `docs/harness/*.md` 5종으로 승격 — 작업 종류별 컨텍스트·검증·리스크 절차를 규정.
- 이유: 루트 문서가 길어져 매 세션 전량 로딩됐고, 규칙이 서술뿐이라 검증·기록·리스크 관리가 강제되지 않았다.
  포렌식 감사에서 루트 문서의 실행 명령 3줄이 전부 존재하지 않는 경로였음이 확인됐다.
- 참고: `docs/audit/forensic-2026-08-06.md`, `docs/harness.md`

## 2026-08-06: CLAUDE.md 생성기(`sot_migrate.py` / `sot_preserve.py`)를 폐기하고 수기 유지로 전환

- 변경: `sot_migrate.py claudemd` · `sot_preserve.py docs`를 사용 중단으로 표시. `CLAUDE.md`와
  `docs/**`는 이제 사람이 직접 유지한다.
- 이유: 42개 `CLAUDE.md`의 실질 정본이 `.md` 파일이 아니라 두 파이썬 스크립트 안의 문자열 딕셔너리였다.
  손으로 고치면 생성기 재실행 한 번에 지워지고, 두 생성기의 관할이 겹쳐 서로를 되돌렸다.
  루트 `CLAUDE.md`의 구 경로 3건이 정확히 이 구조에서 나왔다. **문서 결함의 단일 최대 원인.**
- 참고: `docs/audit/forensic-2026-08-06.md` §문서 2·3, `docs/harness/docs-and-structure.md`

---

# 기존 결정 색인 (원문 링크)

아래 결정은 **원문이 정본**이다. 여기서는 색인만 유지한다.
새 결정은 이 문서 맨 위에 쓰고, 구조·설계에 영향을 주면 원문에도 반영한다.

## 설계 결정 — `docs/spec/AI-Care_Unified_Architecture_Spec_v0.2.md` §0.2

| ID | 결정 |
|---|---|
| D-1 | 컴포넌트 명칭은 slide 16 도해를 정본으로 (`Edge AI Analyzer` → `Manager AI Analyzer`) |
| D-2 | Knowledge Graph와 Intent Audit Database를 분리된 두 저장소로 정의 |
| D-3 | Intent→실행을 5계층 Policy Continuum(L0~L4)으로 형식화 |
| D-4 | A2A를 MCP 2026-07-28 위에 바인딩하는 프로파일로 실현 |
| D-5 | Worker 확장을 Phase 0(단일) → 2(다중 병렬) → 3(W↔W) 3단계로 분리 |
| D-6 | KG는 JSON/YAML 룩업으로 간소 구현하되 IF-1 계약을 고정 |
| D-7 | `limo-MCP`를 Worker 기준 코드베이스로 확정 |
| D-8 | 시뮬 로봇은 turtlebot3 waffle, 월드는 AWS small_house 유지 |

## 구조 결정 — `SOT.md` §6

| ID | 결정 |
|---|---|
| D-9 | A2A 종단점을 각 에이전트 안에 (`manager_ai_agent/mcp_client/`, `worker_ai_agent/mcp_server/`) |
| D-10 | `interfaces/`를 1급 디렉터리로 두고 IF-1~IF-8에 각각 디렉터리 부여 |
| D-11 | PF/RF/AF 디렉터리에서 `_function` 접미사 제거 |
| D-12 | `service_functions/` 중간 계층을 두지 않음 |
| D-13 | 컴포넌트 디렉터리에 정식 명칭 전체 사용 (`manager_ai_core`, `core` 아님) |
| D-14 | `limo-MCP/`·`limo-patrol-viz/`는 원본 그대로 보존, 통째로 배치 |

> **미반영 상태**: D-9~D-13은 spec §0.2에 반영 완료. **D-14는 spec에 미반영** — 반영 필요.
