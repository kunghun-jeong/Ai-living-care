"""yolo_reasoning — Reasoning Function wrapper (실험 · 미승인).

ROS2·ultralytics를 직접 import하지 않는다. 이미 구성된 `ReasoningModule`
(limo-MCP/Worker_functions/Reasonings.py, detect_fn=yolo_detect로 주입됨) 인스턴스를
인자로 받아 위임만 한다. person-scan 5종(G-3, 미노출) 노출은 이번 스코프 밖 — 손대지 않는다.
"""


def yolo_reasoning(reasoning_module, frame, min_conf: float = 0.4) -> dict:
    """주어진 프레임에서 YOLO로 물체를 검출해 min_conf 이상만 반환한다."""
    out = reasoning_module.detect_objects(frame)
    detections = out.get("detections")
    if detections is None:
        return {"detections": [], "reason": out.get("reason", "detection failed")}
    return {"detections": [d for d in detections if d.get("conf", 0.0) >= min_conf]}
