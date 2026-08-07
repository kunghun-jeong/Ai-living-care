#!/usr/bin/env python3
"""앵커 검사 — 문서가 가리키는 것이 실재하는가.

    python3 anchor.py            빠진 앵커만 보고 (커밋 훅 · CI 가 실행)
    python3 anchor.py --status   전 영역 현황 + 자동 로딩 실측 (파일에 쓰지 않는다)

규칙은 하나다: **파일·디렉터리가 생기거나 이름이 바뀌면 그 자리 `CLAUDE.md` 에 한 줄 넣는다.**
감사 도구가 아니다. 점수를 세지 않고 빠진 것만 알려준다.

검사 일곱 — 전부 **양방향**이거나 실재를 본다:
  A1  `CLAUDE.md` 가 자기 디렉터리의 하위·코드 파일을 가리키는가
  A2  MCP tool 집합이 `api-spec.md` · `mcp_server/CLAUDE.md` 에 있는가 (유일한 외부 인터페이스)
  A3  헤더의 `읽을 절` 이 spec 에 **실재하는 절**을 가리키는가
  A4  루트가 50줄 이내이고 **`@` 재귀 총합**이 상한 이내인가 (매 세션 자동 로딩된다)
  A5  안전 결함이 `status.md` 표 ↔ 컴포넌트 `상태` 줄 **양쪽에** 있는가 (D-18 인계 경로)
  A6  `.gitignore` 의 경로 패턴이 실재하는 디렉터리를 가리키는가
  A7  문서가 적은 파일 경로가 실재하는가 — 축약은 **유일하게 해석될 때만** 허용

한 방향만 보는 검사는 지우는 쪽을 못 막는다. A1 과 A5 는 그래서 역방향을 함께 본다.
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SKIP = {".git", "_to_delete", "_bundle", "node_modules", "__pycache__", "slides", "maps"}
CODE = (".py", ".sh")
# 원본 보존 대상 (D-14 · D-17) — 우리 파일이 아니다. 최상위 CLAUDE.md 하나로만 앵커한다.
PRESERVED = ("worker_ai_agent/limo-MCP", "tools/limo-patrol-viz")

SPEC = "docs/spec/AI-Care_Unified_Architecture_Spec_v0.2.md"
STATUS = "docs/status.md"
SAFETY_MARK = "### 안전 — 담당자 통지"
TOOL_SRC = "worker_ai_agent/limo-MCP/MCP_server/MCP_server.py"
TOOL_DOCS = ("docs/api-spec.md", "worker_ai_agent/mcp_server/CLAUDE.md")
IGNORE = ".gitignore"
ROOT_MAX_LINES = 50
AUTOLOAD_MAX_LINES = 420

missing = []


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
    for r, dns, fns in walk_docs():
        doc = doc_of(r)
        named = named_in(read(doc))
        for e in sorted(dns) + sorted(f for f in fns if f.endswith(CODE)):
            if e not in named:
                kind = "디렉터리" if e in dns else "파일"
                missing.append((doc, f"{kind} `{e}` 미등재"))


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
                    missing.append((f"{doc}:{i}", f"표의 `{name}/` 이 실재하지 않음 — 유령 항목"))


# ── A2 · MCP tool 집합 ───────────────────────────────────────────────────────
def check_tools():
    if not has(TOOL_SRC):
        return
    tools = re.findall(r"@mcp\.tool\(\)\s*\n\s*(?:async\s+)?def\s+(\w+)", read(TOOL_SRC))
    for doc in TOOL_DOCS:
        if not has(doc):
            missing.append((doc, "파일 없음 — MCP tool 앵커처"))
            continue
        txt = read(doc)
        for name in tools:
            if name not in txt:
                missing.append((doc, f"MCP tool `{name}` 미등재"))


# ── A3 · 「읽을 절」 이 실재하는가 ────────────────────────────────────────────
def check_spec_refs():
    """48개 헤더가 `§4.1` 같은 절 번호에 의존한다. spec 을 개정하거나 절을 재배치하면
    전부 조용히 어긋난다 — 경로와 달리 절 번호는 깨져도 눈에 안 띈다."""
    if not has(SPEC):
        missing.append((SPEC, "설계 정본 부재 — `읽을 절` 검사 불가"))
        return
    have = set(re.findall(r"^#{2,3} (\d+(?:\.\d+)?)\.? ", read(SPEC), re.M))
    for r, _, _ in walk_docs():
        doc = doc_of(r)
        m = re.search(r"^> \*\*읽을 절\*\* (.*)$", read(doc), re.M)
        if not m:
            continue
        for sec in re.findall(r"§(\d+(?:\.\d+)?)", m.group(1)):
            if sec not in have:
                missing.append((doc, f"spec 에 없는 절 `§{sec}` 지목"))


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
        missing.append(("CLAUDE.md",
                        f"자동 로딩 {total}줄 (상한 {AUTOLOAD_MAX_LINES}) — "
                        f"`@` 는 재귀다. 지금 열리는 것: {' · '.join(files)}"))


# ── A5 · 안전 결함 인계 (D-18) ───────────────────────────────────────────────
def check_safety_handoff():
    """소유 경계(D-17)는 「고치지 마라」이지 「묻어라」가 아니다.
    `status.md` 안전 표의 미해소 결함은 귀속 컴포넌트 `CLAUDE.md` 의 `상태` 줄에 떠 있어야
    한다 — 그래야 `make status` 한 화면에서 담당자 눈에 들어온다. 새 장치를 만들지 않고
    이미 있는 수확 경로에 얹는다."""
    if not has(STATUS):
        missing.append((STATUS, "현황 정본 부재 — 안전 결함 인계 검사 불가"))
        return
    parts = read(STATUS).split(SAFETY_MARK)
    if len(parts) < 2:
        missing.append((STATUS, f"「{SAFETY_MARK}」 절 없음 — 안전 결함 인계 경로 (D-18)"))
        return
    block = re.split(r"\n#{2,3} ", parts[1])[0]
    rows = re.findall(r"^\| \*\*(F-\d+)\*\* \| `([\w./\-]+)` \|", block, re.M)

    # 정방향 — 표에 있으면 그 컴포넌트 `상태` 줄에도 있어야 한다
    owners = {}
    for fid, owner in rows:
        owners.setdefault(fid, []).append(owner)
        doc = f"{owner}/CLAUDE.md"
        if not has(doc):
            missing.append((STATUS, f"`{fid}` 귀속 `{owner}` 에 CLAUDE.md 없음"))
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
                missing.append((doc, f"`상태` 줄의 `{fid}` 이 status.md 안전 표에 없음 — 행을 지웠는가"))
            elif r not in owners[fid]:
                place = "`·`".join(owners[fid])
                missing.append((doc, f"`{fid}` 의 안전 표 귀속은 `{place}` 인데 여기에 박혀 있음"))


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
            missing.append((IGNORE, f"`{ln.strip()}` 가 없는 경로 `{head}` 를 지목 — 규칙이 죽어 있다"))


# ── A7 · 문서가 적은 파일 경로가 실재하는가 (옛 DA-7 자리) ───────────────────
PATH_RE = re.compile(r"`([\w.\-/]*/[\w.\-]+\.(?:py|sh|md|ya?ml|json|world|urdf|rviz|xml|txt))`")
WALK_SKIP = {".git", "_to_delete", "_bundle", "node_modules", "__pycache__"}


def repo_files():
    out = []
    for dp, dns, fns in os.walk(ROOT):
        dns[:] = [x for x in dns if x not in WALK_SKIP]
        out += [rel(os.path.join(dp, f)) for f in fns]
    return out


def check_doc_paths():
    """문서가 가리키는 파일이 실재하는가. 지금까지 이 자리를 지킨 건 사람의 주의력뿐이었다.

    **축약 표기는 규약으로 인정한다** — `limo-MCP/Scenarios/x.json` 처럼 앞을 생략해도
    저장소 안에서 **유일하게 해석되면** 통과한다. 둘 이상으로 해석되면 그것도 결함이다:
    읽는 사람이 어느 파일인지 알 수 없다.
    """
    every = repo_files()
    for r, _, _ in walk_docs():
        doc = doc_of(r)
        base = "" if r == "." else r
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
                missing.append((f"{doc}:{i}", f"경로 `{p}` {what}"))


# ── --status · 전 영역 현황 (파일에 쓰지 않는다) ─────────────────────────────
def status():
    """각 `CLAUDE.md` 헤더의 `상태` 줄을 읽어 한 화면에 모은다.

    생성물을 커밋하면 매 PR 이 그 블록을 건드려 충돌한다
    (실측: 평면 수확 3/4 · 계층 수확 1/4 · 미수확 0/4). 읽는 시점에 만들면 충돌 0 이다.
    """
    rows = sorted((r, state_line(doc_of(r)) or "—") for r, _, _ in walk_docs() if r != ".")
    plain = lambda t: re.sub(r"[`*]", "", t)
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


def report():
    if not missing:
        print("앵커 OK")
        return 0
    print(f"앵커 누락 {len(missing)}건 — 해당 CLAUDE.md 에 한 줄씩 추가할 것\n")
    for where, what in missing:
        print(f"  {where:<52} {what}")
    return 1


if __name__ == "__main__":
    if "--status" in sys.argv:
        status()
        sys.exit(0)
    check_anchors()
    check_ghosts()
    check_tools()
    check_spec_refs()
    check_root_size()
    check_safety_handoff()
    check_ignore_paths()
    check_doc_paths()
    sys.exit(report())
