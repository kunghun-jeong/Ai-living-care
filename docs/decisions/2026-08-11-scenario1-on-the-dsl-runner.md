# 2026-08-11 · 시나리오 1을 에어컨 시나리오와 같은 DSL 위로 옮긴다

## 무엇

`Scenarios/check_grandma.json` (48스텝) 과 파생본 `check_grandma_bedroom_first.json` 을
추가했다. `run_scenario.py` 로 실행되고 RViz2 로 보인다. 실측 256초, 침실에서 발견.

막혀 있던 것을 메웠다:

- `Actions.py` — `look_around` · `is_looking_around` · `interrupt_look_around` (갭 G-4)
- `MCP_server.py` — 위 3개 + `check_object_state` 노출 (갭 G-3 부분 해소). 도구 12 → 16
- `Perceptions.py` — `SimCameraPerception`. `SIM_PERSON="x,y"` 가 있을 때만 동작
- `run_scenario.py` — 버그 2건 (아래)

## 왜

`check_obj_state.json` 은 이동이 한 줄도 없는 "제자리 확인" 조각이고, 부르는 도구 3개가
MCP 에 없어서 **15초 돌다 조용히 fail** 했다. 출력만 보면 "집에 아무도 없다" 와
"도구가 없어서 아무것도 못 했다" 가 구분되지 않았다.

`tools/limo-patrol-viz/patrol_viz.py` 는 MCP 를 쓰지 않는 별도 애니메이션이다. 즉
**"할머니 괜찮은지 확인해 줘" 가 MCP 를 통해 실행되는 형태로는 존재한 적이 없었다.**

에어컨 시나리오는 완주하므로, 그 모양(이름→좌표→A*→이동→도착대기)을 그대로 반복하고
탐색 블록만 얹었다.

## 실측으로 드러난 기존 버그 4건

- `run_scenario.py` `_check_match` 가 `match.target` 을 **대조하지 않는다** — `class` 값이
  있기만 하면 참이라, YOLO 가 의자를 검출해도 "사람 찾음" 이 된다. 에어컨 시나리오는
  `equals` 형식만 써서 드러나지 않았다
- `run_scenario.py` 가 `poll_until_match` 의 `interrupt` 를 **무시한다** —
  `check_obj_state.json` 이 이미 쓰고 있던 필드다
- `Actions._advance_sim_to` 가 yaw 를 정규화하지 않아 웨이포인트마다 누적된다 (`-10.21 rad` 관측)
- `Reasonings.astar_plan` 의 `snap()` 이 목표가 통행 불가일 때 **말없이 가장 가까운 곳으로
  옮기고 성공을 반환**한다. 가구가 빽빽한 침실에서 실제로 일어난다. `GoalNotReachable` 로
  이유를 돌려주게 고쳤다. 경로 솎기가 목표점을 버리던 것도 같이 고쳤다 (도착 오차 0.15 m → 0)

## LLM 의 역할을 정정한다

WORLD.md 는 "LLM 이 순찰 순서를 짠다(판단 ①)" 고 적고 있었다. **틀렸다.** 경로는 시나리오에
하드코딩하고, LLM 은 **어느 시나리오(파생본)를 고를지** 판단한다. Worker agent 에게 시나리오
선택을 학습시킬 때 시나리오가 매번 달라지면 학습 신호가 망가지기 때문이다 (팀 결정).

## 기하 카메라 시뮬을 왜 넣었나

인지 단계에는 카메라 프레임이 필요한데 그건 Gazebo 가 준다. Gazebo 는 RTF 0.04 —
6분 시나리오가 벽시계 2시간이라 반복 검증이 불가능하다.

이미 같은 패턴이 두 번 쓰이고 있다: Nav2 대신 `pathplanning`(A*), Gazebo 물리 대신
`moving_path`(운동학 적분). **인지만 구멍이었다.** 같은 방식으로 메웠다.

섞이지 않게 한 장치:

- `SIM_PERSON` 이 없으면 객체 생성조차 안 된다 (`sim_camera_from_env()` → `None`)
- 모든 응답에 `"source": "geometric_sim"` 이 붙는다
- 합성 화면 하단에 `GEOMETRIC SIM (not a real camera)` 이 찍힌다

**답하지 못하는 것**: YOLO 의 실제 검출력, 인물 액자 20개 오탐, 수직 화각(바닥에 누운 사람).

## 회귀 하나를 만들었다가 잡았다

`/camera/image_raw` 로 시뮬 화면을 발행하게 하자 `PerceptionModule` 이 그 토픽을 구독하고
있어 **자기가 쏜 프레임을 실측으로 착각**했고, 실측 경로는 YOLO 를 부르는데 `ultralytics`
가 없어 검출이 0 이 됐다. `_observe()` 가 시뮬을 먼저 보도록 순서를 뒤집어 고쳤다.
