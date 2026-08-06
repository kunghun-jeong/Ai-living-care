"""카메라 토픽을 구독해서 최신 프레임을 캐시해두는 모듈.

Actions.py와 마찬가지로 ROS2에 의존한다. Reasonings.py의 `ReasoningModule`이
기대하는 `FrameSource` 시그니처((frame_id=None) -> {"frame_id","frame","stamp","pose"})를
그대로 만족하도록 `get_latest_frame`을 노출한다.
"""

import threading
from typing import Optional

import numpy as np
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image


class PerceptionModule:
    def __init__(self, node, topic: str = "/camera/image_raw"):
        self._lock = threading.Lock()
        self._latest: Optional[dict] = None
        self._seq = 0
        node.create_subscription(Image, topic, self._on_image, qos_profile_sensor_data)

    def _on_image(self, msg: Image) -> None:
        # 카메라 SDF가 R8G8B8(=rgb8)로 정의돼 있어 그 가정으로 바로 reshape한다.
        frame = np.frombuffer(msg.data, dtype=np.uint8).reshape(msg.height, msg.width, 3)

        with self._lock:
            self._seq += 1
            self._latest = {
                "frame_id": f"f_{self._seq}",
                "frame": frame,
                "stamp": msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9,
                "pose": None,
            }

    def get_latest_frame(self, frame_id: Optional[str] = None) -> Optional[dict]:
        with self._lock:
            item = self._latest
        if item is None:
            return None
        if frame_id is not None and item["frame_id"] != frame_id:
            return None
        return item
