# 의사결정 기록 (Decision Log)

새 결정은 항상 맨 위에 추가한다.

<!-- 템플릿
## YYYY-MM-DD: 결정 제목
- 변경: 무엇을 바꿨나
- 이유: 왜 바꿨나
- 참고: 관련 파일 / PR
-->

## 2026-08-06: 하네스를 앵커 규칙 하나로 축소 (감사 기구 폐기)

- 변경: `anchor.py`(장치 11종)와 forensic 감사 md를 폐기하고 `anchor.py` 하나로 대체. 하네스를 「읽기·작업·앵커 갱신·결정 로그 한 줄」로 축소하고 사전 점검·검증 관문·리스크 등급을 삭제. `sot_audit.py`는 구조 변경 시에만 쓰는 도구로 강등.
- 이유: **매 작업 비용이 너무 컸다.** 인자 하나 추가에 문서 2,000줄을 읽게 했고, 관문 40여 개 중 실행 가능한 것은 둘뿐이었다. 필요한 규칙은 하나였다 — **파일·디렉터리가 생기거나 바뀌면 그 자리 `CLAUDE.md`에 한 줄, 결정 로그에 한 줄.**
- 남긴 것: 각 참고 노트의 함정 표(코드를 며칠 읽어야 아는 것), 안전 4영역의 실패 경로 실행 요구, `docs/status.md`의 결함 추적.

## 2026-08-06: D-14의 보존 범위를 「구조·파일명·경로」로 확정 (D-17)

- 변경: 원본 보존은 구조·파일명·경로만 얼린다. **내용 변경은 결정 로그 한 줄로 허용.**
- 이유: 내용까지 얼리면 **Phase 0 작업 0-5·0-7~0-12(7건)와 안전 결함 F-1~F-3 수정이 전부 막힌다.**
  보존이 안전 수정을 막으면 그것은 보존이 아니다. `SOT.md` §6 · spec §0.2 양쪽에 반영.

## 2026-08-06: 규범 결함 일괄 정정 (F-13~F-20)

- 변경: `SOT.md` §2 트리 결손 복구(`mcp_server/`·`limo-MCP/`), 배치 규칙 `P-*`→`SP-*`,
  감사 규칙 `R*`→`AR-*`, 하네스 로컬 ID `H*-` 분리, 세션 키 이중 검증 귀속 S-4→S-7,
  D-14를 spec §0.2에 반영, spec §7.3에 `sequential` 추가.
- 이유: 같은 접두가 여러 네임스페이스에서 충돌해 "P-4를 지켰나"의 의미가 결정되지 않았고,
  구조 정본이 파생 문서보다 낡아 있었다.

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
