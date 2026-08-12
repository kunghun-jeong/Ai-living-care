"""시나리오 2: '물 갖다줘' -> 주방 방문 -> 요청 시작점 복귀.

기본 dry-run은 ROS2 없이 전체 정책 변환과 실행 제어 흐름을 검증한다.
``--mode live``는 기존 limo-MCP 서버를 stdio로 띄우고 L4
``navigate_waypoints``를 호출한다. L2 ``execute_policy``가 아직 없어서 이 직접 호출은
Phase 0 데모용 임시 경로다.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path
import sys
import time
from typing import Protocol


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from manager_ai_agent.manager_ai_core.policy_generation.bring_water_policy import (
    generate_high_level_policy,
)
from worker_ai_agent.worker_ai_core.policy_translator.policy_translator import (
    translate_to_limo_policy,
)


KITCHEN = {
    "x": 6.90,
    "y": -3.05,
    "frame": "map",
    # WORLD.md §2의 CookingBench 관측 yaw -0.14 rad를 degree로 옮긴 값이다.
    "yaw_deg": -8.02,
}


class ToolClient(Protocol):
    async def call_tool(self, name: str, arguments: dict) -> dict:
        """MCP tool과 같은 이름/인자 계약으로 호출한다."""


class DryRunToolClient:
    """ROS2 없이 navigate/status 호출 순서를 재현하는 메모리 백엔드."""

    def __init__(self) -> None:
        self._waypoints: list[dict] = []
        self._polls = 0

    async def call_tool(self, name: str, arguments: dict) -> dict:
        if name == "navigate_waypoints":
            self._waypoints = list(arguments.get("waypoints", []))
            if not self._waypoints:
                return {"started": False, "reason": "empty waypoint list"}
            return {"started": True}

        if name == "get_status":
            self._polls += 1
            if self._polls < 2:
                return {
                    "status": "navigating",
                    "sequence_progress": {"index": 0, "total": len(self._waypoints)},
                    "sequence_result": None,
                }
            return {
                "status": "succeeded",
                "sequence_progress": {
                    "index": len(self._waypoints) - 1,
                    "total": len(self._waypoints),
                },
                "sequence_result": {
                    "completed": len(self._waypoints),
                    "total": len(self._waypoints),
                    "interrupted": False,
                },
            }

        if name == "cancel":
            return {"cancelled": True}
        return {"error": f"unknown tool: {name}"}


class LiveMcpToolClient:
    """MCP ClientSession 결과를 일반 dict로 정규화한다."""

    def __init__(self, session) -> None:
        self._session = session

    async def call_tool(self, name: str, arguments: dict) -> dict:
        result = await self._session.call_tool(name, arguments)
        for item in getattr(result, "content", []):
            text = getattr(item, "text", None)
            if not text:
                continue
            try:
                payload = json.loads(text)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict):
                return payload
        return {"error": f"tool {name!r} returned no JSON object"}


def build_policies(utterance: str, start: dict) -> tuple[dict, dict]:
    high_level = generate_high_level_policy(utterance)

    def resolve_place(place: str) -> dict | None:
        locations = {"kitchen": KITCHEN, "request_origin": start}
        return locations.get(place)

    low_level = translate_to_limo_policy(high_level, resolve_place=resolve_place)
    return high_level, low_level


async def execute_policy(
    client: ToolClient,
    low_level_policy: dict,
    *,
    timeout_sec: float,
    poll_interval: float,
) -> dict:
    execution = low_level_policy["execution"]
    started = await client.call_tool(execution["tool"], execution["arguments"])
    if not started.get("started"):
        return {
            "completed": False,
            "reason": started.get("reason", started.get("error", "rejected")),
        }

    deadline = time.monotonic() + timeout_sec
    while time.monotonic() < deadline:
        status = await client.call_tool("get_status", {})
        if status.get("error"):
            await client.call_tool("cancel", {})
            return {"completed": False, "reason": status["error"]}
        sequence_result = status.get("sequence_result")
        if sequence_result is not None:
            total = len(low_level_policy["navigation"]["waypoints"])
            completed = sequence_result.get("completed", 0)
            ok = completed == total and not sequence_result.get("interrupted", False)
            return {
                "completed": ok,
                "status": status.get("status"),
                "sequence_result": sequence_result,
                "visited": [
                    waypoint["location_label"]
                    for waypoint in low_level_policy["navigation"]["waypoints"][:completed]
                ],
                "deferred_operations": low_level_policy["deferred_operations"],
            }
        await asyncio.sleep(poll_interval)

    await client.call_tool("cancel", {})
    return {"completed": False, "reason": "client timeout; navigation cancelled"}


async def _run_live(low_level: dict, timeout_sec: float, poll_interval: float) -> dict:
    try:
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client
    except ImportError as exc:
        raise RuntimeError(
            "live mode requires the packages in worker_ai_agent/limo-MCP/requirements.txt"
        ) from exc

    server = REPO_ROOT / "worker_ai_agent" / "limo-MCP" / "MCP_server" / "MCP_server.py"
    params = StdioServerParameters(command="python3", args=[str(server)], env=dict(os.environ))
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            return await execute_policy(
                LiveMcpToolClient(session),
                low_level,
                timeout_sec=timeout_sec,
                poll_interval=poll_interval,
            )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("utterance", nargs="?", default="물 갖다줘")
    parser.add_argument("--mode", choices=("dry-run", "live"), default="dry-run")
    parser.add_argument("--start-x", type=float, default=3.5)
    parser.add_argument("--start-y", type=float, default=1.0)
    parser.add_argument("--start-yaw-deg", type=float, default=0.0)
    parser.add_argument(
        "--timeout",
        type=float,
        default=None,
        help="wall-clock timeout in seconds (default: policy report.timeout_sec)",
    )
    parser.add_argument("--poll-interval", type=float, default=1.0)
    return parser.parse_args()


async def main() -> int:
    args = _parse_args()
    start = {
        "x": args.start_x,
        "y": args.start_y,
        "frame": "map",
        "yaw_deg": args.start_yaw_deg,
    }
    high_level, low_level = build_policies(args.utterance, start)
    timeout_sec = args.timeout if args.timeout is not None else low_level["report"]["timeout_sec"]

    print("=== L2 high-level policy ===")
    print(json.dumps(high_level, ensure_ascii=False, indent=2))
    print("=== L3 LIMO policy ===")
    print(json.dumps(low_level, ensure_ascii=False, indent=2))

    if args.mode == "dry-run":
        result = await execute_policy(
            DryRunToolClient(), low_level, timeout_sec=timeout_sec, poll_interval=0.0
        )
    else:
        result = await _run_live(low_level, timeout_sec, args.poll_interval)

    print("=== execution result ===")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("completed") else 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
    except (RuntimeError, ValueError) as exc:
        print(f"scenario2 error: {exc}", file=sys.stderr)
        exit_code = 2
    raise SystemExit(exit_code)
