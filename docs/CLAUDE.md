# docs — 문서 저장소

## 무엇이 어디에

| 경로 | 내용 | 신뢰도 |
|---|---|---|
| `spec/AI-Care_Unified_Architecture_Spec_v0.2.md` | **SOT.** 정규화 용어, IF-1~IF-8, L0~L4 정책 계층, A2A-over-MCP 바인딩, 로드맵, 표준화 항목 | **정본** |
| `context/` | 배경 컨텍스트 — A2A 개념 매핑, RCP/MCP 결정 기록, ViLaR-IMO 연계, 연구 자료 계보 | 참고 |
| `handoff/` | 세션 인수인계 — 왜 그렇게 했는지, 다시 겪지 않아도 될 함정 | 참고 |
| `audit/` | IETF-125/126 승계 판정 | **참고 전용, 결정 아님** |
| `slides/` | UKC2026 발표 덱 (42MB, git 제외) | 원본 |

## 읽는 순서

처음 합류하면:

1. 루트 `CLAUDE.md` — 전체 그림과 현재 Phase
2. `spec/` §1~§5 — 설계 원칙, 컴포넌트, 인터페이스, 정책 계층, Report
3. `spec/` §10 — 기존 자산, 시뮬 환경, 크리티컬 갭, Phase 계획
4. `handoff/` — 실제로 겪은 함정 (재발 방지)
5. 담당할 컴포넌트 디렉터리의 `CLAUDE.md`

## 주의

- **`spec/`이 정본이다.** 다른 문서와 어긋나면 spec을 따르고, spec이 틀렸으면 spec을 고친다.
- **`audit/IETF승계issue.md`는 참고 자료다.** 판정이 스펙에 반영되지 않았다. 채택하기로 하면 그때 옮긴다.
- **슬라이드와 UKC 논문에는 용어 불일치가 있다.** spec §2.4와 부록 B의 대조표를 먼저 볼 것.
- `slides/*.pptx`는 `.gitignore` 대상이다 (42MB). 로컬에만 둔다.
