# MCP 대본 + RCP 논문 정리

`MCP 대본.docx`와 `Robot Context Protocol (RCP): A Runtime-Agnostic Interface for Agent-Aware Robot Control` 논문(arXiv:2506.11650, Lee & Lau, IEEE RA-L preprint) 이 두 자료만 가지고 정리한 문서. 슬라이드 9에서 이 논문을 직접 인용하며 "우리 시스템 구조: Manager-Worker" 설계 아이디어를 얻었다고 밝힘.

## 1. MCP 대본.docx 정리

### 1.1 왜 MCP로 갔는가 — 기각된 접근: world model 기반 end-to-end 강화학습
- 로보틱스의 Perception-Judgment-Action을 하나의 강화학습 정책으로 end-to-end 학습시키는 논문들을 조사함.
- 그 논문들은 **world model latent space 위에서 단일 목표**를 다루도록 설계돼 있음 (RSSM 기반 비지도 학습으로 미래 상황을 예측하는 구조).
- 문제: 팀이 필요로 하는 서브골("카메라 활성화", "사물 인식 수행" 등)은 성격이 서로 다른 **다수의 이산적 명령**이라, world model이 학습하는 "도달 가능한 미래 상태"라는 단일 metric으로는 환원이 안 됨 → 하나의 강화학습 정책으로 다루기엔 샘플 복잡도·보상 설계 양쪽에서 비현실적이라고 판단.
- 추가로: 비지도학습에서는 encoding을 아무리 orthonormal하게 만들어도 decoding 결과가 disentangled인지 entangled인지 데이터만으로는 알 수 없다는 논문도 참고 — world model latent state가 목표별로 깔끔히 분리된 표현을 준다는 보장이 없다는 근거로 씀. 목표들을 서로 분리하기 어려운 환경에서는 goal의 의미 자체가 퇴색된다고 판단해서 이 접근을 포기.
- → **결론: edge에 AI(강화학습 정책)를 직접 넣는 걸 포기**하던 중, 지도교수가 MCP를 써보라고 제안 → 조사 시작.

### 1.2 MCP란
- 초기 설계 방향: "함수를 분리하고 MCP가 적절한 function call을 하게 하자."
- 구조: Client가 transport layer를 통해 server에 request를 보내고, server는 response를 보냄.
- Client 예시: Claude 같은 AI. Server 예시: GitHub 같은 앱들.
- "LLM이 외부 도구·데이터소스와 표준화된 방식으로 통신하는 프로토콜." 클라이언트는 서버로부터 도구를 요청하고 서버는 응답.
- Orchestrator가 하위 agent를 관리하는 구조도 있음 — LIMO 여러 대를 쓴다면 LLM에 orchestrator를 둬서 활용 가능하다고 판단.

### 1.3 우리 시스템 구조: Manager-Worker
- **RCP 논문 구조가 자신들 시스템과 유사해서 아이디어를 얻음** (본 문서 2절 참고).
- 실제 구현:
  - Protocol: JSON-RPC 2.0
  - 전송 방식: stdio
  - Manager = MCP client 역할 (Claude API 기반 판단, 추후 RAG로 개선 예정)
  - Worker = MCP server 역할 (LIMO 로봇)
  - Manager가 stdio input으로 요구 → perception/reasoning/action 함수가 output으로 응답 → 로컬 IPC로 직결
  - Worker AI agent는 프롬프트로 설계함. **AI analyzer는 미구현** 상태.
- 구현한 함수 3종류:
  - **Perception** — 외부 데이터 획득 (카메라, 맵). 가장 최근 snapshot을 읽는 방식.
  - **Reasoning** — 판단·해석 (YOLO 객체 탐지, 경로계획). 스레드풀에서 비동기 실행.
  - **Action** — 실행 (Nav2 내비게이션, 주변 스캔 등).

### 1.4 MCP를 쓸 때의 장점 (팀이 정리한 4가지)
1. 다양한 기기·기능을 동일한 방식(같은 tool 호출 인터페이스)으로 호출 가능.
2. 각 기능을 독립적으로 교체·업그레이드 가능 (예: YOLO 모델만 바꾸기).
3. 매 tool 호출과 결과가 로그로 남아서 해석 가능 (end-to-end 블랙박스 정책과 대비됨).
4. 우려했던 "속도 느림" 문제는 stdio 전송 방식으로 해결 가능 (로컬 IPC라 네트워크 오버헤드 없음).

### 1.5 실제 구현/검증
- 데모 시나리오: **"할머니 괜찮은지 확인해줘"** — MCP 서버가 엣지에서 실제로 잘 동작하는지 확인하는 데 초점.
- MCP 서버 인스턴스를 만들고 tool을 정의하는 코드 시연: 카메라 snapshot 함수, YOLO로 탐지하는 `detect_objects` 함수.
- 시나리오 실행 코드: `call`(= MCP `tool/call`), `poll_until_match`(tool을 반복 호출하며 타겟과 일치하는 항목이 나올 때까지 반복) 두 스텝 타입 소개. 각각 "할머니 상태 확인", "look_around & detect_objects 연계"에 활용.
- 시나리오 흐름: 자연어 "할머니의 상태를 확인해줘"가 high-level policy로 변환 → worker agent가 `look_around`로 집을 돌아다니며 `detect_object`로 사람 감지 → 감지되면 `interrupt`로 `look_around` 중지 → `check_object_state`로 상태 확인.
- **MCP mock 서버**를 만들어서 (ROS2·실제 하드웨어 없이) MCP 배선 자체가 잘 되는지 독립적으로 검증함.

### 1.6 부록 — 프로토콜 세부사항
- JSON-RPC가 규정하는 메시지 양식: request/response 등. MCP는 JSON-RPC를 채택.
- 전송방식 비교: stdio는 로컬 서버에 유리, HTTP는 원격 서버에 유리. 팀의 엣지는 로컬 서버를 쓰므로 **stdio 채택**.

### 1.7 결론 & 다음 계획 (대본 원문)
> "저희는 MCP 서버의 배선이 원활하게 작동함을 확인했습니다. 앞으로는 worker function들을 구체적으로 구현하고, 이를 바탕으로 다양한 시나리오를 작성하여 시나리오가 MCP라는 프로토콜 아래서 잘 작동함을 확인할 계획입니다. 이후 잘 정리된 시나리오를 문서화하고 이를 바탕으로 데이터베이스를 구축할 계획입니다. worker ai agent는 RAG로 구현할 수 있을 것입니다."

→ 이 "worker function 구체화 + 다양한 시나리오 작성 + 검증" 단계가 `limo_slam/SESSION_HANDOFF.md`에 정리된 오늘(8/3~4) 작업(action.py의 patrol/dock/interrupt 구현, Nav2 시뮬레이션으로 실제 검증, scenario_runner.py로 시나리오 실행)임.

## 2. RCP 논문 정리

**Robot Context Protocol (RCP): A Runtime-Agnostic Interface for Agent-Aware Robot Control** — Lambert Lee, Joshua Lau (RoboStack Research Group), arXiv:2506.11650 (2025.06), IEEE Robotics and Automation Letters preprint.

### 2.1 문제의식
로봇 시스템이 점점 복잡해지면서(다양한 센서·액추에이터·연산 모듈), 특히 서로 다른 런타임 환경에 걸쳐 로봇과 인터페이스하는 게 어려워짐. 기존 통합 방식은 특정 미들웨어/메시지 전달 시스템/하드웨어 종속 구현에 대한 깊은 지식을 요구해서, 사람 개발자뿐 아니라 프로그래밍 방식으로 로봇 기능에 접근하려는 **AI 에이전트**에게도 진입장벽이 높음.

### 2.2 RCP란
경량·미들웨어-비의존적 통신 프로토콜. 로봇 시스템의 복잡도를 추상화해서, 로봇/사용자/자율 에이전트 사이에 통일되고 의미론적으로 명확한 인터페이스를 제공. 물리 로봇, 클라우드 오케스트레이터, 시뮬레이션 플랫폼까지 다양한 배포 환경을 지원.

rosbridge(ROS API를 웹 프로토콜로 노출)와 개념적으로 유사하지만, 더 엄격하게 계층화된 프로토콜 아키텍처로 차별화됨. Agent-to-robot(A2R)과 human-to-robot(H2R) 상호작용 모델을 둘 다 지원.

### 2.3 계층 구조 (핵심)
RCP는 4개 계층으로 나뉨:

1. **Adapter Layer** — 서로 다른 클라이언트 타입을 통일된 메시지 포맷으로 정규화.
   - **MCP Adapter** — LLM이 생성한 출력을 구조화된 명령 메시지로 번역 (자연어 상호작용 지원)
   - **A2A Adapter** — 에이전트 간 조율. symbolic planning 출력을 실행 가능한 태스크 시퀀스로 변환
   - **Web/Dashboard Adapter** — GUI/대시보드용 RESTful 엔드포인트 제공
   - → 새 클라이언트 타입(모바일 앱, CLI, gRPC 마이크로서비스 등)은 어댑터만 추가하면 되고 transport/core 메시지 포맷은 안 건드려도 됨.
2. **Transport Layer** — 3가지 통신 방식 지원:
   - **HTTP** — 짧은 동기 요청(데이터 조회, 서비스 호출, 설정 변경)
   - **WebSocket** — 실시간 양방향 스트리밍(연속 텔레메트리, 구독 기반 이벤트, 라이브 모니터링)
   - **Server-Sent Events (SSE)** — 경량 단방향 push (브라우저/저사양 클라이언트의 주기적 상태 알림에 적합, WebSocket 오버헤드가 불필요한 경우)
3. **Service Layer** — 최소한의 표현력 있는 연산 집합으로 프로토콜 기능을 캡슐화: **read / write / execute / subscribe** 4가지.
4. **ROS2 Interface Layer** — 위 고수준 연산을 ROS2 네이티브 구성요소(topic/service/action/parameter)로 매핑. 타입-세이프하고 스키마 기반.

부가 모듈: **Status and Monitoring Module** — 프로토콜/어댑터의 실시간 헬스, 진단 메타데이터 노출 (런타임 introspection, 자율 fault handling, 시스템 수준 오케스트레이션 지원).

### 2.4 경로 기반 주소 체계 (Path-based addressing)
로봇의 모든 기능을 의미론적 경로로 노출. 예:
- `/sensor/pose` — 위치·자세 조회
- `/action/move_to` — 목표 지점 내비게이션 실행
- `/param/speed_limit` — 속도 제약 수정
- `/service/reset_system` — 시스템 재부팅/복구

클라이언트는 `/odom`이나 `/move_base` 같은 ROS2 전용 토픽/액션명을 몰라도 됨 — `read /sensor/pose`, `execute /action/move_to`, `write /param/speed_limit`처럼 표준화된 4개 동사(read/write/execute/subscribe)만 알면 됨. 클라이언트가 하드코딩 없이 런타임에 사용 가능한 전체 경로 카탈로그를 discovery API로 조회할 수 있음 (동적 introspection).

**멀티테넌시**: `/tenant/alpha/sensor/pose`처럼 네임스페이스로 클라이언트를 논리적으로 격리 — 여러 에이전트가 동시에 제어하면서도 상태/연산/권한이 안전하게 분리됨.

### 2.5 메시지 포맷
- **Envelope**: `type`(read/write/execute/subscribe/status), `path`(대상 리소스), `id`(request-response 추적용, 특히 비동기 연산에서), `timestamp`(옵션).
- **Body**: 연산 타입에 따라 다름 (write는 data payload, read는 필터/샘플링 힌트 등).
- JSON 스키마 기반 타입 검증: primitive(int/float/bool/string), compound(array/dict/struct), time(ISO-8601/UNIX epoch), geometry(pose/twist/acceleration 등 표준 표현).
- **비동기 피드백**: `execute`/`subscribe` 연산은 상태 업데이트를 받음 — `accepted`(큐에 등록됨) → `in_progress`(실행 시작·모니터링 중) → `completed`(성공) / `failed`(에러, 진단 필드 포함). `id`로 원 요청과 매칭.
- 상태 메시지 예시: `"Command /action/move_to executed successfully."`, `"Warning: action '/navigate_to' is currently in progress; rejecting duplicate request."`, `"Command rejected --- MCP adapter is not connected to the runtime."`

### 2.6 견고성(Robustness) 기능
rosbridge에서 영감받은 프로덕션급 기능들:
- 비동기 서비스 에뮬레이션 (블로킹 호출 대신 이벤트 기반 콜백)
- 대역폭 절약을 위한 메시지 압축
- 대용량 payload(이미지, 맵 등)의 분할·재조립
- 모든 메시지에 대한 엄격한 스키마 검증
- 장시간 세션을 위한 지속적 세션 추적
- 멀티테넌트 환경을 위한 엔드포인트별 접근 제어·인증

### 2.7 향후 방향 (논문이 제시한 것)
- CBOR/Protobuf 같은 대안 인코딩으로 엣지/임베디드 환경 성능 개선
- ROS2 DDS 수준의 QoS 시맨틱 도입
- 스키마 레지스트리 표준화로 벤더 간 상호운용성 확보
- **LLM/VLM 같은 foundation model, 에이전트 플래닝 시스템과의 깊은 통합** — 고수준 목표를 자연어/symbolic reasoning을 통해 프로토콜 수준 액션으로 번역
- 블록체인 기반 접근제어, 멀티에이전트 합의 프로토콜 등 탈중앙 거버넌스

## 3. 두 자료의 연결 — 팀이 실제로 무엇을 가져오고 무엇을 다르게 했는가

| RCP | 팀의 MCP_LIMO 시스템 |
|---|---|
| Adapter Layer (MCP/A2A/Web 어댑터로 클라이언트 다양화) | Manager 하나 = Claude API 기반 MCP client (MCP Adapter 개념과 유사한 진입점) |
| Transport Layer: HTTP + WebSocket + SSE (클라우드/원격 지향) | **stdio만 사용** — "엣지는 로컬서버를 활용하기에 stdio를 채택" (RCP의 원격 지향 tri-channel 대신 로컬 IPC 하나로 단순화) |
| Service Layer: read / write / execute / subscribe (범용 4동사) | **Perception / Reasoning / Action** 3개 함수 카테고리로 분리 — RCP의 "동사(operation) 중심" 대신 "역할(role) 중심" 분류 |
| ROS2 Interface Layer (topic/service/action → 표준 경로로 추상화) | `action.py`가 사실상 이 역할 — Nav2 액션/토픽을 `navigate_to`, `look_around`, `start_patrol` 같은 tool로 감쌈 |
| Status/Monitoring Module + 비동기 accepted→in_progress→completed/failed 피드백 | `get_status`, `is_patrolling`, `is_docking` 같은 폴링형 tool로 유사한 역할 (RCP처럼 push 기반 subscribe가 아니라 pull 기반 poll) |
| 경로 기반 주소 체계 (`/tenant/alpha/...`), 멀티테넌시 | 미구현 — 지금은 로봇 1대, tool 이름이 곧 경로 |
| Adapter를 통해 LLM plan → 프로토콜 액션 번역 (향후 방향으로 제시) | 이미 이 방향으로 감 — Manager(LLM)가 자연어 지시를 tool 호출 시퀀스로 변환 |

**요약**: RCP는 클라우드/멀티테넌트/원격(HTTP·WebSocket) 지향의 범용 로봇 추상화 프로토콜이고, 팀의 시스템은 그 중 "LLM이 표준화된 인터페이스로 로봇 기능을 호출한다"는 핵심 아이디어만 가져와서 **단일 로봇·로컬 엣지 환경에 맞게 stdio 기반 MCP로 단순화**한 구현으로 볼 수 있음. RCP의 read/write/execute/subscribe라는 범용 동사 대신, 팀은 처음부터 Perception/Reasoning/Action이라는 로봇 인지 사이클에 맞춘 역할 기반 함수 분류를 채택함.
