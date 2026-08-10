"""Knowledge Graph — Phase 0 JSON 룩업 구현 (D-6).

정본 스키마와 설계 배경은 CLAUDE.md 참조. 그래프DB로 교체될 때까지
entities.json 하나를 인메모리로 읽어 이름 -> 좌표를 해소한다.

entities.json에 없는 이름은 좌표를 지어내지 않고 UnknownLocationError를
던진다 (G-6, "사실만 기록한다. 확인 못 한 것은 TODO — 추측으로 채우지 않는다").
"""

import json
from pathlib import Path
from typing import Optional

_DEFAULT_ENTITIES_PATH = Path(__file__).parent / "entities.json"


class UnknownLocationError(LookupError):
    """entities.json에 없거나 pose가 아직 해소되지 않은 장소를 조회했을 때."""


class KnowledgeGraph:
    def __init__(self, entities_path: Optional[Path] = None):
        path = entities_path or _DEFAULT_ENTITIES_PATH
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        self._entities: dict = data.get("entities", {})

    def resolve_location(self, name: str) -> dict:
        """장소/디바이스 이름을 좌표({"x","y","frame","yaw_deg"})로 해소한다.

        `name`이 entities.json에 없거나 pose가 비어 있으면 UnknownLocationError.
        """
        entity = self._entities.get(name)
        if entity is None:
            raise UnknownLocationError(f"unknown location: {name!r}")

        pose = entity.get("pose")
        if pose is None:
            raise UnknownLocationError(f"{name!r} has no resolved pose yet (TODO 확인 필요)")

        return {
            "x": pose["x"],
            "y": pose["y"],
            "frame": pose.get("frame", "map"),
            "yaw_deg": pose.get("yaw", 0.0),
        }

    def list_locations(self) -> list:
        """pose가 실제로 해소된 space 엔티티 이름 목록."""
        return [
            name
            for name, entity in self._entities.items()
            if entity.get("type") == "space" and entity.get("pose") is not None
        ]
