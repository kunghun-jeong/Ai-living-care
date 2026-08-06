# Worker AI Management System (WAMS)

> **SOT**: `docs/spec/AI-Care_Unified_Architecture_Spec_v0.2.md`
> **상위**: `worker/` · **Phase**: 1 · **구현 상태**: 미착수

자기 등록(registration)과 SF 컨테이너 수명주기를 담당한다.

## 하위

- `agent_card/` — Worker의 접속 정보와 Skill을 외부에 공개

## 인터페이스

- IF-3 (Registration) ↔ WAC
- **IF-7 (AMS-Facing) ↔ MAMS** — 능력·자원·가용성 공시 (Phase 2)

## 주의

**IF-7이 이 프레임워크의 차별점이다.** A2A의 Agent Card는 정적 능력만 공시해 실시간 자원 상태를
반영하지 못한다. WAMS가 주기적으로 자원 상태를 MAMS에 갱신하는 경로가 그 공백을 메운다 (S-3).

SF를 Kubernetes 컨테이너로 관리하는 것은 UKC 논문이 제시한 방향이나, Phase 0에서는 단일 프로세스
내 모듈로 두고 컨테이너화는 Phase 2 이후로 미룬다.
