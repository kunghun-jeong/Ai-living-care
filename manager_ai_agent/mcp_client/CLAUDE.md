# A2A Client (IF-4 Manager 측 종단점)

> **역할** IF-4 Manager 측 종단점 — 정해진 상대에게 보내고 받는 것만 한다
> **상태** Phase 0 · 미착수
> **읽을 절** spec **§6.4** · **§6.5**(Phase 0 시퀀스) — 그 외 절은 열지 않는다
> **정본** 구조 `SOT.md` · spec §6

MAC이 만든 L2 정책을 Worker에 전달하고 Task 상태·Artifact를 수신한다.
`worker_ai_agent/mcp_server/`의 대응 짝이며, 바인딩 정의는 `interfaces/if04_secure_a2a_channel/`에 있다.

## 흐름

```
MAMS 조회 (required-skill)          → Worker 후보
server/discover + agentcard://self  → Agent Card 확인
tools/call execute_policy(L2)       → {task_id, accepted}
tasks/get(task_id) 폴링              → COMPLETED + Artifact(Report + 증거 이미지)
```

## 주의

- **Worker 선택은 Client의 책임이 아니다.** MAMS의 `worker_selector/`가 정한다.
  Client는 정해진 상대에게 보내고 받는 것만 한다.
- Task 상태 전달 방식(폴링 vs `notifications/progress`)은 미정 (U-5). Phase 0은 폴링.
- 배치 근거: `docs/context/AI-Care_A2A_Core_Context(2).md` §4가 A2A Client를 **Manager AI Agent**에 배정 (D-9).
