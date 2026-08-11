"""moving_path 진행 상황을 RViz2로 실시간 스트리밍하는 보조 퍼블리셔.

tools/limo-patrol-viz/patrol_viz.py와 같은 토픽·같은 시각화 방식(TF map->base_footprint,
/joint_states, /map_walls, /trail)을 쓴다 — 다만 궤적을 오프라인으로 미리 계산해 재생하는
patrol_viz.py와 달리, 이 모듈은 Actions.py의 moving_path가 실제로 움직이는 매 틱의 pose를
그대로 퍼블리시한다. tools/limo-patrol-viz/patrol.rviz로 그대로 볼 수 있다.

ActionModule에 주입하는 선택적 구성요소다 — 없어도(None) moving_path는 정상 동작한다.
"""

import math
import os
import time

import numpy as np
from geometry_msgs.msg import Point, TransformStamped
from rclpy.qos import QoSDurabilityPolicy, QoSProfile, QoSReliabilityPolicy
from sensor_msgs.msg import Image, JointState
from tf2_ros import TransformBroadcaster
from visualization_msgs.msg import Marker, MarkerArray

_MAP_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "tools", "limo-patrol-viz", "maps"
)
_RES, _OX, _OY = 0.05, -10.0, -10.0  # maps/map.yaml과 동일
_WHEELS = [
    "wheel_left_joint", "wheel_right_joint",
    "front_left_wheel", "front_right_wheel", "rear_left_wheel", "rear_right_wheel",
]


class PoseVisualizer:
    """moving_path의 pose를 RViz2 토픽으로 스트리밍한다."""

    def __init__(self, node, sim_cam=None, camera_hz: float = 5.0):
        self._node = node
        transient = QoSProfile(depth=5)
        transient.durability = QoSDurabilityPolicy.TRANSIENT_LOCAL
        transient.reliability = QoSReliabilityPolicy.RELIABLE

        self._wall_pub = node.create_publisher(MarkerArray, "/map_walls", transient)
        self._wp_pub = node.create_publisher(MarkerArray, "/patrol_points", transient)
        self._trail_pub = node.create_publisher(Marker, "/trail", 1)
        self._joint_pub = node.create_publisher(JointState, "/joint_states", 10)
        self._cam_pub = node.create_publisher(Image, "/camera/image_raw", 2)
        self._tf = TransformBroadcaster(node)

        # 기하 시뮬 카메라(Perceptions.SimCameraPerception)를 주면 1인칭 화면도 흘려보낸다.
        # 실제 Gazebo 카메라가 있을 때는 None으로 두면 이 퍼블리셔는 조용히 놀고,
        # /camera/image_raw 는 Gazebo 쪽이 그대로 쓴다.
        self._sim_cam = sim_cam
        self._cam_period = (1.0 / camera_hz) if camera_hz > 0 else None
        self._cam_last = 0.0

        self._trail: list = []
        self._spin = 0.0
        self._publish_walls()

    def _maybe_publish_camera(self, pose: dict) -> None:
        """기하 시뮬 1인칭 화면을 /camera/image_raw 로 발행한다 (RViz2 Image 패널용)."""
        if self._sim_cam is None or self._cam_period is None:
            return
        now = time.monotonic()
        if now - self._cam_last < self._cam_period:
            return
        self._cam_last = now

        frame, _ = self._sim_cam.render(pose)
        msg = Image()
        msg.header.stamp = self._node.get_clock().now().to_msg()
        msg.header.frame_id = "depth_camera_link"
        msg.height, msg.width = frame.shape[:2]
        msg.encoding = "bgr8"
        msg.is_bigendian = 0
        msg.step = msg.width * 3
        msg.data = frame.tobytes()
        self._cam_pub.publish(msg)

    def _publish_walls(self) -> None:
        import cv2

        with open(os.path.join(_MAP_DIR, "map.pgm"), "rb") as f:
            img = cv2.imdecode(np.frombuffer(f.read(), np.uint8), cv2.IMREAD_GRAYSCALE)
        height = img.shape[0]
        free = (img > 250).astype(np.uint8)

        arr = MarkerArray()
        ys, xs = np.nonzero(free)
        arr.markers.append(
            self._cube_list(0, "floor", list(zip(xs[::5], ys[::5])), (.85, .85, .85, .85), 0.0, _RES * 2.5, height)
        )
        ys, xs = np.nonzero(img < 100)
        arr.markers.append(
            self._cube_list(1, "wall", list(zip(xs, ys)), (.12, .12, .12, 1.0), 0.02, _RES, height)
        )
        self._wall_pub.publish(arr)

    @staticmethod
    def _cube_list(mid, ns, pts, rgba, z, scale, height):
        m = Marker()
        m.header.frame_id = "map"
        m.ns = ns
        m.id = mid
        m.type = Marker.CUBE_LIST
        m.action = Marker.ADD
        m.pose.orientation.w = 1.0
        m.scale.x = m.scale.y = scale
        m.scale.z = 0.02
        m.color.r, m.color.g, m.color.b, m.color.a = rgba
        for px, py in pts:
            p = Point()
            p.x = _OX + (px + 0.5) * _RES
            p.y = _OY + (height - py - 0.5) * _RES
            p.z = z
            m.points.append(p)
        return m

    def publish_waypoints(self, waypoints: list) -> None:
        """이번에 따라갈 웨이포인트를 patrol_points 토픽에 표시한다."""
        arr = MarkerArray()
        for i, wp in enumerate(waypoints):
            m = Marker()
            m.header.frame_id = "map"
            m.ns = "wp"
            m.id = i
            m.type = Marker.CYLINDER
            m.action = Marker.ADD
            m.pose.position.x, m.pose.position.y, m.pose.position.z = wp["x"], wp["y"], 0.03
            m.pose.orientation.w = 1.0
            m.scale.x = m.scale.y = 0.3
            m.scale.z = 0.05
            m.color.r, m.color.g, m.color.b, m.color.a = 1.0, 0.6, 0.1, 0.9
            arr.markers.append(m)
        self._wp_pub.publish(arr)

    def reset_trail(self) -> None:
        self._trail.clear()

    def publish_pose(self, pose: dict) -> None:
        """TF·joint_states·trail을 한 번에 갱신한다 — moving_path의 매 틱에서 호출."""
        now = self._node.get_clock().now().to_msg()

        t = TransformStamped()
        t.header.stamp = now
        t.header.frame_id = "map"
        t.child_frame_id = "base_footprint"
        t.transform.translation.x = pose["x"]
        t.transform.translation.y = pose["y"]
        t.transform.rotation.z = math.sin(pose["yaw"] / 2.0)
        t.transform.rotation.w = math.cos(pose["yaw"] / 2.0)
        self._tf.sendTransform(t)

        self._maybe_publish_camera(pose)

        self._spin += 0.35
        js = JointState()
        js.header.stamp = now
        js.name = _WHEELS
        js.position = [self._spin] * len(_WHEELS)
        self._joint_pub.publish(js)

        self._trail.append((pose["x"], pose["y"]))
        tr = Marker()
        tr.header.frame_id = "map"
        tr.header.stamp = now
        tr.ns = "trail"
        tr.id = 0
        tr.type = Marker.LINE_STRIP
        tr.action = Marker.ADD
        tr.pose.orientation.w = 1.0
        tr.scale.x = 0.05
        tr.color.r, tr.color.g, tr.color.b, tr.color.a = 1.0, 0.5, 0.0, 1.0
        for tx, ty in self._trail:
            p = Point()
            p.x, p.y, p.z = tx, ty, 0.03
            tr.points.append(p)
        self._trail_pub.publish(tr)
