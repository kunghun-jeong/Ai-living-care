# tools — 검증·시연 도구

> **역할** Gazebo·Nav2 없이 도는 검증·시연 도구. **비컴포넌트**
> **상태** 동작
> **읽을 절** 없음 — 이 디렉터리만으로 작업한다
> **정본** 구조 `SOT.md` · 실행 명령은 각 하위 `CLAUDE.md`

**컴포넌트가 아니다.** 비즈니스 로직을 두지 않는다 (P-3).

| 경로 | 용도 | 비고 |
|---|---|---|
| `limo-patrol-viz/` | Gazebo·Nav2·YOLO 없이 순찰 로직 검증 | **원본 보존 (D-14)** |

> **MCP 왕복 검증 클라이언트는 여기 없다.** 원본 보존 원칙에 따라
> `worker_ai_agent/limo-MCP/Scenarios/` 안에 그대로 있다.
> ```bash
> cd worker_ai_agent/limo-MCP && python3 Scenarios/send_goal.py 1.0 0.0
> ```
