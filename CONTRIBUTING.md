# 협업 규약

> 처음이면 [`CLAUDE.md`](CLAUDE.md) 를 먼저 읽는다. 이 문서는 **브랜치·PR·리뷰**만 다룬다.

## 규칙의 성격

**여기 규칙은 안내지 통제가 아니다.** 초기 단계 저장소에서 결함을 겪는 비용보다
**움직이지 못하는 비용이 크다.** 그래서 검사는 둘로 나뉜다.

| | 언제 막나 | 무엇 |
|---|---|---|
| **막는다** | 커밋 시점부터 | 조용히 틀리면 위험하고 **고치는 데 한 줄**이면 되는 것 — 앵커 · MCP tool 집합 · 안전 결함 인계 · 루트 분량 · **워크플로 YAML 유효성**(깨지면 CI 가 안 돈다) |
| **알린다** | **PR 에서만** (`--strict`) | 알면 되는 것 — spec 절 번호 · 유령 항목 · 자동 로딩 총량 · `.gitignore` 경로 · 문서 경로(라우팅 문서 포함) · 스키마·원고 미등재 · 자식 `CLAUDE.md` 부재 · **MCP tool 파라미터 불일치** · **ID 채번 경합** |
| **말만 한다** | 커밋·CI 에서 | 막지도 미루지도 않는다 — `상태` 줄 넛지 · **소유 경계 경고**(`OWNER=1` 로 끈다) · 보호 문서 순삭제(CI) · **결정의 「정본 반영」 대조**(CI) |

탐색 중에는 통과시키고 **병합 전에 잡는다.** 안 잡는 게 아니라 잡는 시점을 늦춘다.
`make check` 는 PR 기준(`--strict`)이라 미리 보고 싶을 때 쓴다.

**막는 규칙이 일을 방해한다고 느끼면 그건 규칙이 틀린 것이다** — 등급을 내리거나 없애자고
`docs/decisions/` 에 파일 하나 남기고 PR 을 열면 된다. 규칙을 지키느라 우회하는 것보다 낫다.

## 최초 1회

```bash
make hooks              # 커밋할 때 앵커 검사가 자동으로 돈다
                        # make 가 없으면: git config core.hooksPath .githooks && chmod +x .githooks/*
make status             # 다른 협업자가 어디까지 갔는지 — make 가 없으면 python anchor.py --status
git config user.email   # 비어 있거나 GitHub 계정 이메일이 아니면 아래를 읽는다
```

**`make status` 는 최초 1회가 아니라 세션마다 한 번이다** (`docs/harness.md` §0).
자동 로딩되는 네 문서는 남이 컴포넌트에서 일해도 변하지 않는다 — 갱신을 보는 창구는 여기뿐이다.

### 커밋 신원

**git 은 push 한 사람이 아니라 커밋에 박힌 author 이메일로 기여를 귀속한다.** 그 이메일이
자기 GitHub 계정에 인증돼 있지 않으면 커밋이 아무에게도 연결되지 않는다 — 실제로 이 저장소
초기 커밋 28개가 그렇게 쌓였다.

```bash
git config --global user.name  "<GitHub 사용자명>"
git config --global user.email "<GitHub 계정에 인증된 주소>"
```

실제 주소를 공개하고 싶지 않으면 GitHub → Settings → Emails 의 noreply 주소
(`12345678+사용자명@users.noreply.github.com`)를 쓴다 — 이것도 정상 귀속된다.
**이 저장소에만 다르게 쓰려면 `--global` 을 뺀다.**

## 브랜치 — 2단

```
main     최종본. 저장소 소유자가 master 를 검토한 뒤 PR 로 승격한다. 직접 푸시 금지
master   협업자가 일하는 곳. 여기로 커밋·푸시한다
```

**작은 변경은 `master` 에 바로 커밋한다.**

```bash
git switch master && git pull
# 작업
git add -A && git commit -m "무엇을 왜"
git push                          # upstream 은 자동으로 잡힌다 (push.autoSetupRemote)
```

`.githooks/pre-push` 가 **`main` 으로 가는 푸시를 거부한다** — 브랜치 이름이 아니라
**목적지**를 보므로 `git push origin HEAD:main` 같은 우회도 막힌다. 승격은 GitHub 에서
`master → main` PR 로 하며, 그건 서버 쪽이라 훅과 무관하게 동작한다.
정말 넘겨야 하면 `SKIP_MAIN_PUSH=1 git push origin main`.

### 승격 — 그리고 반드시 되돌린다

소유자가 `master` 를 검토한 뒤 `main` 으로 올린다. **올린 뒤 되돌리지 않으면 다음 사이클이
어긋난 상태에서 시작한다** — 실제로 두 번 그랬다.

```bash
# ① 올린다 — GitHub 에서 master → main PR 이 권장(CI 가 한 번 더 돈다). 터미널로 하려면:
git switch main && git pull
git merge master                  # 병합 커밋이 필요하다 — --ff-only 를 쓰지 말 것
git push origin main              # pre-push 가 승격으로 인식해 통과시킨다

# ② 내린다 — 이걸 빠뜨리면 두 브랜치가 계속 벌어진다
git switch master && git fetch origin
git merge --ff-only origin/main   # 여기서는 반드시 --ff-only
git push
```

**방향에 따라 `--ff-only` 가 반대다.** 올릴 때는 두 갈래를 합치는 것이라 병합 커밋이 필요하고,
내릴 때는 이미 포함된 것을 따라가는 것이라 병합 커밋이 생기면 안 된다. `--ff-only` 가 실패하면
**순서가 틀렸다는 신호다** — ①을 안 했거나 누가 `main` 에 직접 손댔다.

`.githooks/pre-push` 는 `main` 으로 가는 푸시 중 **`master` 를 거치지 않은 것만** 막는다.
승격(= `master` 를 병합한 커밋, 또는 `master` 자신)은 그냥 통과하므로 매번 탈출구를 쓸 일이 없다.

**리뷰가 필요하거나 같은 영역에 둘이 붙으면 브랜치를 판다. base 는 `master` 다.**

```
<영역>/<하려는 일>          (git switch -c 로 판다. base = master)

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
2. PR 을 연다 — **base 는 `master`.** [템플릿](.github/pull_request_template.md)이 자동으로 붙는다.
   (`master → main` 승격 PR 만 base 가 `main` 이고, 그건 소유자가 연다.)
3. CI 가 돈다 — 앵커 · 구조 · 구문 · 순찰 커버리지 하한 90%.
   `master` 직접 푸시에서도 돈다 (`check.yml` 트리거 `[master, main]`).
4. **소유 경계에 걸리면 담당자 승인이 필수다** (아래).

작게 자른다. 한 PR 에 한 가지. 리뷰어가 30분 안에 다 읽을 수 있어야 한다.

## ⛔ 소유 경계 (D-17)

```
worker_ai_agent/limo-MCP/**      코드는 담당 연구원 소유
tools/limo-patrol-viz/**         코드는 담당 연구원 소유
```

**이 트리의 코드는 담당자만 고친다.** 다른 사람은 **읽고 결함만 기록한다** — 안전 경로면
[`docs/safety/`](docs/safety/) 에 파일 하나, 그 외는 [`docs/status-defects.md`](docs/status-defects.md).
각 트리의 `CLAUDE.md`(우리가 만든 규범)만 예외다.

> 담당자가 아직 배정되지 않았고 한 사람이 한 프로젝트만 맡지도 않는다. `CODEOWNERS` 는
> 그래서 못 쓰고, `master` 는 직접 푸시라 리뷰도 못 막는다. **훅이 커밋 때 묻는다 —
> 막지는 않는다.** 담당자 본인이면 `OWNER=1` 로 안내를 끈다.

원본 보존의 범위는 **구조·파일명·경로**다. 담당자가 자기 코드의 **내용**을 고치는 것은
정상이며, 그때 [`docs/decisions/`](docs/decisions/) 에 파일 하나 남긴다.

## Windows 에서

이 저장소의 기본 개발 환경은 **Windows + OneDrive** 다. 문서에서 흔히 보는 `VAR=값 명령` 표기는
**bash 문법**이라 CMD·PowerShell 에서 동작하지 않는다. 훅 안내문은 세 환경을 병기한다.

| | 쓰는 법 |
|---|---|
| Git Bash | `SKIP_ANCHOR=1 git commit ...` |
| CMD | `set SKIP_ANCHOR=1` → 명령 → `set SKIP_ANCHOR=` (지우지 않으면 그 창에서 계속 남는다) |
| PowerShell | `$env:SKIP_ANCHOR=1` → 명령 → `Remove-Item Env:SKIP_ANCHOR` |

- `.gitattributes` 가 저장소를 **LF 로 정규화**한다. 체크아웃에서 CRLF 헛변경이 보이면 그 규칙이
  생기기 전에 받은 클론이다 — `git add --renormalize .` 로 한 번 맞춘다.
- **저장소가 OneDrive 동기 폴더 안에 있으면** 동기 중 `.git/*.lock` 이 남아
  `Another git process seems to be running` 이 뜰 수 있다. 그 파일을 지우면 풀린다.
  같은 폴더를 두 기기에서 동기하지 않는다.

## 커밋 · 문서

- 커밋 메시지는 **무엇을 왜**. 되돌릴 사람이 읽는다고 생각하고 쓴다.
- 파일이나 디렉터리가 생기거나 이름이 바뀌면 **그 자리 `CLAUDE.md` 에 한 줄.** 훅이 확인한다.
- 상태가 바뀌면 그 `CLAUDE.md` 의 `> **상태**` 줄만 고친다 — `make status` 표는 따라온다.
  **그 줄에 「지금 무엇으로」를 넣는다** (`LM encoder(BERT-base, LSTM 에서 전환)`). 논문·표준
  담당자는 그 한 줄만 보고 구현 절을 쓴다 — 기계가 만들 수 없는 유일한 조각이다.
- 결정을 내렸으면 [`docs/decisions/`](docs/decisions/) 에 **파일 하나** (`YYYY-MM-DD-슬러그.md`).
  표에 줄을 넣지 않는다 — 그게 분리된 작업끼리도 충돌시키던 자리다. 형식은 그 디렉터리 `CLAUDE.md`.
- **사실만 쓴다.** 확인 못 한 것은 `TODO(확인 필요)`. 실행해 본 것만 「동작한다」고 쓴다.

## 읽는 양을 늘리지 않는다

- 매 세션 자동 로딩은 **루트 + `@` 3개뿐**이다. 실측치는 `make status` 맨 아래에 나온다 —
  **문서에 숫자를 적지 않는다.** 적으면 낡고, 낡은 숫자는 아무도 다시 재지 않는다.
- **`@` 를 루트 밖에서 쓰지 않는다.** `@` 는 **재귀 import** 라(최대 5홉) 하위 문서에 하나 붙이면
  그것이 부르는 것까지 전부 열린다. 실제로 그렇게 1,330줄까지 부풀었다. 총량 상한은 `anchor.py` 가 막는다.
- 설계 정본은 **통독하지 않는다.** 각 컴포넌트 `CLAUDE.md` 헤더의 `읽을 절`만 연다.
- 절 지목이 틀렸으면 **그 헤더를 고치는 것이 먼저다** — 통독으로 때우지 않는다.
- `docs/context/` · `docs/handoff/` 는 `REFERENCE-ONLY` 다. **인용하지 않는다.**

## 기존 클론을 갖고 있다면

경로가 크게 바뀌었다. [`MIGRATION.md`](MIGRATION.md) 에 옛 경로 ↔ 현재 경로 대응표가 있다.
**진행 중인 로컬 변경은 먼저 커밋하거나 stash 한 뒤 받는다.**
