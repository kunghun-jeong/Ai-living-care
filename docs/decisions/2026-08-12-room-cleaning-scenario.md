# 2026-08-12 · 방청소 시나리오 (clean_room.json)

## 무엇

`Scenarios/clean_room.json`(100 step)을 추가했다. "방"은 `check_grandma.json`과 같은 KG
구역(space) 6개다 — 이 집은 오픈 플랜이라 벽으로 닫힌 방이 없다(WORLD.md §8). 순서도
`check_grandma.json`과 동일하게 맞췄다: 식탁 → 거실 → 침실 → 좌상단 → 현관 → 주방.

각 구역 안에서는 **좌측끝 → 우측끝 → 좌측끝 → 우측끝**(2왕복, 4 leg)을 스윕하고 다음
구역으로 넘어간다. 한 leg는 기존 구역 블록과 같은 `resolve_location → pathplanning →
moving_path → get_path_status(poll)` 4-step 패턴이다. 전용 청소 액추에이터 MCP tool이
없어서(16종 중 없음) **이동 패턴 자체로 "청소"를 표현했다** — `check_grandma.json`이
"확인"을 `look_around`+`detect_objects`로 표현하는 것과 같은 방식. 마지막은 항상
`home` 복귀(`docs/decisions/2026-08-11-home-return-convention.md`).

## 좌측끝/우측끝 좌표는 어떻게 정했나

**지어내지 않았다.** WORLD.md §1·§6이 못 박은 규칙("좌표를 지어내지 말 것 · 자유공간
안이고 벽에서 0.45m 이상 · 도달 가능한지 검증한 뒤 표에 추가")을 그대로 따랐고, 검증을
`Reasonings.py`의 실제 A*(`astar_plan`)로 했다:

1. WORLD.md §2 구역 표의 x 범위(침실 −9.6~−3.4 등)와 `entities.json`의 기존 구역 y 값으로
   그 구역의 가로줄을 잡는다 (`entrance`만 §2의 "하단(TV·현관)" 박스가 신발장 관측점보다
   훨씬 넓어서 그 값을 그대로 안 쓰고 신발장 주변 ±2m로 좁혔다 — 안 그러면 "현관 청소"가
   TV 구역까지 삼킨다).
2. `map.pgm` 점유격자(`Reasonings._load_grid`)를 0.05m 간격으로 스캔해, 벽 여유
   (`dist_m`) ≥0.45m인 셀 중 가장 왼쪽/오른쪽을 찾는다.
3. `astar_plan(home, 그 점)`을 **실제로 호출해서** 홈에서 도달 가능한지 확인한다
   (ROS2/Gazebo 없이 순수 `map.pgm` 위 A* — `import Reasonings`만으로 됨).

6구역 × 2점 = 12점 전부 여유 0.45~0.91m, home에서 도달 가능(13~63 waypoint)을 확인했다.
`manager_ai_agent/knowledge_graph/entities.json`에 `<구역>_left`/`<구역>_right`로 등록했다
(예: `bedroom_left (-7.80, 1.70)` 여유 0.47m).

## 확인 못 한 것 (TODO)

- **RViz2/Gazebo로 실행해 보지 않았다.** 이 환경(Windows, ROS2 미설치)에서는 `rclpy`가
  없어 `run_scenario.py`(MCP 서버 경유)를 못 돌린다 — `astar_plan` 재사용성 검증만
  했다(§ 위). `check_grandma.json`처럼 `SIM_PERSON` 시뮬로 실측 걸어보는 건 ROS2
  환경에서 남은 일이다.
- **좌우 2왕복(4 leg)은 자의적 기본값이다.** "반복해서"라는 요청을 구체적 반복 횟수로
  못박은 것 — 더 많이/적게 왕복해야 하면 `clean_room.json`의 leg 4개 블록을 복사/삭제
  하면 된다(패턴이 반복 구조라 손으로 늘리기 쉽다).
- **arrive step은 실패해도 분기하지 않는다.** `check_grandma.json`의 기존 관례를 그대로
  따랐다 — `get_path_status`가 `failed`로 멈춰도 다음 leg로 그냥 진행한다. 이건 이
  시나리오가 새로 만든 문제가 아니라 기존 DSL 패턴에 이미 있던 갭이다
  (`docs/status-defects.md`감 — 별도로 기록할지는 담당자 판단).

## 정본 반영

`worker_ai_agent/limo-MCP/CLAUDE.md`·`manager_ai_agent/knowledge_graph/CLAUDE.md`에
파일 추가 한 줄씩.

## 검증

```
cd worker_ai_agent/limo-MCP
python3 Scenarios/validate_variant.py Scenarios/clean_room.json   # 구조 검증 PASS
```
