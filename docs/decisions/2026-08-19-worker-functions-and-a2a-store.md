# 2026-08-19 · Worker에 nav2_move/camera_stream/yolo_reasoning wrapper + 두 번째 MCP 서버 + A2A 수신·저장 서버를 추가한다

> **정본 반영** `worker_ai_agent/action/CLAUDE.md` · `worker_ai_agent/perception/CLAUDE.md` ·
> `worker_ai_agent/reasoning/CLAUDE.md` · `worker_ai_agent/mcp_server/CLAUDE.md` ·
> `worker_ai_agent/mcp_server/data/CLAUDE.md` · `worker_ai_agent/CLAUDE.md` · `SOT.md`(D-21) ·
> `interfaces/if04_secure_a2a_channel/CLAUDE.md` · `CLAUDE.md`(9번째 줄) · `.gitignore`

## 왜

Manager 쪽은 `manager_ai_agent/a2a_client/a2a_client.py`(2026-08-18, 실험·미승인, 표준
A2A/HTTP+JSON-RPC 2.0)가 이미 동작하지만, 지금까지 말을 걸 수 있는 상대는
`dev_mock_worker_agent.py`라는 **가짜** Worker뿐이었다. 그 파일 docstring이 스스로 "팀원이
Worker AI Agent를 별도로 설계·구현할 예정"이라고 적어뒀다 — 이 결정이 그 실물이다.

동시에 Worker 쪽 `action/`·`perception/`·`reasoning/`·`mcp_server/`는 지금까지 규범
(CLAUDE.md)만 있고 코드가 0줄이었다. `mcp_server/CLAUDE.md`가 이미 "sys.path로
action/perception/reasoning을 추가해 모듈명 그대로 import한다 — 패키지화는 Phase 1
정리 항목"이라고 이 이행을 예고해뒀다.

## 무엇을 추가했나

| 경로 | 역할 |
|---|---|
| `worker_ai_agent/action/nav2_move.py` | `ActionModule` 인스턴스를 받는 순수 함수 wrapper (`nav2_move`·`nav2_move_waypoints`·`nav2_cancel`·`nav2_status`) |
| `worker_ai_agent/perception/camera_stream.py` | `PerceptionModule` 인스턴스를 받는 순수 함수 wrapper (`camera_stream`) |
| `worker_ai_agent/reasoning/yolo_reasoning.py` | `ReasoningModule` 인스턴스를 받는 순수 함수 wrapper (`yolo_reasoning`) |
| `worker_ai_agent/mcp_server/worker_mcp_server.py` | 위 3개를 쓰는 두 번째 stdio MCP 서버(`"limo-worker-fn"`, 노드 `limo_worker_functions_gateway`) |
| `worker_ai_agent/mcp_server/a2a_server.py` | 표준 A2A HTTP 서버 — `dev_mock_worker_agent.py`의 실제 대체품, 수신+저장만 |
| `worker_ai_agent/mcp_server/task_store.py` | `a2a_server.py`가 받은 task를 `data/{task_id}.json`으로 원자적 저장 |
| `worker_ai_agent/mcp_server/data/` | 위 저장소 — 런타임 전용, 커밋 안 함 |

## (a) wrapper가 순수 함수 + 인스턴스 주입 패턴인 이유

`worker_ai_agent/reasoning/`의 `ReasoningModule`이 이 저장소에서 "가장 잘 분리된 설계"로
칭찬받는 이유는 ROS2 인스턴스를 생성자로 주입받고 백엔드 미주입 시 no-op으로 동작하기
때문이다(`reasoning/CLAUDE.md`). 새 wrapper 3개도 이 패턴을 따른다 — `action/perception/
reasoning` 안의 새 코드는 ROS2를 직접 import하지 않고, 이미 구성된 `ActionModule`/
`PerceptionModule`/`ReasoningModule` **인스턴스를 인자로 받는다.** rclpy 초기화·노드
생성·`sys.path` 등록은 전부 `worker_mcp_server.py`(합성 루트) 한 곳에만 있다.
`limo-MCP/**`는 **한 줄도 고치지 않았다** — D-17(담당 연구원 소유) 미위반.

## (b) 왜 `MCP_server.py`를 고치지 않고 두 번째 서버를 새로 만들었는지

`MCP_server.py`는 D-14 원본 보존 대상이고, `docs/api-spec.md`의 "정본: MCP_server.py"
선언과 `anchor.py` A2가 그 파일에서 파싱한 tool 6종(`plan_and_navigate`·`navigate_waypoints`·
`get_status`·`get_camera_snapshot`·`detect_objects`·`cancel`)을 하드코딩으로 검사한다.
새 tool을 그 파일에 얹으면 원본을 건드리는 셈이라, 별도 프로세스(`worker_mcp_server.py`,
다른 노드 이름·다른 서버 이름)로 분리했다 — 두 서버를 동시에 띄워도 충돌하지 않는다.

## (c) `a2a_server.py`가 구현하는 계약

`manager_ai_agent/a2a_client/CLAUDE.md`가 이미 공개한 "팀원이 Worker A2A 서버를 만들 때
맞춰야 할 계약" 표(`message/send`·`tasks/get`·`tasks/cancel`, JSON-RPC 2.0, Agent Card
`GET /.well-known/agent-card.json`, 포트 9000)를 그대로 구현했다 — `dev_mock_worker_agent.py`가
흉내만 내던 것의 실물이다. 차이는 저장이 **파일 기반으로 영속**된다는 것(mock은 프로세스
재시작하면 사라지는 인메모리 dict였다).

## (d) TaskState `completed` 선택 근거

`a2a_client.py`의 `send_to_worker()`는 `state == "completed"`만 성공 신호로 본다. 저장에는
성공했는데 `failed`/`rejected`를 돌려주면 Manager 쪽에서 오탐이 난다. `interfaces/
if04_secure_a2a_channel/CLAUDE.md`의 TaskState↔report.status 표 자체가 `COMPLETED`를
`completed`/`abnormal`/`not_found`/`partial` 여러 실제 결과로 팬아웃시키는 걸 이미 정상으로
본다 — 즉 A2A wire state는 원래 report의 실제 내용보다 거칠어도 된다는 설계다. 그래서
`message/send`는 저장 성공 시 `completed`를 반환하고, "저장만 했고 미실행"이라는 사실은
응답의 `artifacts` 텍스트(`"stored (미실행 — execute_policy 미착수, G-3)"`)에 정직하게
남긴다. `tasks/cancel`도 같은 이유로 실행 중인 게 없으므로 상태를 `canceled`로 덮어쓰지
않고 그대로 반환한다.

## (e) 스코프 경계 — 수신+저장까지, 실행은 별도

받은 정책을 L3로 번역해 실제로 `nav2_move` 등을 실행하는 것(`execute_policy`)은 Worker AI
Core의 일이고, `worker_ai_core/CLAUDE.md`가 여전히 Phase 0 미착수로 남겨둔 영역이다
(갭 `G-3`, 작업 0-5·0-6). 이번 결정은 그 경계 앞까지만 — Manager가 보낸 명령을 안전하게
받아서 파일로 남기는 것까지가 스코프다.

## 검증 (1회 실측)

Windows에서 ROS2 없이: `a2a_server.py`(9000)를 띄우고 `a2a_client.py`를 단독 실행 —
`discover`가 실제 카드(`"limo-worker-a2a"`)를 반환하고 `send_to_worker`가
`{"ok": true, "state": "completed"}`를 반환함을 확인. `data/<task_id>.json`에
`{axis, evaluation, sequence}` 페이로드가 그대로 저장됨을 확인. 서버를 재시작한 뒤에도
같은 task_id를 `tasks/get`으로 조회 가능함을 확인(파일 기반 영속성 — mock과의 차이).
서버를 끈 채로 재실행하면 `{"ok": false, ...}`가 정상 반환됨을 확인.

`worker_mcp_server.py`(ROS2 의존)는 실물 LIMO 환경에서 별도로 검증한다 — 이 저장소의
모든 이전 검증은 Gazebo 시뮬뿐이었고 이제부터 실물로 전환하므로, U-12(ROS2 배포판
불일치 — 코드·시뮬은 Jazzy, 실물 LIMO는 Humble로 확인됨(2026-08-19))·G-2(카메라 인코딩
rgb8 가정, 실물은 보통 bgr8)를
먼저 확인해야 한다 — 둘 다 이 결정이 고치는 범위 밖(D-17)이고 `limo-MCP`의 기존 알려진
갭이다.
