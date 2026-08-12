# 2026-08-12 · input.object 와 target_class 를 분리한다

## 무엇

`check_grandma.json`류 시나리오의 `input`에 필드를 하나 더 둔다:

```
object        의미적 라벨 — "누구/무엇을 확인하나" (예: "grandma", "dog")
target_class  실제 YOLO/시뮬 탐지 class — detect_objects·check_object_state 가 대조하는 값
```

`zN_scan`(`detect_objects`)의 `match.target`과 `state_check`(`check_object_state`)의
`object_class` 인자를 `$input.object` → `$input.target_class`로 바꿨다. `object`는 이제
탐지 매칭에 쓰이지 않는다 — 시나리오 라벨·의도 표현 전용이다.

매핑은 새 파일 `Scenarios/object_bindings.json`에 둔다 (`scenario_dsl.resolve_target_class`가
읽는다):

```json
{"person": "person", "grandma": "person", "grandpa": "person",
 "child": "person", "dog": "dog", "cat": "cat"}
```

영향받은 파일: `check_grandma.json`·`check_grandma_bedroom_first.json`·`check_obj_state.json`
(`input`·6곳의 `match.target`·`state_check.args.object_class`), `variate_scenario.py`
(`generate_variant`에 `target_class` 인자 추가, `object` 주면 바인딩으로 자동 조회),
`validate_variant.py`(시뮬 미검증 경고를 `object`가 아니라 `target_class` 기준으로).

`turn_on_air_conditioner.json`의 `$input.object`(IR 신호 대상 기기 이름, `entities.json`의
device 엔티티)는 **건드리지 않았다** — 그건 탐지 class 가 아니라 별개 의미다.

## 왜

[[변형기]](2026-08-12-scenario-variator-rules.md)를 쓰다 보니 `object`에 `"grandma"`·`"dog"`
같은 사람이 읽는 라벨을 넣고 싶은데, DSL은 그 값을 그대로 YOLO/시뮬 detection class와
대조한다 — `"grandma"`는 어떤 detection에도 안 걸려 항상 실패한다. 매핑 레이어 없이 `object`
값을 detection class로만 제한하면 `"grandma"`처럼 쓰고 싶은 라벨을 못 쓴다.

## 정본 반영

`worker_ai_agent/limo-MCP/CLAUDE.md`에 파일 추가·내용 수정 한 줄.

## 검증

```
python3 Scenarios/variate_scenario.py Scenarios/check_grandma.json --count 5 --seed 1 \
    --objects grandma,dog,person
python3 Scenarios/validate_variant.py Scenarios/check_obj_state_v*.json \
    Scenarios/check_grandma_bedroom_first.json --base Scenarios/check_grandma.json
```

전부 PASS (`target_class="dog"`인 것만 시뮬 미검증 경고). `object_bindings.json`에 없는
라벨(`hamster` 등)은 변형기가 즉시 `ValueError`로 막는다 — 조용히 person 으로 넘어가지
않는다.
