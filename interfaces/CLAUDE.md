# interfaces — 인터페이스 카탈로그 (IF-1 ~ IF-8)

> **역할** IF-1 ~ IF-8 인터페이스 카탈로그 — 표준화 산출물 `S-6` 의 실체
> **상태** Phase 0~2 · 계약 정의 단계
> **읽을 절** spec **§3**(카탈로그) — 그 외 절은 열지 않는다
> **정본** 구조 `SOT.md` · spec §3

스펙 §3은 *"각 인터페이스가 곧 표준화 문서의 한 절이 된다"* 고 적는다.
**IF-1~IF-8은 표준화 산출물(S-6)이므로 1급 디렉터리를 갖는다** (D-10).

| 디렉터리 | 인터페이스 | 종단점 | Phase |
|---|---|---|---|
| `if01_database/` | Database Interface | MAC ↔ KG/IAD, MAA ↔ IAD | 0 |
| `if02_analytics/` | Analytics Interface | MAC ↔ MAA, WAC ↔ WAA | 0 |
| `if03_registration/` | Registration Interface | MAC ↔ MAMS, WAC ↔ WAMS | 0 |
| `if04_secure_a2a_channel/` | **Secure A2A Channel** | MAC ↔ WAC | 0 |
| `if05_sf_facing/` | SF-Facing Interface | WAC → PF/RF/AF | 0 |
| `if06_agent_monitoring/` | Agent Monitoring Interface | PF/RF/AF → WAA | 0 |
| `if07_ams_facing/` | AMS-Facing Interface | MAMS ↔ WAMS | 2 |
| `if08_analyzer_facing/` | Analyzer-Facing Interface | MAA ↔ WAA | 2 |

## `interfaces/` 와 `contracts/` 의 차이

- **`interfaces/`** = **누가 누구에게 어떻게 말하는가.** 종단점·호출 규약·전송·수명주기.
- **`contracts/`** = **무엇을 말하는가.** 그 위를 흐르는 페이로드 스키마(L1·L2·L3·Report).

예: IF-4는 "MAC이 WAC에 `tools/call execute_policy`로 보내고 `tasks/get`으로 폴링한다"를 정하고,
`contracts/high_level_policy/`는 "그 안에 실리는 `<living-care-policy>`가 어떤 필드를 갖는가"를 정한다.

## 규칙

**컴포넌트 경계를 넘는 직접 호출을 만들지 않는다** (P-2). 필요하면 인터페이스를 새로 정의하고
스펙 §3 표에 추가한 뒤 여기에 디렉터리를 만든다.

인터페이스의 종단점·전달 내용·수명주기 변경은 설계 결정이다. `docs/decisions/`에 파일 하나를 만들고,
`정본 반영`에 spec §3과 실제로 영향받는 `SOT.md` §3·인터페이스/종단점 `CLAUDE.md`·라우팅 문서를
적어 **같은 변경에서** 고친다. 변경 전 종단점·IF-ID를 `rg`로 전후 검색해 옛 지시를 남기지 않는다.
