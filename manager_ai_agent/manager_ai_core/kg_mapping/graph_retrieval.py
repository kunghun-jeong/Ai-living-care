"""
graph_retrieval.py  —  C1: 그래프 조회 (RAG retrieval)

역할:
    축(axis)이 정해지면 Neo4j 지식그래프에서 "판단에 필요한 재료"를 뽑아
    하나의 context 묶음으로 돌려준다. 조회만 하고 판단은 하지 않는다
    (판단은 C2 rule_evaluator, 생성은 C3 sequence_generator 담당).

설계 원칙 (준상님 handoff.md 준수):
    1. read-only  — State 말고는 어떤 노드도 CREATE/SET 하지 않는다.
    2. 데이터 주도 — 축/기기/슬롯 이름을 코드에 하드코딩하지 않는다.
                     그래프에 있는 걸 그대로 읽는다. 준상님이 축이나 기기를
                     추가/수정해도 이 코드는 안 바뀐다.
    3. 격리       — 그래프에 대한 모든 Cypher는 이 파일에만 있다.
                     스키마(관계/속성 이름)가 바뀌면 여기만 고치면 된다.

이 파일 하나만 실행해도(python graph_retrieval.py) 실제 그래프에서 WellBeing
축의 재료가 어떻게 뽑히는지 눈으로 볼 수 있다.
"""

import os
from neo4j import GraphDatabase


def _load_local_env():
    """
    Windows에서 setx/시스템 환경변수는 이미 떠 있는 터미널·IDE에는 반영되지 않는다
    (레지스트리만 갱신되고 살아있는 프로세스는 갱신 전 환경을 그대로 물려받는다).
    그 문제를 피하려고 이 폴더의 .env(git에 올라가지 않음)를 직접 읽어 채운다.
    이미 환경변수로 설정된 값은 덮어쓰지 않는다(setdefault).
    """
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

# --- 접속 정보 (환경변수 또는 이 폴더의 .env로 덮어쓸 수 있음. 기본값 = 로컬 Docker Neo4j) ---
NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "livingcare123")


# ---------------------------------------------------------------------
# Cypher — 모든 그래프 지식은 여기에만. (원칙 3: 격리)
# ---------------------------------------------------------------------

# 한 축에 딸린 기기들 + 각 기기의 기능/상태/기기지식을 한 번에 조회.
# 리스트 컴프리헨션의 WHERE x IS NOT NULL 은 "기능/상태가 없는 기기"에서
# [null] 이 섞여 들어오는 걸 막아준다 (OPTIONAL MATCH 부작용 방어).
_DEVICES_QUERY = """
MATCH (a:Axis {id: $axis_id})-[:HAS_DEVICE]->(d:Device)
OPTIONAL MATCH (d)-[:HAS_FUNCTION]->(f:Function)
OPTIONAL MATCH (d)-[:HAS_STATE]->(s:State)
OPTIONAL MATCH (d)-[:HAS_DEVICE_KNOWLEDGE]->(dk:DeviceKnowledge)
RETURN d.device_id   AS device_id,
       d.device_class AS device_class,
       d.slot         AS slot,
       d.risk_tier    AS risk_tier,
       d.cost_hint    AS cost_hint,
       [x IN collect(DISTINCT f) WHERE x IS NOT NULL | {name: x.name, reachable: x.reachable}] AS functions,
       [x IN collect(DISTINCT s) WHERE x IS NOT NULL | {key: x.key, value: x.value, updated_by: x.updated_by}] AS states,
       [x IN collect(DISTINCT dk) WHERE x IS NOT NULL | properties(x)] AS device_knowledge
ORDER BY d.cost_hint, d.device_id
"""

# 한 축에 딸린 판단 규칙(AxisKnowledge)을 통째로 조회.
# properties(k) 로 규칙의 모든 속성을 그대로 가져온다 - 어떤 속성이 있는지
# 미리 알 필요 없이, 규칙에 threshold_hours가 있든 threshold_celsius가 있든
# 그대로 넘겨서 C2가 알아서 해석한다 (원칙 2: 데이터 주도).
_RULES_QUERY = """
MATCH (a:Axis {id: $axis_id})-[:HAS_AXIS_KNOWLEDGE]->(k:AxisKnowledge)
RETURN properties(k) AS rule
"""

_LABEL_QUERY = "MATCH (a:Axis {id: $axis_id}) RETURN a.label AS label"

_ALL_AXES_QUERY = "MATCH (a:Axis) RETURN a.id AS id, a.label AS label ORDER BY a.label"


class GraphRetriever:
    """Neo4j 연결을 쥐고 있는 조회기. with 문으로 쓰면 자동으로 닫힌다."""

    def __init__(self, uri=NEO4J_URI, user=NEO4J_USER, password=NEO4J_PASSWORD):
        # DeviceKnowledge(아직 0개)나 State.value(아직 null) 관련 "존재하지 않음"
        # 알림은 지금 단계에선 예상된 빈칸이라, 서버가 아예 안 보내도록 끈다.
        # 나중에 채워지면 자동으로 사라질 잡음이라 동작엔 영향 없음.
        try:
            self._driver = GraphDatabase.driver(
                uri, auth=(user, password), notifications_min_severity="OFF"
            )
        except TypeError:
            # 드라이버 버전이 이 옵션을 모르면 그냥 알림을 남겨둔다 (동작엔 영향 없음)
            self._driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self._driver.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    # --- 공개 API ------------------------------------------------------

    def list_axes(self) -> list[dict]:
        """그래프에 있는 모든 축을 반환. (라우팅 결과 검증/디버깅용)"""
        with self._driver.session() as session:
            return session.execute_read(lambda tx: tx.run(_ALL_AXES_QUERY).data())

    def fetch_axis_context(self, axis_id: str) -> dict:
        """
        한 축의 context 묶음을 반환:
            {
              "axis_id": "onto:saref/WellBeing",
              "label":   "WellBeing",
              "devices": [ {device_id, slot, risk_tier, cost_hint,
                            functions[], states[], device_knowledge[]}, ... ],
              "rules":   [ {rule_id, slot, threshold_*, severity, rationale, ...}, ... ],
            }
        """
        with self._driver.session() as session:
            label = session.execute_read(
                lambda tx: tx.run(_LABEL_QUERY, axis_id=axis_id).single()
            )
            devices = session.execute_read(
                lambda tx: tx.run(_DEVICES_QUERY, axis_id=axis_id).data()
            )
            rule_rows = session.execute_read(
                lambda tx: tx.run(_RULES_QUERY, axis_id=axis_id).data()
            )

        return {
            "axis_id": axis_id,
            "label": label["label"] if label else axis_id,
            "devices": devices,
            "rules": [row["rule"] for row in rule_rows],
        }

    def fetch_context_package(self, axis_ids: list[str]) -> dict[str, dict]:
        """여러 축(multi-label)을 한꺼번에. axis_id -> context 딕셔너리."""
        return {axis_id: self.fetch_axis_context(axis_id) for axis_id in axis_ids}


# ---------------------------------------------------------------------
# 단독 실행 데모: 실제 그래프에서 WellBeing 재료가 어떻게 뽑히는지 확인
# ---------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    import json

    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    with GraphRetriever() as g:
        print("=== 그래프에 있는 축 목록 ===")
        for axis in g.list_axes():
            print(f"  {axis['label']:12s} {axis['id']}")

        print("\n=== WellBeing 축 context 묶음 ===")
        ctx = g.fetch_axis_context("onto:saref/WellBeing")
        print(json.dumps(ctx, ensure_ascii=False, indent=2))
