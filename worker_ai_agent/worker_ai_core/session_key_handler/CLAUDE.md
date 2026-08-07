# Session Key Handler

> **역할** Core 단계 키 검증. **AF 직전 재검증과 이중 구조** (`S-7`)
> **상태** Phase 1 · 미착수
> **읽을 절** spec **§9** — 그 외 절은 열지 않는다
> **정본** 구조 `SOT.md` · spec §9

MAC의 `session_key_manager/`가 발급한 세션 키를 검증한다.

## 주의

**Action Function이 실제 액추에이션 직전에 한 번 더 검증한다** (slide 16·18 명시).
Core에서 통과했다고 AF의 검증을 생략하지 말 것 — 이중 검증이 설계 의도다 (S-7).
