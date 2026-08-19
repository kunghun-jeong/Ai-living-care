"""
export_neo4j_snapshot.py  —  실행 중인 Neo4j 그래프를 통째로 JSON 스냅샷으로 뜬다.

역할:
    livingcare_graph_v2.cypher(스키마+시드 스크립트)와는 별개로, **지금 실제로 떠 있는
    그래프의 데이터**를 그대로 내보낸다. 스크립트를 돌린 뒤 수동으로 고친 값이 있어도
    그 변경분까지 포함된다. APOC이 없어도(이 인스턴스엔 없음) 동작하도록 neo4j 드라이버
    쿼리만으로 구현했다.

    노드는 Neo4j 내부 id(재기동하면 바뀔 수 있음) 대신 **내보내기 시점의 순번(export_id)**
    으로 관계를 잇는다 — 스냅샷 파일 자체가 재현 가능한 입력이 되게 하려는 것.

실행:
    NEO4J_PASSWORD=... python export_neo4j_snapshot.py [출력경로]
    (기본 출력: neo4j_snapshot.json, 이 폴더의 .env가 있으면 비밀번호 자동)
"""

import json
import os
import sys
from datetime import datetime, timezone

from neo4j import GraphDatabase


def _load_local_env():
    """kg_mapping/.env와 같은 관례 — 이 폴더에 .env가 있으면 읽어서 os.environ에 채운다."""
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if not os.path.exists(env_path):
        return
    with open(env_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())


_load_local_env()

NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "livingcare123")

_NODES_QUERY = "MATCH (n) RETURN elementId(n) AS eid, labels(n) AS labels, properties(n) AS props"
_RELS_QUERY = """
MATCH (a)-[r]->(b)
RETURN elementId(a) AS start_eid, elementId(b) AS end_eid, type(r) AS type, properties(r) AS props
"""


def export_snapshot(uri: str, user: str, password: str) -> dict:
    driver = GraphDatabase.driver(uri, auth=(user, password))
    try:
        with driver.session() as session:
            node_rows = session.execute_read(lambda tx: tx.run(_NODES_QUERY).data())
            rel_rows = session.execute_read(lambda tx: tx.run(_RELS_QUERY).data())
    finally:
        driver.close()

    eid_to_export_id = {row["eid"]: i for i, row in enumerate(node_rows)}
    nodes = [
        {"export_id": i, "labels": row["labels"], "properties": row["props"]}
        for i, row in enumerate(node_rows)
    ]
    relationships = [
        {
            "start": eid_to_export_id[row["start_eid"]],
            "end": eid_to_export_id[row["end_eid"]],
            "type": row["type"],
            "properties": row["props"],
        }
        for row in rel_rows
    ]

    return {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "source_uri": uri,
        "node_count": len(nodes),
        "relationship_count": len(relationships),
        "nodes": nodes,
        "relationships": relationships,
    }


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    out_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "neo4j_snapshot.json"
    )
    snapshot = export_snapshot(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)

    def _json_default(obj):
        # neo4j 드라이버의 Date/DateTime/Duration 등 temporal 타입 -> 문자열
        if hasattr(obj, "iso_format"):
            return obj.iso_format()
        return str(obj)

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2, default=_json_default)

    print(f"내보낸 노드 {snapshot['node_count']}개, 관계 {snapshot['relationship_count']}개")
    print(f"-> {out_path}")
