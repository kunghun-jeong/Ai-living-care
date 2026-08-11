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
from typing import Optional

import numpy as np
import rclpy
from rclpy.node import Node

from mcp.server.mcpserver import Image, MCPServer

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "Worker_functions"))
# Phase 0 임시: 정식으로는 KG 접근이 IF-1(Manager AI Core 경유)이어야 하지만,
# Manager AI Core가 아직 코드 0줄이라 Worker Reasoning이 직접 import한다.
# 근거: docs/decisions/2026-08-10-worker-side-kg-lookup-phase0.md
sys.path.append(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "manager_ai_agent", "knowledge_graph")
)

from Actions import ActionModule
from Perceptions import PerceptionModule, sim_camera_from_env
from Reasonings import ReasoningModule, astar_plan, yolo_detect
from Visualization import PoseVisualizer
from kg import KnowledgeGraph

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


_kg = KnowledgeGraph()


class LimoGatewayNode(Node):
    def __init__(self):
        super().__init__("limo_mcp_gateway")
        # SIM_PERSON="x,y" 가 있으면 Gazebo 없이도 인지 단계가 돈다 (기하 시뮬). 없으면 None.
        self.sim_cam = sim_camera_from_env()
        if self.sim_cam is not None:
            self.get_logger().info(f"[SIM-CAM] geometric camera on, person at {self.sim_cam.person}")
        # tools/limo-patrol-viz/patrol.rviz와 같은 토픽으로 moving_path 진행을 RViz2에 스트리밍한다.
        # sim_cam 을 넘기면 1인칭 화면도 /camera/image_raw 로 나간다.
        self.viz = PoseVisualizer(self, sim_cam=self.sim_cam)
        self.action = ActionModule(self, viz=self.viz)
        self.perception = PerceptionModule(self)
        self.reasoning = ReasoningModule(
            plan_fn=_plan_fn,
            detect_fn=yolo_detect,
            crop_fn=_crop_fn,
            frame_source=self.perception.get_latest_frame,
            resolve_fn=_kg.resolve_location,
            astar_fn=astar_plan,
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


def _observe(min_conf: float = 0.4):
    """프레임 하나와 그 안의 검출을 가져온다 — (item, detections, source).

    SIM_PERSON 이 켜져 있으면 "Gazebo 없이 돌린다"는 선언이므로 기하 시뮬을 먼저 본다.
    꺼져 있으면 실제 카메라 + YOLO. 둘 다 없으면 (None, [], None).
    결과에는 항상 source 를 실어 실측과 섞이지 않게 한다.

    시뮬을 먼저 보는 것이 중요하다: PoseVisualizer 가 시뮬 화면을 /camera/image_raw 로
    내보내고 PerceptionModule 이 그 토픽을 구독하므로, 실제 카메라를 먼저 보면 자기가 쏜
    프레임을 실측으로 착각하고 YOLO 로 넘긴다.
    """
    if _node.sim_cam is not None:
        item = _node.sim_cam.get_frame(_node.action.last_sim_pose)
        return item, [d for d in item["detections"] if d.get("conf", 0.0) >= min_conf], "geometric_sim"

    item = _node.perception.get_latest_frame()
    if item is not None:
        out = _node.reasoning.detect_objects(item["frame"])
        dets = out.get("detections")
        if dets is None:
            return item, [], "camera"
        return item, [d for d in dets if d.get("conf", 0.0) >= min_conf], "camera"

    return None, [], None


@mcp.tool()
def get_camera_snapshot():
    """카메라의 최신 프레임을 사진(JPEG)으로 가져온다."""
    item, _, source = _observe()
    if item is None:
        return {"image": None, "reason": "no frame available yet"}
    return [
        json.dumps({"frame_id": item["frame_id"], "stamp": item["stamp"], "source": source}),
        Image(data=_encode_jpeg(item["frame"]), format="jpeg"),
    ]


@mcp.tool()
def detect_objects(min_conf: float = 0.4) -> dict:
    """카메라의 최신 프레임에서 물체를 검출해 클래스/신뢰도/bbox 목록을 반환한다."""
    item, detections, source = _observe(min_conf)
    if item is None:
        return {"detections": [], "reason": "no frame available yet"}
    return {"frame_id": item["frame_id"], "detections": detections, "source": source}


@mcp.tool()
def check_object_state(object_class: str = "person", min_conf: float = 0.4):
    """대상이 찍힌 영역만 크롭해 사진(JPEG)으로 올린다 — 상태 판정은 LLM 이 한다."""
    item, detections, source = _observe(min_conf)
    if item is None:
        return {"image": None, "reason": "no frame available yet"}

    targets = [d for d in detections if d.get("class") == object_class]
    if not targets:
        return {"image": None, "reason": f"{object_class} not in frame",
                "frame_id": item["frame_id"], "source": source}

    best = max(targets, key=lambda d: d.get("conf", 0.0))
    return [
        json.dumps({
            "frame_id": item["frame_id"], "object_class": object_class,
            "bbox": best.get("bbox"), "conf": best.get("conf"),
            "pose": item.get("pose"), "source": source,
        }),
        Image(data=_crop_fn(item["frame"], best.get("bbox")), format="jpeg"),
    ]


@mcp.tool()
def look_around(steps: int = 8, step_deg: float = 45.0, step_duration: float = 1.0) -> dict:
    """제자리에서 둘러본다 (기본 45°×8 = 360°). 비동기 — is_looking_around 로 폴링한다."""
    return _node.action.look_around(steps, step_deg, step_duration)


@mcp.tool()
def is_looking_around() -> dict:
    """look_around 가 아직 도는 중인지와 진행 상황을 반환한다."""
    return _node.action.get_look_around_status()


@mcp.tool()
def interrupt_look_around() -> dict:
    """진행 중인 look_around 를 중단한다 (대상을 찾았을 때)."""
    return _node.action.interrupt_look_around()


@mcp.tool()
def cancel() -> dict:
    """진행 중인 목표/웨이포인트 시퀀스를 취소한다."""
    if _node.action.is_running_sequence():
        return _node.action.cancel_goal_sequence()
    return _node.action.cancel_goal()


@mcp.tool()
def resolve_location(name: str) -> dict:
    """장소·디바이스 이름을 좌표로 해소한다 (KG Phase 0 JSON 룩업). 모르면 resolved: false."""
    return _node.reasoning.resolve_location(name)


@mcp.tool()
def pathplanning(x: float, y: float, frame: str = "map") -> dict:
    """A*로 마지막 위치에서 목표 좌표까지 경로를 계산한다. Nav2·Gazebo 불필요 (map.pgm 기준)."""
    if frame != "map":
        return {"waypoints": None, "reason": f"unsupported frame: {frame!r} (map만 지원)"}
    start = _node.action.last_sim_pose
    return _node.reasoning.pathplanning({"x": start["x"], "y": start["y"]}, {"x": x, "y": y})


@mcp.tool()
def moving_path(waypoints: list) -> dict:
    """A*가 계산한 웨이포인트를 따라 이동한다 — 운동학만 적분하는 소프트웨어 시뮬레이션(Nav2·Gazebo 불필요). 비동기, get_path_status로 폴링한다."""
    return _node.action.move_along_path(waypoints)


@mcp.tool()
def get_path_status() -> dict:
    """moving_path 진행 상태(status/pose/progress/result)를 반환한다."""
    return _node.action.get_path_status()


@mcp.tool()
def cancel_path() -> dict:
    """진행 중인 moving_path를 취소한다."""
    return _node.action.cancel_path()


@mcp.tool()
def send_ir_signal(
    device: str, command: str, value: Optional[float] = None, unit: Optional[str] = None
) -> dict:
    """(스텁) 리모컨으로 `device`에 IR 신호를 보낸다. 실제 송신 하드웨어는 미구현 — 로그만 남긴다."""
    return _node.action.send_signal(device, command, value, unit)


if __name__ == "__main__":
    mcp.run(transport="stdio")
