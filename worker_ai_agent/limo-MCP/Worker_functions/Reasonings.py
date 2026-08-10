"""Worker AI agent의 Reasoning 모듈.

ROS2/MCP에 의존하지 않는 순수 로직. 실제 백엔드(YOLO, Nav2, 크롭)는 생성자로
주입하고, 주입하지 않으면 no-op으로 동작하므로 로봇 없이 단독 테스트가 가능하다.
"""

import math
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from typing import Callable, Optional

import numpy as np

DetectFn = Callable[[object], list]          # frame -> [{"class", "conf", "bbox"}]
PlanFn = Callable[[dict, dict], list]        # start, goal -> [{"x", "y", "yaw"}]
CropFn = Callable[[object, list], bytes]     # frame, bbox -> jpeg bytes
FrameSource = Callable[..., Optional[dict]]  # (frame_id=None) -> {"frame_id", "frame", "stamp", "pose"}
ResolveFn = Callable[[str], dict]            # name -> {"x", "y", "frame", "yaw_deg"} (모르면 LookupError)
AstarFn = Callable[[dict, dict], list]       # start, goal -> [{"x","y"}, ...] (경로 없으면 빈 리스트)


def _no_op_detect(_frame) -> list:
    return []


def _no_op_plan(_start: dict, _goal: dict) -> list:
    return []


def _no_op_crop(_frame, _bbox) -> bytes:
    return b""


def _no_op_frame_source(_frame_id: Optional[str] = None) -> Optional[dict]:
    return None


def _no_op_resolve(_name: str) -> dict:
    raise LookupError("no location resolver configured")


def _no_op_astar(_start: dict, _goal: dict) -> list:
    return []


# ---------------------------------------------------------------------- #
# A* 경로계획 — tools/limo-patrol-viz/patrol_sim.py와 같은 맵·같은 알고리즘.
# Nav2·Gazebo 없이 map.pgm 점유격자 위에서 직접 계산한다(순수 로직, cv2는 이
# 함수 안에서만 import).
# ---------------------------------------------------------------------- #
_MAP_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "tools", "limo-patrol-viz", "maps"
)
_MAP_RESOLUTION, _MAP_ORIGIN_X, _MAP_ORIGIN_Y = 0.05, -10.0, -10.0  # maps/map.yaml과 동일
_ROBOT_RADIUS_M = 0.22  # 충돌 여유 (patrol_sim.py의 ROBOT_R과 동일)

_grid_cache: Optional[dict] = None


def _load_grid() -> dict:
    global _grid_cache
    if _grid_cache is not None:
        return _grid_cache

    import cv2

    with open(os.path.join(_MAP_DIR, "map.pgm"), "rb") as f:
        img = cv2.imdecode(np.frombuffer(f.read(), np.uint8), cv2.IMREAD_GRAYSCALE)
    height, width = img.shape
    free = (img > 250).astype(np.uint8)
    dist_m = cv2.distanceTransform(free, cv2.DIST_L2, 5) * _MAP_RESOLUTION
    drivable = dist_m >= _ROBOT_RADIUS_M
    _grid_cache = {"height": height, "width": width, "dist_m": dist_m, "drivable": drivable}
    return _grid_cache


def _to_px(x: float, y: float, height: int) -> tuple:
    return int(round((x - _MAP_ORIGIN_X) / _MAP_RESOLUTION)), int(
        round(height - (y - _MAP_ORIGIN_Y) / _MAP_RESOLUTION)
    )


def _to_m(px: int, py: int, height: int) -> tuple:
    return _MAP_ORIGIN_X + px * _MAP_RESOLUTION, _MAP_ORIGIN_Y + (height - py) * _MAP_RESOLUTION


def astar_plan(start: dict, goal: dict) -> list:
    """map.pgm 점유격자 위에서 A*로 `start`(x,y)에서 `goal`(x,y)까지 경로를 찾는다.

    patrol_sim.py와 동일한 비용함수(벽 근접 페널티)·솎기(0.2m 간격)를 쓴다.
    성공하면 [{"x","y"}, ...], 갈 수 없으면 빈 리스트.
    """
    import heapq

    grid = _load_grid()
    height, width = grid["height"], grid["width"]
    drivable, dist_m = grid["drivable"], grid["dist_m"]

    def snap(p):
        if drivable[p[1], p[0]]:
            return p
        ys, xs = np.nonzero(drivable)
        k = np.argmin((xs - p[0]) ** 2 + (ys - p[1]) ** 2)
        return int(xs[k]), int(ys[k])

    s = snap(_to_px(start["x"], start["y"], height))
    g = snap(_to_px(goal["x"], goal["y"], height))

    neighbors = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
    open_heap = [(0.0, s)]
    came_from: dict = {}
    g_score = {s: 0.0}
    while open_heap:
        _, cur = heapq.heappop(open_heap)
        if cur == g:
            break
        for dx, dy in neighbors:
            nx, ny = cur[0] + dx, cur[1] + dy
            if not (0 <= nx < width and 0 <= ny < height) or not drivable[ny, nx]:
                continue
            step = math.hypot(dx, dy)
            cost = g_score[cur] + step * (1.0 + 2.0 * max(0.0, 0.6 - dist_m[ny, nx]))
            if cost < g_score.get((nx, ny), 1e18):
                g_score[(nx, ny)] = cost
                came_from[(nx, ny)] = cur
                h = math.hypot(nx - g[0], ny - g[1])
                heapq.heappush(open_heap, (cost + h, (nx, ny)))

    if g not in came_from and g != s:
        return []

    path_px, cur = [], g
    while cur != s:
        path_px.append(cur)
        cur = came_from[cur]
    path_px.append(s)
    path_px.reverse()
    path_px = path_px[::4] or [path_px[-1]]

    return [{"x": wx, "y": wy} for wx, wy in (_to_m(px, py, height) for px, py in path_px)]


_yolo_model = None


def yolo_detect(frame) -> list:
    """YOLO(ultralytics)로 프레임 안의 물체를 검출한다. detect_fn 구현체 중 하나.

    ultralytics는 이 함수 안에서만 import한다 — 이 모듈을 그냥 import만 했을 때
    (YOLO를 안 쓸 때)는 무거운 의존성(torch 등)을 안 물게 하기 위함. ultralytics는
    numpy 배열을 BGR로 가정하므로(카메라 프레임은 RGB) 채널을 뒤집어 넣는다.
    """
    global _yolo_model
    from ultralytics import YOLO

    if _yolo_model is None:
        _yolo_model = YOLO("yolov8n.pt")

    results = _yolo_model(frame[:, :, ::-1], verbose=False)[0]
    return [
        {
            "class": results.names[int(box.cls[0])],
            "conf": float(box.conf[0]),
            "bbox": [float(v) for v in box.xyxy[0]],
        }
        for box in results.boxes
    ]


class PersonScan:
    """1Hz로 최신 프레임에 YOLO를 돌려 사람 유무(O/X)만 판별하는 백그라운드 루프.

    상태 판정은 하지 않는다. 사람이 잡히면 그 시점의 프레임/pose만 기록해두고
    실제 "괜찮은지" 판단은 상위 LLM이 크롭 이미지를 보고 내린다.
    """

    def __init__(
        self,
        scan_id: str,
        frame_source: FrameSource,
        detect_fn: DetectFn,
        hz: float = 1.0,
        person_class: str = "person",
        min_conf: float = 0.5,
        stop_on_hit: bool = True,
    ):
        self.scan_id = scan_id
        self._frame_source = frame_source
        self._detect_fn = detect_fn
        self._period = 1.0 / hz if hz > 0 else 1.0
        self._person_class = person_class
        self._min_conf = min_conf
        self._stop_on_hit = stop_on_hit

        self._stop = threading.Event()
        self._hit_event = threading.Event()
        self._lock = threading.Lock()
        self._hit: Optional[dict] = None
        self._ticks = 0
        self._last_frame_id: Optional[str] = None
        self._error: Optional[str] = None
        self._thread = threading.Thread(target=self._run, name=f"person-scan-{scan_id}", daemon=True)

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        self._hit_event.set()  # 대기 중인 wait_for_person을 깨운다

    def wait(self, timeout: float) -> dict:
        self._hit_event.wait(timeout)
        return self.status()

    def status(self) -> dict:
        with self._lock:
            return {
                "scan_id": self.scan_id,
                "running": self._thread.is_alive() and not self._stop.is_set(),
                "ticks": self._ticks,
                "found": self._hit is not None,
                "hit": self._hit,
                "error": self._error,
            }

    def _run(self) -> None:
        while not self._stop.is_set():
            started = time.monotonic()
            try:
                self._tick()
            except Exception as exc:
                with self._lock:
                    self._error = repr(exc)
            self._stop.wait(max(0.0, self._period - (time.monotonic() - started)))

    def _tick(self) -> None:
        item = self._frame_source()
        if item is None or item.get("frame_id") == self._last_frame_id:
            return  # 새 프레임이 없으면 같은 이미지를 두 번 돌리지 않는다
        self._last_frame_id = item.get("frame_id")
        with self._lock:
            self._ticks += 1

        persons = [
            d
            for d in (self._detect_fn(item["frame"]) or [])
            if d.get("class") == self._person_class and d.get("conf", 0.0) >= self._min_conf
        ]
        if not persons:
            return

        best = max(persons, key=lambda d: d.get("conf", 0.0))
        with self._lock:
            self._hit = {
                "frame_id": item.get("frame_id"),
                "stamp": item.get("stamp"),
                "pose": item.get("pose"),
                "bbox": best.get("bbox"),
                "conf": best.get("conf"),
            }
        self._hit_event.set()
        if self._stop_on_hit:
            self._stop.set()


class ReasoningModule:
    def __init__(
        self,
        detect_fn: DetectFn = _no_op_detect,
        plan_fn: PlanFn = _no_op_plan,
        crop_fn: CropFn = _no_op_crop,
        frame_source: FrameSource = _no_op_frame_source,
        resolve_fn: ResolveFn = _no_op_resolve,
        astar_fn: AstarFn = _no_op_astar,
        max_workers: int = 2,
    ):
        self._detect_fn = detect_fn
        self._plan_fn = plan_fn
        self._crop_fn = crop_fn
        self._frame_source = frame_source
        self._resolve_fn = resolve_fn
        self._astar_fn = astar_fn
        self._pool = ThreadPoolExecutor(max_workers=max_workers)
        self._scan: Optional[PersonScan] = None
        self._scan_seq = 0
        self._scan_lock = threading.Lock()

    # --- 단발 검출 / 경로 ---

    def detect_objects(self, frame, timeout: float = 5.0) -> dict:
        future = self._pool.submit(self._detect_fn, frame)
        try:
            return {"detections": future.result(timeout=timeout)}
        except FutureTimeoutError:
            return {"detections": None, "reason": "detection timed out"}

    def plan_path(self, start: dict, goal: dict, timeout: float = 10.0) -> dict:
        future = self._pool.submit(self._plan_fn, start, goal)
        try:
            return {"waypoints": future.result(timeout=timeout)}
        except FutureTimeoutError:
            return {"waypoints": None, "reason": "planning timed out"}

    def pathplanning(self, start: dict, goal: dict, timeout: float = 10.0) -> dict:
        """A*로 start->goal 경로를 계산한다. 실패하면 reason이 담긴 dict."""
        future = self._pool.submit(self._astar_fn, start, goal)
        try:
            waypoints = future.result(timeout=timeout)
        except FutureTimeoutError:
            return {"waypoints": None, "reason": "path planning timed out"}
        if not waypoints:
            return {"waypoints": None, "reason": "no path found"}
        return {"waypoints": waypoints}

    def resolve_location(self, name: str) -> dict:
        """이름(장소·디바이스)을 좌표로 해소한다. KG에 없으면 resolved=False로 이유를 담아 돌려준다."""
        try:
            pose = self._resolve_fn(name)
        except LookupError as exc:
            return {"resolved": False, "name": name, "reason": str(exc)}
        return {"resolved": True, "name": name, **pose}

    # --- 상태 확인용 근거 이미지 (판정은 LLM이 한다) ---

    def check_object_state(self, object_class: str = "person", frame_id: Optional[str] = None) -> dict:
        """대상이 찍힌 프레임에서 해당 영역을 크롭해 JPEG으로 돌려준다."""
        item = self._frame_source(frame_id)
        if item is None:
            return {"image_jpeg": None, "reason": "no frame available"}

        detections = self._detect_fn(item["frame"]) or []
        targets = [d for d in detections if d.get("class") == object_class]
        if not targets:
            return {"image_jpeg": None, "reason": f"{object_class} not in frame", "frame_id": item.get("frame_id")}

        best = max(targets, key=lambda d: d.get("conf", 0.0))
        return {
            "image_jpeg": self._crop_fn(item["frame"], best.get("bbox")),
            "bbox": best.get("bbox"),
            "conf": best.get("conf"),
            "frame_id": item.get("frame_id"),
            "stamp": item.get("stamp"),
            "pose": item.get("pose"),
        }

    # --- 1Hz 사람 탐지 루프 ---

    def start_person_scan(self, hz: float = 1.0, min_conf: float = 0.5, stop_on_hit: bool = True) -> dict:
        with self._scan_lock:
            if self._scan is not None and self._scan.status()["running"]:
                return {"scan_id": self._scan.scan_id, "reason": "already running"}
            self._scan_seq += 1
            self._scan = PersonScan(
                scan_id=f"s_{self._scan_seq}",
                frame_source=self._frame_source,
                detect_fn=self._detect_fn,
                hz=hz,
                min_conf=min_conf,
                stop_on_hit=stop_on_hit,
            )
            self._scan.start()
            return {"scan_id": self._scan.scan_id}

    def wait_for_person(self, timeout: float = 30.0) -> dict:
        scan = self._scan
        if scan is None:
            return {"found": False, "reason": "no scan running"}
        return scan.wait(timeout)

    def get_scan_status(self) -> dict:
        scan = self._scan
        return scan.status() if scan is not None else {"running": False, "found": False}

    def stop_person_scan(self) -> dict:
        scan = self._scan
        if scan is None:
            return {"stopped": False, "reason": "no scan running"}
        scan.stop()
        return {"stopped": True, "scan_id": scan.scan_id}
