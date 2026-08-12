# 2026-08-12 · clean_room.json을 라운모어형(보스트로페돈) 전체 커버리지로 교체한다

## 무엇

`clean_room.json`을 통째로 다시 만들었다(100 step 좌우 1줄 왕복판 → 286 step 다줄 커버리지판).
6구역 × 레인 간격 0.4m로 총 45줄(방별 10·15·5·2·3·10줄), 줄마다 왕복 2 leg = 90 leg,
leg당 `pathplanning`(좌표 직접 지정, `resolve_location` 안 씀) → `moving_path` →
`get_path_status`(poll) 3 step. 구역 진입/이탈에 가상 `send_ir_signal(device="vacuum", ...)`
(`docs/decisions/2026-08-12-virtual-vacuum-actuator.md`)은 그대로 유지. 순서·home 복귀
관례도 그대로(`docs/decisions/2026-08-11-home-return-convention.md`).

사용자가 실제 로봇청소기의 라운모어 커버리지맵(사진)을 보여주며 "이렇게 청소했으면
좋겠다"고 요청 → 침실 1개짜리 시험판(`clean_room_boustrophedon_bedroom_test.json`, 36
step)으로 먼저 검증 → 확인됨 → 나머지 5구역까지 같은 방식으로 확장해 `clean_room.json`을
교체했다. 시험판 파일은 지우지 않고 남겨뒀다(가벼운 스모크 테스트용).

## 줄(row)은 어떻게 뽑았나

이전 결정(`docs/decisions/2026-08-12-room-cleaning-scenario.md`)의 "좌표를 지어내지
않는다" 원칙을 그대로 따르되, 이번엔 방마다 **한 줄이 아니라 여러 줄**이 필요했다:

1. 각 구역의 (x_lo, x_hi, y_lo, y_hi) 박스를 정한다. 4곳(식탁·거실·침실·주방)은
   WORLD.md §2 구역 표를 그대로 썼다. **`upper_left_room`·`entrance` 두 곳은 §2에 정확히
   대응하는 표 항목이 없다** — WORLD.md 8구역 표는 카메라 커버리지 계산용으로 짠 것이라
   `entities.json`의 세분화된 이름과 1:1이 아니다. 이 둘은 박스를 지어내는 대신 기존
   KG 접근점 주변으로 **보수적으로 좁혀** 잡았다(`upper_left_room` 1.5×0.7m,
   `entrance` 4.0×1.0m) — 넓게 잡아 옆 구역(침실·TV구역)을 침범하느니 좁게 잡아 안전한
   쪽을 택했다. **TODO(확인 필요)**: 이 두 구역의 진짜 경계.
2. 박스를 레인 간격 0.4m로 y줄마다 스캔, 각 줄에서 `map.pgm` 점유격자 벽 여유
   (`Reasonings._load_grid`의 `dist_m`) ≥0.22m(=`pathplanning`이 쓰는 `_ROBOT_RADIUS_M`과
   동일 기준 — 이전 판의 신규 좌표 등록 기준 0.45m보다 낮춘 이유는 §3)인 연속 구간을
   찾는다. 한 줄에 여러 조각(가구로 갈라짐)이 나오면 **가장 긴 것만** 쓴다 — 조각까지
   전부 훑으면 지그재그가 훨씬 복잡해지고, 짧은 조각은 대개 가구 틈이라 실제로도 위험
   구간이다(예: 침실 책상 통로, 이미 0.28m로 플래그됨).
3. **home → 방1 줄1 → 방1 줄2 → ... → 방6 마지막 줄 → home** 전체 90-leg 체인을 실제
   `Reasonings.astar_plan()`으로 순서대로 호출해 **전부 경로가 존재하는지** 확인했다
   (`GoalNotReachable`/빈 경로 0건). ROS2 없이 `map.pgm` 순수 A*라 이 검증엔 Gazebo가
   필요 없다.

## 왜 0.45m가 아니라 0.22m 여유로 낮췄나

이전 판(단일 줄)의 0.45m는 **KG에 이름 붙여 영구 등록할 지점**이라 여유를 넉넉히 뒀다.
이번 커버리지 줄은 KG에 등록하지 않는 **일회성 절차적 좌표**이고, 실제 진공청소기가
벽 가까이까지 훑어야 커버리지가 의미 있다 — `pathplanning` 자체가 이미 0.22m 미만은
"통행 불가"로 거부하므로, 그보다 더 보수적으로 깎으면 방 가장자리를 놓친다.

## 확인 못 한 것 (TODO)

- **RViz2/Gazebo로 아직 안 돌려봤다** — 사용자가 WSL에서 직접 실행해서 확인 중.
- **레인 간격 0.4m·최장 구간만 사용은 여전히 자의적 기본값이다.** 더 촘촘하게(간격↓)
  하거나 짧은 조각까지 포함하려면 재계산해야 한다.
- **`upper_left_room`·`entrance`의 진짜 경계**(위 §1) — 확정되면 박스를 넓혀 재생성해야
  더 넓게 커버한다.
- **arrive 실패해도 분기 없음** — 이전 판과 같은 기존 DSL 갭, 그대로 상속.

## 정본 반영

`worker_ai_agent/limo-MCP/CLAUDE.md`에 파일 교체 한 줄.

## 검증

```
python3 Scenarios/validate_variant.py Scenarios/clean_room.json   # 구조 검증 PASS, 286 step
```

체인 도달성(90 leg, home→...→home)은 스크립트로 실측 완료(`Reasonings.astar_plan` 직접
호출, ROS2 불필요). 실제 시뮬레이션 실행 결과는 사용자 확인 대기 중.
