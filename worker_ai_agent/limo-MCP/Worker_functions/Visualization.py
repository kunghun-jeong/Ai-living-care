"""run_scenario.py의 이동 상태를 patrol.rviz로 표시하는 보조 모듈."""

import math
import os

import cv2
import numpy as np

from geometry_msgs.msg import Point, TransformStamped
from rclpy.qos import (
    QoSDurabilityPolicy,
    QoSProfile,
    QoSReliabilityPolicy,
)
from sensor_msgs.msg import Image, JointState
from std_msgs.msg import String
from tf2_ros import TransformBroadcaster
from visualization_msgs.msg import Marker, MarkerArray


_MAP_DIR = os.path.join(
    os.path.dirname(__file__),
    "..",
    "..",
    "..",
    "tools",
    "limo-patrol-viz",
    "maps",
)

_RES = 0.05
_OX = -10.0
_OY = -10.0

_WHEELS = [
    "wheel_left_joint",
    "wheel_right_joint",
    "front_left_wheel",
    "front_right_wheel",
    "rear_left_wheel",
    "rear_right_wheel",
]


class PoseVisualizer:
    """moving_path의 위치를 patrol.rviz용 토픽으로 발행한다."""

    def __init__(self, node):
        self._node = node

        transient = QoSProfile(depth=5)
        transient.durability = QoSDurabilityPolicy.TRANSIENT_LOCAL
        transient.reliability = QoSReliabilityPolicy.RELIABLE

        # patrol.rviz가 사용하는 토픽
        self._wall_pub = node.create_publisher(
            MarkerArray,
            "/map_walls",
            transient,
        )
        self._wp_pub = node.create_publisher(
            MarkerArray,
            "/patrol_points",
            transient,
        )
        self._coverage_pub = node.create_publisher(
            Marker,
            "/coverage",
            5,
        )
        self._fov_pub = node.create_publisher(
            Marker,
            "/camera_fov",
            5,
        )
        self._trail_pub = node.create_publisher(
            Marker,
            "/trail",
            5,
        )
        self._camera_pub = node.create_publisher(
            Image,
            "/camera/image_raw",
            5,
        )
        self._robot_description_pub = node.create_publisher(
            String,
            "/robot_description",
            transient,
        )

        # bring_water.rviz에서도 사용할 수 있는 토픽
        self._planned_path_pub = node.create_publisher(
            Marker,
            "/planned_path",
            transient,
        )

        self._joint_pub = node.create_publisher(
            JointState,
            "/joint_states",
            10,
        )

        self._tf = TransformBroadcaster(node)

        self._trail = []
        self._spin = 0.0
        self._map_image = None
        self._map_height = 0

        self._publish_robot_description()
        self._publish_walls()

    def _publish_robot_description(self) -> None:
        """patrol.rviz의 RobotModel 오류를 방지하기 위한 간단한 로봇 모델."""

        description = String()
        description.data = """
<robot name="bring_water_robot">
  <link name="base_footprint">
    <visual>
      <origin xyz="0 0 0.05"/>
      <geometry>
        <cylinder radius="0.10" length="0.10"/>
      </geometry>
      <material name="robot_gray">
        <color rgba="0.25 0.25 0.25 1.0"/>
      </material>
    </visual>
  </link>
</robot>
"""
        self._robot_description_pub.publish(description)

    def _publish_walls(self) -> None:
        map_path = os.path.join(_MAP_DIR, "map.pgm")

        with open(map_path, "rb") as file:
            raw = np.frombuffer(file.read(), np.uint8)

        image = cv2.imdecode(raw, cv2.IMREAD_GRAYSCALE)

        if image is None:
            raise RuntimeError(f"지도를 읽을 수 없습니다: {map_path}")

        self._map_image = image
        self._map_height = image.shape[0]

        free = (image > 250).astype(np.uint8)

        markers = MarkerArray()

        ys, xs = np.nonzero(free)
        markers.markers.append(
            self._cube_list(
                marker_id=0,
                namespace="floor",
                pixels=list(zip(xs[::5], ys[::5])),
                rgba=(0.85, 0.85, 0.85, 0.85),
                z=0.0,
                scale=_RES * 2.5,
                height=self._map_height,
            )
        )

        ys, xs = np.nonzero(image < 100)
        markers.markers.append(
            self._cube_list(
                marker_id=1,
                namespace="wall",
                pixels=list(zip(xs, ys)),
                rgba=(0.12, 0.12, 0.12, 1.0),
                z=0.02,
                scale=_RES,
                height=self._map_height,
            )
        )

        self._wall_pub.publish(markers)

    @staticmethod
    def _cube_list(
        marker_id,
        namespace,
        pixels,
        rgba,
        z,
        scale,
        height,
    ):
        marker = Marker()
        marker.header.frame_id = "map"
        marker.ns = namespace
        marker.id = marker_id
        marker.type = Marker.CUBE_LIST
        marker.action = Marker.ADD
        marker.pose.orientation.w = 1.0

        marker.scale.x = scale
        marker.scale.y = scale
        marker.scale.z = 0.02

        marker.color.r = rgba[0]
        marker.color.g = rgba[1]
        marker.color.b = rgba[2]
        marker.color.a = rgba[3]

        for pixel_x, pixel_y in pixels:
            point = Point()
            point.x = _OX + (pixel_x + 0.5) * _RES
            point.y = _OY + (height - pixel_y - 0.5) * _RES
            point.z = z
            marker.points.append(point)

        return marker

    def _make_path_marker(
        self,
        waypoints: list,
        namespace: str,
        marker_id: int,
    ) -> Marker:
        marker = Marker()
        marker.header.frame_id = "map"
        marker.header.stamp = self._node.get_clock().now().to_msg()
        marker.ns = namespace
        marker.id = marker_id
        marker.type = Marker.LINE_STRIP
        marker.action = Marker.ADD
        marker.pose.orientation.w = 1.0

        # 경로 선 굵기
        marker.scale.x = 0.06

        marker.color.r = 0.1
        marker.color.g = 0.7
        marker.color.b = 1.0
        marker.color.a = 1.0

        for waypoint in waypoints:
            point = Point()
            point.x = float(waypoint["x"])
            point.y = float(waypoint["y"])
            point.z = 0.06
            marker.points.append(point)

        return marker

    def publish_waypoints(self, waypoints: list) -> None:
        """기존 호출도 여러 점 대신 하나의 선으로 표시한다."""
        self.publish_planned_path(waypoints)

    def publish_planned_path(self, waypoints: list) -> None:
        """계획 경로를 미리 표시하지 않고 기존 마커만 제거한다."""

        # patrol.rviz의 /patrol_points에 남은 계획 경로 제거
        patrol_array = MarkerArray()

        clear_marker = Marker()
        clear_marker.header.frame_id = "map"
        clear_marker.header.stamp = (
            self._node.get_clock().now().to_msg()
        )
        clear_marker.action = Marker.DELETEALL

        patrol_array.markers.append(clear_marker)
        self._wp_pub.publish(patrol_array)

        # bring_water.rviz의 /planned_path에 남은 선도 제거
        delete_path = Marker()
        delete_path.header.frame_id = "map"
        delete_path.header.stamp = (
            self._node.get_clock().now().to_msg()
        )
        delete_path.ns = "planned_path"
        delete_path.id = 0
        delete_path.action = Marker.DELETE

        self._planned_path_pub.publish(delete_path)

    def reset_trail(self) -> None:
        self._trail.clear()

    def _publish_robot_marker(self, pose: dict, stamp) -> None:
        """로봇을 지름 0.5m의 큰 원으로 표시한다."""

        marker = Marker()
        marker.header.frame_id = "map"
        marker.header.stamp = stamp
        marker.ns = "person"
        marker.id = 9000
        marker.type = Marker.CYLINDER
        marker.action = Marker.ADD

        marker.pose.position.x = float(pose["x"])
        marker.pose.position.y = float(pose["y"])
        marker.pose.position.z = 0.10
        marker.pose.orientation.w = 1.0

        marker.scale.x = 0.50
        marker.scale.y = 0.50
        marker.scale.z = 0.14

        marker.color.r = 0.1
        marker.color.g = 0.9
        marker.color.b = 0.25
        marker.color.a = 1.0

        array = MarkerArray()
        array.markers.append(marker)
        self._wp_pub.publish(array)

    def _publish_coverage(self, stamp) -> None:
        """patrol.rviz의 Coverage 표시를 실제 이동 지점으로 갱신한다."""

        marker = Marker()
        marker.header.frame_id = "map"
        marker.header.stamp = stamp
        marker.ns = "cov"
        marker.id = 0
        marker.type = Marker.POINTS
        marker.action = Marker.ADD
        marker.pose.orientation.w = 1.0

        marker.scale.x = 0.22
        marker.scale.y = 0.22

        marker.color.r = 0.1
        marker.color.g = 0.8
        marker.color.b = 0.3
        marker.color.a = 0.18

        for x, y in self._trail:
            point = Point()
            point.x = x
            point.y = y
            point.z = 0.025
            marker.points.append(point)

        self._coverage_pub.publish(marker)

    def _publish_camera_fov(self, pose: dict, stamp) -> None:
        """지도 위에 로봇의 전방 시야를 삼각형으로 표시한다."""

        yaw = float(pose["yaw"])
        half_fov = math.radians(40.0)
        max_range = 4.0

        marker = Marker()
        marker.header.frame_id = "map"
        marker.header.stamp = stamp
        marker.ns = "fov"
        marker.id = 0
        marker.type = Marker.LINE_STRIP
        marker.action = Marker.ADD
        marker.pose.orientation.w = 1.0

        marker.scale.x = 0.035
        marker.color.r = 1.0
        marker.color.g = 0.85
        marker.color.b = 0.1
        marker.color.a = 0.8

        angles = [
            yaw,
            yaw - half_fov,
            yaw + half_fov,
            yaw,
        ]

        distances = [
            0.0,
            max_range,
            max_range,
            0.0,
        ]

        for angle, distance in zip(angles, distances):
            point = Point()
            point.x = float(pose["x"]) + math.cos(angle) * distance
            point.y = float(pose["y"]) + math.sin(angle) * distance
            point.z = 0.075
            marker.points.append(point)

        self._fov_pub.publish(marker)

    def _is_wall(self, world_x: float, world_y: float) -> bool:
        if self._map_image is None:
            return True

        pixel_x = int((world_x - _OX) / _RES)
        pixel_y = int(
            self._map_height - (world_y - _OY) / _RES
        )

        if (
            pixel_x < 0
            or pixel_y < 0
            or pixel_x >= self._map_image.shape[1]
            or pixel_y >= self._map_image.shape[0]
        ):
            return True

        return bool(self._map_image[pixel_y, pixel_x] < 100)

    def _publish_camera(self, pose: dict, stamp) -> None:
        """지도 벽을 이용해 간단한 로봇 전방 영상을 생성한다."""

        width = 640
        height = 360
        horizon = 165

        horizontal_fov = math.radians(80.0)
        max_range = 5.0
        ray_step = 0.05

        frame = np.zeros((height, width, 3), dtype=np.uint8)

        # 하늘과 바닥
        frame[:horizon, :, :] = (55, 45, 40)
        frame[horizon:, :, :] = (65, 65, 65)

        robot_x = float(pose["x"])
        robot_y = float(pose["y"])
        robot_yaw = float(pose["yaw"])

        for column in range(width):
            ratio = column / max(1, width - 1)
            ray_angle = robot_yaw + (ratio - 0.5) * horizontal_fov

            wall_distance = None
            distance = 0.10

            while distance <= max_range:
                sample_x = robot_x + math.cos(ray_angle) * distance
                sample_y = robot_y + math.sin(ray_angle) * distance

                if self._is_wall(sample_x, sample_y):
                    wall_distance = distance
                    break

                distance += ray_step

            if wall_distance is None:
                continue

            projected_height = int(
                min(height, 210.0 / max(wall_distance, 0.20))
            )

            top = max(0, horizon - projected_height // 2)
            bottom = min(
                height - 1,
                horizon + projected_height // 2,
            )

            brightness = int(
                np.clip(230 - wall_distance * 28, 70, 220)
            )

            frame[top:bottom, column] = (
                brightness,
                brightness,
                brightness,
            )

        # 화면 중앙선
        cv2.line(
            frame,
            (width // 2 - 10, horizon),
            (width // 2 + 10, horizon),
            (0, 255, 255),
            1,
        )
        cv2.line(
            frame,
            (width // 2, horizon - 10),
            (width // 2, horizon + 10),
            (0, 255, 255),
            1,
        )

        cv2.putText(
            frame,
            "BRING WATER - FRONT CAMERA",
            (15, 28),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.60,
            (255, 255, 255),
            1,
            cv2.LINE_AA,
        )

        image_message = Image()
        image_message.header.stamp = stamp
        image_message.header.frame_id = "base_footprint"
        image_message.height = height
        image_message.width = width
        image_message.encoding = "bgr8"
        image_message.is_bigendian = 0
        image_message.step = width * 3
        image_message.data = frame.tobytes()

        self._camera_pub.publish(image_message)

    def publish_pose(self, pose: dict) -> None:
        """TF, 경로, 로봇 원, FOV, 카메라를 한 번에 갱신한다."""

        now = self._node.get_clock().now().to_msg()

        # map -> base_footprint TF
        transform = TransformStamped()
        transform.header.stamp = now
        transform.header.frame_id = "map"
        transform.child_frame_id = "base_footprint"

        transform.transform.translation.x = float(pose["x"])
        transform.transform.translation.y = float(pose["y"])
        transform.transform.translation.z = 0.0

        yaw = float(pose["yaw"])
        transform.transform.rotation.z = math.sin(yaw / 2.0)
        transform.transform.rotation.w = math.cos(yaw / 2.0)

        self._tf.sendTransform(transform)

        # wheel joint 갱신
        self._spin += 0.35

        joint_state = JointState()
        joint_state.header.stamp = now
        joint_state.name = _WHEELS
        joint_state.position = [self._spin] * len(_WHEELS)

        self._joint_pub.publish(joint_state)

        # 실제 이동 궤적
        self._trail.append(
            (float(pose["x"]), float(pose["y"]))
        )

        trail = Marker()
        trail.header.frame_id = "map"
        trail.header.stamp = now
        trail.ns = "trail"
        trail.id = 0
        trail.type = Marker.LINE_STRIP
        trail.action = Marker.ADD
        trail.pose.orientation.w = 1.0

        trail.scale.x = 0.05

        trail.color.r = 1.0
        trail.color.g = 0.5
        trail.color.b = 0.0
        trail.color.a = 1.0

        for trail_x, trail_y in self._trail:
            point = Point()
            point.x = trail_x
            point.y = trail_y
            point.z = 0.035
            trail.points.append(point)

        self._trail_pub.publish(trail)

        self._publish_robot_marker(pose, now)
        self._publish_coverage(now)
        self._publish_camera_fov(pose, now)
        self._publish_camera(pose, now)