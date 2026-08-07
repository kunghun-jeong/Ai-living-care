"""카메라 토픽을 구독해서 최신 프레임을 캐시해두는 모듈.

Actions.py와 마찬가지로 ROS2에 의존한다. Reasonings.py의 `ReasoningModule`이
기대하는 `FrameSource` 시그니처((frame_id=None) -> {"frame_id","frame","stamp","pose"})를
그대로 만족하도록 `get_latest_frame`을 노출한다.

세 가지를 지킨다 (2026-08-06):
  · 콜백에서 예외를 내보내지 않는다 — 나가면 `rclpy.spin` 스레드가 죽어
    카메라뿐 아니라 Nav2 액션 콜백까지 전부 멈춘다 (F-1)
  · 오래된 프레임을 새 프레임인 척 돌려주지 않는다 — 카메라가 죽어도
    옛 사진으로 "정상"을 보고하게 된다 (F-3)
  · 나이는 **노드 시계**로 잰다. `use_sim_time`에서 벽시계로 재면 RTF 0.04일 때
    25배로 어긋난다 (F-5와 같은 부류)
"""

import threading
from collections import OrderedDict
from typing import Optional

import numpy as np
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image

# encoding -> (채널 수, RGB로 만드는 변환)
_ENCODINGS = {
    "rgb8":  (3, lambda a: a),
    "bgr8":  (3, lambda a: a[:, :, ::-1]),
    "rgba8": (4, lambda a: a[:, :, :3]),
    "bgra8": (4, lambda a: a[:, :, 2::-1]),
    "mono8": (1, lambda a: np.repeat(a, 3, axis=2)),
}

STALE_AFTER_SEC = 2.0   # 이보다 오래된 프레임은 없는 것으로 취급한다
BUFFER_SIZE = 30        # frame_id로 되짚을 수 있는 과거 프레임 수 (G-1 pinning)


class PerceptionModule:
    def __init__(self, node, topic: str = "/camera/image_raw",
                 stale_after_sec: float = STALE_AFTER_SEC, buffer_size: int = BUFFER_SIZE):
        self._lock = threading.Lock()
        self._buf: "OrderedDict[str, dict]" = OrderedDict()
        self._latest_id: Optional[str] = None
        self._seq = 0
        self._dropped = 0
        self._last_error: Optional[str] = None
        self._stale_after = stale_after_sec
        self._buffer_size = buffer_size
        self._clock = node.get_clock()          # use_sim_time을 따른다
        node.create_subscription(Image, topic, self._on_image, qos_profile_sensor_data)

    # ---------------------------------------------------------------- #
    # 구독 콜백 — 여기서 예외가 새어나가면 spin 스레드가 죽는다 (F-1)
    # ---------------------------------------------------------------- #
    def _on_image(self, msg: Image) -> None:
        try:
            frame = self._decode(msg)
        except Exception as exc:                # noqa: BLE001 — 무엇이든 삼켜야 한다
            with self._lock:
                self._dropped += 1
                self._last_error = f"{type(exc).__name__}: {exc}"
            return

        with self._lock:
            self._seq += 1
            fid = f"f_{self._seq}"
            self._buf[fid] = {
                "frame_id": fid,
                "frame": frame,
                "stamp": msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9,
                "pose": None,                   # TODO(확인 필요) TF 스탬프 — G-2
            }
            self._latest_id = fid
            while len(self._buf) > self._buffer_size:
                self._buf.popitem(last=False)

    def _decode(self, msg: Image):
        """encoding을 검사해 RGB(h, w, 3) 배열로 만든다. 모르는 인코딩이면 예외."""
        enc = (msg.encoding or "").lower()
        if enc not in _ENCODINGS:
            raise ValueError(f"unsupported encoding {msg.encoding!r} "
                             f"(supported: {', '.join(sorted(_ENCODINGS))})")
        ch, to_rgb = _ENCODINGS[enc]
        expected = msg.width * ch
        step = msg.step or expected
        if len(msg.data) < step * msg.height:
            raise ValueError(f"truncated image: {len(msg.data)}B < step {step} x h {msg.height}")
        flat = np.frombuffer(msg.data, dtype=np.uint8)
        if step != expected:                    # 행 패딩이 있으면 잘라낸다
            flat = flat[:step * msg.height].reshape(msg.height, step)[:, :expected]
        arr = flat.reshape(msg.height, msg.width, ch)
        # np.frombuffer 결과는 read-only다 — 나중에 bbox를 그리려면 쓰기가 필요하다
        return np.ascontiguousarray(to_rgb(arr))

    # ---------------------------------------------------------------- #
    # 조회
    # ---------------------------------------------------------------- #
    def _now(self) -> float:
        return self._clock.now().nanoseconds * 1e-9

    def get_latest_frame(self, frame_id: Optional[str] = None,
                         allow_stale: bool = False) -> Optional[dict]:
        """최신(또는 지정한) 프레임. **오래됐으면 None**을 준다 (F-3).

        왜 stale을 None으로 돌려주는가: 호출자는 대부분 `if item is None` 하나로
        분기한다. 오래된 프레임을 돌려주면 그 분기를 통과해 "정상"으로 보고된다.
        사유가 필요하면 `frame_status()`를 본다.
        """
        with self._lock:
            item = self._buf.get(frame_id) if frame_id else self._buf.get(self._latest_id or "")
            if item is None:
                return None
            age = self._now() - item["stamp"]
            if not allow_stale and age > self._stale_after:
                return None
            return dict(item, age_sec=round(age, 3))

    def frame_status(self) -> dict:
        """왜 프레임이 없는지 — 미수신 / 오래됨 / 디코드 실패를 구분한다."""
        with self._lock:
            item = self._buf.get(self._latest_id or "")
            age = None if item is None else self._now() - item["stamp"]
            return {
                "have_frame": item is not None,
                "age_sec": None if age is None else round(age, 3),
                "stale": bool(age is not None and age > self._stale_after),
                "stale_after_sec": self._stale_after,
                "received": self._seq,
                "dropped": self._dropped,
                "last_error": self._last_error,
                "buffered": len(self._buf),
            }
