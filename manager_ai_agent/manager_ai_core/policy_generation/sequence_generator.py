"""
sequence_generator.py  —  C3: Claude로 로봇 intent/sequence 생성 (조립)

역할:
    C2가 내린 판단(should_escalate + 근거)과 C1이 가져온 기기 정보를 받아,
    로봇에게 넘길 intent JSON을 만든다. 준상님이 카톡에서 원했던 그 형식:
        {"intent": "맵을 켜서 할머니를 찾아봐, 찾았으면 관찰해, N분 무동작이면 보고해",
         "device_id": "cap:limo_robot_agent", ...}

핵심 원칙 (handoff.md 원칙 2 — 절대 위반 금지):
    Claude는 "조립"만 한다. 위험한지 아닌지 "판단"은 이미 C2(규칙)가 끝냈고,
    Claude는 그 결정과 지식 문서의 rationale을 자연어 실행 지시로 옮길 뿐이다.
    새로운 판단·임계값·안전 결정을 지어내면 안 된다.

동작 모드:
    - ANTHROPIC_API_KEY가 있으면 → 진짜 Claude(claude-opus-4-8) 호출
    - 없으면 → 결정론적 mock 생성 (키 없이도 파이프라인이 끝까지 돈다)
    둘 다 출력 형식은 동일해서, 나중에 키만 넣으면 진짜로 바뀐다.
"""

import os
import json
import urllib.request
import urllib.error

MODEL = os.environ.get("CLAUDE_MODEL", "claude-opus-4-8")

# 로컬 무료 LLM (Ollama). 한국어 잘하는 qwen2.5:7b를 기본값으로.
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:7b")


def _find_rule(rules: list[dict], rule_id: str) -> dict:
    """rule_id로 C1이 가져온 원본 규칙(threshold 포함)을 다시 찾는다.
    (C2의 triggered_rules는 축약본이라 threshold가 없음 — 설계 노트가 지적한 그 버그를 여기서 방어)"""
    for r in rules:
        if r.get("rule_id") == rule_id:
            return r
    return {}


def _threshold_phrase(rule: dict) -> str:
    """규칙의 임계값을 사람이 읽는 문구로. (여기서 값을 지어내지 않고 규칙에 있는 값만 사용)"""
    if "threshold_hours" in rule:
        return f"{rule['threshold_hours']}시간"
    if "threshold_minutes" in rule:
        return f"{rule['threshold_minutes']}분"
    if "threshold_celsius" in rule:
        return f"{rule['threshold_celsius']}도"
    return "지정된 기준"


def _mock_intent(axis_label, device, rule, rationale) -> str:
    """
    Claude 없이 도는 결정론적 대체 생성. 기기의 기능(functions)과 규칙의 임계값을
    조합해 그럴듯한 자연어 지시를 만든다. (진짜 Claude가 할 일의 뼈대만 흉내)
    """
    func_names = [f["name"] for f in device.get("functions", [])]
    steps = []
    if any("Navigate" in n for n in func_names):
        steps.append("맵을 켜서 대상을 찾고")
    if any("Observe" in n for n in func_names):
        steps.append("찾으면 움직임을 관찰하고")
    steps.append(f"{_threshold_phrase(rule)} 동안 이상 징후가 지속되면 보고")
    return f"[{axis_label}] " + ", ".join(steps) + "해줘."


def _claude_intent(axis_label, device, rule, rationale, evaluation) -> str:
    """진짜 Claude 호출. 조립만 하도록 강하게 제약한 프롬프트."""
    import anthropic

    client = anthropic.Anthropic()  # 키는 환경/프로필에서 자동 해결
    system, user = _build_prompt(axis_label, device, rule, rationale, evaluation)
    resp = client.messages.create(
        model=MODEL, max_tokens=1024, system=system,
        messages=[{"role": "user", "content": user}],
    )
    return next((b.text for b in resp.content if b.type == "text"), "").strip()


# "조립만 하라"는 제약을 Claude·Ollama가 똑같이 쓰도록 프롬프트를 한 곳에서 만든다.
def _build_prompt(axis_label, device, rule, rationale, evaluation) -> tuple[str, str]:
    system = (
        "너는 이미 확정된 판단 결과를 로봇 실행 intent로 '조립'하는 역할이다. "
        "다음 규칙을 반드시 지켜라:\n"
        "1. 새로운 안전 판단이나 임계값을 지어내지 마라. 주어진 rationale과 임계값만 사용해라.\n"
        "2. 주어진 기기의 available functions 안에서만 행동을 구성해라.\n"
        "3. 출력은 한국어 자연어 지시 '한 문장'만. 설명·인사·따옴표 없이 지시문만 출력."
    )
    user = json.dumps({
        "axis": axis_label,
        "decision": {"should_escalate": evaluation["should_escalate"]},
        "triggered_rule": {"rationale": rationale, "threshold": _threshold_phrase(rule)},
        "device": {
            "device_id": device["device_id"],
            "available_functions": [f["name"] for f in device.get("functions", [])],
        },
    }, ensure_ascii=False)
    return system, user


def _ollama_available() -> bool:
    """로컬 Ollama 서버가 떠 있는지 짧게 확인."""
    try:
        urllib.request.urlopen(f"{OLLAMA_URL}/api/tags", timeout=1.5)
        return True
    except Exception:
        return False


def _ollama_intent(axis_label, device, rule, rationale, evaluation) -> str:
    """로컬 오픈소스 LLM(Ollama)으로 intent 생성. 무료, 인터넷 불필요."""
    system, user = _build_prompt(axis_label, device, rule, rationale, evaluation)
    payload = json.dumps({
        "model": OLLAMA_MODEL,
        "messages": [{"role": "system", "content": system},
                     {"role": "user", "content": user}],
        "stream": False,
        "options": {"temperature": 0.3},
    }).encode("utf-8")
    req = urllib.request.Request(f"{OLLAMA_URL}/api/chat", data=payload,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        data = json.loads(r.read().decode("utf-8"))
    return data["message"]["content"].strip()


def _choose_backend() -> str:
    """
    백엔드 우선순위:
      1) LLM_BACKEND 환경변수로 강제 지정 ("ollama"|"claude"|"mock")
      2) 로컬 Ollama가 떠 있으면 → ollama (무료)
      3) ANTHROPIC_API_KEY가 있으면 → claude (유료)
      4) 아무것도 없으면 → mock
    """
    forced = os.environ.get("LLM_BACKEND")
    if forced:
        return forced
    if _ollama_available():
        return "ollama"
    if os.environ.get("ANTHROPIC_API_KEY"):
        return "claude"
    return "mock"


def generate_sequence(axis_label: str, evaluation: dict, device: dict | None,
                      rules: list[dict]) -> dict:
    """
    판단 결과 → 로봇 intent JSON.

    반환:
        {
          "escalate": bool,
          "device_id": str | None,
          "intent": str | None,        # 로봇에게 줄 자연어 지시 (조립 결과)
          "source": "claude" | "mock" | None,
          "grounded_on": {"rule_id", "rationale"} | None,  # 어떤 결정을 근거로 조립했나
        }
    """
    # 에스컬레이션 불필요 → 로봇 intent 안 만듦 (조립할 게 없음)
    if not evaluation["should_escalate"]:
        return {"escalate": False, "device_id": None, "intent": None,
                "source": None, "grounded_on": None}

    # 에스컬레이션 필요한데 고비용 기기(로봇)가 없는 축 (예: Comfort)
    if device is None:
        return {"escalate": True, "device_id": None, "intent": None,
                "source": None, "grounded_on": None}

    top = evaluation["triggered_rules"][0] if evaluation["triggered_rules"] else {}
    rule = _find_rule(rules, top.get("rule_id", ""))
    rationale = top.get("rationale", "")

    backend = _choose_backend()
    try:
        if backend == "ollama":
            intent = _ollama_intent(axis_label, device, rule, rationale, evaluation)
            source = f"ollama:{OLLAMA_MODEL}"
        elif backend == "claude":
            intent = _claude_intent(axis_label, device, rule, rationale, evaluation)
            source = f"claude:{MODEL}"
        else:
            intent = _mock_intent(axis_label, device, rule, rationale)
            source = "mock"
    except Exception as e:
        # 실제 LLM 호출이 실패해도 파이프라인이 멈추지 않게 mock으로 폴백
        intent = _mock_intent(axis_label, device, rule, rationale)
        source = f"mock({backend} 실패: {e})"

    return {
        "escalate": True,
        "device_id": device["device_id"],
        "intent": intent,
        "source": source,
        "grounded_on": {"rule_id": top.get("rule_id"), "rationale": rationale},
    }


if __name__ == "__main__":
    import sys
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    demo_device = {
        "device_id": "cap:limo_robot_agent",
        "functions": [{"name": "NavigateFunction"}, {"name": "ObserveFunction"}],
    }
    demo_eval = {
        "should_escalate": True,
        "triggered_rules": [{"rule_id": "wb_r1_no_motion_day", "severity": "concern",
                              "rationale": "주간에 4시간 이상 활동 신호가 없으면 우려 상황"}],
    }
    demo_rules = [{"rule_id": "wb_r1_no_motion_day", "threshold_hours": 4}]

    print("=== mock 모드 (키 없음) ===")
    print(json.dumps(generate_sequence("WellBeing", demo_eval, demo_device, demo_rules),
                     ensure_ascii=False, indent=2))
