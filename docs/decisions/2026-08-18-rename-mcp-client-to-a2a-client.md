# 2026-08-18 · `manager_ai_agent/mcp_client/`를 `a2a_client/`로 개명한다

> **정본 반영** `SOT.md`(§2 트리·§2.1·§2.2 표·§6 D-9/D-20) · `sot_audit.py`(AR-1·a2a/client 매핑) ·
> `docs/spec/AI-Care_Unified_Architecture_Spec_v0.2.md`(D-9 표) ·
> `interfaces/if04_secure_a2a_channel/CLAUDE.md` · `docs/architecture.md` ·
> `docs/harness/manager-ai.md` · `docs/harness/mcp.md` ·
> `manager_ai_agent/CLAUDE.md` · `manager_ai_agent/manager_ai_core/CLAUDE.md` ·
> `manager_ai_agent/manager_ai_core/api_server.py` · `manager_ai_agent/a2a_client/CLAUDE.md` ·
> `manager_ai_agent/a2a_client/a2a_client.py` · `requirements.txt`(주석)

## 왜

`docs/decisions/2026-08-18-a2a-standard-not-mcp.md`에서 이 폴더의 실험 코드를 MCP가 아니라
**표준 A2A(HTTP+JSON-RPC 2.0)**로 만들기로 했다. 그 결과 `mcp_client`라는 폴더 이름이
내용물과 어긋났다 — 팀장 지시로 실제 디렉터리 이름도 `a2a_client/`로 바꾼다.

**표기**: `A2A_client`가 아니라 `a2a_client`로 했다 — `SOT.md` N-2("표기는 snake_case,
공백·하이픈·대문자를 쓰지 않는다")를 그대로 따른 것이며 다른 모든 컴포넌트 디렉터리
(`manager_ai_core`, `kg_mapping` 등)와 표기를 맞췄다.

## 무엇을 바꿨나

`git mv manager_ai_agent/mcp_client manager_ai_agent/a2a_client` 후, 그 경로를 참조하던
문서·코드 16곳 전부에서 경로를 갱신했다 — spec §0.2의 D-9 표, `SOT.md`의 트리·컴포넌트
표·A2A 종단점 배치표·결정표(D-9 갱신 + D-20 신설), `sot_audit.py`의 디렉터리 존재 검사와
`a2a/client` 매핑, `interfaces/if04_secure_a2a_channel/CLAUDE.md`, `docs/architecture.md`
다이어그램·표, `docs/harness/manager-ai.md`·`docs/harness/mcp.md`, 그리고 이 폴더 자신을
가리키던 모든 상대경로(`api_server.py`의 `sys.path`, 각 `CLAUDE.md`의 상호 참조).

`MIGRATION.md`는 **건드리지 않았다** — 그 문서는 특정 과거 커밋(`27b0f30`) 기준의 역사적
스냅샷이라, 지금 이름을 바꿨다고 그 시점 서술을 고치면 오히려 부정확해진다.
`docs/decisions/2026-08-18-a2a-standard-not-mcp.md`·`2026-08-18-frontend-http-gateway.md`
같은 기존 결정 파일 본문의 `mcp_client` 언급도 그대로 뒀다 — 결정 로그는 그 시점에 무엇을
했는지의 기록이고(`docs/decisions/CLAUDE.md` 관례), 이 파일이 그 뒤를 잇는 새 결정으로
남는다.

## 여전히 안 바뀐 것

- `interfaces/if04_secure_a2a_channel/`이 정의하는 **정본 설계(MCP 기반 A2A)는 미착수 그대로**다.
  이름을 바꿨다고 MCP 기반 설계를 채택한 게 아니고, 반대로 표준 A2A를 채택한 것도 정본
  결정이 아니다 — 둘 다 여전히 **상급자 승인 대기**.
- `SOT.md`는 실험 브랜치에서 고쳤지만, 이 문서 전체가 아직 **상급자 미보고** 상태라는 점은
  변하지 않는다. 승인 전에는 `main`에 머지하지 않는다.

## 검증

`python3 anchor.py`·`python3 sot_audit.py` 재실행, 104/104 통과 확인. `git mv`로 옮겼으므로
`git log --follow`가 `CLAUDE.md`(원래 저장소에 있던 파일)의 이력을 잇는 것도 확인.
