"""ROS2 Nav2 NavigateToPose 액션을 이용한 이동 모듈."""

import math
import threading
import time
from typing import Optional

from action_msgs.msg import GoalStatus
from geometry_msgs.msg import PoseStamped
from nav2_msgs.action import NavigateToPose
from rclpy.action import ActionClient


def _normalize_waypoint(
    waypoint,
    previous_xy: Optional[tuple] = None,
) -> tuple:
    """웨이포인트를 x, y, frame, yaw_deg 형태로 변환한다."""

    if isinstance(waypoint, dict):
        x = float(waypoint["x"])
        y = float(waypoint["y"])
        frame = waypoint.get("frame", "map")
        yaw_deg = waypoint.get("yaw_deg")
    else:
        x = float(waypoint[0])
        y = float(waypoint[1])
        frame = "map"
        yaw_deg = waypoint[2] if len(waypoint) >= 3 else None

    if yaw_deg is None:
        if previous_xy is None:
            yaw_deg = 0.0
        else:
            dx = x - previous_xy[0]
            dy = y - previous_xy[1]
            yaw_deg = math.degrees(math.atan2(dy, dx))

    return x, y, frame, float(yaw_deg)


class ActionModule:
    """Nav2 목표 전송, 상태 확인 및 취소를 담당한다."""

    def __init__(
        self,
        node,
        nav_action: str = "/navigate_to_pose",
    ):
        self._node = node

        self.status = "idle"
        self.last_goal = None
        self.sequence_progress = None
        self.sequence_result = None

        self._goal_handle = None
        self._sequence_thread: Optional[threading.Thread] = None
        self._sequence_interrupt = threading.Event()

        self._action_client = ActionClient(
            node,
            NavigateToPose,
            nav_action,
        )

    def send_goal_sequence(self, waypoints: list) -> dict:
        """웨이포인트들을 별도 스레드에서 순서대로 실행한다."""

        if self.is_running_sequence():
            return {
                "started": False,
                "reason": "a goal sequence is already in progress",
            }

        if not waypoints:
            return {
                "started": False,
                "reason": "empty waypoint list",
            }

        self._sequence_interrupt.clear()
        self.sequence_result = None
        self.sequence_progress = {
            "index": 0,
            "total": len(waypoints),
        }

        def run_sequence() -> None:
            completed = 0
            previous_xy = None
            total = len(waypoints)

            for index, waypoint in enumerate(waypoints):
                if self._sequence_interrupt.is_set():
                    break

                try:
                    x, y, frame, yaw_deg = _normalize_waypoint(
                        waypoint,
                        previous_xy,
                    )
                except (KeyError, TypeError, ValueError, IndexError) as exc:
                    self.status = "failed"
                    self.sequence_result = {
                        "completed": completed,
                        "total": total,
                        "interrupted": False,
                        "reason": f"invalid waypoint: {exc}",
                    }
                    return

                self.sequence_progress = {
                    "index": index,
                    "total": total,
                }

                outcome = self._send_goal_and_wait(
                    x=x,
                    y=y,
                    frame=frame,
                    yaw_deg=yaw_deg,
                )

                if not outcome["succeeded"]:
                    self.sequence_result = {
                        "completed": completed,
                        "total": total,
                        "interrupted": (
                            outcome["reason"] == "interrupted"
                        ),
                        "reason": outcome["reason"],
                    }
                    return

                completed += 1
                previous_xy = (x, y)

            self.sequence_progress = {
                "index": completed,
                "total": total,
            }

            self.sequence_result = {
                "completed": completed,
                "total": total,
                "interrupted": self._sequence_interrupt.is_set(),
            }

        self._sequence_thread = threading.Thread(
            target=run_sequence,
            name="nav2-goal-sequence",
            daemon=True,
        )
        self._sequence_thread.start()

        return {
            "started": True,
            "total": len(waypoints),
        }

    def send_goal(
        self,
        x: float,
        y: float,
        frame: str = "map",
        yaw_deg: float = 0.0,
    ) -> dict:
        """Nav2 액션 서버에 단일 목표를 전송한다."""

        if not self._action_client.wait_for_server(timeout_sec=2.0):
            self.status = "unavailable"
            return {
                "accepted": False,
                "reason": "nav2 action server unavailable",
            }

        goal = NavigateToPose.Goal()
        goal.pose = self._make_pose(
            x=x,
            y=y,
            frame=frame,
            yaw_deg=yaw_deg,
        )

        response_event = threading.Event()
        response_holder = {}

        def on_goal_response(future) -> None:
            try:
                response_holder["goal_handle"] = future.result()
            except Exception as exc:
                response_holder["error"] = repr(exc)
            finally:
                response_event.set()

        future = self._action_client.send_goal_async(
            goal,
            feedback_callback=self._on_feedback,
        )
        future.add_done_callback(on_goal_response)

        if not response_event.wait(timeout=5.0):
            self.status = "failed"
            return {
                "accepted": False,
                "reason": "timed out waiting for goal response",
            }

        if "error" in response_holder:
            self.status = "failed"
            return {
                "accepted": False,
                "reason": response_holder["error"],
            }

        goal_handle = response_holder.get("goal_handle")

        if goal_handle is None or not goal_handle.accepted:
            self.status = "rejected"
            return {
                "accepted": False,
                "reason": "goal rejected by action server",
            }

        self._goal_handle = goal_handle
        self.status = "navigating"
        self.last_goal = {
            "x": x,
            "y": y,
            "frame": frame,
            "yaw_deg": yaw_deg,
        }

        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(self._on_result)

        return {"accepted": True}

    def cancel_goal(self) -> dict:
        """현재 Nav2 목표를 취소한다."""

        if self._goal_handle is None:
            return {
                "cancelled": False,
                "reason": "no active goal",
            }

        self._goal_handle.cancel_goal_async()
        self._goal_handle = None
        self.status = "cancelled"

        return {"cancelled": True}

    def cancel_goal_sequence(self) -> dict:
        """현재 웨이포인트 시퀀스를 중단한다."""

        if not self.is_running_sequence():
            return {
                "cancelled": False,
                "reason": "no goal sequence in progress",
            }

        self._sequence_interrupt.set()
        self.cancel_goal()

        return {"cancelled": True}

    def is_running_sequence(self) -> bool:
        return (
            self._sequence_thread is not None
            and self._sequence_thread.is_alive()
        )

    def get_status(self) -> dict:
        """현재 내비게이션 상태를 반환한다."""

        return {
            "status": self.status,
            "last_goal": self.last_goal,
            "sequence_progress": self.sequence_progress,
            "sequence_result": self.sequence_result,
        }

    def _send_goal_and_wait(
        self,
        x: float,
        y: float,
        frame: str,
        yaw_deg: float,
        timeout: float = 120.0,
    ) -> dict:
        result = self.send_goal(
            x=x,
            y=y,
            frame=frame,
            yaw_deg=yaw_deg,
        )

        if not result.get("accepted"):
            return {
                "succeeded": False,
                "reason": result.get(
                    "reason",
                    "goal not accepted",
                ),
            }

        deadline = time.monotonic() + timeout

        while (
            self.status == "navigating"
            and time.monotonic() < deadline
        ):
            if self._sequence_interrupt.is_set():
                self.cancel_goal()
                return {
                    "succeeded": False,
                    "reason": "interrupted",
                }

            time.sleep(0.1)

        if self.status == "navigating":
            self.cancel_goal()
            self.status = "failed"

            return {
                "succeeded": False,
                "reason": "navigation timeout",
            }

        if self.status != "succeeded":
            return {
                "succeeded": False,
                "reason": self.status,
            }

        return {
            "succeeded": True,
            "reason": "succeeded",
        }

    def _on_feedback(self, _feedback_msg) -> None:
        if self.status not in {"cancelled", "failed"}:
            self.status = "navigating"

    def _on_result(self, future) -> None:
        try:
            result = future.result()
        except Exception:
            self.status = "failed"
            self._goal_handle = None
            return

        if result.status == GoalStatus.STATUS_SUCCEEDED:
            self.status = "succeeded"
        elif result.status == GoalStatus.STATUS_CANCELED:
            self.status = "cancelled"
        else:
            self.status = "failed"

        self._goal_handle = None

    def _make_pose(
        self,
        x: float,
        y: float,
        frame: str,
        yaw_deg: float,
    ) -> PoseStamped:
        pose = PoseStamped()

        pose.header.frame_id = frame
        pose.header.stamp = (
            self._node.get_clock().now().to_msg()
        )

        pose.pose.position.x = float(x)
        pose.pose.position.y = float(y)
        pose.pose.position.z = 0.0

        yaw = math.radians(yaw_deg)

        pose.pose.orientation.x = 0.0
        pose.pose.orientation.y = 0.0
        pose.pose.orientation.z = math.sin(yaw / 2.0)
        pose.pose.orientation.w = math.cos(yaw / 2.0)

        return pose