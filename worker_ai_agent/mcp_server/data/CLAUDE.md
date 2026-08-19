# mcp_server / data

> **역할** `a2a_server.py`가 수신한 task를 파일로 보관하는 런타임 전용 저장소 (실험 · 미승인)
> **상태** Phase 0 · 실험 · 미승인 — 상위 `../CLAUDE.md` 참조
> **정본 아님** — `SOT.md` §2 구조 밖. 근거는 `../CLAUDE.md`

| 파일 | 역할 |
|---|---|
| `.gitkeep` | 이 디렉터리를 git에 존재시키기 위한 빈 파일 |

`*.json`(task_id별 저장 파일)은 런타임에 `task_store.py`가 쓴다 — **커밋하지 않는다**
(`.gitignore` 등재). 이 디렉터리에 코드는 없다.
