"""
dev_mock_worker_agent.py  —  로컬 테스트 전용 가짜 A2A 서버

*** 이건 실제 Worker AI Agent가 아니다. *** 팀원이 Worker AI Agent를 별도로 설계·구현할
예정이다. 이 파일은 그때까지 a2a_client.py(Manager 쪽 A2A 클라이언트)를 로컬에서 시험해
보기 위한 스텁일 뿐이다 — worker_ai_agent/** 는 손대지 않는다(소유 경계 D-17).

표준 A2A 서버 흉내: Agent Card + message/send + tasks/get(+cancel)만 최소로 구현.
message/send를 받으면 Task를 submitted로 만들고, 백그라운드에서 잠깐 뒤 working ->
completed로 전이시켜 tasks/get 폴링이 실제로 뭔가 관찰할 게 있게 한다.

실행: python dev_mock_worker_agent.py   (포트 9000, a2a_client.py 기본값과 일치)
"""

import threading
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI(title="dev_mock_worker_agent (가짜 · 로컬 테스트 전용)")

_tasks: dict[str, dict] = {}


@app.get("/.well-known/agent-card.json")
def agent_card():
    return {
        "name": "dev-mock-worker (가짜)",
        "description": "로컬 테스트용 스텁 — 실제 Worker AI Agent 아님",
        "url": "http://localhost:9000",
        "version": "0.0.0-dev",
        "capabilities": {"streaming": False, "pushNotifications": False},
        "skills": [{"id": "skill.livingcare.mock-intent", "name": "mock intent receiver"}],
    }


def _advance_task(task_id: str):
    """submitted -> working -> completed 를 짧게 흉내낸다 (진짜 로봇 작업 시늉)."""
    time.sleep(0.3)
    if task_id in _tasks:
        _tasks[task_id]["status"] = {"state": "working"}
    time.sleep(0.7)
    if task_id in _tasks:
        _tasks[task_id]["status"] = {"state": "completed"}
        _tasks[task_id]["artifacts"] = [{"type": "text", "text": "(mock) 처리 완료"}]


def _handle_message_send(params: dict) -> dict:
    task_id = str(uuid.uuid4())
    message = params.get("message", {})
    _tasks[task_id] = {
        "id": task_id,
        "status": {"state": "submitted"},
        "received_message": message,
    }
    threading.Thread(target=_advance_task, args=(task_id,), daemon=True).start()
    return _tasks[task_id]


def _handle_tasks_get(params: dict) -> dict:
    task_id = params.get("id")
    task = _tasks.get(task_id)
    if task is None:
        raise KeyError(f"알 수 없는 task_id: {task_id}")
    return task


def _handle_tasks_cancel(params: dict) -> dict:
    task_id = params.get("id")
    task = _tasks.get(task_id)
    if task is None:
        raise KeyError(f"알 수 없는 task_id: {task_id}")
    task["status"] = {"state": "canceled"}
    return task


_METHODS = {
    "message/send": _handle_message_send,
    "tasks/get": _handle_tasks_get,
    "tasks/cancel": _handle_tasks_cancel,
}


@app.post("/")
async def jsonrpc_endpoint(request: Request):
    body = await request.json()
    req_id = body.get("id")
    method = body.get("method")
    params = body.get("params", {})

    handler = _METHODS.get(method)
    if handler is None:
        return JSONResponse(
            {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": f"unknown method: {method}"}}
        )

    try:
        result = handler(params)
    except KeyError as e:
        return JSONResponse({"jsonrpc": "2.0", "id": req_id, "error": {"code": -32602, "message": str(e)}})

    return {"jsonrpc": "2.0", "id": req_id, "result": result}
