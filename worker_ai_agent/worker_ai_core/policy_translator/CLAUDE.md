# Policy Translator

> **역할** L2 device-agnostic 정책을 이 디바이스의 L3 로 번역한다
> **상태** Phase 0 · 미착수
> **읽을 절** spec **§4.4**(80줄) — 그 외 절은 열지 않는다
> **정본** 구조 `SOT.md` · spec §4.4 · 스키마 `contracts/low_level_policy/`

L2 `<living-care-policy>` → L3 `<limo-agent-policy>` 번역. 스키마는 `contracts/`.

| L2 | → L3 | 해소 주체 |
|---|---|---|
| `<place>living_room` | `<waypoint><x/><y/>` | KG 조회 (G-6) |
| `<required-skill>person-scan` | `<perception>` 블록 | 디바이스 능력 |
| `<action-type>inspect-and-report` | 실행 시퀀스 | 시나리오 선택 |
| `<assurance><deadline-sec>` | `<report><timeout-sec>` | 그대로 전달 |

## Phase 3 — RL의 위치 (오독 주의)

docx의 강화학습은 **정책 생성이 아니라, 사전 저장된 시나리오 배열 중 정책에 맞는 것을 고르는 선택 문제**다.
즉 **이 컴포넌트 내부의 선택 모듈**이며, L2→L3 번역을 규칙 기반에서 학습 기반으로 대체하는 것이다.
논문에서 이 위치를 흐리면 "정책 생성을 RL로 한다"로 오독된다. (Search-R1, arXiv:2503.09516)
