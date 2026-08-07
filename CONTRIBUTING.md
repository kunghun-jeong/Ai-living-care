# 협업 규약

> 처음이면 [`CLAUDE.md`](CLAUDE.md) 를 먼저 읽는다. 이 문서는 **브랜치·PR·리뷰**만 다룬다.

## 최초 1회

```bash
make hooks     # 커밋할 때 앵커 검사가 자동으로 돈다
               # make 가 없으면: git config core.hooksPath .githooks && chmod +x .githooks/*
make status    # 다른 협업자가 어디까지 갔는지
```

## 브랜치

`main` 에 직접 커밋하지 않는다. 자기 영역 이름으로 브랜치를 판다.

```
<영역>/<하려는 일>

kg/place-index            manager_ai_agent/knowledge_graph/
mac/intent-extraction     manager_ai_agent/manager_ai_core/
mcp/execute-policy        worker_ai_agent/mcp_server/
if04/task-binding         interfaces/if04_secure_a2a_channel/
contracts/l1-schema       contracts/intent_query/
paper/magazine-draft      논문·제안서
docs/harness-fix          문서·구조
```

**영역이 곧 브랜치 접두다.** 같은 영역에 둘이 붙으면 그때 나눈다 — 미리 규칙을 늘리지 않는다.

## PR

1. `make check` 가 통과하는지 먼저 본다 (앵커 + 구조).
2. PR 을 연다. [템플릿](.github/pull_request_template.md)이 자동으로 붙는다.
3. CI 가 돈다 — 앵커 · 구조 · 구문 · 순찰 커버리지 하한 90%.
4. **소유 경계에 걸리면 담당자 승인이 필수다** (아래).

작게 자른다. 한 PR 에 한 가지. 리뷰어가 30분 안에 다 읽을 수 있어야 한다.

## ⛔ 소유 경계 (D-17)

```
worker_ai_agent/limo-MCP/**      코드는 담당 연구원 소유
tools/limo-patrol-viz/**         코드는 담당 연구원 소유
```

**이 트리의 코드는 담당자만 고친다.** 다른 사람은 **읽고 [`docs/status.md`](docs/status.md) 에
결함을 ID 로 기록할 뿐 고치지 않는다.** 각 트리의 `CLAUDE.md`(우리가 만든 규범)만 예외다.

> 담당자가 아직 배정되지 않았고 한 사람이 한 프로젝트만 맡지도 않는다. 그래서 이 경계는
> **기계가 아니라 PR 설명과 리뷰로 지킨다.** 배정이 정해지면 `CODEOWNERS` 로 강제할 수 있다.

원본 보존의 범위는 **구조·파일명·경로**다. 담당자가 자기 코드의 **내용**을 고치는 것은
정상이며, 그때 [`docs/decisions.md`](docs/decisions.md) 에 한 줄 남긴다.

## 커밋 · 문서

- 커밋 메시지는 **무엇을 왜**. 되돌릴 사람이 읽는다고 생각하고 쓴다.
- 파일이나 디렉터리가 생기거나 이름이 바뀌면 **그 자리 `CLAUDE.md` 에 한 줄.** 훅이 확인한다.
- 상태가 바뀌면 그 `CLAUDE.md` 의 `> **상태**` 줄만 고친다 — `make status` 표는 따라온다.
- 결정을 내렸으면 [`docs/decisions.md`](docs/decisions.md) 맨 위에 한 줄.
- **사실만 쓴다.** 확인 못 한 것은 `TODO(확인 필요)`. 실행해 본 것만 「동작한다」고 쓴다.

## 읽는 양을 늘리지 않는다

- 매 세션 자동 로딩은 **루트 + `@` 3개뿐**이다. 실측치는 `make status` 맨 아래에 나온다 —
  **문서에 숫자를 적지 않는다.** 적으면 낡고, 낡은 숫자는 아무도 다시 재지 않는다.
- **`@` 를 루트 밖에서 쓰지 않는다.** `@` 는 **재귀 import** 라(최대 5홉) 하위 문서에 하나 붙이면
  그것이 부르는 것까지 전부 열린다. 실제로 그렇게 1,330줄까지 부풀었다. 총량 상한은 `anchor.py` 가 막는다.
- 설계 정본 962줄은 **통독하지 않는다.** 각 컴포넌트 `CLAUDE.md` 헤더의 `읽을 절`만 연다.
- 절 지목이 틀렸으면 **그 헤더를 고치는 것이 먼저다** — 통독으로 때우지 않는다.
- `docs/context/` · `docs/handoff/` 는 `REFERENCE-ONLY` 다. **인용하지 않는다.**

## 기존 클론을 갖고 있다면

경로가 크게 바뀌었다. [`MIGRATION.md`](MIGRATION.md) 에 옛 경로 ↔ 현재 경로 대응표가 있다.
**진행 중인 로컬 변경은 먼저 커밋하거나 stash 한 뒤 받는다.**
