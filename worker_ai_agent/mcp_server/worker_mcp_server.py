"""두 번째 stdio MCP 서버 — nav2_move/camera_stream/yolo_reasoning wrapper를 노출한다 (실험 · 미승인).

`limo-MCP/MCP_server/MCP_server.py`(정본, D-14 원본 보존)는 손대지 않는다. 이 파일은
별도 프로세스로 떠서 같은 ActionModule/PerceptionModule/ReasoningModule을 재사용하되,
디렉터리별로 분리된 새 wrapper(action/nav2_move.py · perception/camera_stream.py ·
reasoning/yolo_reasoning.py)를 통해서만 호출한다. 자세한 배경은
docs/decisions/2026-08-19-worker-functions-and-a2a-store.md 참조.

실행: python3 worker_mcp_server.py   (사전에 `pip install mcp`, ROS2 환경 source 필요)
원본 MCP_server.py와 동시에 띄울 수 있다 — 노드 이름·서버 이름이 다르다.
"""

import contextlib
import json
import os
import sys
import threading

import numpy as np
import rclpy
from rclpy.node import Node

from mcp.server.mcpserver import Image, MCPServer

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "limo-MCP", "Worker_functions"))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "action"))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "perception"))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "reasoning"))

from Actions import ActionModule
from Perceptions import PerceptionModule
from Reasonings import ReasoningModule, yolo_detect

from nav2_move import nav2_cancel as _nav2_cancel
from nav2_move import nav2_move as _nav2_move
from nav2_move import nav2_move_waypoints as _nav2_move_waypoints
from nav2_move import nav2_status as _nav2_status
from camera_stream import camera_stream as _camera_stream
from yolo_reasoning import yolo_reasoning as _yolo_reasoning

CROP_MAX_PX = 512  # LLM에 올리는 이미지 크기 상한


def _plan_fn(_start: dict, goal: dict) -> list:
    """MCP_server.py와 동일 — 목표 지점을 검증만 하고 그대로 돌려준다."""
    if not goal or "x" not in goal or "y" not in goal:
        return []
    return [goal]


def _encode_jpeg(frame) -> bytes:
    import io

    from PIL import Image as PILImage

    img = PILImage.fromarray(frame)
    scale = min(1.0, CROP_MAX_PX / max(img.size))
    if scale < 1.0:
        img = img.resize((int(img.width * scale), int(img.height * scale)))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return buf.getvalue()


def _crop_fn(frame, bbox) -> bytes:
    h, w = frame.shape[:2]
    if bbox is None:
        crop = frame
    else:
        x1, y1, x2, y2 = (int(v) for v in bbox)
        mx, my = int((x2 - x1) * 0.15), int((y2 - y1) * 0.15)
        x1, y1 = max(0, x1 - mx), max(0, y1 - my)
        x2, y2 = min(w, x2 + mx), min(h, y2 + my)
        crop = frame[y1:y2, x1:x2]
        if crop.size == 0:
            crop = frame
    return _encode_jpeg(crop)


class WorkerFunctionsNode(Node):
    """MCP_server.py의 LimoGatewayNode와 같은 구성이지만, limo-MCP 원본과 이름이 겹치지
    않도록 별도 노드명을 쓴다 — 두 서버가 동시에 떠도 충돌하지 않는다."""

    def __init__(self):
        super().__init__("limo_worker_functions_gateway")
        self.action = ActionModule(self)
        self.perception = PerceptionModule(self)
        self.reasoning = ReasoningModule(
            plan_fn=_plan_fn,
            detect_fn=yolo_detect,
            crop_fn=_crop_fn,
            frame_source=self.perception.get_latest_frame,
        )


rclpy.init()
_node = WorkerFunctionsNode()
_spin_thread = threading.Thread(target=rclpy.spin, args=(_node,), daemon=True)
_spin_thread.start()

# stdio 트랜스포트는 stdout을 JSON-RPC 전용으로 쓴다 — MCP_server.py와 동일한 이유로
# YOLO 첫 가중치 다운로드 진행표시줄을 stderr로 돌려놓는다. 제거하지 말 것.
with contextlib.redirect_stdout(sys.stderr):
    try:
        yolo_detect(np.zeros((32, 32, 3), dtype=np.uint8))
    except Exception as exc:
        print(f"YOLO warm-up failed (will retry lazily on first real call): {exc!r}", file=sys.stderr)

mcp = MCPServer("limo-worker-fn")


@mcp.tool()
def nav2_move(x: float, y: float, frame: str = "map", yaw_deg: float | None = None) -> dict:
    """목표 좌표 하나로 이동을 시작한다."""
    return _nav2_move(_node.action, x, y, frame, yaw_deg)


@mcp.tool()
def nav2_move_waypoints(waypoints: list) -> dict:
    """웨이포인트 리스트를 순서대로 이동한다."""
    return _nav2_move_waypoints(_node.action, waypoints)


@mcp.tool()
def nav2_cancel() -> dict:
    """진행 중인 목표/시퀀스를 취소한다."""
    return _nav2_cancel(_node.action)


@mcp.tool()
def nav2_status() -> dict:
    """현재 내비게이션 상태를 반환한다."""
    return _nav2_status(_node.action)


@mcp.tool()
def camera_stream():
    """카메라의 최신 프레임을 사진(JPEG)으로 가져온다."""
    item = _camera_stream(_node.perception)
    if item is None:
        return {"image": None, "reason": "no frame available yet"}
    return [
        json.dumps({"frame_id": item["frame_id"], "stamp": item["stamp"]}),
        Image(data=_encode_jpeg(item["frame"]), format="jpeg"),
    ]


@mcp.tool()
def yolo_reasoning(min_conf: float = 0.4) -> dict:
    """카메라의 최신 프레임에서 YOLO로 물체를 검출한다."""
    item = _camera_stream(_node.perception)
    if item is None:
        return {"detections": [], "reason": "no frame available yet"}
    out = _yolo_reasoning(_node.reasoning, item["frame"], min_conf)
    out["frame_id"] = item["frame_id"]
    return out


if __name__ == "__main__":
    mcp.run(transport="stdio")
