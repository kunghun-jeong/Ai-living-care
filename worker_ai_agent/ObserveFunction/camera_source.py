"""ROS2 카메라 토픽을 구독하고 최근 프레임을 보관한다."""

import threading
from collections import deque
from typing import Optional

import numpy as np
from cv_bridge import CvBridge
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image


class PerceptionModule:
    """카메라의 최근 프레임을 캐시해 제공한다."""

    def __init__(
        self,
        node,
        topic: str = "/camera/image_raw",
        buffer_size: int = 30,
    ):
        self._node = node
        self._lock = threading.Lock()
        self._frames = deque(maxlen=buffer_size)
        self._sequence = 0
        self._bridge = CvBridge()

        # subscription 객체를 보관해야 구독이 유지된다.
        self._subscription = node.create_subscription(
            Image,
            topic,
            self._on_image,
            qos_profile_sensor_data,
        )

        node.get_logger().info(
            f"camera subscription created: {topic}"
        )

    def _on_image(self, msg: Image) -> None:
        """ROS Image 메시지를 RGB NumPy 배열로 변환한다."""

        try:
            frame = self._bridge.imgmsg_to_cv2(
                msg,
                desired_encoding="rgb8",
            )
        except Exception as exc:
            self._node.get_logger().error(
                f"failed to convert camera image: {exc}"
            )
            return

        # ROS 메시지 버퍼와 분리해 안전하게 저장한다.
        frame = np.asarray(frame, dtype=np.uint8).copy()

        stamp = (
            msg.header.stamp.sec
            + msg.header.stamp.nanosec * 1e-9
        )

        with self._lock:
            self._sequence += 1

            item = {
                "frame_id": f"f_{self._sequence}",
                "frame": frame,
                "stamp": stamp,
                "source_frame": msg.header.frame_id,
                "pose": None,
            }

            self._frames.append(item)

    def get_latest_frame(
        self,
        frame_id: Optional[str] = None,
    ) -> Optional[dict]:
        """최신 프레임 또는 지정된 frame_id의 프레임을 반환한다."""

        with self._lock:
            if not self._frames:
                return None

            if frame_id is None:
                return self._frames[-1].copy()

            for item in reversed(self._frames):
                if item["frame_id"] == frame_id:
                    return item.copy()

        return None

    def get_frame_count(self) -> int:
        with self._lock:
            return len(self._frames)