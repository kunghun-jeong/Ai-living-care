# 2026-08-12 · PR 전 정리 — 방청소 시나리오 생성기 정식 편입 + 죽은 KG 엔티티 제거

## 무엇

- 라운모어 커버리지 계산 로직을 (대화 세션 중 스크래치 스크립트로만 존재하던 것을)
  `Scenarios/generate_coverage_scenario.py`로 정식 편입했다. **`clean_room.json`은 이제
  이 스크립트의 산출물이다 — 손으로 고치지 않는다.** 저장소 안에 재생성 경로가 없던 게
  진짜 공백이었다(변형기 쪽엔 `variate_scenario.py`가 있는데 방청소 쪽엔 없었다).
- `clean_room_boustrophedon_bedroom_test.json`(스크래치 산출물)을 지우고, 같은 내용을
  정식 스크립트로 재생성한 `clean_room_bedroom_smoketest.json`으로 교체했다
  (`--rooms bedroom` 한 줄로 언제든 다시 만들 수 있다).
- `entities.json`의 `<구역>_left`/`<구역>_right` 12건을 **삭제했다.** 좌우 1줄 왕복판
  전용이었는데 그 판 자체가 라운모어 커버리지로 완전히 교체되면서 아무도 안 쓰는 채로
  남아 있었다 — `docs/decisions/2026-08-12-boustrophedon-coverage.md`가 "엔티티는 유지"라고
  적어놓은 걸 이 결정이 뒤집는다: 안 쓰는 채 남겨두느니 지우는 게 맞다고 판단했다
  (`generate_coverage_scenario.py`가 좌표를 procedural하게 직접 계산하지 KG 이름으로
  안 부르기 때문에 애초에 KG 등록이 불필요했다). `manager_ai_agent/knowledge_graph/
  CLAUDE.md`의 해당 언급 문단도 같이 지웠다 — 결과적으로 두 파일 다 이 변경 전 상태와
  git diff가 없다(추가했다 지운 것이므로).

## 정본 반영

`worker_ai_agent/limo-MCP/CLAUDE.md`의 방청소 관련 문단들을 하나로 합쳐 최종 상태만
남겼다(중간 100→112→286 step 이력은 `docs/decisions/`에 그대로 있으니 CLAUDE.md에서까지
중복 안 해도 된다).

## 검증

`generate_coverage_scenario.py`는 이 PR 하나로 완결된다 — 다른 PR의 파일에 의존하지
않는다(처음엔 `scenario_dsl.save_scenario`를 재사용했는데, 그건 별도 PR(변형기/검증기)
소속이라 이 브랜치만 체크아웃하면 `ModuleNotFoundError`가 난다는 걸 뒤늦게 발견해서
`save_scenario`를 이 파일 안으로 인라인했다).

```
cd worker_ai_agent/limo-MCP
python3 Scenarios/generate_coverage_scenario.py                      # clean_room.json 재생성 확인
python3 Scenarios/generate_coverage_scenario.py --rooms bedroom --out Scenarios/clean_room_bedroom_smoketest.json
cd ../../.. && python3 anchor.py && python3 sot_audit.py
```

`Scenarios/validate_variant.py`(별도 PR·변형기/검증기 소속)가 먼저 머지돼 있으면 그걸로
구조 검증도 추가로 돌릴 수 있다 — 이 PR 자체의 검증(위 명령)은 그거 없이도 끝난다:
`generate_coverage_scenario.py`가 생성 시점에 `Reasonings.astar_plan`으로 전체 체인
도달성을 스스로 확인한다(§ 위 코드 docstring `verify_chain`).
