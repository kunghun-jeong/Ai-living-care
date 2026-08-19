# Knowledge Graph (KG)

> **역할** 사용자·공간·디바이스의 관계와 능력을 보유한다 — 접근은 IF-1 경유
> **상태** Phase 0 · 미착수(정본 JSON 룩업) · 갭 `G-6` · 작업 `0-10` · **Neo4j 그래프 파일 있음(실험·미승인, 2026-08-18)**
> **읽을 절** spec **§3.1**(IF-1 계약) · **§2.3**(KG↔IAD 구분) — 그 외 절은 열지 않는다
> **정본** 구조 `SOT.md` §2.1 · 스키마 `contracts/`

사용자·공간·디바이스의 **관계와 능력**을 보유한다 — 누가 무엇을 할 수 있는가.
`intent_audit_database/`(감사 이력)와는 별개다 (spec §2.3). 접근은 **IF-1 경유**.

## Phase 0: JSON 룩업으로 간소 구현 (D-6)

인터페이스 계약을 **고정**해 후일 그래프DB로 무중단 교체한다.

```json
{
  "entities": {
    "grandma":     {"type":"person","role":"elder","usual_place":"living_room"},
    "living_room": {"type":"space","map_frame":"map","pose":{"x":…,"y":…,"yaw":…}},
    "LIMO_1":      {"type":"device","skills":["navigate","person-scan","state-check"],
                    "sensors":["camera","lidar"],"agent_uri":"stdio://limo_1"}
  },
  "phrase_bindings": { "grandma": [...], "check": [...], "is okay": [...] }
}
```

## G-6 — 채워야 할 공백

현재 코드에 `list_locations` / `locations.json`이 **없다.** `plan_and_navigate`는 좌표만 받는다.
L2의 `<location-label>living_room`을 좌표로 해소할 경로가 없다.
**좌표 ↔ 방 이름 매핑을 만드는 것이 곧 G-6 해소이자 `entities.<space>` 채우기다** (작업 0-10).

## 주의 (중요)

- 저장소에서 좌표에 **의미 있는 이름이 붙은 것은 두 개뿐**이다:
  `(8.10, 1.71)`="식탁 구역", `(-7.77, 0.56)`="좌상단 방" (`tools/limo-patrol-viz/`).
  **나머지 5개 순찰 좌표에는 방 이름이 부여된 바 없다. 임의로 붙이지 말 것.**
- docx의 `locations.json`(`living_room = (1.2, 0.4)`)은 **별개 출처이며 small_house 좌표계와 무관하다.**
- `phrase_bindings`는 데모용 지름길이다. Phase 1에서 그래프 순회 + 임베딩 유사도로 대체하고
  이 표는 회귀 테스트 정답셋으로 전환한다.

## Neo4j 그래프 파일 (실험 · 미승인 — 위 정본 JSON 룩업과 별개)

`manager_ai_core/kg_mapping/graph_retrieval.py`(실험 파이프라인, `docs/decisions/
2026-08-18-graph-inference-distribution.md`)가 읽는 그래프의 **원본**을 2026-08-18에 이
폴더로 들여왔다. **스키마가 위 D-6 JSON과 다르다** — 여기는 `Axis/Device/Function/State/
AxisKnowledge`, D-6 JSON은 `person/space/device`(grandma·living_room·LIMO_1). 하나를
다른 하나로 대체할지 공존시킬지는 여전히 TODO(확인 필요) — `kg_mapping/CLAUDE.md`
「기존 KG와의 관계」참조.

| 파일 | 역할 |
|---|---|
| `livingcare_graph_v2.cypher` | 그래프를 **처음부터 다시 만드는** Cypher 스크립트(준상님 작성, 저장소 밖 개인 작업 폴더에서 복사). Neo4j Browser에 그대로 붙여넣으면 재현된다 |
| `export_neo4j_snapshot.py` | 지금 **실제로 떠 있는** 그래프를 JSON으로 통째로 내보내는 스크립트. `.cypher`를 돌린 뒤 수동으로 고친 값이 있어도 그 변경분까지 잡힌다 |
| `neo4j_snapshot.json` | 위 스크립트로 2026-08-18에 뜬 스냅샷 — 노드 362개·관계 666개(1회 실측) |

`livingcare_graph_v2.cypher`로 새로 만든 그래프와 `neo4j_snapshot.json`이 정확히 같다는
보장은 없다 — 스크립트 실행 이후 수동 수정이 있었는지는 확인 못 했다(TODO 확인 필요).
**`neo4j_snapshot.json`이 "지금 실제로 쓰이는" 값의 정본이고, `.cypher`는 "어떻게 만들어졌는가"의 기록이다.**

### 실행

```bash
cd manager_ai_agent/knowledge_graph
python export_neo4j_snapshot.py                 # .env가 있으면 그대로 인증됨 (kg_mapping/.env와 같은 관례)
python export_neo4j_snapshot.py 다른경로.json     # 출력 경로 지정
```

비밀번호는 `NEO4J_PASSWORD` 환경변수 또는 이 폴더의 `.env`(git에 안 올라감)로 준다.
