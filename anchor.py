#!/usr/bin/env python3
"""앵커 검사 — 문서가 가리키는 것이 실재하는가.

    python3 anchor.py            평시 — 막는 것만 막고 나머지는 알려만 준다
    python3 anchor.py --strict   PR · CI — 알림도 전부 막는다
    python3 anchor.py --status   전 영역 현황 + 자동 로딩 실측 (파일에 쓰지 않는다)
    python3 anchor.py --spec     설계 정본 절 색인 (파일에 쓰지 않는다)

**규칙은 안내지 통제가 아니다.** 초기 단계 저장소에서는 결함을 겪는 비용보다
움직이지 못하는 비용이 크다. 그래서 검사를 둘로 나눈다:

  **막는다**   조용히 틀리면 위험하고, 고치는 데 한 줄이면 되는 것
  **알린다**   알면 되는 것. 평시 커밋은 통과하고 **PR 에서 `--strict` 로 잡힌다**

탐색 중에는 통과시키고 병합 전에 잡는다. 안 잡는 게 아니라 **잡는 시점을 늦춘다.**

규칙은 하나다: **파일·디렉터리가 생기거나 이름이 바뀌면 그 자리 `CLAUDE.md` 에 한 줄 넣는다.**
감사 도구가 아니다. 점수를 세지 않고 빠진 것만 알려준다.

검사 아홉 — 전부 **양방향**이거나 실재를 본다:
  A1  `CLAUDE.md` 가 자기 디렉터리의 하위·코드 파일을 가리키는가        [막는다]
  A2  MCP tool 집합이 `api-spec.md` · `mcp_server/CLAUDE.md` 에 있는가   [막는다]
  A5  안전 결함이 `status.md` 표 ↔ 컴포넌트 `상태` 줄 양쪽에 있는가     [막는다]
  A4  루트가 50줄 이내인가 (매 세션 자동 로딩된다)                      [막는다]
  --
  A1' 표에 적힌 자식이 실재하는가 (유령 항목)                           [알린다]
  A3  헤더의 `읽을 절` 이 spec 에 실재하는 절을 가리키는가              [알린다]
  A4' `@` 재귀 총합이 상한 이내인가                                     [알린다]
  A6  `.gitignore` 의 경로 패턴이 실재하는 디렉터리를 가리키는가        [알린다]
  A7  문서가 적은 파일 경로가 실재하는가 (축약은 유일 해석만)           [알린다]
  A8  데이터·스키마 파일(`.json`·`.xml`)이 등재됐는가                   [알린다]
  A9  등재된 자식 디렉터리에 `CLAUDE.md` 가 있는가                      [알린다]

A7 은 `CLAUDE.md` 뿐 아니라 **라우팅·규약 문서**(`ROUTING_DOCS`)도 본다. 실측으로 확인한
비대칭이었다 — `doc-map.md` 가 가리키는 문서를 지워도 평시·PR 모두 무반응이었다.
**가장 많이 읽히는 문서가 가장 안 지켜지고 있었다.**

A8·A9 는 「존재」 앵커의 사각을 메운다. `CODE` 가 `.py`·`.sh` 뿐이라 다음 산출물
(`contracts/` 스키마 · `docs/papers/` 원고)이 통째로 무반응이었고, 자기 `CLAUDE.md` 가 없는
디렉터리는 `make status` 에 영영 나오지 않아 **협업자에게 존재하지 않았다.**
둘 다 「알린다」다 — 탐색 중에 새 파일을 두는 것을 막을 이유는 없다.

「알린다」 쪽은 **재구조화·개명·정본 개정** 같은 드문 사건에만 걸린다. spec 절 하나를
옮기면 헤더 14개가 함께 걸리는데, 정본을 활발히 고치는 시기에 그것으로 커밋을 막으면
**개정을 벌하는 셈이 된다.**

한 방향만 보는 검사는 지우는 쪽을 못 막는다. A1 과 A5 는 그래서 역방향을 함께 본다.
"""
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SKIP = {".git", "_to_delete", "_bundle", "node_modules", "__pycache__", "slides", "maps"}
CODE = (".py", ".sh")            # 미등재면 막는다 — 실행되는 것이라 조용히 틀리면 위험하다
DATA = (".json", ".xml")         # 미등재면 알린다 — A8. 계약이지 실행물은 아니다
# 원고가 사는 곳에서는 `.md` 도 산출물이다. `docs/` 전역에 걸면 시끄럽기만 하다 —
# 문서를 하나 더 쓰는 것은 늘 일어나는 일이고, 원고가 늘어나는 것은 그렇지 않다.
DATA_MD = ("docs/papers", "docs/standards")
# 원본 보존 대상 (D-14 · D-17) — 우리 파일이 아니다. 최상위 CLAUDE.md 하나로만 앵커한다.
PRESERVED = ("worker_ai_agent/limo-MCP", "tools/limo-patrol-viz")

SPEC = "docs/spec/AI-Care_Unified_Architecture_Spec_v0.2.md"
STATUS = "docs/status.md"
SAFETY_MARK = "## 안전 — 담당자 통지"
SAFETY_DIR = "docs/safety"               # 미해소 안전 결함 — 하나가 파일 하나 (D-18)
DEFECTS = "docs/status-defects.md"
# A10 정의처. `D-*` 는 뺀다 — spec §0.2 와 `SOT.md` §6 양쪽 갱신이 규범이다 (doc-map §3).
ID_DEFS = {"F": (STATUS, DEFECTS), "G": (SPEC,), "U": (SPEC,), "S": (SPEC,)}
TOOL_SRC = "worker_ai_agent/limo-MCP/MCP_server/MCP_server.py"
TOOL_DOCS = ("docs/api-spec.md", "worker_ai_agent/mcp_server/CLAUDE.md")
IGNORE = ".gitignore"
DECISIONS = "docs/decisions.md"          # 이력 표 (동결)
DECISIONS_DIR = "docs/decisions"         # 신규 — 결정 하나가 파일 하나
ROOT_MAX_LINES = 50
AUTOLOAD_MAX_LINES = 420
# 6인이 각자 상위 dir 을 전담하면 한 라운드에 6커밋 + 병합 5개가 쌓인다. 창을 8로 두고
# 병합을 세면 **절반이 창 밖으로 밀린다** (실측: 6인 중 3인만 보였다). 병합 커밋은
# 「무엇이 바뀌었나」를 말하지 않으므로 세지 않고, 창은 한 라운드가 다 들어가게 잡는다.
RECENT_COMMITS = 10
RECENT_DECISIONS = 6

# A7 이 함께 보는 라우팅·규약 문서. 루트 4종 + `docs/` 최상위 + 하네스 노트.
# **목록을 박지 않고 훑는다** — 새 하네스 노트를 추가한 사람이 여기도 고쳐야 한다면
# 이 목록 자체가 낡는다. `docs/spec/` · `context/` · `handoff/` 는 뺀다:
# 앞은 정본이라 경로 표기가 예시투성이고, 뒤 둘은 `REFERENCE-ONLY` 라 낡는 것이 정상이다.
ROUTING_ROOT = ("README.md", "CONTRIBUTING.md", "SOT.md", "MIGRATION.md")
ROUTING_DIRS = ("docs", "docs/harness")

missing = []      # 막는다
advisory = []     # 알린다 (--strict 에서만 막는다)


def rel(p):
    return os.path.relpath(p, ROOT).replace(os.sep, "/")


def read(p):
    return open(os.path.join(ROOT, p), encoding="utf-8").read()


def has(p):
    return os.path.isfile(os.path.join(ROOT, p))


def walk_docs():
    """`CLAUDE.md` 를 가진 디렉터리. 보존 대상 내부는 들어가지 않는다."""
    for dp, dns, fns in os.walk(ROOT):
        dns[:] = [x for x in dns if x not in SKIP and not x.startswith(".")]
        r = rel(dp)
        if any(r.startswith(x + "/") for x in PRESERVED):
            dns[:] = []
            continue
        if "CLAUDE.md" in fns:
            yield r, dns, fns


def doc_of(r):
    return "CLAUDE.md" if r == "." else f"{r}/CLAUDE.md"


def state_line(doc):
    m = re.search(r"^> \*\*상태\*\* (.*)$", read(doc), re.M)
    return m.group(1) if m else None


# ── A1 · CLAUDE.md ↔ 실제 디렉터리 (양방향) ──────────────────────────────────
def named_in(txt):
    """**백틱 안에 적힌 것만** 등재로 친다. 본문 부분문자열은 치지 않는다 —
    `manager_ai_agent/spec/` 를 만들어도 부모 문서에 "spec" 이 흔해서 통과하던 구멍이었다.

    백틱 한 칸을 공백으로 쪼갠 뒤 각 낱말의 **경로 접두**를 넣는다:
    `python3 anchor.py` → `anchor.py` · `Worker_functions/Perceptions.py` → `Worker_functions`.
    `docs/spec/x.md` 는 `docs` · `docs/spec` 만 넣는다 — 맨 `spec` 은 넣지 않는다.
    """
    out = set()
    for span in re.findall(r"`([^`\n]+)`", txt):
        for word in span.split():
            word = word.strip(",.;:()[]").rstrip("/")
            parts = word.split("/")
            for i in range(1, len(parts) + 1):
                out.add("/".join(parts[:i]))
    return out


def check_anchors():
    """A1 [막는다] 디렉터리 · 실행 파일 · A8 [알린다] 데이터·스키마 파일.

    등급을 나누는 기준은 「고치는 데 한 줄이면 되는가」가 아니라 **조용히 틀리면 위험한가**다.
    실행되는 것(`.py`·`.sh`)이 문서에 없으면 다음 사람이 그것이 도는 줄 모른다. 스키마는
    아직 아무도 실행하지 않으므로 PR 까지 미뤄도 늦지 않다.
    """
    for r, dns, fns in walk_docs():
        doc = doc_of(r)
        named = named_in(read(doc))
        for e in sorted(dns) + sorted(f for f in fns if f.endswith(CODE)):
            if e not in named:
                kind = "디렉터리" if e in dns else "파일"
                missing.append((doc, f"{kind} `{e}` 미등재"))
        data = DATA + ((".md",) if r in DATA_MD else ())
        for e in sorted(f for f in fns if f.endswith(data) and f != "CLAUDE.md"):
            if e not in named:
                advisory.append((doc, f"산출물 `{e}` 미등재 — 스키마·원고는 그 자리가 정본이다"))


# ── A9 · 등재된 자식 디렉터리에 `CLAUDE.md` 가 있는가 ─────────────────────────
def check_child_docs():
    """`CLAUDE.md` 가 없는 디렉터리는 `make status` 에 나오지 않는다.

    A1 은 부모가 자식을 **가리키는지**만 본다. 자식이 자기 문서를 갖는지는 아무도 안 봤고,
    실측 결과 그런 디렉터리는 감사 전항목 초록인 채로 **협업자에게 존재하지 않았다.**
    `SOT.md` SP-5 가 규범으로 요구하던 것을 여기서 처음 관측한다 (AR-4 는 하드코딩 목록만 본다).

    보존 대상(D-14 · D-17)은 예외다 — 남의 트리 안에 우리 문서를 심으라는 요구가 된다.
    """
    for r, dns, _ in walk_docs():
        if r in PRESERVED:
            continue
        for d in sorted(dns):
            child = d if r == "." else f"{r}/{d}"
            if any(child == x or child.startswith(x + "/") for x in PRESERVED):
                continue
            if not has(f"{child}/CLAUDE.md"):
                advisory.append((f"{child}/", "`CLAUDE.md` 부재 — `make status` 에 나오지 않는다 (SP-5)"))


def check_ghosts():
    """**표에 적힌 자식이 실재하는가.** 개명하면 새 이름은 A1 이 잡지만 옛 이름은 표에 남는다.

    본문 전체가 아니라 **표 행만** 본다. 본문에는 예시·비교·금지 경로가 섞여 있어
    전체를 보면 오탐이 16건 났다. 구성 표에서 자식이 사라지는 것을 잡는 게 원래 목적이다.
    """
    for r, _, _ in walk_docs():
        doc = doc_of(r)
        base = ROOT if r == "." else os.path.join(ROOT, r)
        for i, ln in enumerate(read(doc).splitlines(), 1):
            if not ln.lstrip().startswith("|"):
                continue
            for name in re.findall(r"`([\w.\-]+)/`", ln):
                if not os.path.isdir(os.path.join(base, name)):
                    advisory.append((f"{doc}:{i}", f"표의 `{name}/` 이 실재하지 않음 — 유령 항목"))


# ── A2 · MCP tool 집합 ───────────────────────────────────────────────────────
def norm_params(s):
    """`x: float, y: float, frame: str = "map"` → `x:float,y:float,frame:str="map"`.

    비교하는 것은 **파라미터 목록뿐**이다. 반환 타입은 뺀다 — `get_camera_snapshot` 처럼
    코드에 애노테이션이 없는데 문서가 실제 거동(`list | dict`)을 적어 두는 편이 정확한
    경우가 있고, 그건 갈라짐이 아니라 문서가 더 많이 아는 것이다.
    """
    return re.sub(r"\s+", "", s)


def check_tools():
    """A2 — MCP tool 은 **코드가 정본**이다 (doc-map §3).

    이름 집합만 보던 것을 **시그니처까지** 넓혔다. 파라미터를 하나 더하거나 기본값을
    바꿔도 `api-spec.md` 는 조용히 낡았는데, 그 문서가 MCP 작업자의 유일한 계약서다.
    이름 누락은 **막고**(그 tool 이 있는 줄도 모르게 된다) 시그니처 불일치는 **알린다**
    (탐색 중에 인자를 바꾸는 것은 정상이고, 병합 전에 맞추면 늦지 않다).
    """
    if not has(TOOL_SRC):
        return
    sigs = re.findall(r"@mcp\.tool\(\)\s*\n\s*(?:async\s+)?def\s+(\w+)\(([^)]*)\)", read(TOOL_SRC))
    for doc in TOOL_DOCS:
        if not has(doc):
            missing.append((doc, "파일 없음 — MCP tool 앵커처"))
            continue
        txt = read(doc)
        for name, params in sigs:
            if name not in txt:
                missing.append((doc, f"MCP tool `{name}` 미등재"))
                continue
            m = re.search(r"`" + re.escape(name) + r"\(([^)]*)\)", txt)
            if not m:                       # 이름만 산문에 있고 시그니처 표기가 없는 문서
                continue
            if norm_params(m.group(1)) != norm_params(params):
                advisory.append((doc, f"`{name}` 시그니처 불일치 — 코드 `({params})` "
                                      f"· 문서 `({m.group(1)})`"))


# ── A3 · 「읽을 절」 이 실재하는가 ────────────────────────────────────────────
def check_spec_refs():
    """컴포넌트 헤더 전부가 `§4.1` 같은 절 번호에 의존한다. spec 을 개정하거나 절을 재배치하면
    전부 조용히 어긋난다 — 경로와 달리 절 번호는 깨져도 눈에 안 띈다."""
    if not has(SPEC):
        advisory.append((SPEC, "설계 정본 부재 — `읽을 절` 검사 불가"))
        return
    have = set(re.findall(r"^#{2,3} (\d+(?:\.\d+)?)\.? ", read(SPEC), re.M))
    for r, _, _ in walk_docs():
        doc = doc_of(r)
        m = re.search(r"^> \*\*읽을 절\*\* (.*)$", read(doc), re.M)
        if not m:
            continue
        for sec in re.findall(r"§(\d+(?:\.\d+)?)", m.group(1)):
            if sec not in have:
                advisory.append((doc, f"spec 에 없는 절 `§{sec}` 지목"))


# ── A4 · 자동 로딩 분량 ──────────────────────────────────────────────────────
def autoload(start="CLAUDE.md", seen=None):
    """`@` 는 **재귀 import** 다 (최대 5홉). 루트가 부른 문서가 부른 문서까지 전부 열린다.
    2026-08-06 에 이것을 몰라 루트 밖 `@` 25건이 자동 로딩을 1,330줄까지 부풀렸다."""
    seen = [] if seen is None else seen
    if start in seen or len(seen) > 40:
        return seen
    seen.append(start)
    for t in re.findall(r"@([\w./\-]+\.md)", read(start)):
        if has(t):
            autoload(t, seen)
    return seen


def autoload_total():
    files = autoload()
    return files, sum(len(read(p).splitlines()) for p in files)


def check_root_size():
    n = len(read("CLAUDE.md").splitlines())
    if n > ROOT_MAX_LINES:
        missing.append(("CLAUDE.md",
                        f"{n}줄 — 루트는 {ROOT_MAX_LINES}줄 이내. **매 세션 자동 로딩된다**"))
    files, total = autoload_total()
    if total > AUTOLOAD_MAX_LINES:
        advisory.append(("CLAUDE.md",
                        f"자동 로딩 {total}줄 (상한 {AUTOLOAD_MAX_LINES}) — "
                        f"`@` 는 재귀다. 지금 열리는 것: {' · '.join(files)}"))


# ── A5 · 안전 결함 인계 (D-18) ───────────────────────────────────────────────
def safety_rows():
    """미해소 안전 결함 — **하나가 파일 하나.** `(ID, 귀속, 제목, 경로)`

    표에 행을 끼워 넣던 방식은 담당자 둘이 각각 결함을 올리면 충돌했다 (실측).
    결정 로그와 같은 문제이고 같은 해법을 쓴다 — 한 사람이 한 파일만 만든다.

    **`status.md` 에는 D-18 절차가 남는다.** 그 문서가 매 세션 자동 로딩되기 때문이다.
    목록은 `make status` 가 맨 위에 띄우고, 각 결함의 존재는 귀속 컴포넌트 `상태` 줄이
    이미 이고 다닌다 — 그 컴포넌트를 건드리는 사람은 그 `CLAUDE.md` 를 먼저 읽는다.
    """
    out = []
    d = os.path.join(ROOT, SAFETY_DIR)
    if not os.path.isdir(d):
        return out
    for f in sorted(os.listdir(d)):
        if not f.endswith(".md") or f == "CLAUDE.md":
            continue
        txt = read(f"{SAFETY_DIR}/{f}")
        m = re.search(r"^# (F-\d+)\s*·\s*(.*)$", txt, re.M)
        o = re.search(r"^> \*\*귀속\*\* `([\w./\-]+)`", txt, re.M)
        if not m or not o:
            advisory.append((f"{SAFETY_DIR}/{f}",
                             "`# F-NN · 제목` 또는 `> **귀속** `경로`` 줄이 없음 — A5 가 못 읽는다"))
            continue
        out.append((m.group(1), o.group(1), m.group(2), f"{SAFETY_DIR}/{f}"))
    return out


def check_safety_handoff():
    """소유 경계(D-17)는 「고치지 마라」이지 「묻어라」가 아니다.
    `status.md` 안전 표의 미해소 결함은 귀속 컴포넌트 `CLAUDE.md` 의 `상태` 줄에 떠 있어야
    한다 — 그래야 `make status` 한 화면에서 담당자 눈에 들어온다. 새 장치를 만들지 않고
    이미 있는 수확 경로에 얹는다."""
    if not has(STATUS):
        missing.append((STATUS, "현황 정본 부재 — 안전 결함 인계 검사 불가"))
        return
    if SAFETY_MARK not in read(STATUS):
        missing.append((STATUS, f"「{SAFETY_MARK}」 절 없음 — 안전 결함 인계 경로 (D-18)"))
        return
    rows = [(fid, owner) for fid, owner, _, _ in safety_rows()]

    # 정방향 — 파일이 있으면 그 컴포넌트 `상태` 줄에도 있어야 한다
    owners = {}
    for fid, owner in rows:
        owners.setdefault(fid, []).append(owner)
        doc = f"{owner}/CLAUDE.md"
        if not has(doc):
            missing.append((SAFETY_DIR, f"`{fid}` 귀속 `{owner}` 에 CLAUDE.md 없음"))
            continue
        st = state_line(doc)
        if not st or f"`{fid}`" not in st:
            missing.append((doc, f"안전 결함 `{fid}` 이 `상태` 줄에 없음 — D-18 인계"))

    # 역방향 — `상태` 줄에 있으면 표에도 있어야 한다.
    # 이쪽이 없으면 **표에서 행을 지우는 것만으로 안전 결함이 통로에서 사라진다.**
    # 막히지 않는 쪽이 더 위험한 방향이라 양방향이 아니면 이 장치는 절반만 작동한다.
    for r, _, _ in walk_docs():
        doc = doc_of(r)
        st = state_line(doc)
        if not st:
            continue
        for fid in re.findall(r"`(F-\d+)`", st):
            if fid not in owners:
                missing.append((doc, f"`상태` 줄의 `{fid}` 에 해당하는 "
                                     f"`{SAFETY_DIR}/` 파일이 없음 — 파일을 지웠는가"))
            elif r not in owners[fid]:
                place = "`·`".join(owners[fid])
                missing.append((doc, f"`{fid}` 의 안전 표 귀속은 `{place}` 인데 여기에 박혀 있음"))


# ── A10 · 같은 ID 가 두 번 정의되지 않았는가 ─────────────────────────────────
def check_id_collisions():
    """**둘이 동시에 `F-70` 을 쓰면 아무도 모른다** — 실측으로 확인한 구멍이다.

    서로 다른 결함 둘이 같은 번호를 갖고도 `--strict` 가 통과했다. 병합은 두 행을 나란히
    남기므로 git 도 조용하다. 협업자가 둘 이상이면 채번 경합은 시간 문제다.

    **정의처만 본다** — 표 행 시작(`| **F-70** |`)이 정의고, 본문 인용은 아니다.
    옛 `DA-5`(참조된 ID 가 정의처에 실재하는가)의 반대 방향이다. 그쪽은 「없는 것을
    가리킴」, 이쪽은 「같은 것을 두 번 만듦」이고, 협업에서 실제로 터지는 것은 이쪽이다.

    `D-*` 는 보지 않는다 — spec §0.2 와 `SOT.md` §6 에 **양쪽 동시 갱신**이 규범이라
    두 곳에 나오는 것이 정상이다 (doc-map §3).
    """
    where = {}
    for pre, docs in ID_DEFS.items():
        for doc in docs:
            if not has(doc):
                continue
            for i, ln in enumerate(read(doc).splitlines(), 1):
                m = re.match(r"^\| \*\*(" + pre + r"-\d+)\*\* \|", ln)
                if m:
                    where.setdefault(m.group(1), []).append(f"{doc}:{i}")
    for tid, spots in sorted(where.items()):
        if len(spots) > 1:
            advisory.append((spots[0], f"`{tid}` 가 {len(spots)}곳에서 정의됨 — "
                                       f"{' · '.join(spots[1:])} (채번 경합)"))


# ── A6 · .gitignore 가 실재하는 경로를 가리키는가 ────────────────────────────
def check_ignore_paths():
    """슬래시가 든 패턴은 저장소 루트 기준으로 **고정**된다. 디렉터리를 옮기면 그 규칙은
    죽는데 git 은 아무 말도 하지 않는다 — 실제로 재구조화 때 세 줄이 그렇게 죽어 있었고,
    `fetch_meshes.sh` 가 받은 텍스처 수백 장이 `git add -A` 한 번에 들어올 뻔했다.
    `CLAUDE.md` 앵커와 같은 규칙이다: **가리키는 것은 실재해야 한다.**"""
    if not has(IGNORE):
        return
    for ln in read(IGNORE).splitlines():
        pat = ln.strip()
        if not pat or pat.startswith("#"):
            continue
        pat = pat.lstrip("!").strip("/")
        if "/" not in pat:                       # 이름만 지정한 패턴은 어디서나 매칭된다
            continue
        head = re.split(r"[*?\[]", pat)[0].rstrip("/")
        if "/" in head and not os.path.exists(os.path.join(ROOT, head)):
            advisory.append((IGNORE, f"`{ln.strip()}` 가 없는 경로 `{head}` 를 지목 — 규칙이 죽어 있다"))


# ── A7 · 문서가 적은 파일 경로가 실재하는가 (옛 DA-7 자리) ───────────────────
PATH_RE = re.compile(r"`([\w.\-/]*/[\w.\-]+\.(?:py|sh|md|ya?ml|json|world|urdf|rviz|xml|txt))`")
WALK_SKIP = {".git", "_to_delete", "_bundle", "node_modules", "__pycache__"}


def repo_files():
    out = []
    for dp, dns, fns in os.walk(ROOT):
        dns[:] = [x for x in dns if x not in WALK_SKIP]
        out += [rel(os.path.join(dp, f)) for f in fns]
    return out


def routing_docs():
    """라우팅·규약 문서를 **훑어서** 모은다 (목록을 박지 않는다 — 박으면 여기가 낡는다)."""
    out = [p for p in ROUTING_ROOT if has(p)]
    for d in ROUTING_DIRS:
        full = os.path.join(ROOT, d)
        if not os.path.isdir(full):
            continue
        out += [f"{d}/{f}" for f in sorted(os.listdir(full)) if f.endswith(".md")]
    return out


def check_doc_paths():
    """문서가 가리키는 파일이 실재하는가. 지금까지 이 자리를 지킨 건 사람의 주의력뿐이었다.

    **축약 표기는 규약으로 인정한다** — `limo-MCP/Scenarios/x.json` 처럼 앞을 생략해도
    저장소 안에서 **유일하게 해석되면** 통과한다. 둘 이상으로 해석되면 그것도 결함이다:
    읽는 사람이 어느 파일인지 알 수 없다.

    `CLAUDE.md` 와 **라우팅 문서**를 같이 본다. 라우팅 문서는 매 세션 자동 로딩되거나
    신규 합류자의 첫 문서인데 검사 밖이었다 — `doc-map` 이 없는 문서를 가리켜도 조용했다.
    """
    every = repo_files()
    seen = [doc_of(r) for r, _, _ in walk_docs()] + routing_docs()
    for doc in dict.fromkeys(seen):          # 두 목록이 겹친다 (`docs/harness/CLAUDE.md`)
        base = os.path.dirname(doc)
        for i, ln in enumerate(read(doc).splitlines(), 1):
            for p in PATH_RE.findall(ln):
                direct = os.path.normpath(os.path.join(base, p)).replace(os.sep, "/")
                if has(p) or has(direct):
                    continue
                tail = "/" + p.lstrip("./")
                hits = [e for e in every if e.endswith(tail)]
                if len(hits) == 1:
                    continue
                what = "실재하지 않음" if not hits else f"{len(hits)}곳으로 해석됨 — 모호하다"
                advisory.append((f"{doc}:{i}", f"경로 `{p}` {what}"))


# ── --spec · 설계 정본 절 색인 (파일에 쓰지 않는다) ──────────────────────────
def spec_index():
    """spec 의 절 색인을 **읽는 시점에** 만든다.

    줄 번호와 절 크기는 spec 이 정본인 **파생 데이터**다. 문서에 박아 두면 spec 을 한 줄만
    고쳐도 전부 밀린다 — 실제로 색인 16행 전량이 조용히 어긋나 있었고 아무도 몰랐다.
    `make status` 와 같은 원리로 읽는 시점에 만든다: 충돌 0 · 낡을 수 없음.

    그래서 컴포넌트 헤더의 `읽을 절` 은 **절 번호만** 쓴다. 크기가 궁금하면 여기서 본다.
    """
    if not has(SPEC):
        print(f"설계 정본 부재: {SPEC}")
        return
    lines = read(SPEC).splitlines()
    total = len(lines)
    hs = [(i, l) for i, l in enumerate(lines, 1) if re.match(r"^#{2,3} ", l)]
    print("=" * 88)
    print(f"  설계 정본 절 색인 — {SPEC} ({total}줄)")
    print("  읽는 시점에 만든다. 문서에 박지 않는다 — spec 을 고치면 전부 밀린다.")
    print("=" * 88)
    for k, (i, l) in enumerate(hs):
        lvl = len(l) - len(l.lstrip("#"))
        nxt = total + 1
        for j, l2 in hs[k + 1:]:
            if len(l2) - len(l2.lstrip("#")) <= lvl:
                nxt = j
                break
        title = l.lstrip("# ").strip()
        pad = "  " if lvl == 3 else ""
        print(f"  {pad}§{title[:60]:<62}{'':<2}L{i:<6}{nxt - i:>4}줄")
    print("\n  헤더의 `읽을 절` 이 지목한 절만 연다. 통독하지 않는다.")


# ── --status · 전 영역 현황 (파일에 쓰지 않는다) ─────────────────────────────
def git(*a):
    """git 출력을 읽는다. git 이 없거나 저장소가 아니면 조용히 빈 문자열."""
    try:
        p = subprocess.run(["git", "-C", ROOT] + list(a),
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        return p.stdout.strip() if p.returncode == 0 else ""
    except (OSError, ValueError):
        return ""


def decisions():
    """최근 결정 — **결정 하나가 파일 하나다.**

    표 맨 위에 한 줄을 넣는 방식은 **완전히 분리된 작업끼리도 충돌시킨다** — 실측에서
    KG 담당과 MAC 담당이 서로 다른 컴포넌트만 건드렸는데 `decisions.md` 에서 충돌했다.
    하네스 §4 가 모든 작업에 결정 한 줄을 요구하므로 **모든 PR 이 그 파일을 지난다.**

    더 나쁜 것은 그 다음이다: 충돌 해소가 남의 줄을 떨어뜨려도 `anchor.py` 도
    `sot_audit.py` 도 통과한다 (실측). **충돌과 무관측이 겹치면 조용히 사라진다.**

    `make status` 가 상태 수확에서 쓴 것과 같은 수법이다 — 한 사람이 한 파일만 만들면
    충돌이 0 이고, 모으는 일은 읽는 시점에 한다.
    """
    out = []
    d = os.path.join(ROOT, DECISIONS_DIR)
    if os.path.isdir(d):
        for f in sorted(os.listdir(d), reverse=True):
            m = re.match(r"^(\d{4}-\d{2}-\d{2})-.+\.md$", f)
            if not m:
                continue
            head = next((l[2:] for l in read(f"{DECISIONS_DIR}/{f}").splitlines()
                         if l.startswith("# ")), f)
            out.append((m.group(1), re.sub(r"^\d{4}-\d{2}-\d{2}\s*·\s*", "", head)))
    if not out and has(DECISIONS):          # 아직 파일이 없으면 이력 표에서 읽는다
        for ln in read(DECISIONS).splitlines():
            if re.match(r"^\| \d{4}-\d{2}-\d{2} \|", ln):
                c = [x.strip() for x in ln.strip("|").split("|")]
                out.append((c[0], c[1]))
    return out[:RECENT_DECISIONS]


def recent():
    """**무엇이 바뀌었나.** `상태` 줄은 사람이 적은 것이고 이쪽은 git 이 아는 사실이다.

    둘을 한 화면에 두는 것이 핵심이다 — 어긋나면 그 자리에서 드러난다. 규칙을 다 지킨
    갱신(코드 추가 + 부모 등재)이어도 `상태` 줄을 안 고치면 위 표는 **옛 값을 자신 있게**
    보여준다. 그것을 혼자 두면 비어 있는 것보다 나쁘다.

    여기서도 파일에 쓰지 않는다. git 과 `decisions.md` 가 정본이고 이 블록은 창일 뿐이다.
    """
    log = git("log", "--no-merges", f"-{RECENT_COMMITS}", "--date=short", "--format=%ad  %an  %s")
    if log:
        print("\n" + "-" * 96)
        print(f"  최근 변경 — git log (병합 제외 최근 {RECENT_COMMITS}커밋)")
        for ln in log.splitlines():
            print(f"    {ln[:92]}")
        branch = git("rev-parse", "--abbrev-ref", "HEAD")
        rows = [x for x in git("status", "--porcelain").splitlines() if x]
        print(f"\n    현재 브랜치 {branch or '?'}"
              + (f" · 커밋 안 된 변경 {len(rows)}개" if rows else " · 작업 트리 깨끗"))
        # 커밋 안 된 변경은 **병합·브랜치 전환을 건너며 조용히 사라지는 유일한 것**이다.
        # fda5e22 「유실 복구」가 그것이었다 — 커밋 간 diff 에는 흔적이 없어 CI 도 못 본다.
        # 그래서 세션 시작 화면에 파일 이름까지 띄운다.
        for x in rows[:8]:
            print(f"      {x[:88]}")
        if len(rows) > 8:
            print(f"      … 외 {len(rows) - 8}개")
        if rows:
            print("      ↑ 커밋하지 않은 채 브랜치를 옮기거나 병합하면 이것이 사라진다")

    rows = decisions()
    if rows:
        src = DECISIONS_DIR + "/" if os.path.isdir(os.path.join(ROOT, DECISIONS_DIR)) else DECISIONS
        print(f"\n  최근 결정 — {src}")
        for date, what in rows:
            print(f"    {date}  {re.sub(r'[`*]', '', what)[:78]}")
    if log or rows:
        print("\n    「상태」 줄과 여기가 어긋나 보이면 그 디렉터리 CLAUDE.md 를 고칠 때다.")


def status():
    """각 `CLAUDE.md` 헤더의 `상태` 줄을 읽어 한 화면에 모은다.

    생성물을 커밋하면 매 PR 이 그 블록을 건드려 충돌한다
    (실측: 평면 수확 3/4 · 계층 수확 1/4 · 미수확 0/4). 읽는 시점에 만들면 충돌 0 이다.
    """
    rows = sorted((r, state_line(doc_of(r)) or "—") for r, _, _ in walk_docs() if r != ".")
    plain = lambda t: re.sub(r"[`*]", "", t)
    sf = safety_rows()
    if sf:
        # 맨 위다. 독거 어르신 돌봄 로봇이고, 이건 「나중에 볼 것」이 아니다.
        print("=" * 96)
        print(f"  ⚠ 미해소 안전 결함 {len(sf)}건 — 담당자 통지 (D-18) · {SAFETY_DIR}/")
        print("=" * 96)
        for fid, owner, title, _ in sorted(sf, key=lambda x: int(x[0][2:])):
            print(f"  {fid:<7}{owner:<34}{plain(title)[:50]}")
        print("\n  담당자는 고치고 **실패 경로를 한 번 실행한 뒤** 파일과 `상태` 줄을 함께 지운다.\n")
    print("=" * 96)
    print("  영역 현황 — 각 CLAUDE.md 헤더의 `상태` 줄 (파일에 쓰지 않는다)")
    print("=" * 96)
    top = None
    for r, st in rows:
        head = r.split("/")[0]
        if head != top:
            top = head
            print(f"\n■ {top}/")
        print(f"  {'  ' * r.count('/')}{r.split('/')[-1] + '/':<34}{plain(st)[:60]}")
    print(f"\n  총 {len(rows)}개 컴포넌트")
    print("  상태를 바꾸려면 그 디렉터리 CLAUDE.md 의 `> **상태**` 줄만 고친다 — 이 표는 따라온다.")
    print("  ⚠ 가 붙은 안전 결함은 담당자가 고치고 실패 경로를 한 번 실행한 뒤 지운다 (D-18).")
    files, total = autoload_total()
    print("\n" + "-" * 96)
    print(f"  매 세션 자동 로딩 (`@` 재귀 실측) — {total}줄 / 상한 {AUTOLOAD_MAX_LINES}줄")
    for p in files:
        print(f"    {p:<38}{len(read(p).splitlines()):>5}줄")
    recent()


def report(strict=False):
    if advisory:
        print(f"알림 {len(advisory)}건 — 지금 막지는 않는다. PR 전에 정리한다\n")
        for where, what in advisory:
            print(f"  {where:<52} {what}")
        print()
    if missing:
        print(f"앵커 누락 {len(missing)}건 — 해당 CLAUDE.md 에 한 줄씩 추가할 것\n")
        for where, what in missing:
            print(f"  {where:<52} {what}")
        return 1
    if strict and advisory:
        print("--strict — 알림도 통과시키지 않는다 (PR · CI)")
        return 1
    if not advisory:
        print("앵커 OK")
    else:
        print("막는 것 없음 — 위 알림은 지금 고치지 않아도 커밋된다")
    return 0


if __name__ == "__main__":
    if "--spec" in sys.argv:
        spec_index()
        sys.exit(0)
    if "--status" in sys.argv:
        status()
        sys.exit(0)
    check_anchors()
    check_child_docs()
    check_ghosts()
    check_tools()
    check_spec_refs()
    check_root_size()
    check_safety_handoff()
    check_id_collisions()
    check_ignore_paths()
    check_doc_paths()
    sys.exit(report("--strict" in sys.argv))
