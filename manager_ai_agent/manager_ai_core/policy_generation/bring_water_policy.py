"""시나리오 2의 자연어를 device-agnostic L2 정책으로 만든다.

현재는 L2 직렬화 형식(U-2)이 확정되지 않았으므로 내부 JSON 데모만 생성한다.
실제 물 운반 능력이 없는 상태를 숨기지 않기 위해 action은
``visit-source-and-return``이고 modality는 ``navigation-rehearsal``이다.
"""

from __future__ import annotations

from datetime import datetime
from typing import Callable
from uuid import uuid4
from zoneinfo import ZoneInfo


SUPPORTED_UTTERANCES = {
    "물갖다줘",
    "물가져다줘",
    "물을갖다줘",
    "물을가져다줘",
}


class UnsupportedUtterance(ValueError):
    """현재 규칙 기반 데모가 처리하지 못하는 자연어다."""


def _normalize(utterance: str) -> str:
    return "".join(utterance.strip().split()).rstrip(".!?")


def generate_high_level_policy(
    utterance: str,
    *,
    now: Callable[[], datetime] | None = None,
    id_factory: Callable[[], str] | None = None,
) -> dict:
    """지원하는 물 요청을 시나리오 2 L2 정책으로 변환한다.

    ID/시간 생성기를 주입할 수 있게 해 ROS2나 외부 서비스 없이 테스트한다.
    """

    if _normalize(utterance) not in SUPPORTED_UTTERANCES:
        raise UnsupportedUtterance(
            f"unsupported utterance: {utterance!r}; current scenario supports '물 갖다줘'"
        )

    now_fn = now or (lambda: datetime.now(ZoneInfo("Asia/Seoul")))
    make_id = id_factory or (lambda: uuid4().hex[:12])
    intent_id = f"int-{make_id()}"
    policy_id = f"pol-{make_id()}"

    return {
        "schema_version": "demo-0.1",
        "policy_id": policy_id,
        "intent_id": intent_id,
        "policy_name": "BringWaterRouteRehearsal",
        "issued_by": "manager-ai-core-scenario2",
        "issued_at": now_fn().isoformat(timespec="seconds"),
        "rule": {
            "rule_name": "visit-water-source-and-return",
            "event": {"event_type": "user_request", "trigger": "on-demand"},
            "condition": {
                "target_role": "water",
                "place": "kitchen",
                "modality": "navigation-rehearsal",
            },
            "action": {
                "action_type": "visit-source-and-return",
                "required_skills": ["waypoint-navigation"],
                "dispatch_mode": "single-worker",
            },
        },
        "context": {
            "original_utterance": utterance,
            "return_place": "request_origin",
            "deferred_skills": ["object-pickup", "object-dropoff"],
        },
        "assurance": {
            "deadline_sec": 240,
            "report_mode": "on-completion",
            "escalation_on": ["navigation_failed", "timeout"],
        },
    }
