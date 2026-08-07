"""Action/Reasoning 모듈을 묶는 MCP 서버.

Reasoning이 목표를 "계획"(plan_path)해서 Action에 넘기면(send_goal_sequence)
로봇이 Nav2를 통해 실제로 움직인다. plan_path는 목표 지점을 검증/정리만 하고
실제 전역 경로계획은 각 웨이포인트마다 Nav2의 NavigateToPose가 내부적으로
수행한다.

실행: python3 MCP_server.py   (사전에 `pip install mcp`, ROS2 환경 source 필요)
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

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "Worker_functions"))

from Actions import ActionModule
from Perceptions import PerceptionModule
from Reasonings import ReasoningModule, yolo_detect

CROP_MAX_PX = 512  # LLM에 올리는 이미지 크기 상한


def _plan_fn(_start: dict, goal: dict) -> list:
    """단순 웨이포인트 전달: 목표 지점을 검증만 하고 그대로 돌려준다.

    실제 전역 경로계획은 send_goal_sequence가 각 웨이포인트마다 보내는
    NavigateToPose 액션이 Nav2 내부에서 다시 수행하므로 여기서 별도로
    ComputePathToPose 등을 호출할 필요가 없다.
    """
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
    """bbox 영역을 여유 있게 잘라 JPEG으로 인코딩한다."""
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


class LimoGatewayNode(Node):
    def __init__(self):
        super().__init__("limo_mcp_gateway")
        self.action = ActionModule(self)
        self.perception = PerceptionModule(self)
        self.reasoning = ReasoningModule(
            plan_fn=_plan_fn,
            detect_fn=yolo_detect,
            crop_fn=_crop_fn,
            frame_source=self.perception.get_latest_frame,
        )


rclpy.init()
_node = LimoGatewayNode()
_spin_thread = threading.Thread(target=rclpy.spin, args=(_node,), daemon=True)
_spin_thread.start()

# 첫 detect_objects 호출 때 YOLO 가중치를 처음 내려받으면 진행 표시줄이 stdout으로
# 나가는데, stdio 트랜스포트는 stdout을 MCP JSON-RPC 프로토콜 전용으로 쓰기 때문에
# 그 출력이 프로토콜을 깨뜨린다. mcp.run()으로 stdout을 넘기기 전에 미리 한 번
# 돌려서(더미 프레임) 다운로드/로딩을 끝내고, 그 출력은 stderr로 돌려놓는다.
with contextlib.redirect_stdout(sys.stderr):
    try:
        yolo_detect(np.zeros((32, 32, 3), dtype=np.uint8))
    except Exception as exc:
        print(f"YOLO warm-up failed (will retry lazily on first real call): {exc!r}", file=sys.stderr)

mcp = MCPServer("limo-worker")


@mcp.tool()
def plan_and_navigate(x: float, y: float, frame: str = "map", yaw_deg: float = None) -> dict:
    """목표 좌표까지 경로를 계획하고 바로 이동을 시작한다."""
    start = _node.action.last_goal or {"x": 0.0, "y": 0.0}
    goal = {"x": x, "y": y, "frame": frame}
    if yaw_deg is not None:
        goal["yaw_deg"] = yaw_deg

    planned = _node.reasoning.plan_path(start, goal)
    waypoints = planned.get("waypoints")
    if not waypoints:
        return {"started": False, "reason": planned.get("reason", "invalid goal")}
    return _node.action.send_goal_sequence(waypoints)


@mcp.tool()
def navigate_waypoints(waypoints: list) -> dict:
    """웨이포인트 리스트([{x, y, frame?, yaw_deg?}, ...])를 순서대로 이동한다."""
    return _node.action.send_goal_sequence(waypoints)


@mcp.tool()
def get_status() -> dict:
    """현재 내비게이션 상태, 마지막 목표, 시퀀스 진행 상황을 반환한다."""
    a = _node.action
    return {
        "status": a.status,
        "last_goal": a.last_goal,
        "sequence_progress": a.sequence_progress,
        "sequence_result": a.sequence_result,
    }


@mcp.tool()
def get_camera_snapshot():
    """카메라의 최신 프레임을 사진(JPEG)으로 가져온다."""
    item = _node.perception.get_latest_frame()
    if item is None:
        return {"image": None, "reason": "no frame available yet"}
    return [
        json.dumps({"frame_id": item["frame_id"], "stamp": item["stamp"]}),
        Image(data=_encode_jpeg(item["frame"]), format="jpeg"),
    ]


@mcp.tool()
def detect_objects(min_conf: float = 0.4) -> dict:
    """카메라의 최신 프레임에서 YOLO로 물체를 검출해 클래스/신뢰도/bbox 목록을 반환한다."""
    item = _node.perception.get_latest_frame()
    if item is None:
        return {"detections": [], "reason": "no frame available yet"}

    out = _node.reasoning.detect_objects(item["frame"])
    detections = out.get("detections")
    if detections is None:
        return {"detections": [], "reason": out.get("reason", "detection failed")}

    return {
        "frame_id": item["frame_id"],
        "detections": [d for d in detections if d.get("conf", 0.0) >= min_conf],
    }


@mcp.tool()
def cancel() -> dict:
    """진행 중인 목표/웨이포인트 시퀀스를 취소한다."""
    if _node.action.is_running_sequence():
        return _node.action.cancel_goal_sequence()
    return _node.action.cancel_goal()


if __name__ == "__main__":
    mcp.run(transport="stdio")
