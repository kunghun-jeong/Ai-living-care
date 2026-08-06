# Manager AI Agent

> **SOT**: `docs/spec/AI-Care_Unified_Architecture_Spec_v0.2.md`
> **상위**: 저장소 루트 · **Phase**: 0 · **구현 상태**: 부분 (Core만 착수 예정)

사용자의 자연어 의도를 해석해 **고수준 정책(L2)** 을 만들고, 적절한 Worker를 선택해 A2A로 배포하며,
돌아온 Report를 해석해 재시도·전환·에스컬레이션을 결정한다.

## 구성 (P-1 대칭성)

| 하위 | 정규화 명칭 | 책임 |
|---|---|---|
| `core/` | Manager AI Core (MAC) | Intent Translator + Session Key Manager. L0→L1→L2 변환의 주체 |
| `analyzer/` | Manager AI Analyzer (MAA) | Report 해석, 임무 완료 판정, 재시도/Worker 전환 결정 |
| `mgmt_system/` | Manager AI Management System (MAMS) | Worker 등록·상태·수명주기. **Agent Registry 역할 겸함** |
| `knowledge_graph/` | Knowledge Graph (KG) | 사용자·공간·디바이스의 관계와 능력 (누가 무엇을 할 수 있는가) |
| `intent_audit_db/` | Intent Audit Database (IAD) | intent/policy 이력, 스키마 프롬프트, 검증 규칙 |

> **KG와 IAD는 별개다.** 원 자료(slide 16·17·21, 논문 Fig.1)에서 이 자리에 박스가 하나만 그려져 있고
> 자료마다 이름이 다르지만, 접근 패턴과 수명이 달라 두 저장소로 분리했다. spec §2.3 참조.

## 인터페이스

| ID | 상대 | 내용 |
|---|---|---|
| IF-1 | KG / IAD | KG 조회, intent·policy 감사 레코드, KB audit |
| IF-2 | MAA | 해석된 report, 완료/재시도/전환 판정 |
| IF-3 | MAMS | Worker 등록·조회·상태 |
| **IF-4** | **WAC (Secure A2A Channel)** | **L2 고수준 정책, Task 상태, Artifact** |
| IF-7 | WAMS | Worker 능력·자원·가용성 공시 (Phase 2) |
| IF-8 | WAA | 상세 진단·이상 이벤트 (Phase 2) |

## 주의

docx는 Manager를 "우리 스코프 아님"으로 두었으나 **2026-08-06 사용자 결정으로 구현 범위에 포함**됐다.
단 KG는 그래프DB가 아니라 JSON 룩업으로 간소 구현한다 (D-6).
