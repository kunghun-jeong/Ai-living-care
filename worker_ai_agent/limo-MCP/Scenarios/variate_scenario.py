"""check_grandma.json 류 시나리오의 변형기 — 정책은 고정한 채 시나리오 개수를 늘린다.

변주 규칙(docs/decisions/2026-08-12-scenario-variator-rules.md 요약):

  고정(정책, 절대 안 바꾼다)
    - 구역 블록 하나의 모양 — resolve_location → pathplanning → moving_path →
      get_path_status(poll) → look_around → detect_objects(poll) → branch(found),
      7 step 고정 순서·tool·layer·args 키. check_object_state 를 부르는 것도 여기 포함.
    - found 분기 정책 — on_true 는 항상 "state_check", on_false 는 다음 구역
      (마지막 구역이면 "go_home_resolve", state_check 를 건너뛴다)
    - 꼬리 블록(state_check → go_home_resolve → go_home_plan → go_home_move →
      go_home_arrive → outcome) — base 와 완전히 동일하게 복사

  변주(이 스크립트가 바꾸는 두 축)
    1. input.object — 확인 대상의 의미적 라벨 (예: "grandma", "dog"). 실제 탐지에 쓰이는
       input.target_class 는 object_bindings.json 매핑으로 따로 채운다
       (docs/decisions/2026-08-12-object-target-class-split.md).
    2. steps[] 의 구역 순서/구성 — base 시나리오에 이미 있는 구역들을 다른 순서·다른
       부분집합으로 재배열

  생성되는 시나리오의 scenario_id 는 base 파일 이름이 아니라 정책 이름
  "check_obj_state_*" 를 쓴다 — "check_grandma_v2" 처럼 base 의 특정 용례(할머니 확인)
  이름이 다른 object(dog 등) 변형에 그대로 붙는 걸 막는다.

  주의: 기하 카메라 시뮬(Perceptions.py SimCameraPerception)은 SIM_PERSON 환경변수 기반이라
  target_class="person" 만 실제로 검증된다. 그 외 target_class 는 구조적으로는 유효하지만
  시뮬 검증 대상이 아니다 — validate_variant.py 가 이를 경고로만 표시한다.

사용:
    cd worker_ai_agent/limo-MCP
    python3 Scenarios/variate_scenario.py Scenarios/check_grandma.json --count 5 --seed 1 \
        --objects grandma,dog
    python3 Scenarios/variate_scenario.py Scenarios/check_grandma.json \
        --zones bedroom,kitchen,entrance --object dog --out Scenarios/check_obj_state_dog.json
"""

import argparse
import random
import sys
from pathlib import Path

from scenario_dsl import (
    load_object_bindings,
    load_scenario,
    rebuild_zone_block,
    resolve_target_class,
    save_scenario,
    split_scenario,
)

DEFAULT_ID_PREFIX = "check_obj_state"


def generate_variant(
    base: dict, zone_order: list[str], object_: str | None = None,
    target_class: str | None = None, scenario_id: str | None = None,
    label: str | None = None, bindings: dict | None = None,
) -> dict:
    zone_blocks, tail = split_scenario(base)
    missing = [z for z in zone_order if z not in zone_blocks]
    if missing:
        raise ValueError(f"base 시나리오에 없는 구역: {missing} (가능: {list(zone_blocks)})")
    if not zone_order:
        raise ValueError("zone_order 가 비어 있다 — 구역을 최소 1개는 골라야 한다")

    steps: list[dict] = []
    for i, zone in enumerate(zone_order, start=1):
        steps.extend(rebuild_zone_block(zone, i, zone_blocks[zone]))

    n = len(zone_order)
    for i in range(n):
        found_step = steps[i * 7 + 6]
        found_step["on_true"] = "state_check"
        found_step["on_false"] = f"z{i + 2}_resolve" if i + 1 < n else "go_home_resolve"

    variant = dict(base)
    variant["scenario_id"] = scenario_id or f"{DEFAULT_ID_PREFIX}_variant"
    if label is not None:
        variant["label"] = label
    variant["steps"] = steps + [dict(s) for s in tail]

    new_input = dict(base.get("input", {}))
    if object_ is not None:
        new_input["object"] = object_
        new_input["target_class"] = target_class or resolve_target_class(object_, bindings)
    elif target_class is not None:
        new_input["target_class"] = target_class
    variant["input"] = new_input
    return variant


def _generate_batch(base: dict, count: int, objects: list[str], min_zones: int | None, seed):
    zones = list(split_scenario(base)[0])
    bindings = load_object_bindings()
    rng = random.Random(seed)
    seen = set()
    variants = []
    lo = min_zones or len(zones)
    attempts, attempt_cap = 0, count * 50
    while len(variants) < count and attempts < attempt_cap:
        attempts += 1
        k = rng.randint(lo, len(zones))
        order = rng.sample(zones, k)
        obj = rng.choice(objects)
        key = (tuple(order), obj)
        if key in seen:
            continue
        seen.add(key)
        idx = len(variants) + 1
        variants.append(
            generate_variant(
                base, order, object_=obj, bindings=bindings,
                scenario_id=f"{DEFAULT_ID_PREFIX}_v{idx}",
                label=f"변형 {idx} — {'→'.join(order)} (object={obj})",
            )
        )
    if len(variants) < count:
        print(
            f"경고: 중복 회피 후 {len(variants)}/{count} 개만 만들었다"
            f" (구역 {len(zones)}개·object {len(objects)}종 조합 한계)",
            file=sys.stderr,
        )
    return variants


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("base", help="기준 시나리오 JSON (check_grandma.json 류)")
    p.add_argument("--zones", help="쉼표구분 구역 순서 — 지정하면 이거 하나만 생성 (예: bedroom,kitchen)")
    p.add_argument("--object", help="--zones 와 함께 쓴다. input.object 값 (object_bindings.json 에 있어야 함)")
    p.add_argument("--target-class", help="--object 대신/함께. object_bindings.json 조회를 건너뛰고 직접 지정")
    p.add_argument("--out", help="--zones 와 함께 쓴다. 출력 경로")
    p.add_argument("--count", type=int, default=5, help="배치 생성 개수 (기본 5, --zones 없을 때)")
    p.add_argument("--objects", default="person", help="배치 생성용 쉼표구분 object 후보 (기본 person)")
    p.add_argument("--min-zones", type=int, default=None, help="부분집합 최소 구역 수 (기본: 전체)")
    p.add_argument("--seed", type=int, default=None)
    p.add_argument("--out-dir", default=None, help="배치 출력 디렉터리 (기본: base 와 같은 디렉터리)")
    args = p.parse_args()

    base = load_scenario(args.base)

    if args.zones:
        order = [z.strip() for z in args.zones.split(",") if z.strip()]
        variant = generate_variant(
            base, order, object_=args.object, target_class=args.target_class,
            scenario_id=f"{DEFAULT_ID_PREFIX}_custom",
            label=f"변형(수동) — {'→'.join(order)}" + (f" (object={args.object})" if args.object else ""),
        )
        out_path = Path(args.out) if args.out else Path(args.base).parent / f"{variant['scenario_id']}.json"
        save_scenario(variant, out_path)
        print(f"wrote {out_path}")
        return 0

    objects = [o.strip() for o in args.objects.split(",") if o.strip()]
    variants = _generate_batch(base, args.count, objects, args.min_zones, args.seed)
    out_dir = Path(args.out_dir) if args.out_dir else Path(args.base).parent
    for v in variants:
        out_path = out_dir / f"{v['scenario_id']}.json"
        save_scenario(v, out_path)
        print(f"wrote {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
