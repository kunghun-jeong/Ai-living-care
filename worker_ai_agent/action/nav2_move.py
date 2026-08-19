"""nav2_move — Action Function wrapper (실험 · 미승인).

ROS2를 직접 import하지 않는다. 이미 구성된 `ActionModule`(limo-MCP/Worker_functions/Actions.py)
인스턴스를 인자로 받아 위임만 한다 — ReasoningModule의 의존성 주입 패턴을 따른다
(worker_ai_agent/reasoning/CLAUDE.md 「이 저장소에서 가장 잘 분리된 설계」).

rclpy 초기화·노드 생성·sys.path 트릭은 합성 루트인 mcp_server/worker_mcp_server.py에만 있다.
"""


def nav2_move(action_module, x: float, y: float, frame: str = "map", yaw_deg: float | None = None) -> dict:
    """목표 좌표 하나로 이동을 시작한다. 비동기 — 즉시 반환, nav2_status로 폴링한다."""
    goal = {"x": x, "y": y, "frame": frame}
    if yaw_deg is not None:
        goal["yaw_deg"] = yaw_deg
    return action_module.send_goal_sequence([goal])


def nav2_move_waypoints(action_module, waypoints: list) -> dict:
    """웨이포인트 리스트([{x, y, frame?, yaw_deg?}, ...])를 순서대로 이동한다."""
    return action_module.send_goal_sequence(waypoints)


def nav2_cancel(action_module) -> dict:
    """진행 중인 목표/웨이포인트 시퀀스를 취소한다."""
    if action_module.is_running_sequence():
        return action_module.cancel_goal_sequence()
    return action_module.cancel_goal()


def nav2_status(action_module) -> dict:
    """현재 내비게이션 상태, 마지막 목표, 시퀀스 진행 상황을 반환한다."""
    return {
        "status": action_module.status,
        "last_goal": action_module.last_goal,
        "sequence_progress": action_module.sequence_progress,
        "sequence_result": action_module.sequence_result,
    }
