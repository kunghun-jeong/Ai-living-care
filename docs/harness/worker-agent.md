# 하네스 — Worker AI Agent (Perception · Reasoning · Action)

> 대상: `worker_ai_agent/limo-MCP/Worker_functions/*.py`, `worker_ai_agent/{perception,reasoning,action}/`,
> `worker_ai_core/`, `worker_ai_analyzer/`, `worker_ai_management_system/`
>
> 이 문서는 **관문이 아니라 참고 노트**다. 이 영역을 처음 건드릴 때 한 번 읽는다.
> 작업 절차는 @docs/harness.md — 앵커 갱신과 결정 로그 한 줄이 전부다.

## 0. 먼저 알아야 할 것

**`limo-MCP/`는 원본 보존 대상이다 (D-14).** 내부 구조·파일명·경로를 바꾸지 않는다.
**파일 *내용* 수정은 D-17에 따라 허용된다** — `docs/decisions.md`에 결정을 한 줄 남긴다.
Phase 0 작업 0-5·0-7~0-12가 전부 여기 해당한다.
컴포넌트 디렉터리(`perception/` 등)는 **규범**을 갖고 코드는 없다 — 규범을 읽고 구현을 고친다.

| 규범 (읽을 곳) | 구현 (고칠 곳) |
|---|---|
| `worker_ai_agent/perception/CLAUDE.md` | `limo-MCP/Worker_functions/Perceptions.py` |
| `worker_ai_agent/reasoning/CLAUDE.md` | `limo-MCP/Worker_functions/Reasonings.py` |
| `worker_ai_agent/action/CLAUDE.md` | `limo-MCP/Worker_functions/Actions.py` |

## 1. 읽을 것

1. @docs/status.md 의 갭·결함 표 — **건드릴 모듈의 G-*/F-* 를 먼저 확인**
2. 해당 컴포넌트 `CLAUDE.md`
3. @docs/conventions.md §2(의존성 주입) §4(에러 처리) §6(동시성)

## 3. 모듈별 필수 검증

### (a) Perception — `Perceptions.py`

| # | 검증 | 왜 |
|---|---|---|
| HW-1 | **`msg.encoding` 분기가 있는가.** `rgb8`/`bgr8`/`rgba8`/`mono8`/`16UC1`을 각각 넣고, 미지원 인코딩에서 **예외 대신 `None` + `reason`** 을 반환하는지 | 현재 무검증 `reshape`. 콜백 예외가 `rclpy.spin` 스레드를 죽여 **카메라뿐 아니라 Nav2 액션 콜백까지 전부 정지**한다 (F-1) |
| HW-2 | **콜백에서 예외가 새어나가지 않는가.** `ros2 topic pub /camera/image_raw ... '{encoding: "mono8", ...}'` 발행 후 `get_status`가 계속 응답하는지 | 〃 |
| HW-3 | **`msg.step != width*3`**(행 패딩) 프레임에서 이미지가 기울어지지 않는가 | 〃 |
| HW-4 | **신선도.** `get_latest_frame`이 `age_sec`를 함께 반환하고 임계 초과 시 `None`+`reason="stale"`을 주는가. 카메라 노드를 `kill` 한 뒤 `detect_objects`가 **빈 검출 + stale 사유**를 내는지 | 현재 카메라가 죽어도 옛 사진으로 **"할머니 정상"을 계속 보고**한다 (F-3) |
| HW-5 | **프레임 pinning(G-1).** 링버퍼를 넣었다면 `PersonScan` hit의 `frame_id`로 `check_object_state`를 호출해 **그 프레임이 실제로 돌아오는지** 왕복 확인 | 지금은 1프레임만 지나도 `"no frame available"` |
| HW-6 | **`pose`(G-2).** TF(`map`←`base_link`)를 프레임에 스탬프했는가 | Report의 `observation.pose`를 채울 수 없다 |
| HW-7 | `create_subscription` 반환 핸들을 보관하고 해제 경로가 있는가 | 구독 해제 불가 |
| HW-8 | `np.frombuffer` 결과는 **read-only**다. 쓰기가 필요하면 `.copy()` | in-place 그리기 시 `ValueError` |

### (b) Reasoning — `Reasonings.py`

**이 저장소에서 유일하게 하네스 없이 단위 테스트가 되는 모듈이다. 회귀 방어선으로 삼는다.**

| # | 검증 | 왜 |
|---|---|---|
| HW-9 | **YOLO 동시성.** `_yolo_model` 초기화에 락이 있는가. `detect_objects`를 8스레드에서 동시 100회 호출해 결과가 뒤섞이지 않고 예외도 없는지 | 호출 경로 3개가 전부 다른 스레드인데 락이 없다. 가중치 이중 로딩 가능 |
| HW-10 | **풀 포화.** 추론 시간보다 빠르게 20회 연속 호출한 뒤 21번째가 **정상 응답으로 복귀**하는지 | `future.cancel()`이 없고 큐 상한도 없어 영구 고착된다 |
| HW-11 | **예외 계약.** `detect_fn`을 `raise RuntimeError`로 주입해 **MCP 에러가 아니라 dict가 반환**되는지 | 현재 `except FutureTimeoutError`만 잡아 ImportError·CUDA 에러가 계약을 뚫는다 |
| HW-12 | **종료.** 추론 중 SIGTERM을 보내고 5초 내 종료되는지 | `_pool.shutdown()`이 없어 인터프리터 종료가 블록된다 |
| HW-13 | **증거 체인 (가장 중요).** 가짜 `frame_source`(3프레임) + 가짜 `detect_fn`(2번째만 person)으로 `start_person_scan` → hit → **hit의 `frame_id`와 `bbox`로 크롭 이미지가 나오는지** | 지금은 반드시 `"no frame available"`. **시나리오 1의 결론부** |
| HW-14 | `PlanFn` 계약이 `yaw` / `yaw_deg` 중 하나로 통일됐는가 | 주석대로 `yaw`를 채우면 조용히 무시되고 0도가 된다 |
| HW-15 | PersonScan을 노출한다면: `hz` 상한 검증, `stop()` 없이 GC될 때 스레드가 남지 않는지 | `hz=1000`이면 CPU를 태우는 핫루프 |

### (c) Action — `Actions.py`

| # | 검증 | 왜 |
|---|---|---|
| HW-16 | **입력 검증.** `navigate_waypoints([{"x":1,"y":0}])`(정수), `[{"y":1}]`, `["kitchen"]`, `[]`, `[{}]`를 차례로 호출해 **매번 즉시 사유가 담긴 dict**가 오고 그 후 `get_status`가 정상인지 | 현재 정수 하나로 시퀀스 스레드가 조용히 죽고 `get_status`가 영원히 거짓말한다 (F-4) |
| HW-17 | **스레드 예외 격리.** `run()` 전체가 `try/except`로 감싸여 `sequence_result`에 에러가 남는가 | 〃 |
| HW-18 | **goal_id 가드.** goal A 전송 → 즉시 `cancel()` → 곧바로 goal B 전송 → **A의 결과 콜백 도착 후에도 `_goal_handle`이 B를 가리키고 `status`가 `navigating`인지** | stale 콜백이 새 goal의 핸들을 파괴한다 (G-5) |
| HW-19 | **수락 타임아웃 누수.** Nav2 응답을 인위적으로 6초 지연시키고, 타임아웃 반환 후 **로봇이 실제로 움직이지 않는지 `/odom`으로 확인** | **안전 항목.** 현재 로봇은 달리는데 핸들이 없어 `cancel()`로 못 멈춘다 (F-2) |
| HW-20 | **`cancel()`이 항상 멈추는가.** `idle`·`navigating`·`rejected`·타임아웃 직후 4개 상태에서 각각 호출해 `/cmd_vel`이 0이 되는지 | 〃 |
| HW-21 | **시간축.** 타임아웃이 `node.get_clock()`(sim time) 기준인가, 아니면 RTF를 반영해 충분히 큰가. `use_sim_time:=true`에서 10 m 이동이 타임아웃 없이 완주하는지 | 120초 벽시계 = RTF 0.04에서 sim 5초 ≈ 1.3 m. **모든 내비게이션이 실패로 보고**된다 (F-5) |
| HW-22 | **상태 보호.** `status`/`last_goal`/`_goal_handle`/`sequence_*`가 하나의 락으로 묶였는가. `is_running_sequence` 체크와 스레드 시작이 **같은 락 안**인가 | 3개 스레드가 무보호 공유. TOCTOU로 시퀀스 2개가 동시에 붙을 수 있다 |
| HW-23 | **yaw.** `prev_xy is None`일 때 0도로 떨어지지 않고 "현재 헤딩 유지" 또는 "명시 필수"인가 | 단일 목표는 항상 맵 +x축을 보고 정지한다 |
| HW-24 | `pose.header.stamp`를 채웠는가 | 이동 프레임 사용 시 엉뚱한 위치로 간다 |
