"""camera_stream — Perception Function wrapper (실험 · 미승인).

ROS2를 직접 import하지 않는다. 이미 구성된 `PerceptionModule`(limo-MCP/Worker_functions/Perceptions.py)
인스턴스를 인자로 받아 위임만 한다. JPEG 인코딩(PIL 의존)은 여기 두지 않는다 — 서버 경계
(mcp_server/worker_mcp_server.py)에서 한다. limo-MCP의 알려진 갭(G-1 프레임 pinning 부재,
G-2 pose 항상 None, 인코딩 검사 없음)은 이 wrapper가 고치지 않는다 — 그대로 물려받는다.
"""


def camera_stream(perception_module, frame_id: str | None = None) -> dict | None:
    """카메라의 최신 프레임을 반환한다. `{"frame_id","frame","stamp","pose"}` 또는 없으면 None."""
    return perception_module.get_latest_frame(frame_id)
