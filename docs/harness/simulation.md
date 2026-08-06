# 하네스 — 시뮬레이션 · 순찰 도구

> 대상: `worker_ai_agent/limo-MCP/Simulation/**`, `tools/limo-patrol-viz/**`
>
> 이 문서는 **관문이 아니라 참고 노트**다. 이 영역을 처음 건드릴 때 한 번 읽는다.
> 작업 절차는 @docs/harness.md — 앵커 갱신과 결정 로그 한 줄이 전부다.

## 0. 먼저 알아야 할 것

**두 디렉터리 모두 원본 보존 대상이다 (D-14).** 내부 구조를 바꾸지 않는다.

**`sim/` 이라는 디렉터리는 없다.** 시뮬레이션은 `worker_ai_agent/limo-MCP/Simulation/` 안에 있다.
`sim/`·`tools/scenarios/`·`tools/patrol_viz/`는 `sot_audit.py`의 **금지 경로**다.

## 1. 읽을 것

1. `worker_ai_agent/limo-MCP/CLAUDE.md` — 실행 방법과 알려진 함정
2. `tools/limo-patrol-viz/CLAUDE.md` — 커버리지 수치의 한정어
3. `worker_ai_agent/limo-MCP/Simulation/sim_bringup.launch.py` **docstring** —
   cmd_vel 타입 불일치, 상대경로 이중결합, X11 연결 실패의 실화가 사유와 함께 기록돼 있다.
   **이 저장소에서 가장 밀도 높은 문서다. 반드시 읽는다.**
4. `docs/handoff/limo-MCP_SESSION_HANDOFF.md` — 개발 경위

### map.yaml ↔ 코드 상수 일치 (현재 아무도 안 하는 검사)

```bash
python3 - <<'EOF'
import re, yaml
y = yaml.safe_load(open("tools/limo-patrol-viz/maps/map.yaml"))
for f in ("patrol_sim.py", "patrol_viz.py"):
    s = open(f"tools/limo-patrol-viz/{f}").read()
    m = re.search(r"RES, OX, OY = ([\d.]+), (-?[\d.]+), (-?[\d.]+)", s)
    got = tuple(map(float, m.groups()))
    want = (y["resolution"], y["origin"][0], y["origin"][1])
    assert got == want, f"FAIL {f}: 코드 {got} != map.yaml {want}"
print("OK: map.yaml 과 코드 상수 일치")
EOF
```

> **`map.yaml`을 코드가 아무도 읽지 않는다.** 같은 값이 두 파일에 하드코딩돼 있고,
> 임계값은 아예 다르다(yaml `occupied_thresh 0.65` vs 코드 `img > 250`).
> **맵을 교체하면 yaml만 갱신되고 코드는 조용히 옛 원점으로 계산한다.** 커버리지 93.6%가 여기에 직결된다.

## 알아 둘 것 (함정)

| # | 검증 | 방법 |
|---|---|---|
| HS-1 | **경량 경로가 완주하는가** | `cd tools/limo-patrol-viz && ./run_coverage.sh` — ROS2·GUI 불필요, 수십 초. `커버리지` 출력 확인 |
| HS-2 | **커버리지 회귀 감시** | 위 출력에서 % 를 뽑아 하한(예: 90%)을 건다. 좌표·`CAM_RANGE`를 바꿨다면 필수 |
| HS-3 | **프로세스 누수** | `./run_patrol.sh & sleep 20; kill %1; sleep 2; pgrep -f "patrol_viz.py\|robot_state_publisher"` — **현재는 통과 못 한다.** `exec rviz2`가 EXIT 트랩을 무력화한다 |
| HS-4 | **Gazebo 기동 대기** | `sim_bringup.launch.py`는 spawn +20초, nav2 +35초 타이머를 갖는다. RTF 0.04라 실제 대기는 수 분이다. **Nav2 준비 전에 클라이언트를 치면 무한 루프한다** |
| HS-5 | **카메라 프레임 실측** | `ros2 topic hz /camera/image_raw` — 자료마다 30/10/2~3.8 Hz로 갈린다. **실제 값을 재서 기록한다** (작업 0-0) |
| HS-6 | **좌표 변경 시** | `PATROL` 상수를 바꿨으면 맵 범위 안인지 확인. A* `snap()`은 범위 검사가 없어 **음수 인덱스면 numpy가 조용히 반대편 끝을 읽는다** |

## 4. 알려진 함정 (재발 방지)

| 함정 | 내용 |
|---|---|
| **`cmd_vel` 타입 불일치** | 스톡 브리지 yaml은 `TwistStamped`, Nav2 `collision_monitor`는 `Twist` 발행 → ROS2가 별개 토픽으로 취급해 **로봇이 영영 안 움직였다.** `waffle_bridge_fixed.yaml`로 해결 |
| **RViz2 Map 디스플레이 미동작** | `indexed_8bit_image` 셰이더 링크 실패(RViz2 자체 버그). **Nav2 costmap 시각화도 같은 이유로 실패할 것** |
| **RViz2 ↔ Gazebo 렌더링 요구가 반대** | Gazebo는 `GALLIUM_DRIVER=d3d12`(하드웨어), RViz2는 `LIBGL_ALWAYS_SOFTWARE=1`(소프트웨어) |
| **WSL2 GPU** | `/dev/dri`가 아니라 **`/dev/dxg`**. `GALLIUM_DRIVER=d3d12` + `LD_LIBRARY_PATH=/usr/lib/wsl/lib` |
| **numpy ABI 충돌** | `ultralytics`가 numpy 2.x를 깔면 apt matplotlib과 충돌. `numpy==1.26.4` 고정 |
| **상대경로 이중결합** | `__file__`에 `abspath`를 안 쓰면 `GZ_SIM_RESOURCE_PATH`가 상대경로로 등록돼 메시 로드가 전부 실패 |
| **`pkill`이 전역** | `run_patrol.sh`의 `pkill -f robot_state_publisher`는 **다른 세션의 Gazebo까지 죽인다** |
| **RTF 0.04~0.06** | headless·무로봇에서도 그렇다. 6.3분 시나리오 = 벽시계 2시간 |

## 5. 수치를 인용할 때

**커버리지 93.6%는 "실측"이 아니라 기하 시뮬레이션 결과다.** 논문·제안서에 쓸 때 반드시 한정어를 붙인다.

- 물리(바퀴 미끄러짐·충돌)와 Nav2 실제 재계획 없음 → 실소요는 더 걸린다
- **YOLO를 돌리지 않음** — "FOV 안 + 시야 확보 = 발견"으로 처리
- `CAM_RANGE = 4.0 m`는 **미측정 가정**이며 커버리지가 여기에 가장 민감
- **수직 FOV 미반영 (U-13)** — 4 m 거리에서 **바닥에 누운 사람이 화면 아래로 벗어나는 경우**를 못 잡는다.
  쓰러진 상황이 리빙케어에서 가장 위험한데 바로 그 부분이 미검증이다
- **"사각지대 0"이 아니라 "2 m² 이상 사각지대 0"** 이다. 93.6%면 정의상 6.4%의 미커버가 존재한다
- 사람 배치 `PERSON=(-7.5, 0.30)`는 웨이포인트 `(-7.77, 0.56)`에서 **0.38 m** 거리다.
  그 웨이포인트는 사각지대를 메우려고 나중에 추가한 점이므로, **"순찰이 사람을 찾는다"는 결론은
  검증이 아니라 구성상 보장된 결과다**
