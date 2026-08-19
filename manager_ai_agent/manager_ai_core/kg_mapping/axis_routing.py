"""
axis_routing.py  —  자연어 → 축(axis) 라우팅

역할:
    자연어 발화가 어느 축(WellBeing/Safety/Comfort)에 해당하는지 임베딩
    유사도로 점수를 매긴다. graph_retrieval.py(C1)가 Neo4j를 조회할 axis_id를
    여기서 정한다.

출처:
    준상님의 end_to_end_pipeline.py(라우팅부) + onto_axes.py를 발췌했다.
    원본은 multi_axis_coordination.py·device_calling_pipeline.py(JSON registry
    기반의 별도 파이프라인)까지 이어지는 임포트 체인을 갖고 있었는데, 이 KG
    매핑은 그 체인을 쓰지 않으므로 라우팅 부분만 떼어 왔다.

두 가지 모드로 동작한다:
    1. 진짜 모드: axis_centroids.json + sentence-transformers가 있으면
       ko-sroberta 임베딩으로 코사인 유사도 계산.
    2. 폴백 모드: 위 둘 중 하나라도 없으면 단어 겹침으로 점수를 흉내낸다.
       구조 검증용일 뿐 라우팅 정확도를 보장하지 않는다.
"""

import json
import os
import re

_DIR = os.path.dirname(os.path.abspath(__file__))

ONTO_AXES = [
    {
        "id": "onto:saref/WellBeing",
        "label": "WellBeing",
        "embed_text": "사람의 상태, 웰빙, 안부 확인, 괜찮은지 확인, 활동 여부",
        "linked_capabilities": [
            "cap:wearable_vitals",
            "cap:motionsensor",
            "cap:limo_robot_agent",
        ],
    },
    {
        "id": "onto:saref/Safety",
        "label": "Safety",
        "embed_text": "위험 감지, 화재, 낙상, 침입, 안전, 비상상황",
        "linked_capabilities": [
            "cap:smokesensor",
            "cap:doorswitch",
            "cap:motionsensor",
            "cap:limo_robot_agent",
        ],
    },
    {
        "id": "onto:saref/Comfort",
        "label": "Comfort",
        "embed_text": "실내 환경, 온도, 습도, 쾌적함, 조명",
        "linked_capabilities": [
            "cap:temperaturesensor",
        ],
    },
]

THRESHOLD = 0.4677  # 준상 컴퓨터에서 캘리브레이션된 실제 값 (진짜 임베딩 모드 전용)


def _try_real_embeddings():
    """axis_centroids.json + sentence-transformers가 있으면 진짜 임베딩 함수를 반환, 없으면 None."""
    centroid_path = os.path.join(_DIR, "axis_centroids.json")
    if not os.path.exists(centroid_path):
        return None
    try:
        import numpy as np
        from sentence_transformers import SentenceTransformer
    except ImportError:
        return None

    with open(centroid_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    model = SentenceTransformer(data["model"])
    centroids = {axis_id: np.array(vec) for axis_id, vec in data["centroids"].items()}

    def real_scorer(text: str) -> dict:
        vec = model.encode(text)
        vec = vec / np.linalg.norm(vec)
        return {
            axis_id: float(np.dot(vec, c) / np.linalg.norm(c))
            for axis_id, c in centroids.items()
        }

    return real_scorer


def _fallback_scorer(text: str) -> dict:
    """!!! 구조 검증 전용 폴백 — 실제 라우팅 정확도를 보장하지 않는다 !!!"""
    def tokenize(s):
        return set(re.findall(r"[가-힣]+", s))

    text_tokens = tokenize(text)
    scores = {}
    for axis in ONTO_AXES:
        axis_tokens = tokenize(axis["embed_text"])
        overlap = len(text_tokens & axis_tokens)
        scores[axis["id"]] = min(0.15 + overlap * 0.25, 0.95)
    return scores


_real_scorer = _try_real_embeddings()
USING_REAL_EMBEDDINGS = _real_scorer is not None


def get_axis_scores(text: str) -> dict:
    if USING_REAL_EMBEDDINGS:
        return _real_scorer(text)
    return _fallback_scorer(text)


if __name__ == "__main__":
    import sys
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    mode = "진짜 임베딩(ko-sroberta)" if USING_REAL_EMBEDDINGS else "폴백(단어겹침, 부정확)"
    print(f"[모드] {mode}")
    for q in ["할머니 괜찮은지 확인해줘", "가스레인지 안 껐는지 확인해줘",
              "방 온도 너무 낮은 거 아니야?", "파스타 맛있게 만드는 법 알려줘"]:
        print(q, "->", get_axis_scores(q))
