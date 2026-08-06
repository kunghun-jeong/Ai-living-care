# Session Key Handler

> **SOT**: `docs/spec/AI-Care_Unified_Architecture_Spec_v0.2.md`
> **상위**: `worker/core/` · **Phase**: 1 · **구현 상태**: 미착수

MAC의 `session_key_manager/`가 발급한 세션 키를 검증한다.

## 주의

**Action Function이 실제 액추에이션 직전에 한 번 더 검증한다** (slide 16·18 명시).
Core에서 통과했다고 AF의 검증을 생략하지 말 것 — 이중 검증이 설계 의도다 (표준화 항목 S-4).
