"""
pipeline.py  —  전체 통합 (C1 → C2 → C3)

자연어 → [라우팅(임베딩, 준상님 것 재사용)] → 활성 축
       → [C1] Neo4j 그래프 조회
       → 관측값 구성 (State가 비면 mock)
       → [C2] 규칙 평가(판단, 코드)
       → [코드 게이트] safety_critical 에스컬레이션 선행조건
       → [C3] Claude/mock 로봇 intent 생성(조립)

실제로 띄운 Neo4j(livingcare-neo4j)에 붙어서 돈다.
키가 없으면 C3는 mock으로, 임베딩 모델이 없으면 라우팅은 폴백으로 — 그래도 끝까지 돈다.
"""

import sys
import json

# Windows 콘솔/Git Bash에서 한글이 깨지지 않게 출력 인코딩을 UTF-8로 고정
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from graph_retrieval import GraphRetriever          # C1
from rule_evaluator import evaluate                  # C2
from sequence_generator import generate_sequence     # C3

# 라우팅은 준상님 코드 재사용 (진짜 임베딩이 있으면 그걸, 없으면 단어겹침 폴백)
from end_to_end_pipeline import get_axis_scores, THRESHOLD, USING_REAL_EMBEDDINGS
from onto_axes import ONTO_AXES

AXIS_BY_ID = {a["id"]: a for a in ONTO_AXES}

# 개발용 mock 관측값 — State가 아직 안 채워졌을 때만 대체로 쓴다.
# 나중에 실제 센서가 State에 값을 쓰면, 이 mock은 자동으로 안 쓰이게 된다(계약 동일).
MOCK_OBSERVATIONS = {
    "motion": 5.0,       # 낮이면 4h 초과 → concern
    "heartrate": 1.0,    # 정상
    "temperature": 16,   # 18도 미만 → concern
    "smoke": False,
    "doorswitch": 10,    # 주간 30분 미만 → 정상
}


def determine_active_axes(scores: dict, threshold: float) -> list[str]:
    """threshold 넘는 축 전부 활성화 (multi-label). 하나도 없으면 OOS."""
    return [axis_id for axis_id, s in scores.items() if s >= threshold]


def build_observations(context: dict) -> tuple[dict, list[str]]:
    """C1 context의 State에서 관측값을 뽑고, 비면 mock으로 채운다."""
    obs, mock_slots = {}, []
    for dev in context["devices"]:
        slot = dev["slot"]
        value = None
        for s in dev["states"]:
            if s.get("value") is not None:
                value = s["value"]
        if value is None and slot in MOCK_OBSERVATIONS:
            value = MOCK_OBSERVATIONS[slot]
            mock_slots.append(slot)
        if value is not None:
            obs[slot] = value
    return obs, mock_slots


def pick_escalation_device(context: dict) -> dict | None:
    """고비용(로봇 등) 기기를 에스컬레이션 후보로 고른다."""
    for d in context["devices"]:
        if d.get("cost_hint") == "high":
            return d
    return None


def safety_gate(context: dict, device: dict | None, observations: dict) -> tuple[bool, str]:
    """
    코드 게이트: safety_critical 고비용 기기는 저비용 기기를 먼저 거쳤어야 함.
    (requires_escalation_from이 아직 그래프에 없어서, axis의 저비용 기기 관측 여부로 대체 판정)
    """
    if device is None or device.get("risk_tier") != "safety_critical":
        return True, "ok"
    low_cost = [d for d in context["devices"] if d.get("cost_hint") == "low"]
    missing = [d["device_id"] for d in low_cost if d["slot"] not in observations]
    if missing:
        return False, f"{missing}를 먼저 관측했어야 함"
    return True, "ok"


def run(query: str, hour: int, retriever: GraphRetriever | None = None) -> dict:
    own_retriever = retriever is None
    g = retriever or GraphRetriever()
    try:
        mode = "진짜 임베딩" if USING_REAL_EMBEDDINGS else "폴백(단어겹침, 부정확)"
        threshold = THRESHOLD if USING_REAL_EMBEDDINGS else 0.35
        print("=" * 72)
        print(f"[입력] \"{query}\"  (hour={hour}, 라우팅={mode}, threshold={threshold})")

        # --- 라우팅 (준상님 코드 재사용) ---
        scores = get_axis_scores(query)
        active = determine_active_axes(scores, threshold)
        print(f"[라우팅] 점수={ {AXIS_BY_ID[k]['label']: round(v,3) for k,v in scores.items()} }")
        print(f"[라우팅] 활성 축: {[AXIS_BY_ID[a]['label'] for a in active] or '없음'}")

        if not active:
            print("[OOS] 다룰 수 있는 영역이 아닙니다.\n")
            return {"query": query, "active_axes": [], "results": []}

        results = []
        for axis_id in active:
            ctx = g.fetch_axis_context(axis_id)                       # C1
            obs, mock_slots = build_observations(ctx)
            evaluation = evaluate(ctx["rules"], obs, hour)            # C2
            device = pick_escalation_device(ctx)
            ok, reason = safety_gate(ctx, device, obs)               # 코드 게이트
            gated_device = device if ok else None
            seq = generate_sequence(ctx["label"], evaluation, gated_device, ctx["rules"])  # C3

            print(f"\n  ── {ctx['label']} ──")
            print(f"     관측값: {obs}" + (f"  (mock: {mock_slots})" if mock_slots else ""))
            trg = [r['rule_id'] for r in evaluation['triggered_rules']]
            print(f"     [C2 판단] should_escalate={evaluation['should_escalate']} "
                  f"(발화 규칙: {trg or '없음'})")
            if device is not None:
                print(f"     [게이트] {device['device_id']}: {ok} ({reason})")
            if seq["intent"]:
                print(f"     [C3 생성/{seq['source']}] {seq['intent']}")
            elif seq["escalate"]:
                print(f"     [C3] 에스컬레이션 필요하나 로봇 대응 기기 없음(예: Comfort)")
            else:
                print(f"     [C3] 특별한 이상 없음 — 로봇 출동 불필요")

            results.append({"axis": ctx["label"], "evaluation": evaluation, "sequence": seq})

        print()
        return {"query": query, "active_axes": active, "results": results}
    finally:
        if own_retriever:
            g.close()


if __name__ == "__main__":
    test_cases = [
        ("할머니 괜찮은지 확인해줘", 15),    # 낮 → WellBeing 발화 기대
        ("할머니 괜찮은지 확인해줘", 3),     # 새벽 → 야간 기준이라 발화 안 함 기대
        ("가스레인지 안 껐는지 확인해줘", 15),  # Safety
        ("방 온도 너무 낮은 거 아니야?", 15),   # Comfort (로봇 대응 없음)
        ("파스타 맛있게 만드는 법 알려줘", 15),  # OOS 기대
    ]
    with GraphRetriever() as g:
        for query, hour in test_cases:
            run(query, hour, retriever=g)
