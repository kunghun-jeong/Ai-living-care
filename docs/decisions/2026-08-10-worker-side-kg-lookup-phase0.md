# 2026-08-10 · Worker Reasoning이 KG를 IF-1 없이 직접 import한다 (Phase 0 임시)

> **정본 반영** `worker_ai_agent/mcp_server/CLAUDE.md` · `manager_ai_agent/knowledge_graph/CLAUDE.md` · `docs/api-spec.md`

`turn_on_air_conditioner` 시나리오가 실제로 동작하려면 "에어컨을 켤 수 있는 자리"를 좌표로
해소해야 한다. 정식 아키텍처(spec §2.3, IF-1)에서는 이 해소를 **Manager AI Core가 KG를
IF-1로 조회**해서 처리하고 Worker에는 이미 해소된 좌표만 L2/L3 정책으로 내려와야 한다.

그런데 Manager AI Core는 아직 **코드 0줄**이다(전부 규범만). IF-1이 없는 상태에서 이 계층을
먼저 만드는 것은 지금 시나리오 하나를 돌리는 데 필요한 범위를 넘는다. 그래서 임시로
**Worker의 `ReasoningModule`이 `manager_ai_agent/knowledge_graph/kg.py`를 `sys.path` 조작으로
직접 import**해서 `resolve_location` MCP tool로 노출했다.

## 되돌릴 조건

Manager AI Core(0-2)와 IF-1이 구현되면:
1. `resolve_location` tool을 Worker에서 제거하거나 내부 전용으로 낮춘다.
2. 장소 해소는 Manager AI Core가 IF-1로 KG를 조회해 L2 정책에 **이미 해소된 좌표**를 실어
   Worker로 내려보내는 방식으로 되돌린다.
3. `MCP_server.py`의 `sys.path.append(...manager_ai_agent/knowledge_graph)` 줄과
   `from kg import KnowledgeGraph` import를 제거한다.

## 남는 제약

`entities.json`에 등록된 것은 지금 **3건**이다: `dining_area`·`upper_left_room`(실측 좌표),
`air_conditioner`(`tools/limo-patrol-viz/WORLD.md` §2가 확인한 `AirconditionerB`의 소속 구역
접근점 — 가구 자체 좌표가 아니라 그 구역에서 가장 트인 지점이다). 그 외 이름은
`resolve_location`이 좌표를 지어내지 않고 `{"resolved": false, "reason": "unknown location: ..."}`을
돌려준다 — 침실의 `AirconditionerA`가 그 예로, 맵이 침실을 미탐색이라(67.5%) 등록을 보류했다.
침실 시나리오가 필요해지면 `slam_toolbox`로 맵을 다시 뜬 뒤 등록해야 한다.
