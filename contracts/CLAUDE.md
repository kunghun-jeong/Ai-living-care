# contracts — 계층 간 페이로드 스키마

> **역할** L1~L3·Report 페이로드 스키마를 보관한다 — 계층 간 계약의 정본
> **상태** Phase 0 · **미작성** · 작업 `0-4`
> **읽을 절** spec **§4.1**(계층 정의) — 그 외 절은 열지 않는다
> **정본** 구조 `SOT.md` · 스키마는 **이 디렉터리** (`SP-4`)

컴포넌트 사이의 **유일한 계약**이다. P-2에 따라 각 계층은 바로 아래 계층만 알고, 그 앎은 전부 여기 있는 스키마로만 이뤄진다.

| 경로 | 계층 | 형식 | 흐르는 인터페이스 |
|---|---|---|---|
| `intent_query/` | **L1** Intent Query | JSON | (MAC 내부) |
| `high_level_policy/` | **L2** High-level Policy (ECA) | XML (내부 JSON 병용 검토 — U-2) | **IF-4** |
| `low_level_policy/` | **L3** Low-level Policy | XML | **IF-5** |
| `worker_report/` | Worker Report | JSON | IF-6 → IF-4 |

## `interfaces/` 와의 차이

`interfaces/`는 **누가 누구에게 어떻게 말하는가**, `contracts/`는 **무엇을 말하는가**이다.

## 규칙

1. **스키마 변경은 설계 결정이다.** 여기부터 고치고 `docs/decisions/`에 파일 하나를 만든 뒤,
   spec과 영향받는 소비자 `CLAUDE.md`를 `정본 반영`에 적어 같은 변경에서 고친다.
2. **L2에 디바이스 이름을 넣지 않는다.** device-agnostic이어야 다중 Worker fan-out이 성립한다.
3. **검증기를 함께 둔다.** 스키마만 있고 검증이 없으면 P-4가 성립하지 않는다.
4. L3 요소명은 SF가 실제로 받는 자료구조와 1:1로 맞춘다.

## 원본 자료의 알려진 오류 (수정해서 쓸 것)

- slide 21의 `<goal>37.5665, 126.9781</goal>`은 **WGS84 위경도(서울시청)** 다. 실내 Nav2 로봇은 `map` 프레임 x/y/yaw를 쓴다.
- slide 21의 `<rate>10Hz`는 **순찰 시나리오에 잘못 붙은 값**이다. 구현은 1 Hz이고 10 Hz는 I2ICF의 주행 중 회피 값이다.
- slide 21의 XML은 닫는 태그가 없는 **표현용 의사코드**다. 논문·제안서에는 정규화안을 쓸 것.

## 미결정

**U-2**: L2 직렬화 — XML(YANG/NETCONF 정합) vs JSON(LLM 생성 정확도·MCP 친화).
현재 권고는 **내부 JSON, 표준 문서·전시 XML, 양방향 변환**.
