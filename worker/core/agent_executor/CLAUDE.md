# Agent Executor

> **SOT**: `docs/spec/AI-Care_Unified_Architecture_Spec_v0.2.md`
> **상위**: `worker/core/` · **Phase**: 0 · **구현 상태**: 미착수

A2A Message에서 정책을 꺼내 Worker AI Core로 넘기는 얇은 어댑터.
**A2A 통신 계층과 실행 로직을 잇는 지점**이다 — 이게 없으면 A2A 서버만 있고 기기는 움직이지 않는다.

```
A2A Message 수신 → Agent Executor → Policy Translator
                 → Perception / Reasoning / Action → Task Status / Artifact 반환
```

## 주의

정책을 **해석하지 않는다.** 꺼내서 넘기고, 수락/거부(`rejected`)만 판정한다.
능력 불일치·자원 부족으로 거부할 때 이유를 반드시 채운다 — MAMS의 재선택 입력이 된다.
