# 2026-08-10 · Nav2·Gazebo 없이 A*+운동학 시뮬레이션으로 이동을 검증한다

> **정본 반영** `worker_ai_agent/mcp_server/CLAUDE.md` · `docs/api-spec.md`

## 배경

`plan_and_navigate`(Nav2 경유)는 이 개발 환경(WSL2 Ubuntu, ROS2 Jazzy)에 **Gazebo가 설치돼
있지 않아** 검증 자체가 불가능했다(`nav2 action server unavailable`로 즉시 실패). 시나리오
JSON을 여러 개 검증해야 하는데(50개+ 목표) 매번 Gazebo(RTF 0.04~0.06, 6분 시나리오가
벽시계 2시간)를 띄우는 건 `tools/limo-patrol-viz/`가 이미 같은 이유로 존재하는 것과
동일한 문제다.

## 결정

`tools/limo-patrol-viz/patrol_sim.py`·`patrol_viz.py`와 **같은 접근**(A* + 운동학 적분,
Gazebo·Nav2 불필요)을 MCP tool로 노출했다:

- `pathplanning` — `Reasonings.astar_plan`이 `map.pgm` 점유격자 위에서 A*로 계산 (순수 로직)
- `moving_path` — `Actions.ActionModule.move_along_path`가 실물 오도메트리 대신 **자체
  적분한 pose**(`_sim_pose`)를 실시간으로 갱신하며 이동을 시뮬레이션
- `Visualization.PoseVisualizer` — `patrol_viz.py`와 같은 토픽(TF·`/joint_states`·`/trail`·
  `/map_walls`)으로 매 틱 스트리밍 → `tools/limo-patrol-viz/patrol.rviz`로 실시간 확인 가능

`plan_and_navigate`/Nav2 경로는 **제거하지 않고 유지한다** — Gazebo가 실제로 뜨는 환경(실기
검증 단계)에서는 그쪽이 물리까지 검증하는 정본이다. `pathplanning`/`moving_path`는 그 전
단계의 반복 검증용 대체 경로다.

## 소유 경계 관련

`tools/limo-patrol-viz/patrol_sim.py`·`patrol_viz.py` 자체는 **건드리지 않았다** (D-14/D-17,
코드는 담당 연구원 소유). 같은 맵·같은 알고리즘·같은 RViz 토픽을 **재구현**해서
`worker_ai_agent/limo-MCP/Worker_functions/`(경계 밖, 이번 작업 소유)에 새로 만들었다 —
`Visualization.py`가 그 새 파일이다.

## 검증

WSL2(ROS2 Jazzy, Gazebo 미설치)에서 실제 MCP 서버로 왕복 확인함:
- `resolve_location → pathplanning → moving_path → get_path_status폴링 → send_ir_signal×2`
  전체 성공 (`Scenarios/turn_on_air_conditioner.py`, `Scenarios/run_scenario.py`)
- `/trail`(~12Hz)·`/joint_states`(~11Hz)·TF(`map`→`base_footprint`)가 이동 중 실시간 퍼블리시됨

## 남는 제약

- `_sim_pose`는 **실물 오도메트리가 아니다.** 바퀴 미끄러짐·충돌·Nav2 재계획을 반영하지
  않는다 — `tools/limo-patrol-viz/CLAUDE.md`가 이미 경고한 것과 같은 종류의 한정어가 붙는다
  ("기하 시뮬레이션 결과이지 실측이 아니다").
- Gazebo가 설치되면 최종 확인은 `plan_and_navigate`(Nav2)로 다시 해야 한다.
