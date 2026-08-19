"""a2a_server.py — Worker 측 표준 A2A HTTP 서버, 수신+저장만 한다 (실험 · 미승인).

`manager_ai_agent/a2a_client/dev_mock_worker_agent.py`(가짜 스텁)의 **실제 대체품**이다.
`manager_ai_agent/a2a_client/CLAUDE.md`가 이미 공개한 "팀원이 Worker A2A 서버를 만들 때
맞춰야 할 계약"(message/send · tasks/get · tasks/cancel, JSON-RPC 2.0)을 그대로 구현한다.

**스코프: 수신 즉시 `task_store`에 저장하고 끝난다. 실행(execute_policy, L2→L3 번역·
디바이스 디스패치)은 하지 않는다** — 그건 Worker AI Core의 몫이고 아직 미착수다(G-3,
작업 0-5·0-6). `message/send`가 바로 `completed`를 반환하는 이유: `a2a_client.py`의
`send_to_worker()`가 `state == "completed"`만 성공 신호로 보므로, 저장에 성공했는데
`failed`/`rejected`를 돌려주면 Manager 쪽에서 오탐이 난다. 실제로 무엇을 했는지(저장만,
미실행)는 `artifacts` 텍스트에 정직하게 남긴다.

rclpy·ultralytics를 import하지 않는다 — ROS2/WSL 없이 Windows에서 단독으로 뜬다.

실행: python a2a_server.py   (또는 python -m uvicorn a2a_server:app --port 9000)
"""

import os
import uuid
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

import task_store

app = FastAPI(title="limo-worker-a2a (실험 · 미승인 — 수신+저장만, 실행 안 함)")


@app.get("/.well-known/agent-card.json")
def agent_card():
    return {
        "name": "limo-worker-a2a",
        "description": "LIMO Worker 측 A2A 수신 서버 (실험·미승인) — 받은 명령을 저장만 한다. "
        "실행(execute_policy)은 아직 미착수(G-3).",
        "url": f"http://localhost:{os.environ.get('PORT', 9000)}",
        "version": "0.1.0-dev",
        "capabilities": {"streaming": False, "pushNotifications": False},
        "skills": [{"id": "skill.livingcare.store-only", "name": "receive and store A2A task (no execution)"}],
    }


def _handle_message_send(params: dict) -> dict:
    task_id = str(uuid.uuid4())
    message = params.get("message", {})
    task = {
        "id": task_id,
        "status": {"state": "completed"},
        "artifacts": [{"type": "text", "text": "stored (미실행 — execute_policy 미착수, G-3)"}],
        "received_message": message,
        "received_at": datetime.now(timezone.utc).isoformat(),
    }
    task_store.save_task(task)
    return task


def _handle_tasks_get(params: dict) -> dict:
    task_id = params.get("id")
    task = task_store.load_task(task_id)
    if task is None:
        raise KeyError(f"알 수 없는 task_id: {task_id}")
    return task


def _handle_tasks_cancel(params: dict) -> dict:
    task_id = params.get("id")
    task = task_store.load_task(task_id)
    if task is None:
        raise KeyError(f"알 수 없는 task_id: {task_id}")
    # 저장만 하고 실행은 안 하므로 취소할 진행 중인 작업이 없다 — 상태를 거짓으로
    # canceled로 덮어쓰지 않고 이미 완료된 그대로 반환한다.
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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 9000)))
