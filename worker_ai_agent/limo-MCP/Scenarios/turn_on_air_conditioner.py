"""MCP_server.py를 통해 turn_on_air_conditioner 시나리오를 왕복 검증하는 클라이언트.

Nav2·Gazebo가 없어도 전체가 검증된다 — resolve_location(KG 룩업) -> pathplanning(A*,
map.pgm 기준) -> moving_path(운동학만 적분하는 소프트웨어 시뮬레이션) -> send_ir_signal
순서로, 전부 Nav2·실물 로봇 없이 동작하는 tool이다 (tools/limo-patrol-viz/patrol_sim.py와
같은 이동 모델을 MCP tool로 노출한 것).

사용:
    source /opt/ros/jazzy/setup.bash
    cd limo-MCP
    python3 Scenarios/turn_on_air_conditioner.py
"""

import asyncio
import json
import os
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SERVER_PATH = os.path.join(os.path.dirname(__file__), "..", "MCP_server", "MCP_server.py")

DEVICE = "air_conditioner"
SET_TEMPERATURE = 24
UNIT = "celsius"


def _as_dict(tool_result) -> dict:
    """CallToolResult.content의 첫 텍스트 블록을 dict로 파싱한다."""
    text = tool_result.content[0].text
    return json.loads(text)


async def main() -> None:
    params = StdioServerParameters(
        command="python3",
        args=[SERVER_PATH],
        env=dict(os.environ),
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            print("[1] resolve_location")
            resolved = _as_dict(await session.call_tool("resolve_location", {"name": DEVICE}))
            print("    ->", resolved)
            if not resolved.get("resolved"):
                print(f"FAIL: {DEVICE} 위치를 해소하지 못했다: {resolved.get('reason')}")
                return

            print("[2] pathplanning")
            planned = _as_dict(
                await session.call_tool(
                    "pathplanning", {"x": resolved["x"], "y": resolved["y"], "frame": resolved["frame"]}
                )
            )
            waypoints = planned.get("waypoints")
            print(f"    -> {len(waypoints) if waypoints else 0} waypoints"
                  + ("" if waypoints else f" (reason: {planned.get('reason')})"))
            if not waypoints:
                print("FAIL: 경로를 찾지 못했다")
                return

            print("[3] moving_path")
            started = _as_dict(await session.call_tool("moving_path", {"waypoints": waypoints}))
            print("    ->", started)
            if not started.get("started"):
                print(f"FAIL: 이동을 시작하지 못했다: {started.get('reason')}")
                return

            print("[4] get_path_status 폴링 (최대 120초)")
            status = {}
            for _ in range(240):
                await asyncio.sleep(0.5)
                status = _as_dict(await session.call_tool("get_path_status", {}))
                if status.get("status") in ("succeeded", "failed", "cancelled"):
                    break
                progress = status.get("progress") or {}
                pose = status.get("pose") or {}
                print(
                    f"    ... {progress.get('index', '?')}/{progress.get('total', '?')}"
                    f"  pos=({pose.get('x', 0):.2f},{pose.get('y', 0):.2f})",
                    end="\r",
                )
            print()
            print("    ->", status)
            if status.get("status") != "succeeded":
                print(f"FAIL: 이동이 succeeded로 끝나지 않았다 (status={status.get('status')})")
                return

            print("[5] send_ir_signal(power_on)")
            power_on = _as_dict(
                await session.call_tool("send_ir_signal", {"device": DEVICE, "command": "power_on"})
            )
            print("    ->", power_on)

            print("[6] send_ir_signal(set_temperature)")
            set_temp = _as_dict(
                await session.call_tool(
                    "send_ir_signal",
                    {
                        "device": DEVICE,
                        "command": "set_temperature",
                        "value": SET_TEMPERATURE,
                        "unit": UNIT,
                    },
                )
            )
            print("    ->", set_temp)
            print("DONE: 시나리오 전체 성공")


if __name__ == "__main__":
    asyncio.run(main())
