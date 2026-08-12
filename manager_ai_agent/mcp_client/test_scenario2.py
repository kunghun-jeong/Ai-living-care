"""시나리오 2의 ROS2 비의존 회귀 테스트."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import unittest

from manager_ai_agent.manager_ai_core.policy_generation.bring_water_policy import (
    UnsupportedUtterance,
    generate_high_level_policy,
)
from manager_ai_agent.mcp_client.run_scenario2 import (
    DryRunToolClient,
    build_policies,
    execute_policy,
)


class Scenario2Test(unittest.TestCase):
    def test_natural_language_becomes_truthful_rehearsal_policy(self) -> None:
        ids = iter(("intent123", "policy456"))
        policy = generate_high_level_policy(
            "물 갖다줘",
            now=lambda: datetime(2026, 8, 10, tzinfo=timezone.utc),
            id_factory=lambda: next(ids),
        )

        self.assertEqual(policy["intent_id"], "int-intent123")
        self.assertEqual(policy["policy_id"], "pol-policy456")
        self.assertEqual(policy["rule"]["action"]["action_type"], "visit-source-and-return")
        self.assertEqual(policy["rule"]["condition"]["modality"], "navigation-rehearsal")
        self.assertIn("object-pickup", policy["context"]["deferred_skills"])

    def test_unsupported_natural_language_fails_closed(self) -> None:
        with self.assertRaises(UnsupportedUtterance):
            generate_high_level_policy("창문 열어줘")

    def test_translator_uses_world_kitchen_then_original_start(self) -> None:
        _, policy = build_policies(
            "물 갖다줘", {"x": 3.5, "y": 1.0, "frame": "map", "yaw_deg": 0.0}
        )
        waypoints = policy["navigation"]["waypoints"]

        self.assertEqual(
            [point["location_label"] for point in waypoints],
            ["kitchen", "request_origin"],
        )
        self.assertEqual((waypoints[0]["x"], waypoints[0]["y"]), (6.9, -3.05))
        self.assertEqual((waypoints[1]["x"], waypoints[1]["y"]), (3.5, 1.0))
        self.assertFalse(policy["deferred_operations"][0]["enabled"])
        self.assertFalse(policy["deferred_operations"][1]["enabled"])

    def test_dry_run_completes_both_waypoints(self) -> None:
        _, policy = build_policies(
            "물 갖다줘", {"x": 3.5, "y": 1.0, "frame": "map", "yaw_deg": 0.0}
        )
        result = asyncio.run(
            execute_policy(DryRunToolClient(), policy, timeout_sec=1.0, poll_interval=0.0)
        )

        self.assertTrue(result["completed"])
        self.assertEqual(result["visited"], ["kitchen", "request_origin"])


if __name__ == "__main__":
    unittest.main()
