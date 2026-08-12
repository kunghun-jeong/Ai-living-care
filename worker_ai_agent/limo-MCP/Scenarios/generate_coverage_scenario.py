"""구역별 라운모어형(보스트로페돈) 커버리지 청소 시나리오를 생성한다.

`clean_room.json`(및 `--rooms`로 부분 생성한 스모크 테스트 파일들)의 정본 생성기다 —
286 step짜리 JSON을 손으로 유지하지 않고 이 스크립트에서 매번 다시 뽑는다. 규칙은
docs/decisions/2026-08-12-boustrophedon-coverage.md 참고.

각 구역을 레인 간격만큼 y로 나눠 줄을 만들고, 줄마다 map.pgm 점유격자에서 벽 여유가
`_ROBOT_RADIUS_M`(pathplanning이 쓰는 것과 동일) 이상인 가장 긴 연속 구간만 왕복한다.
좌표는 절대 지어내지 않는다 — 이 스크립트가 실측(occupancy grid)에서 뽑고,
`Reasonings.astar_plan`으로 home부터 전체 체인이 실제 도달 가능한지 생성 시점에
검증한다(ROS2 불필요, map.pgm 위 순수 A*).

`Reasonings._load_grid`·`_to_px`·`_ROBOT_RADIUS_M`은 밑줄 접두 사설(private) 심볼이지만
일부러 그대로 가져다 쓴다 — pathplanning이 실제로 쓰는 것과 **다른 계산식으로 "갈 수
있다"고 판단하면** 검증이 무의미해지기 때문이다. 이 결합은 의도된 것이다.

사용:
    cd worker_ai_agent/limo-MCP
    python3 Scenarios/generate_coverage_scenario.py                       # 6구역 전부 -> clean_room.json
    python3 Scenarios/generate_coverage_scenario.py --rooms bedroom       # 침실만 -> clean_room_bedroom.json
    python3 Scenarios/generate_coverage_scenario.py --rooms bedroom,kitchen --out Scenarios/foo.json
"""

import argparse
import json
import sys
from collections import OrderedDict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "Worker_functions"))
import Reasonings as R  # noqa: E402  (sys.path 조작 뒤에 import)

HOME = {"x": 3.5, "y": 1.0}


def save_scenario(scenario: dict, path) -> None:
    Path(path).write_text(
        json.dumps(scenario, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
ROBOT_R = R._ROBOT_RADIUS_M  # pathplanning과 동일 기준 — 여기서만 낮춰 잡으면 생성 따로, 실행 따로 논다
LANE_SPACING_DEFAULT = 0.4
MIN_SEG_LEN = 0.5  # 이보다 짧은 조각(대개 가구 틈)은 버린다

# 순서는 check_grandma.json과 맞춘다.
ROOM_ORDER = ["dining_area", "living_room", "bedroom", "upper_left_room", "entrance", "kitchen"]

# (x_lo, x_hi, y_lo, y_hi). dining_area·living_room·bedroom·kitchen 4곳은 WORLD.md §2
# 구역 표를 그대로 썼다. upper_left_room·entrance 두 곳은 §2에 정확히 대응하는 표 항목이
# 없어서(그 표는 카메라 커버리지 계산용 8구역이라 entities.json의 세분화된 이름과 다르다)
# 기존 KG 접근점 주변으로 보수적으로 좁혀 잡았다 — TODO(확인 필요): 진짜 방 경계.
ROOM_BOX = {
    "dining_area": (5.5, 9.3, -1.0, 3.0),
    "living_room": (-3.5, 1.5, -3.0, 3.0),
    "bedroom": (-9.6, -3.4, 0.6, 3.4),
    "upper_left_room": (-8.5, -7.0, -0.2, 0.5),  # 보수적 추정
    "entrance": (1.0, 5.0, -4.4, -3.4),  # 보수적 추정
    "kitchen": (5.5, 9.3, -5.6, -1.0),
}


def rows_for(x_lo, x_hi, y_lo, y_hi, lane_spacing, grid, height):
    """이 박스 안에서 레인 간격만큼 y줄을 내고, 줄마다 가장 긴 주행 가능 구간을 찾는다."""
    dist_m = grid["dist_m"]
    rows = []
    y = y_lo + lane_spacing / 2
    while y <= y_hi:
        xs_ok = []
        x = x_lo
        while x <= x_hi:
            px, py = R._to_px(x, y, height)
            if 0 <= px < grid["width"] and 0 <= py < height and dist_m[py, px] >= ROBOT_R:
                xs_ok.append(x)
            x += 0.05
        segments = []
        if xs_ok:
            seg_start = prev = xs_ok[0]
            for xv in xs_ok[1:]:
                if xv - prev > 0.075:
                    segments.append((seg_start, prev))
                    seg_start = xv
                prev = xv
            segments.append((seg_start, prev))
        segments = [s for s in segments if s[1] - s[0] >= MIN_SEG_LEN]
        if segments:
            longest = max(segments, key=lambda s: s[1] - s[0])
            rows.append((round(y, 2), round(longest[0], 2), round(longest[1], 2)))
        y += lane_spacing
    return rows


def points_for_room(rows):
    """줄마다 진입/이탈 방향을 번갈아 지그재그로 — 왕복 2점씩."""
    pts = []
    for i, (y_, xl, xr) in enumerate(rows):
        if i % 2 == 0:
            pts.append((xl, y_))
            pts.append((xr, y_))
        else:
            pts.append((xr, y_))
            pts.append((xl, y_))
    return pts


def verify_chain(room_points, room_order):
    """home -> 방1 전체 줄 -> ... -> 방N 전체 줄 -> home 을 실제 A*로 순서대로 확인한다."""
    cur = dict(HOME)
    for room in room_order:
        for x, y in room_points[room]:
            goal = {"x": x, "y": y}
            path = R.astar_plan(cur, goal)  # GoalNotReachable이면 여기서 그대로 터진다
            if not path:
                raise RuntimeError(f"경로 없음: {cur} -> {goal} ({room})")
            cur = goal
    if not R.astar_plan(cur, HOME):
        raise RuntimeError(f"경로 없음: {cur} -> home")


def _add_leg(steps, leg_no, x, y):
    prefix = f"leg{leg_no}"
    steps.append({
        "id": f"{prefix}_plan", "type": "call", "layer": "reasoning",
        "tool": "pathplanning", "args": {"x": x, "y": y, "frame": "map"},
        "next": f"{prefix}_move",
    })
    steps.append({
        "id": f"{prefix}_move", "type": "call", "layer": "action",
        "tool": "moving_path", "args": {"waypoints": f"${prefix}_plan.waypoints"},
        "next": f"{prefix}_arrive",
    })
    steps.append({
        "id": f"{prefix}_arrive", "type": "poll_until_match", "layer": "action",
        "tool": "get_path_status", "args": {},
        "match": {"field": "status", "equals": "succeeded"},
        "stop_when": {"tool": "get_path_status", "field": "status", "equals": "failed"},
        "poll_interval": 0.5, "timeout": 90.0, "next": None,  # 아래서 채운다
    })
    return prefix


def build_scenario(room_order, room_points, lane_spacing) -> dict:
    steps = []
    idx_by_id = {}
    leg_no = 0
    room_bounds = []  # (clean_start_id, clean_stop_id)

    for ri, room in enumerate(room_order, start=1):
        start_id, stop_id = f"r{ri}_clean_start", f"r{ri}_clean_stop"
        steps.append({
            "id": start_id, "type": "call", "layer": "action",
            "tool": "send_ir_signal", "args": {"device": "vacuum", "command": "clean_start"},
            "next": None,
        })
        arrive_ids = []
        for x, y in room_points[room]:
            leg_no += 1
            prefix = _add_leg(steps, leg_no, x, y)
            arrive_ids.append(f"{prefix}_arrive")
        steps.append({
            "id": stop_id, "type": "call", "layer": "action",
            "tool": "send_ir_signal", "args": {"device": "vacuum", "command": "clean_stop"},
            "next": None,
        })
        room_bounds.append((start_id, stop_id, arrive_ids))

    idx_by_id = {s["id"]: i for i, s in enumerate(steps)}

    for start_id, stop_id, arrive_ids in room_bounds:
        first_prefix = arrive_ids[0].rsplit("_", 1)[0]
        steps[idx_by_id[start_id]]["next"] = f"{first_prefix}_plan"
        for i, aid in enumerate(arrive_ids):
            nxt = f"{arrive_ids[i + 1].rsplit('_', 1)[0]}_plan" if i + 1 < len(arrive_ids) else stop_id
            steps[idx_by_id[aid]]["next"] = nxt

    for i, (start_id, stop_id, _) in enumerate(room_bounds):
        next_start = room_bounds[i + 1][0] if i + 1 < len(room_bounds) else "go_home_resolve"
        steps[idx_by_id[stop_id]]["next"] = next_start

    tail = [
        {"id": "go_home_resolve", "type": "call", "layer": "reasoning",
         "tool": "resolve_location", "args": {"name": "home"}, "next": "go_home_plan"},
        {"id": "go_home_plan", "type": "call", "layer": "reasoning",
         "tool": "pathplanning",
         "args": {"x": "$go_home_resolve.x", "y": "$go_home_resolve.y", "frame": "$go_home_resolve.frame"},
         "next": "go_home_move"},
        {"id": "go_home_move", "type": "call", "layer": "action",
         "tool": "moving_path", "args": {"waypoints": "$go_home_plan.waypoints"}, "next": "go_home_arrive"},
        {"id": "go_home_arrive", "type": "poll_until_match", "layer": "action",
         "tool": "get_path_status", "args": {},
         "match": {"field": "status", "equals": "succeeded"},
         "stop_when": {"tool": "get_path_status", "field": "status", "equals": "failed"},
         "poll_interval": 0.5, "timeout": 240.0, "next": "success"},
    ]

    n_rows = sum(len(room_points[r]) // 2 for r in room_order)
    scenario = OrderedDict()
    scenario["scenario_id"] = "clean_room" if room_order == ROOM_ORDER else f"clean_room_{'_'.join(room_order)}"
    scenario["label"] = f"보스트로페돈 커버리지 청소 — {'→'.join(room_order)}"
    scenario["input"] = OrderedDict([("intent", "clean_room")])
    scenario["note"] = (
        f"라운모어형(보스트로페돈) 전체 커버리지. {len(room_order)}구역 × 레인 간격 "
        f"{lane_spacing}m로 총 {n_rows}줄. 각 줄은 map.pgm 점유격자에서 벽 여유 {ROBOT_R}m "
        "이상(=pathplanning의 drivable 기준과 동일) 연속 구간 중 가장 긴 것만 쓴다. "
        "좌표는 지어내지 않았다 — generate_coverage_scenario.py가 생성 시점에 뽑고 "
        "home부터 전체 체인 실제 A* 도달 가능함을 확인했다. "
        "구역 진입/이탈마다 send_ir_signal(device=\"vacuum\", ...) 가상 신호를 쓴다 "
        "(docs/decisions/2026-08-12-virtual-vacuum-actuator.md — 실존 장치 아님). "
        "이 파일은 손으로 고치지 않는다 — generate_coverage_scenario.py를 다시 돌린다. "
        "상세는 docs/decisions/2026-08-12-boustrophedon-coverage.md."
    )
    scenario["steps"] = steps + tail
    scenario["fail"] = {"error": "cleaning_path_blocked"}
    return scenario


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--rooms", help="쉼표구분 구역 부분집합 (기본: 6구역 전부, check_grandma.json 순서)")
    p.add_argument("--lane-spacing", type=float, default=LANE_SPACING_DEFAULT)
    p.add_argument("--out", help="출력 경로 (기본: 전부면 Scenarios/clean_room.json, 부분집합이면 이름에 반영)")
    args = p.parse_args()

    room_order = [r.strip() for r in args.rooms.split(",")] if args.rooms else list(ROOM_ORDER)
    unknown = [r for r in room_order if r not in ROOM_BOX]
    if unknown:
        print(f"모르는 구역: {unknown} (가능: {list(ROOM_BOX)})", file=sys.stderr)
        return 1

    grid = R._load_grid()
    height = grid["height"]
    room_points = {
        room: points_for_room(rows_for(*ROOM_BOX[room], args.lane_spacing, grid, height))
        for room in room_order
    }
    empty = [r for r, pts in room_points.items() if not pts]
    if empty:
        print(f"줄이 하나도 안 나온 구역: {empty} — 박스 재검토 필요", file=sys.stderr)
        return 1

    verify_chain(room_points, room_order)  # 실패하면 RuntimeError로 여기서 멈춘다

    scenario = build_scenario(room_order, room_points, args.lane_spacing)

    if args.out:
        out_path = Path(args.out)
    elif room_order == ROOM_ORDER:
        out_path = Path(__file__).parent / "clean_room.json"
    else:
        out_path = Path(__file__).parent / f"clean_room_{'_'.join(room_order)}.json"

    save_scenario(scenario, out_path)
    n_rows = sum(len(room_points[r]) // 2 for r in room_order)
    print(f"wrote {out_path} — {len(scenario['steps'])} step, {n_rows} row, 체인 검증 완료")
    return 0


if __name__ == "__main__":
    sys.exit(main())
