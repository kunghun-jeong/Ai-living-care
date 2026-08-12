"""variate_scenario.py 가 만든 시나리오를 검증한다.

두 층위로 확인한다:

  1. 구조 검증(모든 run_scenario.py 스키마 시나리오에 적용) — id 중복, 미지 tool, next/
     on_true/on_false 가 존재하지 않는 step 을 가리키는지, 첫 step 에서 시작해 도달 못 하는
     step 이 있는지, "success"/"fail" 이 실제로 도달 가능한지.
  2. 정책 불변 검증(--base 를 줬을 때만, check_grandma.json 류) — 변형기가 바꾸면 안 되는
     것(구역 블록의 모양·found 분기 정책·꼬리 블록)을 실제로 안 바꿨는지 base 와 대조한다.
     이건 run_scenario.py 로 실제 실행하지 않고도 "변형기가 정책을 지켰다"를 정적으로
     증명하는 층이다 — RViz 시뮬 기반 검증기(별도 태스크)와는 역할이 다르다.

target_class 값이 "person" 이 아니면 실행 자체는 막지 않고 경고만 낸다 — 기하 카메라 시뮬이
SIM_PERSON 만 지원해서 다른 클래스는 구조는 유효해도 시뮬 실행으로 확인된 적이 없기 때문
(object 는 의미적 라벨일 뿐이라 검증 대상이 아니다 — 실제 탐지 대조는 target_class 가 한다).

사용:
    cd worker_ai_agent/limo-MCP
    python3 Scenarios/validate_variant.py Scenarios/check_grandma_v1.json --base Scenarios/check_grandma.json
    python3 Scenarios/validate_variant.py Scenarios/*.json --base Scenarios/check_grandma.json
"""

import argparse
import sys
from pathlib import Path

from scenario_dsl import KNOWN_TOOLS, STEP_TYPES, load_scenario, normalize_block_for_compare, split_scenario

SIM_VERIFIED_OBJECTS = {"person"}


def _structural_errors(scenario: dict) -> list[str]:
    errors = []
    steps = scenario.get("steps")
    if not steps:
        return ["steps[] 가 없거나 비어 있다"]

    by_id = {}
    for i, s in enumerate(steps):
        sid = s.get("id")
        if not sid:
            errors.append(f"id 없는 step: {s}")
            continue
        if sid in by_id:
            errors.append(f"id 중복: {sid!r}")
        by_id[sid] = s
    order_index = {s["id"]: i for i, s in enumerate(steps) if "id" in s}

    for i, s in enumerate(steps):
        sid = s.get("id", "<no-id>")
        stype = s.get("type")
        if stype not in STEP_TYPES:
            errors.append(f"[{sid}] 알 수 없는 type: {stype!r}")
            continue
        if stype in ("call", "poll_until_match"):
            tool = s.get("tool")
            if tool not in KNOWN_TOOLS:
                errors.append(f"[{sid}] 알 수 없는 tool: {tool!r}")
            targets = [s["next"]] if "next" in s else []
        else:  # branch
            condition = s.get("condition")
            if not condition:
                errors.append(f"[{sid}] branch 인데 condition 이 없다")
            else:
                cond_step_id = condition.partition(".")[0]
                if cond_step_id not in by_id:
                    errors.append(f"[{sid}] condition 이 존재하지 않는 step 을 가리킨다: {condition!r}")
                elif order_index[cond_step_id] >= i:
                    errors.append(
                        f"[{sid}] condition 이 자기 자신이거나 아직 실행 전인 step 을 가리킨다: {condition!r}"
                    )
            targets = [s.get("on_true"), s.get("on_false")]
        for t in targets:
            if t is None:
                continue
            if t not in ("success", "fail") and t not in by_id:
                errors.append(f"[{sid}] 존재하지 않는 대상 참조: {t!r}")

    # 도달성 — 첫 step 에서 시작해 success/fail 까지 갈 수 있는가, 고립된 step 은 없는가
    def default_next(idx: int) -> str:
        return steps[idx + 1]["id"] if idx + 1 < len(steps) else "success"

    visited = set()
    stack = [steps[0]["id"]] if steps and "id" in steps[0] else []
    reached_success = reached_fail = False
    while stack:
        cur = stack.pop()
        if cur in ("success", "fail"):
            reached_success |= cur == "success"
            reached_fail |= cur == "fail"
            continue
        if cur in visited or cur not in by_id:
            continue
        visited.add(cur)
        s = by_id[cur]
        idx = order_index[cur]
        if s.get("type") == "branch":
            for t in (s.get("on_true"), s.get("on_false")):
                if t:
                    stack.append(t)
        else:
            stack.append(s.get("next", default_next(idx)))

    unreached = set(by_id) - visited
    if unreached:
        errors.append(f"첫 step 에서 도달 불가능한 step: {sorted(unreached)}")
    if not reached_success:
        errors.append('"success" 로 끝나는 경로가 없다')

    return errors


def _policy_errors(variant: dict, base: dict) -> list[str]:
    errors = []
    try:
        v_blocks, v_tail = split_scenario(variant)
    except ValueError as e:
        return [f"구역 블록 파싱 실패: {e}"]
    try:
        b_blocks, b_tail = split_scenario(base)
    except ValueError as e:
        return [f"base 구역 블록 파싱 실패: {e}"]

    unknown_zones = [z for z in v_blocks if z not in b_blocks]
    if unknown_zones:
        errors.append(f"base 에 없는 구역이 등장한다: {unknown_zones}")

    for zone, block in v_blocks.items():
        if zone in unknown_zones:
            continue
        if normalize_block_for_compare(block) != normalize_block_for_compare(b_blocks[zone]):
            errors.append(f"구역 '{zone}' 블록의 정책(모양)이 base 와 다르다")

    if v_tail != b_tail:
        errors.append("꼬리 블록(state_check..outcome)이 base 와 다르다")

    zone_order = list(v_blocks)
    n = len(zone_order)
    for i in range(n):
        found = v_blocks[zone_order[i]][6]
        if found.get("on_true") != "state_check":
            errors.append(f"구역 '{zone_order[i]}' found.on_true 가 state_check 가 아니다")
        expected_false = f"z{i + 2}_resolve" if i + 1 < n else "go_home_resolve"
        if found.get("on_false") != expected_false:
            errors.append(
                f"구역 '{zone_order[i]}' found.on_false 가 정책과 다르다: "
                f"{found.get('on_false')!r} != {expected_false!r}"
            )

    return errors


def validate_file(path: Path, base: dict | None) -> tuple[bool, list[str], list[str]]:
    scenario = load_scenario(path)
    errors = _structural_errors(scenario)
    warnings = []

    input_block = scenario.get("input", {})
    target_class = input_block.get("target_class")
    if target_class and target_class not in SIM_VERIFIED_OBJECTS:
        obj = input_block.get("object", target_class)
        warnings.append(
            f"object={obj!r} -> target_class={target_class!r} 는 기하 카메라 시뮬로"
            " 검증된 적 없다 (SIM_PERSON 전용)"
        )

    if base is not None and not errors:
        errors.extend(_policy_errors(scenario, base))

    return (not errors), errors, warnings


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("targets", nargs="+", help="검증할 시나리오 JSON (여러 개 가능)")
    p.add_argument("--base", help="정책 불변 검증에 쓸 기준 시나리오 (check_grandma.json 류)")
    args = p.parse_args()

    base = load_scenario(args.base) if args.base else None
    all_ok = True
    for target in args.targets:
        path = Path(target)
        ok, errors, warnings = validate_file(path, base)
        all_ok &= ok
        status = "PASS" if ok else "FAIL"
        print(f"[{status}] {path}")
        for w in warnings:
            print(f"    warn: {w}")
        for e in errors:
            print(f"    fail: {e}")

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
