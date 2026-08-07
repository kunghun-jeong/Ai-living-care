"""MCP_server.py를 통해 목표 좌표로 로봇을 이동시키는 커맨드라인 클라이언트.

시뮬레이션이 이미 떠 있는 상태에서 실행한다 (별도 터미널).

사용:
    source /opt/ros/jazzy/setup.bash
    cd limo-MCP
    python3 Scenarios/send_goal.py <x> <y> [yaw_deg]
"""

import asyncio
import os
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SERVER_PATH = os.path.join(os.path.dirname(__file__), "..", "MCP_server", "MCP_server.py")


async def main(x: float, y: float, yaw_deg: float | None, timeout: float = 300.0) -> None:
    params = StdioServerParameters(
        command="python3",
        args=[SERVER_PATH],
        env=dict(os.environ),
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            args = {"x": x, "y": y, "frame": "map"}
            if yaw_deg is not None:
                args["yaw_deg"] = yaw_deg

            started = await session.call_tool("plan_and_navigate", args)
            print("plan_and_navigate:", started.content)
            if '"started": false' in str(started.content).lower():
                print("시작하지 못했다 — 위 reason 확인")
                return

            # F-6 — 예전에는 succeeded/failed 두 개만 봐서, Nav2 가 안 떠 있으면
            # 에러 없이 영원히 돌았다. status 열거값 전부와 벽시계 상한을 본다.
            TERMINAL = ("succeeded", "failed", "cancelled", "rejected", "idle")
            deadline = asyncio.get_event_loop().time() + timeout
            while True:
                await asyncio.sleep(1.0)
                status = await session.call_tool("get_status", {})
                print("status:", status.content)
                text = str(status.content)
                if any(f'"status": "{v}"' in text for v in TERMINAL):
                    break
                if asyncio.get_event_loop().time() > deadline:
                    print(f"{timeout}s 안에 종료 상태에 도달하지 못했다 — 취소를 보낸다")
                    print("cancel:", (await session.call_tool("cancel", {})).content)
                    break


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(f"usage: python3 {sys.argv[0]} <x> <y> [yaw_deg]")
        sys.exit(1)
    goal_x = float(sys.argv[1])
    goal_y = float(sys.argv[2])
    goal_yaw = float(sys.argv[3]) if len(sys.argv) > 3 else None
    asyncio.run(main(goal_x, goal_y, goal_yaw))
