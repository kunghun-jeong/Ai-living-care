# 2026-08-12 · 시나리오 변형기 — 변주 규칙

## 무엇

`check_grandma.json` 류(구역 순찰 + `check_object_state`) 시나리오에서 시나리오 개수를
늘리는 변형기·검증기를 `worker_ai_agent/limo-MCP/Scenarios/`에 추가했다.

- `scenario_dsl.py` — 구역 블록 파싱/재조립/정규화 공유 유틸
- `variate_scenario.py` — 변형기 (CLI)
- `validate_variant.py` — 검증기 (CLI, 정적 — RViz 미사용)

## 변주 규칙

**고정(정책 — 변형기가 절대 건드리지 않는다)**

- 구역 블록 하나의 모양: `resolve_location → pathplanning → moving_path →
  get_path_status(poll) → look_around → detect_objects(poll) → branch(found)`,
  7 step 고정 순서·tool·layer·args 키. `check_object_state`를 부르는 꼬리 블록 포함.
- found 분기 정책: `on_true`는 항상 `state_check`, `on_false`는 다음 구역
  (마지막 구역이면 `go_home_resolve` — `state_check`를 건너뛴다).
- 꼬리 블록(`state_check → go_home_resolve → go_home_plan → go_home_move →
  go_home_arrive → outcome`)은 base와 완전히 동일하게 복사한다.

**변주(이 두 축만 바꾼다)**

1. `input.object` — 탐지 대상 클래스.
2. `steps[]`의 구역 순서/구성 — base 시나리오에 이미 있는 구역들을 다른 순서·다른
   부분집합으로 재배열한다 (`check_grandma_bedroom_first.json`이 손으로 만든 선례).

## 왜

시나리오 1(`check_grandma.json`)은 43~48 step짜리 하드코딩 경로다. Worker agent의 시나리오
선택 학습 신호가 흔들리지 않으려면(`docs/decisions/2026-08-11-scenario1-on-the-dsl-runner.md`
"LLM은 순서를 짜지 않고 시나리오를 고르기만 한다") 새 시나리오도 같은 정책 모양을 유지한
채 다양성만 늘려야 한다. 손으로 매번 43 step을 복사·수정하면 정책이 조용히 갈라질 위험이
있어 기계적으로 보장한다.

## 검증기(정적)가 하는 일과 안 하는 일

`validate_variant.py`는 (1) 일반 DSL 구조 검증(id 중복·미지 tool·존재하지 않는
next/on_true/on_false/condition 참조·도달성)과 (2) `--base`를 주면 정책 불변 검증(구역 블록
모양·found 분기 규칙·꼬리 블록이 base와 동일한지)을 한다. **RViz·MCP로 실제 실행하지는
않는다** — 그건 별도 태스크(시나리오 검증기, rviz 시뮬레이션)의 역할이다.

`object`가 `"person"`이 아니면 경고만 낸다 — `SimCameraPerception`(기하 카메라 시뮬)이
`SIM_PERSON` 환경변수 기반이라 다른 클래스는 구조는 유효해도 시뮬 실행으로 확인된 적이
없다 (`TODO(확인 필요)`: YOLO 실측 시 다른 클래스 검출력).

## 실측

```
python3 Scenarios/variate_scenario.py Scenarios/check_grandma.json --count 5 --seed 1
python3 Scenarios/validate_variant.py Scenarios/check_grandma_v*.json \
    Scenarios/check_grandma_bedroom_first.json --base Scenarios/check_grandma.json
```

생성 5건 + 기존 손수 파생본(`check_grandma_bedroom_first.json`) 전부 PASS. 개발 중
`rebuild_zone_block`이 `branch` step의 `condition` 필드(`"z1_scan.matched"`류)를
재번호 매김하지 않는 버그를 검증기가 실제로 잡아냈다 — 재배선 후 `condition`이 엉뚱한
구역의 (아직 실행 전인) step을 가리켜 매 실행마다 "못 찾음"으로 오판했을 것이다. 고쳤다.

## 정본 반영

이 디렉터리(`worker_ai_agent/limo-MCP/`)의 `CLAUDE.md`에 파일 추가 한 줄 반영.
