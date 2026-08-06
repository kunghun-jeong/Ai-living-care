# limo-patrol-viz

`limo-MCP` 시나리오("할머니 괜찮은지 확인해줘")의 **순찰 로직을 Gazebo·Nav2·YOLO 없이**
검증/시연하는 도구. AWS small_house 맵 위에서 A*로 경로를 뽑고 운동학만 적분해
로봇을 실제로 움직이며, 카메라 1인칭 뷰까지 합성해 `/camera/image_raw`로 발행한다.

Gazebo가 이 WSL2 환경에서 **RTF 0.04~0.06**(실시간의 1/20~1/26)으로 도는 문제 때문에
반복 검증이 사실상 불가능해서 만든 대체 수단이다. 6.3분짜리 시나리오를 Gazebo로 돌리면
벽시계로 2시간이 걸리지만, 이 도구는 실시간(또는 배속)으로 돈다.

---

## 구성

```
run_patrol.sh      RViz2 애니메이션 실행 (로봇 이동 + 카메라 스트리밍)
run_coverage.sh    오프라인 커버리지 시뮬 (GUI 없이 통계 + PNG)
patrol_viz.py      ROS2 노드 — TF/마커/카메라 발행
patrol_sim.py      오프라인 시뮬 — 커버리지 계산 + 시각화 PNG
patrol.rviz        RViz2 설정 (맵/커버리지/FOV/궤적/로봇/카메라)
maps/              AWS small_house 점유격자 (608x384, 0.05 m/px, origin -10,-10)
limo/limo.urdf     WeGo LIMO(four_diff) URDF — ROS1 xacro에서 변환한 것
tools/make_urdf.sh LIMO URDF 재생성 스크립트
```

## 요구사항

- ROS2 (Jazzy에서 검증). `rviz2`, `robot_state_publisher` 필요
- Python3 + `numpy`, `opencv-python`(또는 `python3-opencv`)
- **Nav2 / Gazebo / turtlebot3 / YOLO 는 필요 없음**

```bash
sudo apt install -y ros-jazzy-rviz2 ros-jazzy-robot-state-publisher python3-opencv python3-numpy
```

## 실행

```bash
./run_patrol.sh      # RViz2 창이 뜨고 로봇이 순찰을 돈다
./run_coverage.sh    # GUI 없이 커버리지 수치 + patrol_sim.png
```

RViz에서 보이는 것
- **회색 큐브** 벽/가구, **연두** 카메라가 이미 본 영역
- **파란 부채꼴** 현재 카메라 FOV, **주황 선** 주행 궤적
- **빨간 원기둥 + 번호** 순찰 지점, **주황 원기둥 PERSON** 배치된 "할머니"
- 좌측 하단 **CameraStream** 패널에 1인칭 뷰 (발견 시 `PERSON` 오버레이)

---

## 검증 결과 (기본 설정)

```
경로점 7개 · 375초(6.3분) · 스캔 376회 · 주행 50m
커버리지 93.6%  ·  2m² 이상 사각지대 0개
```

경로점 5개였을 때는 83.8%였고, 사각지대 두 곳
(`(-7.77, 0.56)` 좌상단 방 11.1m², `(8.10, 1.71)` 식탁 구역 6.5m²)을
경로점으로 추가해 93.6%로 올렸다.

### 현재 순찰 좌표 (map 프레임, origin -10,-10)

```
(8.10, 1.71) (4.30,-0.55) (1.45, 4.35) (-2.00,-0.80)
(-7.77, 0.56) (-7.90,-2.95) (7.15,-3.30)
```
스폰 `(3.5, 1.0)` — AWS README 권장 지점, 이 맵에서 여유 1.40m.

---

## 파라미터

`patrol_viz.py` / `patrol_sim.py` 상단에서 조정한다.

| 값 | 기본 | 의미 |
|---|---|---|
| `V_LIN` / `V_ANG` | 0.22 m/s / 0.5 rad/s | 로봇 속도 (turtlebot3 waffle 기준) |
| `CAM_FOV` | 62° | 수평 화각 |
| `CAM_RANGE` | 4.0 m | **사람 검출 유효 거리 — 커버리지에 가장 민감** |
| `SCAN_HZ` | 1.0 | 스캔 주기 |
| `SPEED` | 3.0 | 재생 배속 (`patrol_viz.py`만) |
| `PATROL` | 7점 | 순찰 좌표 리스트 |
| `PERSON` | (-7.5, 0.30) | 배치된 사람 위치 |

---

## 알아둘 것 (실제로 겪은 것들)

### 1. WSL2 GPU — `/dev/dri`가 없어도 하드웨어 가속이 된다

WSL2는 `/dev/dri`가 아니라 **`/dev/dxg`**를 쓴다. Mesa가 기본으로 llvmpipe를
고를 뿐이고, 드라이버를 명시하면 하드웨어 가속이 살아난다.

```bash
export GALLIUM_DRIVER=d3d12
export LD_LIBRARY_PATH=/usr/lib/wsl/lib:$LD_LIBRARY_PATH
glxinfo -B | grep "OpenGL renderer"
#  -> D3D12 (Intel(R) Arc(TM) Graphics),  OpenGL 4.6
```

이 설정으로 **Gazebo Harmonic 카메라 센서가 640x480에서 10Hz** 나온다
(llvmpipe로도 같은 씬에서 10Hz는 나오지만, 복잡한 씬에서 차이가 벌어진다).

### 2. 그런데 RViz2는 반대다

RViz2의 Ogre는 d3d12 경로에서 `D3D12: Removing Device`로 컨텍스트가 죽어
**3D 뷰 전체가 검게** 나온다. 그래서 `run_patrol.sh`는 `LIBGL_ALWAYS_SOFTWARE=1`로
소프트웨어 렌더링을 강제한다.

### 3. RViz2 Map 디스플레이는 이 Mesa에서 작동하지 않는다

```
GLSL link result: active samplers with a different type
                  refer to the same texture image unit
```
`indexed_8bit_image` 셰이더 링크 실패 — RViz2 자체 버그라 설정으로 못 고친다.
그래서 이 패키지는 `nav_msgs/OccupancyGrid` 대신 **벽/바닥을 `CUBE_LIST` 마커로**
직접 그린다. Nav2를 붙일 때 **costmap 시각화도 같은 이유로 실패**할 것이다.

### 4. Gazebo의 small_house.world는 RTF 0.04~0.06

로봇도 렌더링도 없이 headless로 돌려도 그렇다. 원인 후보: include 89개,
82MB 충돌 메시, 남아 있는 inertia 오류 1건. 개선하려면 가구 collision을
단순 박스로 바꾸거나 `<collision>` 자체를 빼는 게 효과가 클 것이다.

### 5. LIMO URDF는 Jazzy에서 파싱된다

WeGo `limo_gazebo`(ROS1/Gazebo Classic)에서 `$(find limo_description)`를 절대경로로
바꾸고 `.gazebo` include만 제거하면 xacro 변환이 통과한다 (11링크: base, 바퀴 4,
`laser_link`, `depth_camera_link`, `imu_link`). 메시 없이 기본 도형만 쓴다.
`tools/make_urdf.sh` 참고. **가제보 플러그인 3블록만 Harmonic 문법으로 새로 쓰면**
실제 시뮬에도 쓸 수 있다.

---

## 검증되지 않은 것

- 물리(바퀴 미끄러짐·충돌), Nav2 실제 재계획 → 실제 소요시간은 20~30% 더 걸릴 것
- YOLO 실제 검출 — 이 도구는 "FOV 안 + 시야 확보 = 발견"으로 처리
- **수직 FOV** — 2D 가정이라 바닥에 누운 사람이 4m에서 화면 아래로 벗어나는 경우를
  반영하지 못한다. 쓰러진 상황이 가장 위험한 시나리오인데 바로 그 부분이 미검증이다
- `CAM_RANGE=4.0m` 가정 — 실사진으로 YOLO 유효 거리를 재야 93.6%가 의미를 갖는다
