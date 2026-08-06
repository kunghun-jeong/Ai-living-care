# contracts — 계층 간 스키마

> **SOT**: `docs/spec/AI-Care_Unified_Architecture_Spec_v0.2.md` §4(정책 계층) · §5(Report)
> **Phase**: 0 · **구현 상태**: 미착수 (작업 0-4)

컴포넌트 사이의 **유일한 계약**이다. P-2(정책 계층 분리)에 따라 각 계층은 바로 아래 계층만 알고,
그 앎은 전부 여기 있는 스키마로만 이뤄진다.

## 구성

| 경로 | 계층 | 형식 |
|---|---|---|
| `intent_query/` | **L1** Intent Query | JSON |
| `high_level_policy/` | **L2** High-level Policy (ECA) | XML (내부는 JSON 병용 검토 — U-2) |
| `low_level_policy/` | **L3** Low-level Policy (디바이스 특화) | XML |
| `worker_report/` | Worker Report | JSON |

## 규칙

1. **스키마를 바꾸면 여기부터 고치고 스펙에 반영한다.** 코드가 스펙을 앞서면 SOT가 깨진다.
2. **L2에 디바이스 이름을 넣지 않는다.** device-agnostic이어야 다중 Worker fan-out이 성립한다.
3. **검증기를 함께 둔다.** 스키마만 있고 검증이 없으면 P-4(실패 안전)가 성립하지 않는다.
4. L3의 요소명은 SF가 실제로 받는 자료구조와 1:1로 맞춘다
   (예: `<waypoint>` ↔ `Actions._goal_xy_yaw()`가 받는 `{"x","y","frame"?,"yaw_deg"?}`).

## 원본 자료의 알려진 오류 (수정해서 쓸 것)

- slide 21의 `<goal>37.5665, 126.9781</goal>`은 **WGS84 위경도(서울시청)** 다.
  실내 Nav2 로봇은 `map` 프레임 x/y/yaw를 쓴다. GPS 좌표를 목표로 줄 수 없다.
- slide 21의 `<rate>10Hz`는 **순찰 시나리오에 잘못 붙은 값**이다.
  구현은 1 Hz이고, 10 Hz는 I2ICF의 주행 중 장애물 회피 값이다.
- slide 21의 XML은 닫는 태그가 없는 **표현용 의사코드**다. 논문·제안서에는 정규화안을 쓸 것.

## 미결정

- **U-2**: L2 직렬화 — XML(YANG/NETCONF 정합) vs JSON(LLM 생성 정확도·MCP 친화).
  현재 권고는 **내부 JSON, 표준 문서·전시 XML, 양방향 변환**.
