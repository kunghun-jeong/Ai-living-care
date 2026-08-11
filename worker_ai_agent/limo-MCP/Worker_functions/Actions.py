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


def _normalize_angle(angle: float) -> float:
    return (angle + math.pi) % (2 * math.pi) - math.pi


# 시나리오 1(README)과 같은 스폰 — A* 웨이포인트 추종의 초기 위치로 쓴다.
_SIM_SPAWN = {"x": 3.5, "y": 1.0, "yaw": 0.0}
_SIM_V_LIN = 0.22  # m/s (tools/limo-patrol-viz/patrol_sim.py의 V_LIN과 동일)
_SIM_V_ANG = 0.50  # rad/s
_SIM_DT = 0.1      # s, 적분 스텝(실제 시간으로 페이싱)


class ActionModule:
    def __init__(self, node, nav_action: str = "navigate_to_pose", viz=None):
        self.status = "idle"
        self.last_goal = None
        self.sequence_progress = None
        self.sequence_result = None

        self._node = node
        self._goal_handle = None
        self._action_client = ActionClient(node, NavigateToPose, nav_action)
        self._sequence_thread: Optional[threading.Thread] = None
        self._sequence_interrupt = threading.Event()

        # --- A* 웨이포인트 추종 (Nav2·Gazebo 없이 운동학만 적분하는 소프트웨어 시뮬레이션) ---
        self._sim_pose: Optional[dict] = None  # {"x","y","yaw"} — 실물 오도메트리가 아니라 자체 적분값
        self._path_thread: Optional[threading.Thread] = None
        self._path_interrupt = threading.Event()
        self._path_status = "idle"
        self._path_progress = None
        self._path_result = None
        self._viz = viz  # Visualization.PoseVisualizer 또는 None — RViz2로 pose를 실시간 스트리밍

        # --- 제자리 둘러보기 (G-4) — 같은 sim_pose를 회전시킨다 ---
        self._look_thread: Optional[threading.Thread] = None
        self._look_interrupt = threading.Event()
        self._look_progress = None

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

    # ------------------------------------------------------------------ #
    # 리모컨 IR 신호 (스텁) — 실제 송신 하드웨어는 미구현, 로그만 남긴다
    # ------------------------------------------------------------------ #
    def send_signal(
        self,
        device: str,
        command: str,
        value: Optional[float] = None,
        unit: Optional[str] = None,
    ) -> dict:
        """리모컨으로 `device`에 IR 신호를 보냈다고 가정하고 로그만 남긴다.

        실제 IR 송신 하드웨어가 붙기 전까지는 항상 성공을 반환한다.
        """
        self._node.get_logger().info(
            f"[IR-SIGNAL] device={device} command={command} value={value} unit={unit}"
        )
        return {"sent": True, "device": device, "command": command, "value": value, "unit": unit}

    # ------------------------------------------------------------------ #
    # A* 웨이포인트 추종 — Nav2·Gazebo·실물 오도메트리 없이 운동학만 적분한다
    # (tools/limo-patrol-viz/patrol_sim.py의 advance_to와 같은 모델, 실시간 페이싱)
    # ------------------------------------------------------------------ #
    def _ensure_sim_pose(self) -> dict:
        """sim_pose가 아직 없으면 스폰 위치로 초기화한다 (pathplanning의 시작점으로도 쓰인다)."""
        if self._sim_pose is None:
            self._sim_pose = dict(_SIM_SPAWN)
        return self._sim_pose

    @property
    def last_sim_pose(self) -> dict:
        return self._ensure_sim_pose()

    def is_running_path(self) -> bool:
        return self._path_thread is not None and self._path_thread.is_alive()

    def move_along_path(self, waypoints: list, timeout: float = 120.0) -> dict:
        if self.is_running_sequence() or self.is_running_path():
            return {"started": False, "reason": "a motion is already in progress"}
        if not waypoints:
            return {"started": False, "reason": "empty waypoint list"}
        for wp in waypoints:
            if not isinstance(wp, dict) or "x" not in wp or "y" not in wp:
                return {"started": False, "reason": f"invalid waypoint: {wp!r}"}

        self._ensure_sim_pose()
        if self._viz is not None:
            self._viz.publish_waypoints(waypoints)
            self._viz.reset_trail()

        self._path_interrupt.clear()
        self._path_result = None
        total = len(waypoints)
        self._path_status = "moving"
        self._path_progress = {"index": 0, "total": total}

        def run() -> None:
            deadline = time.time() + timeout
            for i, wp in enumerate(waypoints):
                self._path_progress = {"index": i, "total": total}
                if not self._advance_sim_to(wp["x"], wp["y"], deadline):
                    if self._path_interrupt.is_set():
                        self._path_status = "cancelled"
                        self._path_result = {"completed": i, "total": total, "interrupted": True}
                    else:
                        self._path_status = "failed"
                        self._path_result = {"completed": i, "total": total, "reason": "timeout"}
                    return
            self._path_status = "succeeded"
            self._path_result = {"completed": total, "total": total, "interrupted": False}

        self._path_thread = threading.Thread(target=run, daemon=True)
        self._path_thread.start()
        return {"started": True}

    def _advance_sim_to(self, nx: float, ny: float, deadline: float) -> bool:
        """제자리 회전 후 직진 — patrol_sim.py의 advance_to를 실시간 페이싱으로 옮긴 것.

        중단/타임아웃이면 False, 정상 도착이면 True를 반환한다.
        """
        pose = self._sim_pose
        tgt = math.atan2(ny - pose["y"], nx - pose["x"])
        dyaw = _normalize_angle(tgt - pose["yaw"])
        turn_dur = abs(dyaw) / _SIM_V_ANG
        move_dur = math.hypot(nx - pose["x"], ny - pose["y"]) / _SIM_V_LIN

        for phase, dur in (("turn", turn_dur), ("move", move_dur)):
            t0 = time.monotonic()
            x0, y0, yaw0 = pose["x"], pose["y"], pose["yaw"]
            while True:
                if self._path_interrupt.is_set() or time.time() > deadline:
                    return False
                elapsed = time.monotonic() - t0
                if elapsed >= dur:
                    break
                f = elapsed / dur if dur > 0 else 1.0
                if phase == "turn":
                    # 정규화하지 않으면 웨이포인트마다 누적돼 yaw가 -10 rad 같은 값이 된다.
                    pose["yaw"] = _normalize_angle(yaw0 + dyaw * f)
                else:
                    pose["x"], pose["y"] = x0 + (nx - x0) * f, y0 + (ny - y0) * f
                if self._viz is not None:
                    self._viz.publish_pose(pose)
                time.sleep(_SIM_DT)
            if phase == "turn":
                pose["yaw"] = _normalize_angle(yaw0 + dyaw)
            else:
                pose["x"], pose["y"] = nx, ny
            if self._viz is not None:
                self._viz.publish_pose(pose)
        return True

    def get_path_status(self) -> dict:
        return {
            "status": self._path_status,
            "pose": self._sim_pose,
            "progress": self._path_progress,
            "result": self._path_result,
        }

    def cancel_path(self) -> dict:
        if not self.is_running_path():
            return {"cancelled": False, "reason": "no path motion in progress"}
        self._path_interrupt.set()
        return {"cancelled": True}

    # ------------------------------------------------------------------ #
    # 제자리 둘러보기 (G-4) — moving_path와 같은 sim_pose·같은 RViz2 스트리밍을 쓴다.
    # 도착한 자리에서 yaw만 돌리므로 x,y는 건드리지 않는다.
    # ------------------------------------------------------------------ #
    def is_looking_around(self) -> bool:
        return self._look_thread is not None and self._look_thread.is_alive()

    def look_around(self, steps: int = 8, step_deg: float = 45.0,
                    step_duration: float = 1.0) -> dict:
        """제자리에서 `steps`번 `step_deg`씩 돌며 각 단계에서 `step_duration`초 멈춘다.

        기본값은 45°×8 = 360°. 비동기이며 is_looking_around()로 폴링한다.
        멈추는 이유는 그 사이에 다른 층(perception)이 프레임을 볼 시간을 주기 위함이다.
        """
        if self.is_running_path() or self.is_looking_around():
            return {"started": False, "reason": "a motion is already in progress"}
        if steps <= 0:
            return {"started": False, "reason": f"steps must be positive: {steps!r}"}

        self._ensure_sim_pose()
        self._look_interrupt.clear()
        self._look_progress = {"index": 0, "total": steps}

        def run() -> None:
            pose = self._sim_pose
            for i in range(steps):
                if self._look_interrupt.is_set():
                    break
                self._look_progress = {"index": i, "total": steps}
                target = _normalize_angle(pose["yaw"] + math.radians(step_deg))
                if not self._turn_sim_to(target):
                    break
                # 멈춰 서 있는 구간 — 인터럽트를 확인하며 잘게 잔다
                waited = 0.0
                while waited < step_duration and not self._look_interrupt.is_set():
                    time.sleep(min(_SIM_DT, step_duration - waited))
                    waited += _SIM_DT
            self._look_progress = {"index": steps, "total": steps}

        self._look_thread = threading.Thread(target=run, daemon=True)
        self._look_thread.start()
        return {"started": True, "steps": steps, "step_deg": step_deg}

    def _turn_sim_to(self, target_yaw: float) -> bool:
        """제자리 회전. 중단되면 False."""
        pose = self._sim_pose
        yaw0 = pose["yaw"]
        dyaw = _normalize_angle(target_yaw - yaw0)
        dur = abs(dyaw) / _SIM_V_ANG
        t0 = time.monotonic()
        while True:
            if self._look_interrupt.is_set():
                return False
            elapsed = time.monotonic() - t0
            if elapsed >= dur:
                break
            pose["yaw"] = _normalize_angle(yaw0 + dyaw * (elapsed / dur if dur > 0 else 1.0))
            if self._viz is not None:
                self._viz.publish_pose(pose)
            time.sleep(_SIM_DT)
        pose["yaw"] = _normalize_angle(target_yaw)
        if self._viz is not None:
            self._viz.publish_pose(pose)
        return True

    def get_look_around_status(self) -> dict:
        return {
            "looking_around": self.is_looking_around(),
            "progress": self._look_progress,
            "pose": self._sim_pose,
        }

    def interrupt_look_around(self) -> dict:
        if not self.is_looking_around():
            return {"interrupted": False, "reason": "not looking around"}
        self._look_interrupt.set()
        # 다음 동작(moving_path)이 "이미 동작 중"으로 거절당하지 않도록 실제로 멎을 때까지 기다린다.
        self._look_thread.join(timeout=2.0)
        return {"interrupted": True, "stopped": not self.is_looking_around()}

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
