"""Worker AI agent의 Reasoning 모듈.

ROS2/MCP에 의존하지 않는 순수 로직. 실제 백엔드(YOLO, Nav2, 크롭)는 생성자로
주입하고, 주입하지 않으면 no-op으로 동작하므로 로봇 없이 단독 테스트가 가능하다.

판정 경로에서 지키는 것 (2026-08-06):
  · 증거 이미지에도 신뢰도 하한을 건다. 하한이 없으면 conf 0.08짜리 오탐이
    "할머니 사진"으로 올라간다 (F-47)
  · 스캔을 멈춘 뒤에는 결과를 쓰지 않는다. 멈춘 스캔이 사람을 "발견"하면
    이미 밀려난 프레임을 증거로 요구하게 된다 (F-50)
  · **새 프레임을 한 장도 못 봤으면 "사람 없음"이 아니다.** 죽은 카메라를
    "확인했고 아무도 없었다"로 읽으면 쓰러진 사람을 놓친다 (F-51)
"""

import threading
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from typing import Callable, Optional

DetectFn = Callable[[object], list]          # frame -> [{"class", "conf", "bbox"}]
PlanFn = Callable[[dict, dict], list]        # start, goal -> [{"x", "y", "yaw"}]
CropFn = Callable[[object, list], Optional[bytes]]  # frame, bbox -> jpeg bytes | None
FrameSource = Callable[..., Optional[dict]]  # (frame_id=None) -> {"frame_id", "frame", "stamp", "pose"}

EVIDENCE_MIN_CONF = 0.5   # 증거 이미지로 승격하는 최소 신뢰도 (F-47)


def _no_op_detect(_frame) -> list:
    return []


def _no_op_plan(_start: dict, _goal: dict) -> list:
    return []


def _no_op_crop(_frame, _bbox) -> Optional[bytes]:
    return b""


def _no_op_frame_source(_frame_id: Optional[str] = None) -> Optional[dict]:
    return None


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

    # 연속 이 횟수를 넘겨 새 프레임을 못 받으면 "사람 없음"이라 결론짓지 않는다
    STARVED_TICKS = 2

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
        self.hz = hz
        self.min_conf = min_conf
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
        self._frames_seen = 0          # 실제로 **새** 프레임을 본 횟수 (F-51)
        self._no_frame_ticks = 0
        self._consec_no_frame = 0      # 스캔이 굶은 채로 끝났는지
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
            frames, no_frame = self._frames_seen, self._no_frame_ticks
            consec, hit = self._consec_no_frame, self._hit
            st = {
                "scan_id": self.scan_id,
                "running": self._thread.is_alive() and not self._stop.is_set(),
                "ticks": self._ticks,
                "frames_seen": frames,          # F-51
                "no_frame_ticks": no_frame,
                "found": hit is not None,
                "hit": hit,
                "error": self._error,
            }
        # 사람을 못 찾은 것이 "없다"인지 "못 봤다"인지 구분한다 (F-51).
        # 카메라가 스캔 도중 죽으면 마지막 캐시 프레임 한 장만 보고 끝난다 —
        # 그것을 "방을 확인했고 아무도 없었다"로 읽으면 쓰러진 사람을 놓친다.
        if hit is not None:
            st["conclusive"] = True
            return st
        st["consecutive_no_frame"] = consec
        if frames == 0:
            st["conclusive"] = False
            st["reason"] = "no camera frame during scan — cannot conclude person absence"
        elif consec > self.STARVED_TICKS:
            st["conclusive"] = False
            st["reason"] = (f"camera stopped producing frames ({consec} consecutive ticks "
                            f"with no new frame) — cannot conclude person absence")
        else:
            st["conclusive"] = True
        return st

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
        with self._lock:
            self._ticks += 1
        item = self._frame_source()
        if item is None or item.get("frame_id") == self._last_frame_id:
            # 새 프레임이 없으면 같은 이미지를 두 번 돌리지 않는다.
            # 다만 **몇 번 그랬는지는 센다** — 이게 0이 아니면 결론을 못 낸다 (F-51).
            with self._lock:
                self._no_frame_ticks += 1
                self._consec_no_frame += 1
            return
        self._last_frame_id = item.get("frame_id")
        with self._lock:
            self._frames_seen += 1
            self._consec_no_frame = 0

        persons = [
            d
            for d in (self._detect_fn(item["frame"]) or [])
            if d.get("class") == self._person_class and d.get("conf", 0.0) >= self._min_conf
        ]
        if not persons:
            return

        best = max(persons, key=lambda d: d.get("conf", 0.0))
        with self._lock:
            if self._stop.is_set():
                return          # F-50 — 멈춘 스캔은 결과를 쓰지 않는다
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
        max_workers: int = 2,
    ):
        self._detect_fn = detect_fn
        self._plan_fn = plan_fn
        self._crop_fn = crop_fn
        self._frame_source = frame_source
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

    # --- 상태 확인용 근거 이미지 (판정은 LLM이 한다) ---

    def check_object_state(self, object_class: str = "person",
                           frame_id: Optional[str] = None,
                           min_conf: float = EVIDENCE_MIN_CONF) -> dict:
        """대상이 찍힌 프레임에서 해당 영역을 크롭해 JPEG으로 돌려준다.

        `min_conf` 미만은 증거로 올리지 않는다 (F-47). 이 경로에만 하한이 없어서
        `detect_objects`(0.4)와 `PersonScan`(0.5)이 거른 오탐이 여기로 통과했다.
        """
        item = self._frame_source(frame_id)
        if item is None:
            return {"image_jpeg": None,
                    "reason": "no fresh frame available"
                              + (f" for frame_id={frame_id}" if frame_id else "")}

        detections = self._detect_fn(item["frame"]) or []
        targets = [d for d in detections if d.get("class") == object_class]
        if not targets:
            return {"image_jpeg": None, "reason": f"{object_class} not in frame",
                    "frame_id": item.get("frame_id")}

        best = max(targets, key=lambda d: d.get("conf", 0.0))
        conf = best.get("conf", 0.0)
        if conf < min_conf:
            return {"image_jpeg": None,
                    "reason": f"{object_class} detected but confidence {conf:.2f} "
                              f"< {min_conf:.2f} — not used as evidence",
                    "conf": conf, "bbox": best.get("bbox"),
                    "frame_id": item.get("frame_id")}

        jpeg = self._crop_fn(item["frame"], best.get("bbox"))
        if jpeg is None:
            # 크롭이 실패했는데 전체 프레임으로 조용히 대체하면 "이 사람"의
            # 사진이 아닌 "이 방"의 사진이 판정 근거가 된다 (F-47).
            return {"image_jpeg": None, "reason": "crop failed for detected bbox",
                    "bbox": best.get("bbox"), "conf": conf,
                    "frame_id": item.get("frame_id")}

        return {
            "image_jpeg": jpeg,
            "bbox": best.get("bbox"),
            "conf": conf,
            "frame_id": item.get("frame_id"),
            "stamp": item.get("stamp"),
            "age_sec": item.get("age_sec"),
            "pose": item.get("pose"),
        }

    # --- 1Hz 사람 탐지 루프 ---

    def start_person_scan(self, hz: float = 1.0, min_conf: float = 0.5,
                          stop_on_hit: bool = True) -> dict:
        with self._scan_lock:
            if self._scan is not None and self._scan.status()["running"]:
                # 파라미터를 조용히 버리지 않는다 — 호출자는 새 min_conf가
                # 적용됐다고 믿고 더 민감해졌다고 오판한다 (F-50).
                return {
                    "started": False,
                    "scan_id": self._scan.scan_id,
                    "reason": (f"already running with min_conf={self._scan.min_conf}, "
                               f"hz={self._scan.hz} — requested min_conf={min_conf}, "
                               f"hz={hz} was NOT applied. stop_person_scan() first."),
                    "active_min_conf": self._scan.min_conf,
                    "active_hz": self._scan.hz,
                }
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
            return {"started": True, "scan_id": self._scan.scan_id,
                    "min_conf": min_conf, "hz": hz}

    def wait_for_person(self, timeout: float = 30.0) -> dict:
        with self._scan_lock:
            scan = self._scan
        if scan is None:
            return {"found": False, "conclusive": False, "reason": "no scan running"}
        return scan.wait(timeout)

    def get_scan_status(self) -> dict:
        with self._scan_lock:
            scan = self._scan
        if scan is None:
            return {"running": False, "found": False, "conclusive": False,
                    "reason": "no scan has been started"}
        return scan.status()

    def stop_person_scan(self) -> dict:
        with self._scan_lock:
            scan = self._scan
        if scan is None:
            return {"stopped": False, "reason": "no scan running"}
        scan.stop()
        return {"stopped": True, "scan_id": scan.scan_id, "final": scan.status()}
