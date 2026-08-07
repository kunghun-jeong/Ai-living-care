# API 스펙 — MCP tool

> **HTTP API는 없다.** 이 시스템의 유일한 외부 인터페이스는 MCP tool이다.
> 정본: `worker_ai_agent/limo-MCP/MCP_server/MCP_server.py` (`@mcp.tool()` 데코레이터)
> 이 문서를 고치면 반드시 코드와 대조한다. 반대도 마찬가지다.

## 접속

| 항목 | 값 |
|---|---|
| 트랜스포트 | **stdio** (`mcp.run(transport="stdio")`) |
| 서버 이름 | `limo-worker` |
| SDK | `from mcp.server.mcpserver import Image, MCPServer` — **mcp ≥ 2.0 전용** |
| 기동 | 클라이언트가 `MCP_server.py`를 서브프로세스로 실행 (`StdioServerParameters`) |

> ⚠️ **mcp 1.x에는 `mcp.server.mcpserver` 모듈이 없다** (1.x는 `mcp.server.fastmcp`).
> `requirements.txt`에 하한이 없어 1.x가 잡히면 서버가 import 단계에서 죽는다.
> 하한 고정 필요: `mcp[cli]>=2.0,<3`.

## tool 6종 (현재 노출된 전부)

### `plan_and_navigate(x: float, y: float, frame: str = "map", yaw_deg: Optional[float] = None) -> dict`

목표 좌표까지 경로를 계획하고 이동을 시작한다. **비동기** — 즉시 반환하고 `get_status`로 폴링한다.

```json
{"started": true}
{"started": false, "reason": "invalid goal"}
{"started": false, "reason": "nav2 action server unavailable"}
{"started": false, "reason": "a goal sequence is already in progress"}
{"started": false, "reason": "empty waypoint list"}
{"started": false, "reason": "waypoint[0] has non-numeric coordinate: ..."}
```

**Nav2가 없으면 `started: false`가 즉시 나온다.** 예전에는 `started: true`를 주고 백그라운드에서 실패해 호출자가 알 방법이 없었다 (F-49).

- `_plan_fn`은 목표를 **검증만** 하고 그대로 웨이포인트 1개로 돌려준다. 실제 전역 경로계획은
  Nav2의 `NavigateToPose`가 내부적으로 수행한다.
- ⚠️ 웨이포인트가 1개이므로 `prev_xy`가 없어 **`yaw_deg`를 생략하면 항상 0도(맵 +x축)를 보고 정지**한다.
- ~~시그니처가 `float = None`이라 스키마가 자기모순~~ → **해소** (2026-08-06) `Optional[float]`.

### `navigate_waypoints(waypoints: list) -> dict`

웨이포인트 리스트를 순서대로 이동한다. **순찰 시나리오의 진입점.**

```python
[{"x": 1.0, "y": 0.0, "frame": "map", "yaw_deg": 90.0}, ...]   # frame·yaw_deg 선택
```

- `yaw_deg` 생략 시 이전 → 현재 방향으로 자동 계산. 첫 점은 0.0.
- `list` bare 어노테이션이지만 **스레드를 띄우기 전에 `validate_waypoints()`가 검사한다** (F-4 해소).
  정수 좌표는 float으로 강제 변환하고, 형식·NaN·필수 키 누락은 `started: false` + 사유로 거부한다.
  시퀀스 스레드에도 `try/except`가 있어 예외 시 goal을 취소하고 `sequence_result.reason`에 남긴다.

### `get_status() -> dict`

```json
{
  "status": "navigating",
  "last_goal": {"x": 1.0, "y": 0.0, "frame": "map", "yaw_deg": 0.0},
  "sequence_progress": {"index": 0, "total": 1},
  "sequence_result": {"completed": 1, "total": 1, "interrupted": false, "reason": "completed"},
  "camera": {"have_frame": true, "age_sec": 0.31, "stale": false, "stale_after_sec": 2.0,
             "received": 412, "dropped": 0, "last_error": null, "buffered": 30},
  "detector_error": null
}
```

**`status` 열거값 6종**: `idle` · `navigating` · `rejected` · `cancelled` · `succeeded` · `failed`

> ⚠️ `Scenarios/send_goal.py`는 `succeeded`/`failed` **2종만** 탈출 조건으로 검사한다.
> Nav2 미기동(`idle`) · goal 거부(`rejected`) · 120초 초과(`navigating` 유지) 시 **에러 없이 무한 루프**한다.

### `get_camera_snapshot() -> list | dict`

최신 프레임을 JPEG으로 반환한다.

```python
[ '{"frame_id": "f_47", "stamp": 1234.5}', Image(data=..., format="jpeg") ]   # 성공
{"image": None, "reason": "no frame available yet"}                           # 실패
```

- 최대 512px로 리사이즈(`CROP_MAX_PX`), JPEG quality 85.
- ⚠️ **성공과 실패의 반환 타입이 다르다**(list vs dict). `capture_and_detect.py`가 실패를 감지하지 못하고
  파일을 안 만든 채 exit 0으로 끝난다.
- ⚠️ **프레임 신선도 검사가 없다.** 카메라가 죽어도 마지막 프레임을 무기한 "최신"으로 반환한다.

### `detect_objects(min_conf: float = 0.4) -> dict`

최신 프레임에서 YOLO 검출.

```json
{"frame_id": "f_47", "detections": [{"class": "person", "conf": 0.87, "bbox": [x1,y1,x2,y2]}]}
{"detections": [], "reason": "no frame available yet"}
```

- 모델 `yolov8n.pt`, 첫 호출 전 서버 기동 시 워밍업.
- ⚠️ 신선도 검사 없음 — **카메라가 죽어도 옛 프레임에서 사람을 계속 검출**한다.
  돌봄 로봇에서 가장 위험한 무음 실패 경로.

### `cancel() -> dict`

진행 중인 목표/시퀀스를 취소한다.

```json
{"cancelled": true}
{"cancelled": false, "reason": "no active goal"}
```

- goal 수락이 5초를 넘겨 포기한 뒤 Nav2가 늦게 수락하면 **그 콜백이 즉시 취소를 보낸다** (F-2 해소).
- 완주 타임아웃(120초, **노드 시계** 기준)에 걸려도 goal을 취소한다 (F-48 해소). 예전에는 감시만
  포기해 로봇이 계속 달렸다.
- `cancel()` 사유는 항상 `interrupted` 하나다. 예전에는 타이밍에 따라 `cancelled`/`failed`로 갈렸다 (F-46 해소).

## 미노출 — 구현은 있으나 tool이 아닌 것 (G-3)

`ReasoningModule`에 있으나 `@mcp.tool()`이 붙지 않아 외부에서 호출 불가:

| 메서드 | 용도 |
|---|---|
| `start_person_scan(hz, min_conf, stop_on_hit)` | 1 Hz 배경 사람 탐지 루프 시작 |
| `wait_for_person(timeout)` | 발견까지 블로킹 대기 |
| `get_scan_status()` | 스캔 상태 조회 |
| `stop_person_scan()` | 스캔 정지 |
| `check_object_state(object_class, frame_id, min_conf=0.5)` | 대상 영역 크롭 JPEG 반환 (**증거 이미지**). `min_conf` 미만은 이미지 대신 사유를 돌려준다 (F-47) |

**시나리오 1("할머니 괜찮은지 확인")의 탐색·판정 경로 전체가 여기 있다.**

> ⚠️ 노출 시 주의: `wait_for_person`은 최대 30초 블로킹이다. stdio 서버 tool로 그대로 노출하면
> 서버 루프가 멈춘다. 비동기화 또는 폴링 방식으로 바꿔야 한다.
> `get_scan_status()`는 스캔 유무에 따라 **반환 스키마가 다르다**.

## 미구현 — 문서·시나리오가 참조하지만 없는 것 (G-4)

`Scenarios/check_obj_state.json`이 참조하나 코드에 없다:
`look_around` · `is_looking_around` · `interrupt_look_around`

> 게다가 이 JSON DSL(`poll_until_match`/`branch`/`$input.x` 치환)을 **해석하는 실행기가 저장소에 없다.**
> `check_object_state`에 넘기는 `detections` 인자도 시그니처에 없다. **현재 실행 불가한 사문서.**

## Phase 0에 추가되어야 할 A2A 최소 집합

현재 tool 6종은 **전부 L4(함수 호출) 수준**이다. IF-4 종단점이 되려면 L2 정책을 받는 층이 필요하다.

```
server/discover                  → 프로토콜 버전·능력·정체성 (= Agent Card 코어)
resources/read agentcard://self  → 확장 Agent Card
tools/call execute_policy        → L2 정책 수락 → {task_id, accepted, reject_reason?}
tools/call get_task_report       → 상태 + 최종 Report
tools/call cancel_task           → 취소
```

기존 6종은 디버깅·회귀 테스트용으로 남긴다. 상세는 `interfaces/if04_secure_a2a_channel/CLAUDE.md`.

## 실패 시 반환에 반드시 있는 것 (2026-08-06)

「조용히 잘못 보고하는 것이 요란하게 실패하는 것보다 위험하다」를 반환 스키마로 옮긴 것:

| 상황 | 예전 | 지금 |
|---|---|---|
| 카메라가 죽음 | 옛 사진을 정상 반환 | `get_camera_snapshot` → `{"image": null, "reason": "camera frame is stale", "camera": {...}}` |
| YOLO 로딩 실패 | 조용히 기동, 첫 판정에서 터짐 | `get_status.detector_error` 에 사유, `detect_objects` 가 즉시 사유 반환 |
| Nav2 부재 | `{"started": true}` | `{"started": false, "reason": "nav2 action server unavailable"}` |
| 스캔 중 카메라 정지 | `found: false` (=「없음」으로 읽힘) | `{"found": false, "conclusive": false, "reason": "camera stopped producing frames ..."}` |
| 저신뢰 오탐 | 크롭 이미지를 증거로 반환 | `{"image_jpeg": null, "reason": "confidence 0.08 < 0.50 — not used as evidence"}` |
| 크롭 실패 | 방 전체 사진으로 조용히 대체 | `{"image_jpeg": null, "reason": "crop failed for detected bbox"}` |

**`found: false` 는 `conclusive` 와 함께 읽어야 한다.** `conclusive: false` 는 「없다」가 아니라 「못 봤다」다.
