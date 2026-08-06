"""MCP_server.py를 통해 카메라 스냅샷을 저장하고 YOLO 검출 결과를 출력하는
커맨드라인 클라이언트.

시뮬레이션이 이미 떠 있는 상태에서 실행한다 (별도 터미널).

사용:
    source /opt/ros/jazzy/setup.bash
    cd limo-MCP
    python3 Scenarios/capture_and_detect.py [저장할_경로.jpg]
"""

import asyncio
import base64
import os
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SERVER_PATH = os.path.join(os.path.dirname(__file__), "..", "MCP_server", "MCP_server.py")


async def main(out_path: str) -> None:
    params = StdioServerParameters(
        command="python3",
        args=[SERVER_PATH],
        env=dict(os.environ),
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            snap = await session.call_tool("get_camera_snapshot", {})
            for item in snap.content:
                if getattr(item, "type", None) == "text":
                    print("snapshot meta:", item.text)
                else:
                    data = item.data
                    raw = base64.b64decode(data) if isinstance(data, str) else data
                    with open(out_path, "wb") as f:
                        f.write(raw)
                    print(f"saved snapshot -> {out_path} ({len(raw)} bytes)")

            print("running detect_objects (첫 호출은 YOLO 모델 로딩 때문에 몇 초 걸릴 수 있음)...")
            det = await session.call_tool("detect_objects", {"min_conf": 0.25})
            for item in det.content:
                print("detections:", item.text)


if __name__ == "__main__":
    output = sys.argv[1] if len(sys.argv) > 1 else "snapshot.jpg"
    asyncio.run(main(output))
