# interfaces — 인터페이스 카탈로그 (IF-1 ~ IF-8)

> **구조 정본**: `SOT.md` §3 · **설계 정본**: `docs/spec/AI-Care_Unified_Architecture_Spec_v0.2.md` §3

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
