# 2026-08-11 · 시작점 = 도착점 (홈 복귀 규약)

## 무엇

모든 시나리오는 `home` 에서 출발해 `home` 으로 돌아온다. KG 에 엔티티를 추가했다:

```
home = (3.5, 1.0, yaw 0)
```

복귀 블록은 어느 시나리오에서나 같은 4스텝이다 —
`go_home_resolve` → `go_home_plan` → `go_home_move` → `go_home_arrive`.

- `turn_on_air_conditioner.json`  9 → 13스텝 (실측 115초)
- `check_grandma.json`           43 → 48스텝 (실측 256초)
- `check_grandma_bedroom_first.json` 43 → 48스텝

할머니 시나리오는 복귀 뒤 `outcome` 브랜치가 `state_check.bbox` 유무로 성패를 가른다 —
**실패해도 집에 돌아온 뒤에 실패한다.**

`Scenarios/check_obj_state.json` 에는 붙이지 않았다. 이동이 없는 조각이라 돌아올 곳이 없다.

## 왜

팀 합의사항이다. 그리고 좌표를 시나리오마다 박아 넣으면 어긋나므로 KG 엔티티로 뒀다.

## 주의 — 두 곳이 같아야 한다

```
manager_ai_agent/knowledge_graph/entities.json : "home".pose
worker_ai_agent/limo-MCP/Worker_functions/Actions.py : _SIM_SPAWN
```

한쪽만 바꾸면 로봇이 A 에서 출발했다고 믿으면서 B 로 돌아가려 한다. `entities.json` 의
`note` 에 적어 뒀다. 현재 둘 다 `(3.5, 1.0, 0.0)` 으로 일치한다 (확인함).
