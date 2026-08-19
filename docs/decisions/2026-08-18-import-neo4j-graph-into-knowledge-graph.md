# 2026-08-18 · Neo4j 그래프 원본을 knowledge_graph/로 들여온다

> **정본 반영** 없음 — `SOT.md`·spec §3.1·D-6은 이 변경에서 바꾸지 않았다. 대신
> `manager_ai_agent/knowledge_graph/CLAUDE.md`에 실험 코드로 캐비어트를 남겼다.

## 왜

`manager_ai_core/kg_mapping/graph_retrieval.py`(2026-08-18, `docs/decisions/
2026-08-18-graph-inference-distribution.md`)가 접속하는 Neo4j 그래프는 그동안
`bolt://localhost:7687`의 로컬 인스턴스에만 있었고, 그 그래프를 만드는 원본
(`livingcare_graph_v2.cypher`)은 이 저장소 밖 `DATAS/`(준상님 개인 작업 폴더)에만
있었다. 팀장 지시로 둘 다 `manager_ai_agent/knowledge_graph/`로 들여왔다 — 이제
이 저장소만으로 그래프를 재현하거나 현재 상태를 확인할 수 있다.

## 무엇을 들여왔나

| 경로 | 정체 |
|---|---|
| `livingcare_graph_v2.cypher` | `DATAS/livingcare_graph_v2.cypher`를 그대로 복사. 그래프를 처음부터 다시 만드는 Cypher 스크립트 |
| `export_neo4j_snapshot.py` | 신규 작성. 지금 실제로 떠 있는 Neo4j 인스턴스를 JSON으로 통째로 내보낸다 (APOC 없이 순수 드라이버 쿼리로 동작 — 이 인스턴스엔 APOC이 없다) |
| `neo4j_snapshot.json` | 위 스크립트로 뜬 실제 스냅샷 (1회 실측: 노드 362개, 관계 666개) |

**둘 다 가져온 이유**: `.cypher`는 사람이 읽을 수 있는 "어떻게 만들어졌는가"의 기록이고,
`neo4j_snapshot.json`은 스크립트 실행 이후 수동으로 고친 값까지 포함해 "지금 실제로
무엇이 있는가"를 보장한다. 후자가 스크립트를 다시 실행해서 얻는 결과와 정확히 같다는
보장은 없다 — 확인 못 했다(TODO 확인 필요).

## 여전히 안 바뀐 것

- **D-6("KG는 그래프DB가 아니라 JSON")은 그대로다.** 이 Neo4j 그래프를 들여왔다고
  정본 KG 형식이 바뀐 게 아니다.
- **스키마 불일치는 그대로 미해소**다 — 이 그래프는 `Axis/Device/Function/State/
  AxisKnowledge`, D-6 JSON은 `person/space/device`. `knowledge_graph/CLAUDE.md`에
  이미 있던 TODO(확인 필요)를 새 파일 위치에 맞춰 이어받았을 뿐이다.
- `SOT.md` §2 트리는 안 바꿨다 — `knowledge_graph/`는 이미 정본 디렉터리라 새 폴더가
  필요 없었다.

## 검증 (1회 실측)

`python export_neo4j_snapshot.py`를 로컬 Neo4j(`bolt://localhost:7687`)에 대해 실행해
`neo4j_snapshot.json`(노드 362·관계 666, `kg_mapping/graph_retrieval.py`가 이전에 확인한
노드 수와 일치)을 실제로 만들어냈다.
