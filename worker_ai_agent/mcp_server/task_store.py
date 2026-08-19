"""a2a_server.py가 수신한 task를 파일로 영속화한다 (실험 · 미승인).

task 하나 = JSON 파일 하나(`data/{task_id}.json`). 원자적 쓰기(임시 파일 + os.replace)로
쓰다 만 파일이 남지 않게 하고, task_id별 락으로 같은 task에 대한 동시 read-modify-write를
막는다. uvicorn을 단일 워커(기본값)로 돌린다는 전제다 — 멀티 워커 프로세스 간 락 공유는
지원하지 않는다(이 파일이 그 상황을 다루지 않는다는 것을 알고 있을 것).

rclpy·ultralytics를 import하지 않는다 — a2a_server.py와 함께 Windows에서 ROS2 없이
단독으로 돌아가야 한다.
"""

import json
import os
import tempfile
import threading

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

_locks_guard = threading.Lock()
_locks: dict[str, threading.RLock] = {}


def _lock_for(task_id: str) -> threading.RLock:
    """RLock — `update_task`가 `load_task`/`save_task`를 같은 스레드에서 다시 부르므로
    일반 Lock을 쓰면 자기 자신과 데드락한다."""
    with _locks_guard:
        return _locks.setdefault(task_id, threading.RLock())


def _path(task_id: str) -> str:
    return os.path.join(DATA_DIR, f"{task_id}.json")


def save_task(task: dict) -> None:
    """`task['id']`를 파일명으로 원자적으로 저장한다."""
    task_id = task["id"]
    os.makedirs(DATA_DIR, exist_ok=True)
    with _lock_for(task_id):
        fd, tmp_path = tempfile.mkstemp(dir=DATA_DIR, prefix=f".{task_id}.", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(task, f, ensure_ascii=False, indent=2)
            os.replace(tmp_path, _path(task_id))
        except BaseException:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            raise


def load_task(task_id: str) -> dict | None:
    path = _path(task_id)
    if not os.path.isfile(path):
        return None
    with _lock_for(task_id):
        with open(path, encoding="utf-8") as f:
            return json.load(f)


def update_task(task_id: str, **fields) -> dict | None:
    """기존 task를 읽어 `fields`로 병합한 뒤 다시 저장한다. 없으면 None."""
    with _lock_for(task_id):
        task = load_task(task_id)
        if task is None:
            return None
        task.update(fields)
        save_task(task)
        return task
