#!/usr/bin/env python3
"""시나리오 2를 기존 A* 기하 시뮬레이터로 RViz에 재생한다.

Gazebo와 Nav2는 사용하지 않는다. ``tools/limo-patrol-viz/patrol_viz.py``의
맵 판독, 장애물 팽창, A*, RViz publisher를 그대로 재사용하고 경유지만
주방 -> 요청 시작점으로 교체한다.
"""

from __future__ import annotations

import importlib.util
import math
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from manager_ai_agent.mcp_client.run_scenario2 import build_policies


PATROL_VIZ_PATH = REPO_ROOT / "tools" / "limo-patrol-viz" / "patrol_viz.py"
SCENARIO2_UTTERANCE = "물 갖다줘"
SCENARIO2_START = {"x": 3.5, "y": 1.0, "frame": "map", "yaw_deg": 0.0}


def _scenario2_waypoints() -> list[tuple[float, float]]:
    _, low_level_policy = build_policies(SCENARIO2_UTTERANCE, SCENARIO2_START)
    return [
        (waypoint["x"], waypoint["y"])
        for waypoint in low_level_policy["navigation"]["waypoints"]
    ]


def _load_patrol_viz():
    spec = importlib.util.spec_from_file_location("scenario2_patrol_backend", PATROL_VIZ_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load A* visualizer: {PATROL_VIZ_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _build_round_trip_timeline(backend, waypoints):
    """기존 운동학과 A*를 사용해 look-around 없는 왕복 궤적을 만든다."""

    timeline = []
    x, y, yaw = backend.SPAWN

    def emit() -> None:
        timeline.append((x, y, yaw, False))

    for goal_x, goal_y in waypoints:
        path = backend.astar((x, y), (goal_x, goal_y))
        if not path:
            raise RuntimeError(f"A* path not found: {(x, y)} -> {(goal_x, goal_y)}")

        for waypoint_x, waypoint_y in path[1:]:
            target_yaw = math.atan2(waypoint_y - y, waypoint_x - x)
            delta_yaw = (target_yaw - yaw + math.pi) % (2 * math.pi) - math.pi
            turn_steps = max(1, int(abs(delta_yaw) / backend.V_ANG / backend.DT))
            for _ in range(turn_steps):
                yaw += delta_yaw / turn_steps
                emit()

            distance = math.hypot(waypoint_x - x, waypoint_y - y)
            move_steps = max(1, int(distance / backend.V_LIN / backend.DT))
            start_x, start_y = x, y
            for step in range(move_steps):
                fraction = (step + 1) / move_steps
                x = start_x + (waypoint_x - start_x) * fraction
                y = start_y + (waypoint_y - start_y) * fraction
                emit()

    return timeline


def main() -> None:
    backend = _load_patrol_viz()
    waypoints = _scenario2_waypoints()
    backend.PATROL = waypoints
    backend.PERSON = (1000.0, 1000.0)  # 시나리오 1의 사람 마커/검출을 화면 밖으로 제외한다.
    backend.build_timeline = lambda: _build_round_trip_timeline(backend, waypoints)
    backend.main()


if __name__ == "__main__":
    main()
