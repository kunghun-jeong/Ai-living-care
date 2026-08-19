"""
sequence_generator.py  —  C3: 로봇 실행 계약(RobotTask) 생성

역할:
    C2가 내린 판단(should_escalate + 발화 규칙)과 C1이 가져온 기기 정보를 받아,
    Worker가 결정론으로 받아쓸 수 있는 '구조화된 계약(JSON)'을 만든다.
    (예전엔 prose 한 문장 = 블랙박스였음 → 이제 구조화된 계약 = 투명)

핵심 원칙:
    - functions(무엇을 할지)는 '규칙'이 이미 정한다 — LLM은 못 고른다(안전).
    - LLM은 그 functions를 자연스러운 한국어 `goal`로 '번역·연결'만 한다.
    - LLM 출력은 반드시 검증한다(functions가 바뀌면 폐기 → 결정론 fallback).

출력(C안 계약):
    {
      "device_id":  str | None,
      "functions":  [함수이름, ...],          # 규칙이 정함
      "goal":       str,                       # LLM(또는 템플릿)이 한국어로 렌더
      "params_hint":{...},
      "report_condition": str | None,
      "grounded_on":{"axis", "rule_id", "rationale"},
      # --- 파이프라인 호환 메타 ---
      "escalate":   bool,
      "source":     "ollama:..|claude:..|rule|mock(..)",
      "intent":     goal 또는 None(구 코드 호환)
    }

백엔드: Ollama(무료) → Claude(유료) → mock. functions가 비면 LLM 안 부르고 결정론 처리.
"""

import os
import json
import urllib.request
import urllib.error

MODEL = os.environ.get("CLAUDE_MODEL", "claude-opus-4-8")
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:7b")

# 함수 실행 순서 (그래프가 뒤섞어 줘도 여기서 정규화 — Navigate 먼저)
_FUNCTION_ORDER = {"NavigateFunction": 0, "ObserveFunction": 1, "SensingFunction": 2}


# ---------------------------------------------------------------------
# few-shot 프롬프트 (LLM에게: functions → 한국어 goal + JSON 조립)
# ---------------------------------------------------------------------
_FEWSHOT_SYSTEM = """너는 로봇 실행 계약(RobotTask)을 조립하는 '포매터'다.
입력으로 '이미 규칙이 결정한' 정보(기기 · 선택된 함수 목록 · 파라미터 힌트 · 판단 근거 · 보고조건)를 받는다.
네 임무는 두 가지뿐이다:
  1. 주어진 함수들을 순서대로 자연스러운 한국어 `goal` 한 문장으로 번역·연결한다.
  2. 아래 JSON 스키마로만 출력한다.

엄수 규칙:
  - functions를 추가·삭제·재정렬하지 마라. 입력 그대로 옮긴다.
  - params_hint·report_condition·grounded_on은 입력 값을 그대로 옮긴다. 지어내지 마라.
  - JSON만 출력한다. 설명·인사·코드펜스 금지.

함수 → 한국어 번역 가이드 (예시에 없는 함수도 이 원칙으로 일반화):
  NavigateFunction → "맵을 켜서 <target>(으)로 이동해 찾고"
  ObserveFunction  → "찾으면 <observe_minutes>분 관찰하고"
  SensingFunction  → "<target> 값을 측정하고"
  그 외 함수 → 함수명의 동사 의미를 살려 간결한 한국어 동작으로.
  report_condition이 있으면 문장 끝을 "<report_condition>"으로 맺는다.

출력 스키마:
{"device_id":<string|null>,"functions":[...],"goal":<string>,"params_hint":<object>,"report_condition":<string|null>,"grounded_on":{"axis":<string>,"rule_id":<string|null>}}

[예시 1 — WellBeing · 로봇 출동]
입력:
{"device_id":"cap:limo_robot_agent","functions":["NavigateFunction","ObserveFunction"],"params_hint":{"target":"할머니","observe_minutes":240},"report_condition":"240분 무동작 시 보고","grounded_on":{"axis":"WellBeing","rule_id":"wb_r1_no_motion_day"}}
출력:
{"device_id":"cap:limo_robot_agent","functions":["NavigateFunction","ObserveFunction"],"goal":"맵을 켜서 할머니를 찾고, 찾으면 240분 관찰하고, 240분 무동작이면 보고","params_hint":{"target":"할머니","observe_minutes":240},"report_condition":"240분 무동작 시 보고","grounded_on":{"axis":"WellBeing","rule_id":"wb_r1_no_motion_day"}}

[예시 2 — Comfort · 센서만]
입력:
{"device_id":"cap:temperaturesensor","functions":["SensingFunction"],"params_hint":{"target":"방 온도","threshold_celsius":18},"report_condition":"18도 미만 시 보고","grounded_on":{"axis":"Comfort","rule_id":"cf_r1_temp_too_low"}}
출력:
{"device_id":"cap:temperaturesensor","functions":["SensingFunction"],"goal":"방 온도 값을 측정하고, 18도 미만이면 보고","params_hint":{"target":"방 온도","threshold_celsius":18},"report_condition":"18도 미만 시 보고","grounded_on":{"axis":"Comfort","rule_id":"cf_r1_temp_too_low"}}

[예시 3 — Safety · 로봇 출동, 다른 대상]
입력:
{"device_id":"cap:limo_robot_agent","functions":["NavigateFunction","ObserveFunction"],"params_hint":{"target":"현관","observe_minutes":5},"report_condition":"침입 의심 시 보고","grounded_on":{"axis":"Safety","rule_id":"sf_r3_door_open_night"}}
출력:
{"device_id":"cap:limo_robot_agent","functions":["NavigateFunction","ObserveFunction"],"goal":"맵을 켜서 현관으로 이동해 확인하고, 찾으면 5분 관찰하고, 침입 의심 시 보고","params_hint":{"target":"현관","observe_minutes":5},"report_condition":"침입 의심 시 보고","grounded_on":{"axis":"Safety","rule_id":"sf_r3_door_open_night"}}

이제 아래 실제 입력을 같은 방식으로 처리해 JSON만 출력하라."""


# ---------------------------------------------------------------------
# 규칙 조회 유틸
# ---------------------------------------------------------------------
def _find_rule(rules: list[dict], rule_id: str) -> dict:
    for r in rules:
        if r.get("rule_id") == rule_id:
            return r
    return {}


def _threshold_phrase(rule: dict) -> str:
    if "threshold_hours" in rule:
        return f"{rule['threshold_hours']}시간"
    if "threshold_minutes" in rule:
        return f"{rule['threshold_minutes']}분"
    if "threshold_celsius" in rule:
        return f"{rule['threshold_celsius']}도"
    return "지정 기준"


def _report_condition(rule: dict, params_hint: dict) -> str | None:
    """규칙에서 보고 조건 문구를 결정론적으로 만든다."""
    if not rule:
        return None
    if "threshold_hours" in rule:
        mins = params_hint.get("observe_minutes")
        return f"{mins}분 무동작 시 보고" if mins else f"{_threshold_phrase(rule)} 무동작 시 보고"
    if "threshold_minutes" in rule:
        return f"{rule['threshold_minutes']}분 초과 시 보고"
    if "threshold_celsius" in rule:
        direction = "미만" if rule.get("direction") == "below" else "초과"
        return f"{rule['threshold_celsius']}도 {direction} 시 보고"
    return "이상 감지 시 보고"


# ---------------------------------------------------------------------
# ① decision 조립 — 규칙 결과에서 계약 입력을 만든다 (결정론, LLM 아님)
# ---------------------------------------------------------------------
def _build_decision(axis_label: str, evaluation: dict, device: dict | None,
                    rules: list[dict], target: str) -> dict:
    top = evaluation["triggered_rules"][0] if evaluation.get("triggered_rules") else {}
    rule = _find_rule(rules, top.get("rule_id", "")) if top else {}

    # 에스컬레이션 불필요 or 대응 기기 없음 → 함수 없는(빈) 계약
    if not evaluation.get("should_escalate") or device is None:
        return {
            "device_id": None,
            "functions": [],
            "params_hint": {},
            "report_condition": None,
            "grounded_on": {"axis": axis_label, "rule_id": top.get("rule_id"),
                            "rationale": top.get("rationale")},
        }

    # 기기의 함수를 규칙 순서로 정규화 (Navigate → Observe → Sensing)
    functions = sorted(
        (f["name"] for f in device.get("functions", [])),
        key=lambda n: _FUNCTION_ORDER.get(n, 9),
    )
    params_hint = {"target": target}
    if "threshold_hours" in rule:
        params_hint["observe_minutes"] = rule["threshold_hours"] * 60
    if "threshold_celsius" in rule:
        params_hint["threshold_celsius"] = rule["threshold_celsius"]

    return {
        "device_id": device["device_id"],
        "functions": functions,
        "params_hint": params_hint,
        "report_condition": _report_condition(rule, params_hint),
        "grounded_on": {"axis": axis_label, "rule_id": top.get("rule_id"),
                        "rationale": top.get("rationale")},
    }


# ---------------------------------------------------------------------
# ② goal 렌더링 — 결정론 템플릿 (LLM fallback / 검증 실패 시)
# ---------------------------------------------------------------------
def _render_goal_template(decision: dict) -> str:
    functions = decision["functions"]
    if not functions:
        return "특별한 조치가 필요하지 않습니다"
    ph = decision["params_hint"]
    target = ph.get("target", "대상")
    mins = ph.get("observe_minutes")
    parts = []
    if "NavigateFunction" in functions:
        parts.append(f"맵을 켜서 {target}을(를) 찾고")
    if "ObserveFunction" in functions:
        parts.append(f"찾으면 {mins}분 관찰하고" if mins else "찾으면 관찰하고")
    if "SensingFunction" in functions:
        parts.append(f"{target} 값을 측정하고")
    # 위 셋에 없는 함수는 이름 그대로라도 넣어준다 (일반화)
    for fn in functions:
        if fn not in ("NavigateFunction", "ObserveFunction", "SensingFunction"):
            parts.append(f"{fn} 수행하고")
    if decision.get("report_condition"):
        parts.append(decision["report_condition"])
    return ", ".join(parts)


def _fallback_contract(decision: dict) -> dict:
    """LLM 없이 계약을 완성 (goal은 템플릿)."""
    return {**decision, "goal": _render_goal_template(decision)}


# ---------------------------------------------------------------------
# ③ LLM 호출 (Ollama / Claude) — few-shot으로 goal + JSON 조립
# ---------------------------------------------------------------------
def _strip_fences(text: str) -> str:
    t = text.strip()
    if t.startswith("```"):
        t = t.split("```")[1] if "```" in t[3:] else t.lstrip("`")
        t = t.replace("json", "", 1).strip()
    # 첫 { 부터 마지막 } 까지만
    if "{" in t and "}" in t:
        t = t[t.index("{"): t.rindex("}") + 1]
    return t


def _call_ollama(decision: dict) -> str:
    payload = json.dumps({
        "model": OLLAMA_MODEL,
        "messages": [{"role": "system", "content": _FEWSHOT_SYSTEM},
                     {"role": "user", "content": json.dumps(decision, ensure_ascii=False)}],
        "stream": False,
        "options": {"temperature": 0.2},
    }).encode("utf-8")
    req = urllib.request.Request(f"{OLLAMA_URL}/api/chat", data=payload,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        data = json.loads(r.read().decode("utf-8"))
    return data["message"]["content"]


def _call_claude(decision: dict) -> str:
    import anthropic
    client = anthropic.Anthropic()
    resp = client.messages.create(
        model=MODEL, max_tokens=1024, system=_FEWSHOT_SYSTEM,
        messages=[{"role": "user", "content": json.dumps(decision, ensure_ascii=False)}],
    )
    return next((b.text for b in resp.content if b.type == "text"), "")


def _ollama_available() -> bool:
    try:
        urllib.request.urlopen(f"{OLLAMA_URL}/api/tags", timeout=1.5)
        return True
    except Exception:
        return False


def _choose_backend() -> str:
    forced = os.environ.get("LLM_BACKEND")
    if forced:
        return forced
    if _ollama_available():
        return "ollama"
    if os.environ.get("ANTHROPIC_API_KEY"):
        return "claude"
    return "mock"


# ---------------------------------------------------------------------
# ④ 검증 — LLM이 함수를 바꿨는지 확인 (블랙박스 방지)
# ---------------------------------------------------------------------
def _validate(contract: dict, decision: dict):
    if contract.get("functions") != decision["functions"]:
        raise ValueError(f"LLM이 functions를 변경함: {contract.get('functions')} != {decision['functions']}")
    if not contract.get("goal"):
        raise ValueError("goal 비어있음")


def _finalize(contract: dict, decision: dict, evaluation: dict, source: str) -> dict:
    """계약에 파이프라인 호환 메타(escalate/source/intent)를 붙여 마무리."""
    contract.setdefault("grounded_on", decision["grounded_on"])
    contract["escalate"] = bool(evaluation.get("should_escalate"))
    contract["source"] = source
    # 실제 로봇 동작(함수)이 있을 때만 intent 채움 — 없으면 파이프라인이 딴 분기 타게
    contract["intent"] = contract.get("goal") if contract.get("functions") else None
    return contract


# ---------------------------------------------------------------------
# 공개 API — 시그니처 유지(드롭인). target만 선택 인자로 추가.
# ---------------------------------------------------------------------
def generate_sequence(axis_label: str, evaluation: dict, device: dict | None,
                      rules: list[dict], target: str = "할머니") -> dict:
    """
    판단 결과 → 로봇 실행 계약(C안).
    target: 대상(예: "할머니"). 지금은 기본값/mock — 나중에 의도추출·KG로 교체(TODO 확인 필요).
    """
    decision = _build_decision(axis_label, evaluation, device, rules, target)

    # 함수가 없으면(조치 불필요/로봇 없음) LLM 안 부르고 결정론 처리
    if not decision["functions"]:
        return _finalize(_fallback_contract(decision), decision, evaluation, "rule")

    backend = _choose_backend()
    try:
        if backend == "ollama":
            raw, source = _call_ollama(decision), f"ollama:{OLLAMA_MODEL}"
        elif backend == "claude":
            raw, source = _call_claude(decision), f"claude:{MODEL}"
        else:
            raise RuntimeError("mock")
        contract = json.loads(_strip_fences(raw))
        _validate(contract, decision)             # 함수 안 바꿨는지 검증
    except Exception as e:
        # LLM 실패/검증 실패 → 결정론 템플릿으로 안전하게 대체
        contract = _fallback_contract(decision)
        source = f"mock({backend} 실패: {str(e)[:40]})"

    return _finalize(contract, decision, evaluation, source)


# ---------------------------------------------------------------------
# 단독 실행 데모
# ---------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # Windows 콘솔 한글 깨짐 방지
    except Exception:
        pass
    demo_device = {
        "device_id": "cap:limo_robot_agent",
        "functions": [{"name": "ObserveFunction"}, {"name": "NavigateFunction"}],
    }
    demo_eval = {
        "should_escalate": True,
        "triggered_rules": [{"rule_id": "wb_r1_no_motion_day", "severity": "concern",
                             "rationale": "주간 4시간 무동작이면 우려"}],
    }
    demo_rules = [{"rule_id": "wb_r1_no_motion_day", "slot": "motion",
                   "time_context": "day", "threshold_hours": 4, "severity": "concern"}]

    print("=== 백엔드:", _choose_backend(), "===")
    result = generate_sequence("WellBeing", demo_eval, demo_device, demo_rules, target="할머니")
    print(json.dumps(result, ensure_ascii=False, indent=2))
