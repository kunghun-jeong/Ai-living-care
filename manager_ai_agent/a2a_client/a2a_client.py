"""
a2a_client.py  —  Manager 쪽 A2A(Agent2Agent) 클라이언트 (실험 · 미승인)

표준 A2A(Google -> Linux Foundation 기증 규격)를 따른다: HTTP(S) + JSON-RPC 2.0,
Agent Card, Task 생명주기. 이 저장소의 spec §6/interfaces/if04_secure_a2a_channel/가
정의한 "A2A-over-MCP(stdio)"와는 다른 전송이다 — 자세한 이유는 이 폴더의 CLAUDE.md와
docs/decisions/2026-08-18-a2a-standard-not-mcp.md 참조. mcp를 전혀 쓰지 않는다
(패키지 의존성 없음, requests만 씀).

흐름 (send_to_worker 하나로 캡슐화):
    GET  {WORKER_AGENT_URL}/.well-known/agent-card.json   (discover, 실패해도 계속 진행)
    POST {WORKER_AGENT_URL}/   method="message/send"       -> Task
    POST {WORKER_AGENT_URL}/   method="tasks/get" (폴링)    -> Task (완료 상태까지)

Worker 선택 로직은 넣지 않는다 (a2a_client/CLAUDE.md 규칙 — MAMS의 몫). 이 파일은
정해진 한 Worker(WORKER_AGENT_URL)에게 보내고 받는 것만 한다.
"""

import os
import time
import uuid

import requests

WORKER_AGENT_URL = os.environ.get("WORKER_AGENT_URL", "http://localhost:9000").rstrip("/")

_DISCOVER_TIMEOUT_SEC = 2
_RPC_TIMEOUT_SEC = 3
_POLL_INTERVAL_SEC = 0.5
_POLL_MAX_WAIT_SEC = 10

_TERMINAL_STATES = {"completed", "failed", "canceled", "rejected"}


class A2AError(Exception):
    pass


def _rpc_call(base_url: str, method: str, params: dict) -> dict:
    """JSON-RPC 2.0 요청 하나. 실패하면 A2AError."""
    req_id = str(uuid.uuid4())
    try:
        resp = requests.post(
            f"{base_url}/",
            json={"jsonrpc": "2.0", "id": req_id, "method": method, "params": params},
            timeout=_RPC_TIMEOUT_SEC,
        )
        resp.raise_for_status()
        body = resp.json()
    except requests.RequestException as e:
        raise A2AError(f"{method} 요청 실패: {e}") from e
    except ValueError as e:
        raise A2AError(f"{method} 응답이 JSON이 아님: {e}") from e

    if "error" in body:
        raise A2AError(f"{method} 서버 에러: {body['error']}")
    if body.get("id") != req_id:
        raise A2AError(f"{method} 응답 id 불일치 (보낸 id={req_id}, 받은 id={body.get('id')})")
    return body.get("result", {})


def discover(base_url: str = WORKER_AGENT_URL) -> dict | None:
    """Agent Card 조회. 실패해도 None만 반환하고 예외를 올리지 않는다 —
    Card가 없어도 message/send는 시도해볼 수 있다(discover는 선택 단계)."""
    try:
        resp = requests.get(f"{base_url}/.well-known/agent-card.json", timeout=_DISCOVER_TIMEOUT_SEC)
        resp.raise_for_status()
        return resp.json()
    except (requests.RequestException, ValueError):
        return None


def send_message(base_url: str, parts: list[dict]) -> dict:
    """message/send. 표준 A2A Message: role + parts. 우리는 판단·intent를
    하나의 DataPart로 실어 보낸다. 반환은 Task(비동기) 또는 Message(즉시 완료) —
    Task인지는 result 안에 status/id가 있는지로 구분한다."""
    message = {
        "role": "agent",
        "messageId": str(uuid.uuid4()),
        "parts": parts,
    }
    return _rpc_call(base_url, "message/send", {"message": message})


def get_task(base_url: str, task_id: str) -> dict:
    return _rpc_call(base_url, "tasks/get", {"id": task_id})


def cancel_task(base_url: str, task_id: str) -> dict:
    return _rpc_call(base_url, "tasks/cancel", {"id": task_id})


def send_to_worker(payload: dict) -> dict:
    """
    api_server.py가 부르는 진입점. 예전 send_to_worker.py와 같은 시그니처를 유지한다.

    반환: {"ok": bool, "detail": str, "task_id": str | None, "state": str | None}
    실패(연결 안 됨, 타임아웃, 프로토콜 에러)해도 예외를 올리지 않는다 — Worker가
    아직 없어도 Manager API가 죽으면 안 된다는 원칙은 그대로 유지한다.
    """
    base_url = WORKER_AGENT_URL
    card = discover(base_url)
    agent_name = card.get("name", base_url) if card else base_url

    try:
        result = send_message(base_url, parts=[{"type": "data", "data": payload}])
    except A2AError as e:
        return {"ok": False, "detail": f"{agent_name} 전달 실패: {e}", "task_id": None, "state": None}

    task_id = result.get("id")
    state = (result.get("status") or {}).get("state")

    if task_id is None:
        # Task가 아니라 즉시 완료된 Message로 응답한 경우
        return {"ok": True, "detail": f"{agent_name} 즉시 처리 완료", "task_id": None, "state": "completed"}

    deadline = time.monotonic() + _POLL_MAX_WAIT_SEC
    while state not in _TERMINAL_STATES and time.monotonic() < deadline:
        time.sleep(_POLL_INTERVAL_SEC)
        try:
            result = get_task(base_url, task_id)
        except A2AError as e:
            return {"ok": False, "detail": f"{agent_name} 상태 조회 실패: {e}", "task_id": task_id, "state": state}
        state = (result.get("status") or {}).get("state")

    ok = state == "completed"
    detail = f"{agent_name} task {task_id} -> {state or 'timeout'}"
    return {"ok": ok, "detail": detail, "task_id": task_id, "state": state}


if __name__ == "__main__":
    import sys
    import json

    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    demo_payload = {
        "axis": "WellBeing",
        "evaluation": {"should_escalate": True},
        "sequence": {"intent": "맵을 켜서 대상을 찾고 관찰해줘.", "device_id": "cap:limo_robot_agent"},
    }
    print(f"WORKER_AGENT_URL={WORKER_AGENT_URL}")
    print("[discover]", discover())
    print("[send_to_worker]", json.dumps(send_to_worker(demo_payload), ensure_ascii=False))
