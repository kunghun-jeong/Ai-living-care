"""Nav2 NavigateToPose로 웨이포인트 시퀀스를 수행하는 모듈.

취소·타임아웃 경로에서 지키는 것 (2026-08-06):
  · 대기 시간은 **노드 시계**로 잰다. `use_sim_time`에서 벽시계로 재면
    RTF 0.04일 때 모든 내비게이션이 실패로 보고된다 (F-5)
  · 타임아웃으로 감시를 포기할 때 **goal을 반드시 취소한다.** 안 그러면
    로봇은 계속 달리는데 시퀀스는 끝난 것으로 보고된다 (F-2 · F-48)
  · 취소 사유를 한 가지로 고정한다. 같은 `cancel()`이 타이밍에 따라
    `cancelled`/`failed`/`interrupted`로 갈리면 상위가 오판한다 (F-46)
  · Nav2가 없으면 **시작 시점에** 실패를 돌려준다. `started: True`를 주고
    뒤에서 실패하면 호출자가 알 방법이 없다 (F-49)
"""

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

    **float으로 강제 변환한다.** ROS2 메시지 필드는 double이라 int를 넣으면
    대입 시점에 예외가 나고, 그 예외가 시퀀스 스레드를 조용히 죽인다 (F-4).
    """
    if isinstance(waypoint, dict):
        x, y = waypoint["x"], waypoint["y"]
        frame = waypoint.get("frame", "map")
        yaw_deg = waypoint.get("yaw_deg")
    else:
        x, y = waypoint[0], waypoint[1]
        frame = "map"
        yaw_deg = waypoint[2] if len(waypoint) >= 3 else None

    x, y = float(x), float(y)
    if yaw_deg is None:
        yaw_deg = math.degrees(math.atan2(y - prev_xy[1], x - prev_xy[0])) if prev_xy else 0.0

    return x, y, frame, float(yaw_deg)


def validate_waypoints(waypoints) -> Optional[str]:
    """받아들일 수 없는 입력이면 사유 문자열, 괜찮으면 None (F-4).

    스레드를 띄우기 **전에** 검사한다. 스레드 안에서 터지면 `get_status`가
    영원히 옛 상태를 보고한다.
    """
    if not isinstance(waypoints, (list, tuple)):
        return f"waypoints must be a list, got {type(waypoints).__name__}"
    if not waypoints:
        return "empty waypoint list"
    for i, wp in enumerate(waypoints):
        try:
            if isinstance(wp, dict):
                if "x" not in wp or "y" not in wp:
                    return f"waypoint[{i}] missing 'x' or 'y'"
                x, y = float(wp["x"]), float(wp["y"])
                if wp.get("yaw_deg") is not None:
                    float(wp["yaw_deg"])
                if not isinstance(wp.get("frame", "map"), str):
                    return f"waypoint[{i}].frame must be a string"
            elif isinstance(wp, (list, tuple)):
                if len(wp) < 2:
                    return f"waypoint[{i}] needs at least (x, y)"
                x, y = float(wp[0]), float(wp[1])
                if len(wp) >= 3:
                    float(wp[2])
            else:
                return f"waypoint[{i}] must be dict or (x, y), got {type(wp).__name__}"
        except (TypeError, ValueError) as exc:
            return f"waypoint[{i}] has non-numeric coordinate: {exc}"
        if not (math.isfinite(x) and math.isfinite(y)):
            return f"waypoint[{i}] coordinate is NaN or inf"
    return None


class ActionModule:
    def __init__(self, node, nav_action: str = "navigate_to_pose"):
        self.status = "idle"
        self.last_goal = None
        self.sequence_progress = None
        self.sequence_result = None

        self._node = node
        self._clock = node.get_clock()          # use_sim_time을 따른다 (F-5)
        self._goal_handle = None
        self._action_client = ActionClient(node, NavigateToPose, nav_action)
        self._sequence_thread: Optional[threading.Thread] = None
        self._sequence_interrupt = threading.Event()

    def _now(self) -> float:
        return self._clock.now().nanoseconds * 1e-9

    # ------------------------------------------------------------------ #
    # waypoint 리스트 -> 순차적인 ROS2 NavigateToPose 액션으로 번역해 전송
    # ------------------------------------------------------------------ #
    def send_goal_sequence(self, waypoints: list) -> dict:
        if self.is_running_sequence():
            return {"started": False, "reason": "a goal sequence is already in progress"}

        bad = validate_waypoints(waypoints)     # F-4 — 스레드 띄우기 전에
        if bad:
            return {"started": False, "reason": bad}

        # F-49 — Nav2가 없으면 여기서 실패를 돌려준다. 뒤에서 실패하면 아무도 모른다.
        if not self._action_client.wait_for_server(timeout_sec=2.0):
            self.status = "failed"
            return {"started": False, "reason": "nav2 action server unavailable"}

        self._sequence_interrupt.clear()
        self.sequence_result = None
        total = len(waypoints)
        self.sequence_progress = {"index": 0, "total": total}

        def run() -> None:
            completed = 0
            prev_xy = None
            try:
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
            except Exception as exc:            # noqa: BLE001 — 조용히 죽지 않는다 (F-4)
                self.cancel_goal()
                self.status = "failed"
                self.sequence_result = {
                    "completed": completed, "total": total,
                    "interrupted": False, "reason": f"sequence crashed: {exc!r}",
                }
                return

            self.sequence_result = {
                "completed": completed,
                "total": total,
                "interrupted": self._sequence_interrupt.is_set(),
                "reason": "interrupted" if self._sequence_interrupt.is_set() else "completed",
            }

        self._sequence_thread = threading.Thread(target=run, daemon=True)
        self._sequence_thread.start()
        return {"started": True}

    def cancel_goal_sequence(self) -> dict:
        if not self.is_running_sequence():
            return {"cancelled": False, "reason": "no goal sequence in progress"}
        # 순서가 중요하다: interrupt를 먼저 세워야 감시 루프가 "interrupted"로
        # 판정한다. cancel_goal()이 먼저 status를 바꾸면 루프가 그걸 종료 사유로
        # 읽어 같은 취소가 cancelled/failed 로 갈린다 (F-46).
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
            self.status = "failed"
            return {"accepted": False, "reason": "nav2 action server unavailable"}

        goal = NavigateToPose.Goal()
        goal.pose = self._make_pose(x, y, frame, yaw_deg)

        accepted_event = threading.Event()
        result_holder: dict = {}
        holder_lock = threading.Lock()

        def on_goal_response(future) -> None:
            handle = future.result()
            with holder_lock:
                if result_holder.get("abandoned"):
                    # F-2 — 우리는 이미 포기했는데 Nav2는 수락했다.
                    # 여기서 취소하지 않으면 핸들 없는 로봇이 계속 달린다.
                    if handle is not None and handle.accepted:
                        handle.cancel_goal_async()
                    return
                result_holder["goal_handle"] = handle
            accepted_event.set()

        send_future = self._action_client.send_goal_async(goal, feedback_callback=self._on_feedback)
        send_future.add_done_callback(on_goal_response)

        if not accepted_event.wait(timeout=5.0):
            with holder_lock:
                result_holder["abandoned"] = True
            self.status = "failed"
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

    def _send_goal_and_wait(self, x: float, y: float, frame: str, yaw_deg: float,
                            timeout: float = 120.0) -> dict:
        result = self.send_goal(x, y, frame, yaw_deg)
        if not result.get("accepted"):
            return {"succeeded": False, "reason": result.get("reason", "goal not accepted")}

        deadline = self._now() + timeout        # 노드 시계 — sim time을 따른다 (F-5)
        while True:
            # interrupt를 status보다 **먼저** 본다. cancel_goal_sequence()가
            # status를 이미 "cancelled"로 바꿔 놨어도 사유는 interrupted 하나다 (F-46).
            if self._sequence_interrupt.is_set():
                self.cancel_goal()
                return {"succeeded": False, "reason": "interrupted"}
            if self.status != "navigating":
                break
            if self._now() >= deadline:
                # F-48 — 감시만 포기하면 로봇은 계속 달린다. 반드시 취소한다.
                self.cancel_goal()
                self.status = "failed"
                return {"succeeded": False, "reason": f"navigation timed out after {timeout}s"}
            time.sleep(0.1)

        if self.status != "succeeded":
            return {"succeeded": False, "reason": self.status}
        return {"succeeded": True, "reason": "succeeded"}

    def _on_feedback(self, feedback_msg) -> None:
        # 취소 요청이 들어온 뒤 늦게 도착한 피드백이 status를 navigating으로
        # 되돌리면 감시 루프가 다시 돈다.
        if self._sequence_interrupt.is_set() or self.status == "cancelled":
            return
        self.status = "navigating"

    def _on_result(self, future) -> None:
        result = future.result()
        if result.status == GoalStatus.STATUS_SUCCEEDED:
            self.status = "succeeded"
        elif result.status == GoalStatus.STATUS_CANCELED:
            self.status = "cancelled"           # 취소를 실패로 보고하지 않는다 (F-46)
        else:
            self.status = "failed"
        self._goal_handle = None

    @staticmethod
    def _make_pose(x: float, y: float, frame: str, yaw_deg: float) -> PoseStamped:
        pose = PoseStamped()
        pose.header.frame_id = frame
        yaw = math.radians(yaw_deg)
        pose.pose.position.x = float(x)
        pose.pose.position.y = float(y)
        pose.pose.orientation.z = math.sin(yaw / 2.0)
        pose.pose.orientation.w = math.cos(yaw / 2.0)
        return pose
