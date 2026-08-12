"""시나리오 2 L2 정책을 LIMO waypoint 정책으로 번역한다."""

from __future__ import annotations

from typing import Callable
from uuid import uuid4


PlaceResolver = Callable[[str], dict | None]


class PolicyTranslationError(ValueError):
    """L2 정책이 이 translator의 지원 범위를 벗어났다."""


def _require(mapping: dict, key: str, path: str):
    if key not in mapping:
        raise PolicyTranslationError(f"missing field: {path}.{key}")
    return mapping[key]


def _waypoint(place: str, location: dict) -> dict:
    try:
        waypoint = {
            "x": float(location["x"]),
            "y": float(location["y"]),
            "frame": str(location.get("frame", "map")),
            "location_label": place,
        }
    except (KeyError, TypeError, ValueError) as exc:
        raise PolicyTranslationError(f"invalid location for {place!r}: {location!r}") from exc


    if location.get("yaw_deg") is not None:
        waypoint["yaw_deg"] = float(location["yaw_deg"])
    return waypoint


def translate_to_limo_policy(
    high_level_policy: dict,
    *,
    resolve_place: PlaceResolver,
    task_id_factory: Callable[[], str] | None = None,
) -> dict:
    """``visit-source-and-return`` L2를 LIMO의 2-waypoint L3로 바꾼다.

    장소 좌표는 translator 안에 하드코딩하지 않고 resolver로 주입한다. 현재 G-6의
    정식 KG 연결이 없으므로 시나리오 실행기가 WORLD.md 기반 resolver를 제공한다.
    """

    rule = _require(high_level_policy, "rule", "policy")
    condition = _require(rule, "condition", "policy.rule")
    action = _require(rule, "action", "policy.rule")
    context = _require(high_level_policy, "context", "policy")
    assurance = _require(high_level_policy, "assurance", "policy")

    action_type = _require(action, "action_type", "policy.rule.action")
    if action_type != "visit-source-and-return":
        raise PolicyTranslationError(f"unsupported action_type: {action_type!r}")

    skills = _require(action, "required_skills", "policy.rule.action")
    if "waypoint-navigation" not in skills:
        raise PolicyTranslationError("required skill 'waypoint-navigation' is missing")

    modality = _require(condition, "modality", "policy.rule.condition")
    if modality != "navigation-rehearsal":
        raise PolicyTranslationError(f"unsupported modality: {modality!r}")

    source_place = _require(condition, "place", "policy.rule.condition")
    return_place = _require(context, "return_place", "policy.context")
    source = resolve_place(source_place)
    destination = resolve_place(return_place)
    if source is None:
        raise PolicyTranslationError(f"unknown place: {source_place!r}")
    if destination is None:
        raise PolicyTranslationError(f"unknown place: {return_place!r}")

    waypoints = [
        _waypoint(source_place, source),
        _waypoint(return_place, destination),
    ]
    make_task_id = task_id_factory or (lambda: uuid4().hex[:12])

    return {
        "schema_version": "demo-0.1",
        "policy_id": _require(high_level_policy, "policy_id", "policy"),
        "task_id": f"task-{make_task_id()}",
        "rule_name": _require(rule, "rule_name", "policy.rule"),
        "navigation": {"frame": "map", "waypoints": waypoints},
        "execution": {
            "tool": "navigate_waypoints",
            "arguments": {
                "waypoints": [
                    {key: value for key, value in point.items() if key != "location_label"}
                    for point in waypoints
                ]
            },
        },
        "deferred_operations": [
            {
                "after_waypoint": 0,
                "skill": "object-pickup",
                "enabled": False,
                "future_mcp_tool": "pick_object",
            },
            {
                "after_waypoint": 1,
                "skill": "object-dropoff",
                "enabled": False,
                "future_mcp_tool": "place_object",
            },
        ],
        "report": {
            "on": _require(assurance, "report_mode", "policy.assurance"),
            "timeout_sec": _require(assurance, "deadline_sec", "policy.assurance"),
        },
    }
