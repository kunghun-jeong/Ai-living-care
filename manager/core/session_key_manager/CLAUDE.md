# Session Key Manager

> **SOT**: `docs/spec/AI-Care_Unified_Architecture_Spec_v0.2.md`
> **상위**: `manager/core/` · **Phase**: 1 · **구현 상태**: 미착수

IF-4(Secure A2A Channel)의 세션 키를 발급·검증·갱신한다. Worker 측 대응은 `worker/core/session_key_handler/`.

## Phase별 범위

| Phase | 내용 |
|---|---|
| 0 | stdio 로컬 통신 — OS 프로세스 격리에 의존. 키 발급만 인메모리로 |
| 1+ | mTLS over Streamable HTTP, rekeying 주기 정책화 |
| 2+ | Skill 단위 권한, `AUTH_REQUIRED` TaskState 활용 |

## 주의

slide 16·18은 **Action Function이 실제 액추에이션 직전에 Session Key Check를 한 번 더** 수행하도록
명시한다. 즉 키 검증이 Core에만 있지 않은 **이중 검증 구조**다. 이 설계를 유지할 것 (표준화 항목 S-4의 근거).
