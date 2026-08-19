# Worker AI Agent

> **역할** L2 정책을 받아 L3 로 번역하고 수행한 뒤 Report 를 되돌린다
> **상태** Phase 0 · 구현체 동작 — 프레임워크 계층 미착수
> **읽을 절** spec **§2.2**(Worker 컴포넌트) — 그 외 절은 열지 않는다
> **정본** 구조 `SOT.md` · spec §2.2

Manager가 만든 **고수준 정책(L2)** 을 받아 디바이스별 **저수준 정책(L3)** 으로 번역하고,
실제로 수행한 뒤 결과를 Report로 되돌린다.

## 두 층으로 구성된다

**① 프레임워크 컴포넌트** — SOT가 정의하는 규범 계층. 설계·인터페이스·갭이 각 `CLAUDE.md`에 있다.

| 디렉터리 | 정규화 명칭 | 상태 |
|---|---|---|
| `worker_ai_core/` | Worker AI Core (WAC) | 미착수 |
| `worker_ai_analyzer/` | Worker AI Analyzer (WAA) | 미착수 |
| `worker_ai_management_system/` | Worker AI Management System (WAMS) | 미착수 |
| `perception/` | Perception Function (PF) | 규범 + 실험 wrapper(①, `camera_stream.py`) — limo-MCP 구현은 ② |
| `reasoning/` | Reasoning Function (RF) | 규범 + 실험 wrapper(①, `yolo_reasoning.py`) — limo-MCP 구현은 ② |
| `action/` | Action Function (AF) | 규범 + 실험 wrapper(①, `nav2_move.py`) — limo-MCP 구현은 ② |
| `mcp_server/` | A2A Server + Agent Executor | 규범 + 실험 코드(①, `worker_mcp_server.py`·`a2a_server.py`) — limo-MCP 구현은 ② |

**② Worker 구현체** — 디바이스별 실현체. **원본 보존 (D-14).**

| 디렉터리 | 디바이스 | 상태 |
|---|---|---|
| `limo-MCP/` | LIMO (현재 turtlebot3 waffle로 시뮬) | **동작** |

다중 Worker로 확장하면 `refrigerator/`, `smart_tv/`가 형제로 늘어난다.

> **왜 나누는가**: 프레임워크는 디바이스와 무관해야 하고(P-2), 구현체는 팀이 이미 돌리고 있는
> 원본이라 손대지 않아야 한다. 규범은 ①에, 코드는 ②에 둔다.
> **컴포넌트 CLAUDE.md가 규범이고, 그 구현이 어디 있는지도 거기 적혀 있다.**

## 인터페이스

**IF-4**(↔MAC, `mcp_server/`) · **IF-5**(→PF/RF/AF) · **IF-6**(←PF/RF/AF) · IF-3(↔WAMS) · IF-7(↔MAMS, P2)

## 주의

**`ReasoningModule`은 ROS2에 의존하지 않는다.** 백엔드를 생성자로 주입받고 미주입 시 no-op으로 동작해
로봇 없이 단독 테스트가 가능하다. **이 저장소에서 가장 잘 분리된 설계이므로 훼손하지 말 것.**
