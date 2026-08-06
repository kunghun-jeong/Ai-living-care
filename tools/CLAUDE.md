# tools — 검증·시연 도구

> **구조 정본**: `SOT.md` · **설계 정본**: `docs/spec/AI-Care_Unified_Architecture_Spec_v0.2.md`
> **상위**: 저장소 루트 · **Phase**: — · **구현 상태**: —

**컴포넌트가 아니다.** 비즈니스 로직을 두지 않는다 (P-3).

| 경로 | 용도 | 비고 |
|---|---|---|
| `limo-patrol-viz/` | Gazebo·Nav2·YOLO 없이 순찰 로직 검증 | **원본 보존 (D-14)** |

> **MCP 왕복 검증 클라이언트는 여기 없다.** 원본 보존 원칙에 따라
> `worker_ai_agent/limo-MCP/Scenarios/` 안에 그대로 있다.
> ```bash
> cd worker_ai_agent/limo-MCP && python3 Scenarios/send_goal.py 1.0 0.0
> ```
