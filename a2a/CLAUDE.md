# Secure A2A Channel (IF-4) — A2A-over-MCP 바인딩

> **SOT**: `docs/spec/AI-Care_Unified_Architecture_Spec_v0.2.md`
> **상위**: 저장소 루트 · **Phase**: 0 · **구현 상태**: 부분 — MCP 서버 동작, A2A 의미론 미구현

Manager AI Core ↔ Worker AI Core 간 **고수준 정책·Task 상태·Artifact** 전달 계층.
**A2A 의미론을 유지하면서 전송·직렬화는 MCP를 재사용한다.**

## 하위

| 하위 | 책임 | 상태 |
|---|---|---|
| `server/` | Worker 측 A2A/MCP 종단점 | **동작** (`MCP_server.py`) |
| `client/` | Manager 측 A2A 클라이언트 | 미착수 |
| `binding/` | A2A ↔ MCP 객체 매핑 정의 | 미착수 |

## 왜 이 바인딩인가 (★핵심 기여 — 표준화 항목 S-4)

업계 통념은 "MCP는 agent↔tool, A2A는 agent↔agent"로 역할이 갈린다는 것이다. 이 프로젝트가
A2A 의미론을 MCP 위에 얹는 근거:

1. **엣지 로컬성** — Manager와 Worker가 같은 엣지에 있는 배치가 다수. stdio 로컬 IPC가 지연·전력에서 유리
2. **툴체인 단일화** — Worker 내부 SF 호출(L4)이 이미 MCP tool이다. 외부까지 MCP로 통일하면
   Worker는 **서버 구현 하나**만 가진다
3. **2026-07-28 MCP 개정이 격차를 없앰** — A2A 핵심 객체 전부가 현행 MCP에 대응물을 갖게 됨

> **포지셔닝**: "A2A를 MCP로 대체한다"가 아니라 **"A2A 의미론의 MCP 전송 바인딩을 정의한다"**.
> A2A 명세가 이미 JSON-RPC / gRPC / HTTP+JSON 3종 바인딩을 인정하므로
> **제4의 바인딩을 제안하는 형태**가 표준화 트랙에서 가장 방어 가능하다.

## 주의

**A2A TaskState와 report.status를 혼동하지 말 것.** 전자는 전송 계층의 작업 수명주기,
후자는 임무의 의미론적 결과다. `COMPLETED` ≠ 정상.
