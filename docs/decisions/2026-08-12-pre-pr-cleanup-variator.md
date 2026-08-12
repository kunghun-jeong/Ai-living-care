# 2026-08-12 · PR 전 정리 — 변형기 데모 산출물 삭제

## 무엇

`check_obj_state_v1.json`~`v5.json`을 삭제했다. `variate_scenario.py`가 언제든 그대로
재생성 가능한 데모 산출물이라(`--count 5 --seed 1 --objects grandma,dog,person`),
결과물을 리뷰 대상으로 커밋할 이유가 없다. 도구(`scenario_dsl.py`·`variate_scenario.py`·
`validate_variant.py`·`object_bindings.json`) 자체는 유지.

## 정본 반영

`worker_ai_agent/limo-MCP/CLAUDE.md`에 파일 삭제 한 줄.

## 검증

```
cd worker_ai_agent/limo-MCP
python3 Scenarios/variate_scenario.py Scenarios/check_grandma.json --count 5 --seed 1 \
    --objects grandma,dog,person   # 동일 산출물 재생성 가능함을 확인
```
