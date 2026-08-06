# A2A Client (Manager 측)

> **SOT**: `docs/spec/AI-Care_Unified_Architecture_Spec_v0.2.md`
> **상위**: `a2a/` · **Phase**: 0 · **구현 상태**: 미착수

Manager AI Core가 Worker의 Agent Card를 조회하고, L2 정책을 `SendMessage`로 전달하며,
Task 상태와 Artifact를 수신한다.

## 흐름

```
MAMS 조회 (required-skill)      → Worker 후보
server/discover + agentcard://self → Agent Card 확인
tools/call execute_policy(L2)   → {task_id, accepted}
tasks/get(task_id) 폴링          → COMPLETED + Artifact(Report + 증거 이미지)
```

## 주의

**Worker 선택은 Client의 책임이 아니다.** MAMS의 `worker_selector/`가 정한다.
Client는 정해진 상대에게 보내고 받는 것만 한다.

Task 상태 전달 방식(폴링 vs `notifications/progress` 스트리밍)은 미정 (U-5).
Phase 0은 폴링으로 간다.
