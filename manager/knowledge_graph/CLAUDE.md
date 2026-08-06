# Knowledge Graph (KG)

> **SOT**: `docs/spec/AI-Care_Unified_Architecture_Spec_v0.2.md`
> **상위**: `manager/` · **Phase**: 0 · **구현 상태**: 미착수 — G-6

사용자·공간·디바이스의 **관계와 능력**을 보유한다 — 누가 무엇을 할 수 있는가.
`intent_audit_db/`(감사 이력)와는 별개다 (spec §2.3).

## Phase 0: JSON 룩업으로 간소 구현 (D-6)

인터페이스 계약을 아래로 **고정**하여 후일 그래프DB로 무중단 교체한다.

```
resolve(phrase: str, context: dict) -> list[Binding]
```

`kg.json` 형태:

```json
{
  "entities": {
    "grandma":     {"type": "person", "role": "elder", "usual_place": "living_room"},
    "living_room": {"type": "space", "map_frame": "map", "pose": {"x":…, "y":…, "yaw":…}},
    "LIMO_1":      {"type": "device", "skills": ["navigate","person-scan","state-check"],
                    "sensors": ["camera","lidar"], "agent_uri": "stdio://limo_1"}
  },
  "phrase_bindings": { "grandma": [...], "check": [...], "is okay": [...] }
}
```

## G-6 — 이 컴포넌트가 채워야 할 공백

현재 코드에 `list_locations` / `locations.json`이 **없다.** `plan_and_navigate`는 좌표만 받는다.
따라서 L2 정책의 `<location-label>living_room`을 좌표로 해소할 경로가 없다.

**좌표 ↔ 방 이름 매핑을 만드는 것이 곧 G-6 해소이자 `entities.<space>` 채우기다** (작업 0-10).

## 주의 (중요)

- 저장소에서 좌표에 **의미 있는 이름이 붙은 것은 두 개뿐**이다:
  `(8.10, 1.71)`="식탁 구역", `(-7.77, 0.56)`="좌상단 방" (`tools/patrol_viz/`).
  **나머지 5개 순찰 좌표에는 방 이름이 부여된 바 없다.** 임의로 붙이지 말 것.
- docx의 `locations.json`(`living_room = (1.2, 0.4)`)은 **별개 출처이며 small_house 좌표계와 무관하다.**
  두 좌표계를 섞지 말 것.
- `phrase_bindings`는 데모용 지름길이다. Phase 1에서 `entities` 그래프 순회 + 임베딩 유사도로 대체하고,
  이 표는 회귀 테스트의 정답셋으로 전환한다.
