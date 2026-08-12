"""check_grandma.json 류(구역 순찰 + check_object_state) 시나리오가 공유하는 DSL 유틸.

variate_scenario.py(변형기)·validate_variant.py(검증기)가 함께 쓴다. run_scenario.py 가
해석하는 스키마(§ 그 파일 docstring)를 전제로, 그 중에서도 "구역 블록을 순서대로 돌다 하나를
찾으면 상태를 확인하고 집으로 돌아온다" 모양(check_grandma.json/check_grandma_bedroom_first.json)
만 다룬다.

구역 블록 하나는 7 step 고정 순서다: resolve → plan → move → arrive → look → scan → found
(id 는 `z<N>_<suffix>`). 이 모양 자체가 "정책"이다 — 변형기는 이 모양을 절대 바꾸지 않고
구역의 순서/구성과 input.object 만 바꾼다. 상세 규칙은
docs/decisions/2026-08-12-scenario-variator-rules.md.
"""

import copy
import json
import re
from pathlib import Path

KNOWN_TOOLS = {
    "plan_and_navigate",
    "navigate_waypoints",
    "get_status",
    "get_camera_snapshot",
    "detect_objects",
    "check_object_state",
    "look_around",
    "is_looking_around",
    "interrupt_look_around",
    "cancel",
    "resolve_location",
    "pathplanning",
    "moving_path",
    "get_path_status",
    "cancel_path",
    "send_ir_signal",
}

STEP_TYPES = {"call", "branch", "poll_until_match"}

ZONE_BLOCK_SUFFIXES = ["resolve", "plan", "move", "arrive", "look", "scan", "found"]
ZONE_ID_RE = re.compile(r"^z(\d+)_(resolve|plan|move|arrive|look|scan|found)$")

OBJECT_BINDINGS_PATH = Path(__file__).parent / "object_bindings.json"


def load_object_bindings(path=OBJECT_BINDINGS_PATH) -> dict[str, str]:
    """input.object(의미적 대상, 예: "grandma") -> target_class(탐지 class, 예: "person") 매핑.

    check_object_state 정책 시나리오는 이 둘을 분리한다: object 는 시나리오 라벨·의도용,
    target_class 는 detect_objects/check_object_state 가 실제로 대조하는 값
    ($input.target_class, docs/decisions/2026-08-12-object-target-class-split.md).
    """
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    return {k: v for k, v in raw.items() if not k.startswith("_")}


def resolve_target_class(object_label: str, bindings: dict[str, str] | None = None) -> str:
    bindings = bindings if bindings is not None else load_object_bindings()
    if object_label not in bindings:
        raise ValueError(
            f"object_bindings.json 에 {object_label!r} 매핑이 없다 (가능: {sorted(bindings)})"
        )
    return bindings[object_label]


def load_scenario(path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_scenario(scenario: dict, path) -> None:
    Path(path).write_text(
        json.dumps(scenario, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def split_scenario(scenario: dict):
    """steps[] 를 (zone_blocks: {zone_name: [7 step]}, tail: [step...]) 로 나눈다.

    zone_blocks 는 base 시나리오에 등장하는 순서를 보존한 dict(파이썬 3.7+ 는 삽입 순서 유지).
    구역 블록이 하나도 없으면 ValueError — check_grandma.json 류가 아니라는 뜻이다.
    """
    steps = scenario["steps"]
    zone_positions: dict[int, list[int]] = {}
    for i, s in enumerate(steps):
        m = ZONE_ID_RE.match(s["id"])
        if m:
            zone_positions.setdefault(int(m.group(1)), []).append(i)

    if not zone_positions:
        raise ValueError(
            "구역 블록(z<N>_resolve..found)을 찾지 못했다 — check_grandma.json 류 시나리오가 아니다"
        )

    zone_blocks: dict[str, list[dict]] = {}
    last_idx = -1
    for n in sorted(zone_positions):
        idxs = zone_positions[n]
        if len(idxs) != len(ZONE_BLOCK_SUFFIXES):
            raise ValueError(f"z{n} 블록이 {len(idxs)} step 이다 (7 이어야 한다)")
        block = [steps[i] for i in idxs]
        expected = [f"z{n}_{suf}" for suf in ZONE_BLOCK_SUFFIXES]
        actual = [s["id"] for s in block]
        if actual != expected:
            raise ValueError(f"z{n} 블록 step 순서/이름이 표준과 다르다: {actual} != {expected}")
        resolve_step = block[0]
        zone_name = resolve_step.get("args", {}).get("name")
        if not zone_name:
            raise ValueError(f"z{n}_resolve 에 args.name 이 없다")
        zone_blocks[zone_name] = block
        last_idx = max(last_idx, max(idxs))

    tail = steps[last_idx + 1 :]
    return zone_blocks, tail


def _rewrite_zone_refs(value, new_prefix: str):
    """"$z1_plan.x" / "z1_plan" 형태의 참조에서 zN_ 부분만 new_prefix 로 바꾼다."""
    if isinstance(value, str):
        body = value[1:] if value.startswith("$") else value
        m = re.match(r"^z\d+_(.+)$", body)
        if m:
            rebuilt = f"{new_prefix}_{m.group(1)}"
            return f"${rebuilt}" if value.startswith("$") else rebuilt
        return value
    if isinstance(value, dict):
        return {k: _rewrite_zone_refs(v, new_prefix) for k, v in value.items()}
    if isinstance(value, list):
        return [_rewrite_zone_refs(v, new_prefix) for v in value]
    return value


def rebuild_zone_block(zone_name: str, index: int, template: list[dict]) -> list[dict]:
    """template(어떤 구역의 원본 7 step)을 z<index>_* 로 재번호 매김해 새 블록을 만든다.

    내부 next 체인은 순서대로 다시 잇는다. found step 의 on_true/on_false 는 호출자가
    (전체 순서를 알아야 정할 수 있으므로) 나중에 덮어쓴다.
    """
    prefix = f"z{index}"
    new_block = []
    for step, suffix in zip(template, ZONE_BLOCK_SUFFIXES):
        s = copy.deepcopy(step)
        s["id"] = f"{prefix}_{suffix}"
        s["args"] = _rewrite_zone_refs(s.get("args", {}), prefix)
        if "condition" in s:
            s["condition"] = _rewrite_zone_refs(s["condition"], prefix)
        new_block.append(s)

    for i in range(len(new_block) - 1):
        if "next" in new_block[i]:
            new_block[i]["next"] = new_block[i + 1]["id"]

    new_block[0]["args"]["name"] = zone_name
    return new_block


def normalize_block_for_compare(block: list[dict]) -> list[dict]:
    """구역 블록에서 "위치마다 달라지는 것"(id·zone 이름·내부 next·found 분기 대상)을 지우고
    "정책상 고정이어야 하는 것"(type·layer·tool·args 나머지·match·poll_interval·timeout 등)만
    남긴다. 두 블록을 이 형태로 비교하면 변형기가 정책을 건드리지 않았는지 확인할 수 있다.
    """
    canon = []
    for step in block:
        s = copy.deepcopy(step)
        s.pop("id", None)
        s.pop("next", None)
        s.pop("on_true", None)
        s.pop("on_false", None)
        s["args"] = _rewrite_zone_refs(s.get("args", {}), "Z")
        if "condition" in s:
            s["condition"] = _rewrite_zone_refs(s["condition"], "Z")
        canon.append(s)
    canon[0]["args"].pop("name", None)
    return canon
