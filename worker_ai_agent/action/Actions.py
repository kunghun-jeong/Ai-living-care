import math
import threading
import time
from typing import Optional

from action_msgs.msg import GoalStatus
from geometry_msgs.msg import PoseStamped
from nav2_msgs.action import NavigateToPose
from rclpy.action import ActionClient


def _goal_xy_yaw(waypoint, prev_xy: Optional[tuple] = None) -> tuple:
    """웨이포인트 하나를 (x, y, frame, yaw_deg)로 정규화한다.

    dict({"x","y","frame?","yaw_deg?"}) 와 (x, y) / (x, y, yaw_deg) 형태를 모두 받는다.
    yaw가 주어지지 않으면 이전 웨이포인트 -> 현재 웨이포인트 방향을 바라보도록 계산한다.
    """
    if isinstance(waypoint, dict):
        x, y = waypoint["x"], waypoint["y"]
        frame = waypoint.get("frame", "map")
        yaw_deg = waypoint.get("yaw_deg")
    else:
        x, y = waypoint[0], waypoint[1]
        frame = "map"
        yaw_deg = waypoint[2] if len(waypoint) >= 3 else None

    if yaw_deg is None:
        yaw_deg = math.degrees(math.atan2(y - prev_xy[1], x - prev_xy[0])) if prev_xy else 0.0

    return x, y, frame, yaw_deg


class ActionModule:
    def __init__(self, node, nav_action: str = "navigate_to_pose"):
        self.status = "idle"
        self.last_goal = None
        self.sequence_progress = None
        self.sequence_result = None

        self._goal_handle = None
        self._action_client = ActionClient(node, NavigateToPose, nav_action)
        self._sequence_thread: Optional[threading.Thread] = None
        self._sequence_interrupt = threading.Event()

    # ------------------------------------------------------------------ #
    # waypoint 리스트 -> 순차적인 ROS2 NavigateToPose 액션으로 번역해 전송
    # ------------------------------------------------------------------ #
    def send_goal_sequence(self, waypoints: list) -> dict:
        if self.is_running_sequence():
            return {"started": False, "reason": "a goal sequence is already in progress"}
        if not waypoints:
            return {"started": False, "reason": "empty waypoint list"}

        self._sequence_interrupt.clear()
        self.sequence_result = None
        total = len(waypoints)
        self.sequence_progress = {"index": 0, "total": total}

        def run() -> None:
            completed = 0
            prev_xy = None
            for i, waypoint in enumerate(waypoints):
                if self._sequence_interrupt.is_set():
                    break
                x, y, frame, yaw_deg = _goal_xy_yaw(waypoint, prev_xy)
                self.sequence_progress = {"index": i, "total": total}

                outcome = self._send_goal_and_wait(x, y, frame, yaw_deg)
                if not outcome["succeeded"]:
                    self.sequence_result = {
                        "completed": completed,
                        "total": total,
                        "interrupted": outcome["reason"] == "interrupted",
                        "reason": outcome["reason"],
                    }
                    return

                completed += 1
                prev_xy = (x, y)

            self.sequence_result = {
                "completed": completed,
                "total": total,
                "interrupted": self._sequence_interrupt.is_set(),
            }

        self._sequence_thread = threading.Thread(target=run, daemon=True)
        self._sequence_thread.start()
        return {"started": True}

    def cancel_goal_sequence(self) -> dict:
        if not self.is_running_sequence():
            return {"cancelled": False, "reason": "no goal sequence in progress"}
        self._sequence_interrupt.set()
        self.cancel_goal()
        return {"cancelled": True}

    def is_running_sequence(self) -> bool:
        return self._sequence_thread is not None and self._sequence_thread.is_alive()

    # ------------------------------------------------------------------ #
    # 단일 목표 전송 (send_goal_sequence가 웨이포인트마다 내부적으로 사용)
    # ------------------------------------------------------------------ #
    def send_goal(self, x: float, y: float, frame: str, yaw_deg: float) -> dict:
        if not self._action_client.wait_for_server(timeout_sec=2.0):
            return {"accepted": False, "reason": "nav2 action server unavailable"}

        goal = NavigateToPose.Goal()
        goal.pose = self._make_pose(x, y, frame, yaw_deg)

        accepted_event = threading.Event()
        result_holder: dict = {}

        def on_goal_response(future) -> None:
            result_holder["goal_handle"] = future.result()
            accepted_event.set()

        send_future = self._action_client.send_goal_async(goal, feedback_callback=self._on_feedback)
        send_future.add_done_callback(on_goal_response)

        if not accepted_event.wait(timeout=5.0):
            return {"accepted": False, "reason": "timed out waiting for goal response"}

        goal_handle = result_holder.get("goal_handle")
        if goal_handle is None or not goal_handle.accepted:
            self.status = "rejected"
            return {"accepted": False, "reason": "goal rejected by action server"}

        self._goal_handle = goal_handle
        self.status = "navigating"
        self.last_goal = {"x": x, "y": y, "frame": frame, "yaw_deg": yaw_deg}

        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(self._on_result)
        return {"accepted": True}

    def cancel_goal(self) -> dict:
        if self._goal_handle is None:
            return {"cancelled": False, "reason": "no active goal"}
        self._goal_handle.cancel_goal_async()
        self._goal_handle = None
        self.status = "cancelled"
        return {"cancelled": True}

    def _send_goal_and_wait(self, x: float, y: float, frame: str, yaw_deg: float, timeout: float = 120.0) -> dict:
        result = self.send_goal(x, y, frame, yaw_deg)
        if not result.get("accepted"):
            return {"succeeded": False, "reason": result.get("reason", "goal not accepted")}

        deadline = time.time() + timeout
        while self.status == "navigating" and time.time() < deadline:
            if self._sequence_interrupt.is_set():
                self.cancel_goal()
                return {"succeeded": False, "reason": "interrupted"}
            time.sleep(0.1)

        if self.status != "succeeded":
            return {"succeeded": False, "reason": self.status}
        return {"succeeded": True, "reason": "succeeded"}

    def _on_feedback(self, feedback_msg) -> None:
        self.status = "navigating"

    def _on_result(self, future) -> None:
        result = future.result()
        self.status = "succeeded" if result.status == GoalStatus.STATUS_SUCCEEDED else "failed"
        self._goal_handle = None

    @staticmethod
    def _make_pose(x: float, y: float, frame: str, yaw_deg: float) -> PoseStamped:
        pose = PoseStamped()
        pose.header.frame_id = frame
        yaw = math.radians(yaw_deg)
        pose.pose.position.x = x
        pose.pose.position.y = y
        pose.pose.orientation.z = math.sin(yaw / 2.0)
        pose.pose.orientation.w = math.cos(yaw / 2.0)
        return pose
