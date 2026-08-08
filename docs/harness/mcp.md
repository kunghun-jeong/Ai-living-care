# 하네스 — MCP / A2A (IF-4)

> 대상: `worker_ai_agent/limo-MCP/MCP_server/MCP_server.py`, `Scenarios/*.py`,
> `worker_ai_agent/mcp_server/`, `manager_ai_agent/mcp_client/`, `interfaces/if04_secure_a2a_channel/`
>
> 이 문서는 **관문이 아니라 참고 노트**다. 이 영역을 처음 건드릴 때 한 번 읽는다.
> 작업 절차는 `docs/harness.md` — 앵커 갱신과 결정 로그 한 줄이 전부다. 이 문서는 MCP 고유 항목만 다룬다.

## 1. 읽을 것

1. `docs/api-spec.md` — **현재 tool 6종의 정확한 시그니처와 알려진 결함**
2. `worker_ai_agent/mcp_server/CLAUDE.md` — 규범과 U-1(SDK 버전)
3. `interfaces/if04_secure_a2a_channel/CLAUDE.md` — A2A ↔ MCP 객체 매핑, TaskState 정렬
4. 필요 시 설계 정본 §6 (A2A-over-MCP 바인딩 프로파일)

## 3. 작업 중 규칙

### stdout은 프로토콜 전용이다

stdio 트랜스포트는 stdout을 JSON-RPC에만 쓴다. **서버 코드에 `print`를 쓰지 않는다.**
로그는 `sys.stderr` 또는 ROS2 logger로. 초기화 중 stdout에 쓰는 라이브러리는
`contextlib.redirect_stdout(sys.stderr)`로 감싼다 (YOLO 워밍업이 그 예 — **지우지 말 것**).

### 타입 어노테이션이 곧 스키마다

- `list` bare 금지 → **pydantic 모델**로 아이템 스키마를 준다. 현재 `navigate_waypoints(waypoints: list)`는
  아이템 검증이 전혀 없어 정수 좌표 하나로 시퀀스 스레드가 죽는다.
- `float = None` 금지 → `Optional[float] = None`. 전자는 `{"type":"number","default":null}`인
  자기모순 스키마를 만들고 LLM이 `null`을 명시하면 호출 전체가 실패한다.

### 반환 타입을 성공·실패에서 같게 한다

`get_camera_snapshot`은 성공 시 `list`, 실패 시 `dict`를 반환해 호출자가 실패를 감지하지 못한다.
**신규 tool은 항상 같은 컨테이너 타입을 반환한다.**

### 블로킹 tool을 만들지 않는다

`wait_for_person`은 최대 30초 블로킹이다. stdio 서버 tool로 그대로 노출하면 서버 루프가 멈춘다.
장기 작업은 **즉시 핸들을 반환하고 폴링**하게 만든다 (`{task_id, accepted}` → `get_task_report`).

### 모듈 최상위에 부작용을 두지 않는다

현재 `MCP_server.py`는 import만 해도 `rclpy.init()` + 노드 생성 + YOLO 다운로드가 일어나고,
`rclpy.shutdown()`·`destroy_node()`·`_pool.shutdown()`이 하나도 없다.
**신규 코드는 `main()` 안으로 넣는다.** 기존 코드를 건드릴 기회가 있으면 함께 정리한다.

## 알아 둘 것 (함정)

`docs/harness.md` 의 공통 절차에 더해, MCP 고유 항목:

| # | 검증 | 방법 |
|---|---|---|
| HM-1 | **스키마 덤프 확인** | `tools/list` 결과를 출력해 새 tool의 파라미터 타입·default·required가 의도대로인지 눈으로 확인. `default: null` + `type: number` 조합이 없어야 한다 |
| HM-2 | **stdout 무결성** | tool 함수 안에 일부러 `print("x")`를 넣고 클라이언트가 JSON 파싱 에러 없이 동작하는지 확인 → 확인 후 제거 |
| HM-3 | **잘못된 인자 전수** | 새 tool에 정수 대신 실수, 필수 키 누락, 빈 리스트, 타입 불일치를 각각 넣고 **매번 사유가 담긴 dict가 즉시 오는지**, 그 후 `get_status`가 정상인지 |
| HM-4 | **의존 서비스 부재** | Nav2/Gazebo를 **끈 상태로** 클라이언트를 돌려 **유한 시간 안에 명확한 에러로 끝나는지.** 현재 `send_goal.py`는 무한 루프한다 |
| HM-5 | **동시 호출** | 같은 tool을 동시에 2번 호출해 두 번째가 거부되는지 (`{"started": false, "reason": ...}`) |
| HM-6 | **시나리오 JSON 대조** | tool을 추가·개명했으면 `Scenarios/check_obj_state.json`이 참조하는 이름·인자와 대조한다. 현재 이 파일은 없는 tool 3종을 참조하는 사문서다 |
| HM-7 | **왕복 스모크** | `rclpy`를 `sys.modules` 스텁으로 대체하면 ROS2 없이 서버 기동 + `initialize` + `tools/list` + `call_tool` 왕복을 검증할 수 있다. **CI에 넣으면 SDK 버전 리스크가 영구히 잡힌다** |

## 7. 알려진 함정 (재확인용)

- `mcp.server.mcpserver`는 **mcp 2.0 전용**이다. 1.x에는 이 모듈이 없다.
- `session.initialize()`는 2.0에서도 **살아 있다** — 이걸 근거로 "구 SDK"라 판단하지 말 것.
- `ClientSession`의 read timeout 기본값은 `None`이라 서버 기동이 20초 걸려도 핸드셰이크는 안 깨진다.
- `MCP_server.py:23`의 `sys.path.append`에 `abspath`가 없다. 현재는 우연히 동작한다.