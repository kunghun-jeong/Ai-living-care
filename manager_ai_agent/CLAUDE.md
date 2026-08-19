# Manager AI Agent

> **역할** 의도 해석 → 고수준 정책 생성 → Worker 선택·배포 → Report 해석
> **상태** Phase 0 · 미착수 — MAC(`manager_ai_core/`) 안에 실험·미승인 Neo4j 추론 코드 존재, 그 외 코드 0줄
> **읽을 절** spec **§2.1**(Manager 컴포넌트) — 그 외 절은 열지 않는다
> **정본** 구조 `SOT.md` · spec §2.1

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
| `a2a_client/` | A2A Client — IF-4 Manager 측 종단점 (2026-08-18에 옛 mcp_client 폴더를 개명, 실험·미승인) | — |

> **KG와 IAD는 별개다.** 원 자료(slide 16·17·21, 논문 Fig.1)에서 이 자리에 박스가 하나만 그려져 있고
> 자료마다 이름이 다르지만, 접근 패턴과 수명이 달라 두 저장소로 분리했다 (spec §2.3).

## 인터페이스

IF-1(→KG/IAD) · IF-2(↔MAA) · IF-3(↔MAMS) · **IF-4**(↔WAC) · IF-7(↔WAMS, P2) · IF-8(↔WAA, P2)
정의는 `interfaces/`에 있다.

## 주의

docx는 Manager를 "우리 스코프 아님"으로 두었으나 **2026-08-06 결정으로 구현 범위에 포함**됐다.
KG는 그래프DB가 아니라 JSON 룩업으로 간소 구현한다 (D-6).

- **Neo4j 기반 추론 파이프라인(실험·미승인)**: 옛 `graph_inference/`를 2026-08-18에 폐기하고
  MAC 하위 컴포넌트로 분배했다 — `manager_ai_core/kg_mapping/`(그래프 조회·라우팅),
  `manager_ai_core/policy_generation/`(판단·생성), `manager_ai_core/pipeline.py`(통합).
  기존 JSON KG(D-6)·"DB 없음"과의 관계는 여전히 **TODO(확인 필요)** — `manager_ai_core/kg_mapping/CLAUDE.md` 참조.
  `SOT.md` 등재는 팀 승인 후. 결정 기록: `docs/decisions/2026-08-18-graph-inference-distribution.md`.
