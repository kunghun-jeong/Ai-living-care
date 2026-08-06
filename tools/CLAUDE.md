# tools — 검증·시연 도구

> **SOT**: `docs/spec/AI-Care_Unified_Architecture_Spec_v0.2.md` §10.1
> **컴포넌트가 아니다.** 여기에 비즈니스 로직을 두지 않는다.

| 경로 | 용도 |
|---|---|
| `patrol_viz/` | Gazebo·Nav2·YOLO **없이** 순찰 로직을 검증·시연 |
| `scenarios/` | MCP 왕복 CLI 클라이언트 + 시나리오 DSL. **정책 실행 회귀 테스트 하네스로 승격 예정** |

## patrol_viz — 왜 존재하는가

Gazebo RTF가 0.04~0.06이라 6.3분 시나리오가 벽시계 2시간이 된다. **반복 검증이 불가능해 만든 대체 수단**이다.
AWS small_house 맵 위에서 A*로 경로를 뽑고 운동학만 적분해 로봇을 움직이며, 카메라 1인칭 뷰까지 합성한다.

```bash
cd tools/patrol_viz
./run_coverage.sh    # GUI 없이 커버리지 수치 + patrol_sim.png
./run_patrol.sh      # RViz2에서 순찰 애니메이션 + 카메라 스트리밍
```

### 결과: 경로점 7개 · 375초 · 스캔 376회 · 주행 50 m · **커버리지 93.6%** · 사각지대 0

**⚠️ 이 수치는 "실측"이 아니라 기하 시뮬레이션 결과다.** 논문·제안서에 반드시 이렇게 표기할 것:

- 물리(바퀴 미끄러짐·충돌)와 Nav2 실제 재계획 없음 → **실소요는 20~30% 더 걸릴 것**
- **YOLO를 돌리지 않음** — "FOV 안 + 시야 확보 = 발견"으로 처리
- `CAM_RANGE = 4.0 m`는 **미측정 가정**이며 커버리지가 여기에 가장 민감
- **수직 FOV 미반영 (U-13)** — 2D 가정이라 4 m 거리에서 **바닥에 누운 사람이 화면 아래로 벗어나는 경우**를
  못 잡는다. 쓰러진 상황이 리빙케어에서 가장 위험한데 바로 그 부분이 미검증이다

## scenarios

```bash
python3 tools/scenarios/send_goal.py 1.0 0.0        # plan_and_navigate 왕복
python3 tools/scenarios/capture_and_detect.py out.jpg  # 스냅샷 + YOLO
```

**`check_obj_state.json`은 현재 실행 불가**다 — 참조하는 `look_around`·`is_looking_around`·
`interrupt_look_around`가 AF에 없고(G-4), `check_object_state`도 tool로 노출되지 않았으며(G-3),
게다가 RF의 `check_object_state`는 JSON이 넘기는 `detections` 인자를 받지 않는다.

## 자산 메모

`patrol_viz/limo/limo.urdf` — WeGo `limo_gazebo`(ROS1 xacro)에서 변환한 **실제 LIMO 모델**.
Jazzy 파싱은 통과한다. **Gazebo 플러그인 3블록만 Harmonic 문법으로 재작성하면 시뮬에 투입 가능**하다.
