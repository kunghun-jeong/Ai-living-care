# 의사결정 기록 (Decision Log)

새 결정은 항상 맨 위에 추가한다.

<!-- 템플릿
## YYYY-MM-DD: 결정 제목
- 변경: 무엇을 바꿨나
- 이유: 왜 바꿨나
- 참고: 관련 파일 / PR
-->

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
