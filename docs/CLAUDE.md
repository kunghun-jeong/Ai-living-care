# docs — 문서 저장소

> **역할** 설계·구조·상태·절차 문서. 라우팅은 `docs/doc-map.md` 가 한다
> **상태** 상시
> **읽을 절** 없음 — 이 디렉터리만으로 작업한다
> **정본** 구조 `SOT.md` · 문서 라우팅 `docs/doc-map.md`

| 경로 | 내용 | 신뢰도 |
|---|---|---|
| `harness.md` · `harness/` | **작업 하네스** — 작업 전 반드시 읽는다 | 정본 |
| `doc-map.md` | **정본 소유권 + 전파 체크리스트** | 정본 |
| `architecture.md` · `api-spec.md` · `conventions.md` · `status.md`(지금 작업에 영향 주는 것) · `status-defects.md`(F-1~F-63 이력, 자동 로딩 안 됨) · `decisions.md` | 파생 문서 | 정본 |
| `spec/` | **설계 정본.** 정규화 용어, IF-1~IF-8, L0~L4, A2A-over-MCP 바인딩, 로드맵, 표준화 항목 | **정본** |
| `context/` | 배경 — A2A 개념 매핑, RCP/MCP 결정 기록, ViLaR-IMO 연계, 연구 자료 계보 | 참고 |
| `handoff/` | 세션 인수인계 — 왜 그렇게 했는지, 다시 겪지 않아도 될 함정 | 참고 |
| `audit/` | IETF-125/126 승계 판정 | **참고 전용, 결정 아님** |
| `slides/` | UKC2026 발표 덱 (42MB, git 제외) | 원본 |

## 읽는 순서

1. 루트 `CLAUDE.md` — 전체 그림과 현재 Phase
2. `../SOT.md` — 구조·명명 규범
3. `spec/` §1~§5 — 설계 원칙, 컴포넌트, 인터페이스, 정책 계층, Report
4. `spec/` §10 — 기존 자산, 시뮬 환경, 크리티컬 갭, Phase 계획
5. `handoff/` — 실제로 겪은 함정
6. 담당 컴포넌트의 `CLAUDE.md`

## 주의

- **`spec/`이 설계 정본이다.** 어긋나면 spec을 따르고, spec이 틀렸으면 spec을 고친다.
- **`audit/IETF승계issue.md`는 참고 자료다.** 판정이 스펙에 반영되지 않았다.
- **슬라이드와 UKC 논문에는 용어 불일치가 있다.** spec §2.4와 부록 B 대조표를 먼저 볼 것.
