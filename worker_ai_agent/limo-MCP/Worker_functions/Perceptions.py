"""카메라 토픽을 구독해서 최신 프레임을 캐시해두는 모듈.

Actions.py와 마찬가지로 ROS2에 의존한다. Reasonings.py의 `ReasoningModule`이
기대하는 `FrameSource` 시그니처((frame_id=None) -> {"frame_id","frame","stamp","pose"})를
그대로 만족하도록 `get_latest_frame`을 노출한다.
"""

import math
import os
import threading
import time
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


# --------------------------------------------------------------------------- #
# 기하 카메라 시뮬레이션 — Gazebo·YOLO 없이 인지 단계를 돌리기 위한 것.
#
# Actions.py의 moving_path가 Nav2 없이 운동학만 적분하는 것과 같은 성격이다:
# 실물을 대신하는 게 아니라, 상위 흐름(시나리오 DSL)을 검증하기 위한 대역이다.
# tools/limo-patrol-viz/patrol_viz.py의 render_camera와 같은 방식(점유격자 레이캐스팅)
# 을 쓴다. 결과에는 항상 source="geometric_sim"이 붙으므로 실측과 섞이지 않는다.
#
# SIM_PERSON="x,y" 환경변수로 켠다. 없으면 이 클래스는 만들어지지 않는다.
# --------------------------------------------------------------------------- #
_MAP_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "tools", "limo-patrol-viz", "maps"
)


def _read_map_meta(map_dir: str) -> tuple:
    """map.yaml에서 해상도·원점을 읽는다. 맵을 다시 뜨면 바뀌므로 하드코딩하지 않는다."""
    res, ox, oy = 0.05, -10.0, -10.0
    try:
        with open(os.path.join(map_dir, "map.yaml"), encoding="utf-8") as f:
            for line in f:
                if line.startswith("resolution:"):
                    res = float(line.split(":", 1)[1])
                elif line.startswith("origin:"):
                    ox, oy = [float(v) for v in line.split("[", 1)[1].split("]")[0].split(",")[:2]]
    except (OSError, ValueError, IndexError):
        pass
    return res, ox, oy


def _normalize_angle(a: float) -> float:
    return (a + math.pi) % (2 * math.pi) - math.pi


class SimCameraPerception:
    """점유격자 위에서 1인칭 화면을 합성하고, 그 안의 사람을 기하학적으로 검출한다."""

    def __init__(self, person_xy: Optional[tuple] = None, fov_deg: float = 62.0,
                 range_m: float = 4.0, img_w: int = 320, img_h: int = 240,
                 person_r: float = 0.30, map_dir: Optional[str] = None):
        import cv2

        self.map_dir = map_dir or _MAP_DIR
        self.res, self.ox, self.oy = _read_map_meta(self.map_dir)
        with open(os.path.join(self.map_dir, "map.pgm"), "rb") as f:
            img = cv2.imdecode(np.frombuffer(f.read(), np.uint8), cv2.IMREAD_GRAYSCALE)
        self.h_px, self.w_px = img.shape
        self.blocked = img < 250          # 벽 + 미탐색 = 시야 차단 (patrol_sim.py와 동일)

        self.person = tuple(person_xy) if person_xy else None
        self.fov = math.radians(fov_deg)
        self.range_m = range_m
        self.img_w, self.img_h = img_w, img_h
        self.person_r = person_r
        self._seq = 0

    # --- 격자 좌표 ---
    def _px(self, x: float, y: float) -> tuple:
        return (int(round((x - self.ox) / self.res)),
                int(round(self.h_px - (y - self.oy) / self.res)))

    def _ray(self, x: float, y: float, ang: float) -> Optional[float]:
        """(x,y)에서 ang 방향으로 쏴서 처음 막히는 거리(m). 사거리 안에 없으면 None."""
        ux, uy = math.cos(ang), math.sin(ang)
        for s in range(1, int(self.range_m / self.res) + 1):
            d = s * self.res
            px, py = self._px(x + ux * d, y + uy * d)
            if not (0 <= px < self.w_px and 0 <= py < self.h_px):
                return d
            if self.blocked[py, px]:
                return d
        return None

    def _clear(self, x: float, y: float, tx: float, ty: float) -> bool:
        """(x,y)에서 (tx,ty)까지 시야가 트였나."""
        d = math.hypot(tx - x, ty - y)
        if d < 1e-6:
            return True
        ux, uy = (tx - x) / d, (ty - y) / d
        for s in range(1, int(d / self.res)):
            px, py = self._px(x + ux * s * self.res, y + uy * s * self.res)
            if not (0 <= px < self.w_px and 0 <= py < self.h_px) or self.blocked[py, px]:
                return False
        return True

    # --- 사람 ---
    def detect_person(self, pose: dict) -> Optional[dict]:
        """pose에서 사람이 보이면 {"bbox","dist","conf"}, 안 보이면 None."""
        if self.person is None:
            return None
        px_, py_ = self.person
        dist = math.hypot(px_ - pose["x"], py_ - pose["y"])
        if dist > self.range_m or dist < 1e-3:
            return None
        rel = _normalize_angle(math.atan2(py_ - pose["y"], px_ - pose["x"]) - pose["yaw"])
        if abs(rel) > self.fov / 2:
            return None
        if not self._clear(pose["x"], pose["y"], px_, py_):
            return None

        focal = self.img_w / (2 * math.tan(self.fov / 2))
        cx = int((rel + self.fov / 2) / self.fov * (self.img_w - 1))
        w = int(np.clip(self.person_r * 2 / dist * focal, 8, self.img_w))
        h = int(np.clip(1.6 / dist * focal, 12, self.img_h))
        cy = self.img_h // 2
        bbox = [max(0, cx - w // 2), max(0, cy - h // 2),
                min(self.img_w - 1, cx + w // 2), min(self.img_h - 1, cy + h // 2)]
        # 가까울수록 크고 또렷하다 — 사거리 끝에서 0.5, 코앞에서 0.95
        conf = float(np.clip(0.95 - 0.45 * (dist / self.range_m), 0.5, 0.95))
        return {"bbox": bbox, "dist": round(dist, 2), "conf": round(conf, 2)}

    # --- 화면 합성 ---
    def render(self, pose: dict) -> tuple:
        """(frame, person_hit) — frame은 BGR ndarray."""
        import cv2

        W, H = self.img_w, self.img_h
        frame = np.empty((H, W, 3), np.uint8)
        frame[: H // 2] = (70, 55, 45)      # 천장
        frame[H // 2:] = (50, 50, 58)       # 바닥

        # 열마다 레이캐스팅 — 5 Hz로 흘려보내야 하므로 numpy로 한 번에 계산한다.
        rel = np.linspace(-self.fov / 2, self.fov / 2, W)
        angs = pose["yaw"] + rel
        steps = np.arange(1, int(self.range_m / self.res) + 1) * self.res
        xs = pose["x"] + np.cos(angs)[:, None] * steps[None, :]
        ys = pose["y"] + np.sin(angs)[:, None] * steps[None, :]
        px = np.rint((xs - self.ox) / self.res).astype(np.int32)
        py = np.rint(self.h_px - (ys - self.oy) / self.res).astype(np.int32)
        inside = (px >= 0) & (px < self.w_px) & (py >= 0) & (py < self.h_px)
        stop = ~inside
        stop[inside] |= self.blocked[py[inside], px[inside]]

        any_hit = stop.any(axis=1)
        first = np.argmax(stop, axis=1)
        dist = np.where(any_hit, (first + 1) * self.res, np.inf)
        dist = dist * np.maximum(np.cos(rel), 1e-3)          # 어안 보정
        bars = np.clip(H / np.maximum(dist, 0.3) * 0.55, 4, H).astype(np.int32)
        shades = np.clip(235 - dist * 45, 45, 235).astype(np.uint8)

        for col in range(W):
            if not any_hit[col]:
                continue
            top = (H - bars[col]) // 2
            frame[top:top + bars[col], col] = shades[col]

        hit = self.detect_person(pose)
        if hit:
            x1, y1, x2, y2 = hit["bbox"]
            cv2.rectangle(frame, (x1, y1), (x2, y2), (90, 140, 220), -1)
            cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 255, 255), 1)
            cv2.putText(frame, f"person {hit['dist']}m", (max(0, x1 - 4), max(12, y1 - 4)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.35, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(frame, "GEOMETRIC SIM (not a real camera)", (6, H - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.34, (120, 200, 255), 1, cv2.LINE_AA)
        return frame, hit

    def get_frame(self, pose: dict) -> dict:
        """PerceptionModule.get_latest_frame과 같은 모양으로 돌려준다."""
        frame, hit = self.render(pose)
        self._seq += 1
        return {
            "frame_id": f"sim_{self._seq}",
            "frame": frame,
            "stamp": time.time(),
            "pose": dict(pose),
            "detections": ([{"class": "person", "conf": hit["conf"], "bbox": hit["bbox"]}]
                           if hit else []),
            "source": "geometric_sim",
        }


def sim_camera_from_env() -> Optional["SimCameraPerception"]:
    """SIM_PERSON="x,y" 가 있으면 시뮬 카메라를 만든다. 없으면 None (기본 동작 유지)."""
    raw = os.environ.get("SIM_PERSON", "").strip()
    if not raw:
        return None
    try:
        x, y = [float(v) for v in raw.split(",")[:2]]
    except (ValueError, IndexError):
        return None
    return SimCameraPerception(person_xy=(x, y))
