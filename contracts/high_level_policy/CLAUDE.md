# L2 High-level Policy (ECA)

> **역할** MAC 가 만들고 MAMS 가 Worker 를 골라 IF-4 로 보낸다
> **상태** Phase 0 · **미작성** · 작업 `0-4`
> **읽을 절** spec **§4.3** — 그 외 절은 열지 않는다
> **정본** **이 디렉터리** (`SP-4`: 스키마는 `contracts/` 먼저 → spec 반영 → 코드)

## 형태 (spec 기준 — 확정 아님)

`<living-care-policy>` — event · condition · action · required-skill · dispatch-mode · assurance

## 여기에 무엇을 넣나

JSON Schema 또는 XSD 파일 하나와, 그 스키마로 검증되는 **예시 페이로드 최소 2건**
(정상 1 · 경계 1). 파일을 추가하면 **이 문서에 한 줄 넣는다** (`python3 anchor.py` 가 확인).

## 정하기 전에 알아야 할 것

- **필드를 정하는 것은 설계 결정이다.** 정하면 `docs/decisions.md` 에 한 줄, 그리고
  spec §4.3 에도 반영한다 — 한쪽만 하면 두 정본이 갈라진다.
- 스키마가 확정되면 **정본이 spec 에서 이 디렉터리로 옮겨온다** (doc-map §3).
  그때 spec 은 요약 + 링크로 줄인다.
- 지금 코드에 이 스키마를 소비하는 곳은 **없다.** 소비자가 생기면 `V-4`(열거값 소비자 전수)가
  적용되기 시작한다.
