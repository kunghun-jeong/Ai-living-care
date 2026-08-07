#!/usr/bin/env python3
"""앵커 검사 — `CLAUDE.md`가 자기 디렉터리 안의 것을 가리키고 있는가.

    python3 anchor.py

규칙은 하나다: **파일이나 디렉터리가 생기거나 이름이 바뀌면 그 자리의 `CLAUDE.md`에 한 줄 넣는다.**
빠진 한 줄만 알려준다. 그 외에는 아무것도 검사하지 않는다.

`CLAUDE.md`가 없는 하위 디렉터리는 잘못이 아니다 — 부모가 가리키고 있으면 앵커된 것이다.
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SKIP = {".git", "_to_delete", "_bundle", "node_modules", "__pycache__", "slides", "maps"}
CODE = (".py", ".sh")
# 원본 보존 대상 (D-14) — 우리 파일이 아니다. 최상위 CLAUDE.md 하나로만 앵커한다.
PRESERVED = ("worker_ai_agent/limo-MCP", "tools/limo-patrol-viz")

missing = []


def _noop():
    pass


def rel(p):
    return os.path.relpath(p, ROOT).replace(os.sep, "/")


def check():
    for dp, dns, fns in os.walk(ROOT):
        dns[:] = [x for x in dns if x not in SKIP and not x.startswith(".")]
        r = rel(dp)
        if any(r.startswith(x + "/") for x in PRESERVED):
            dns[:] = []                       # 보존 대상 내부는 들어가지 않는다
            continue
        if "CLAUDE.md" not in fns:
            continue                          # 앵커가 없는 디렉터리는 부모가 가리킨다
        txt = open(os.path.join(dp, "CLAUDE.md"), encoding="utf-8").read()
        named = set(re.findall(r"`([\w.\-/]+?)/?`", txt))
        for e in sorted(dns) + sorted(f for f in fns if f.endswith(CODE)):
            if e not in named and e not in txt:
                kind = "디렉터리" if e in dns else "파일"
                missing.append((f"{r}/CLAUDE.md" if r != "." else "CLAUDE.md",
                                f"{kind} `{e}` 미등재"))
    
    # MCP tool 은 이 저장소의 유일한 외부 인터페이스라 파일과 같은 급의 앵커다.
    # tool 을 추가·개명하면 아래 두 문서에 한 줄 넣는다.
    TOOL_SRC = "worker_ai_agent/limo-MCP/MCP_server/MCP_server.py"
    TOOL_DOCS = ("docs/api-spec.md", "worker_ai_agent/mcp_server/CLAUDE.md")
    
    src = os.path.join(ROOT, TOOL_SRC)
    if os.path.isfile(src):
        tools = re.findall(r"@mcp\.tool\(\)\s*\n\s*(?:async\s+)?def\s+(\w+)",
                           open(src, encoding="utf-8").read())
        for doc in TOOL_DOCS:
            p = os.path.join(ROOT, doc)
            if not os.path.isfile(p):
                missing.append((doc, "파일 없음 — MCP tool 앵커처"))
                continue
            txt = open(p, encoding="utf-8").read()
            for name in tools:
                if name not in txt:
                    missing.append((doc, f"MCP tool `{name}` 미등재"))
    
    if not missing:
        print("앵커 OK")
        sys.exit(0)
    
    print(f"앵커 누락 {len(missing)}건 — 해당 CLAUDE.md에 한 줄씩 추가할 것\n")
    for where, what in missing:
        print(f"  {where:<52} {what}")
    sys.exit(1)

def status():
    """48개 CLAUDE.md 헤더의 `상태` 줄을 모아 한 화면에 보여준다.

    **파일에 쓰지 않는다.** 생성물을 커밋하면 매 PR 이 그 블록을 건드려 충돌한다
    (실측: 평면 수확 3/4, 계층 수확 1/4, 미수확 0/4). 읽는 시점에 만들면
    충돌 0 이고 낡을 수가 없다.
    """
    rows = []
    for dp, dns, fns in os.walk(ROOT):
        dns[:] = [x for x in dns if x not in SKIP and not x.startswith(".")]
        if "CLAUDE.md" not in fns:
            continue
        r = rel(dp)
        if r == ".":
            continue
        txt = open(os.path.join(dp, "CLAUDE.md"), encoding="utf-8").read()
        title = txt.splitlines()[0].lstrip("# ").strip()
        m = re.search(r"^> \*\*상태\*\* (.*)$", txt, re.M)
        role = re.search(r"^> \*\*역할\*\* (.*)$", txt, re.M)
        rows.append((r, title, (m.group(1) if m else "—"),
                     (role.group(1) if role else "")))
    rows.sort()
    plain = lambda t: re.sub(r"[`*]", "", t)
    top = None
    print("=" * 100)
    print("  영역 현황 — 각 CLAUDE.md 헤더의 `상태` 줄을 읽은 것 (파일에 쓰지 않는다)")
    print("=" * 100)
    for r, title, st, role in rows:
        head = r.split("/")[0]
        if head != top:
            top = head
            print(f"\n■ {top}/")
        depth = r.count("/")
        print(f"  {'  ' * depth}{r.split('/')[-1] + '/':<34}{plain(st)[:62]}")
    print(f"\n  총 {len(rows)}개 컴포넌트")
    print("  상태를 바꾸려면 그 디렉터리 CLAUDE.md 의 `> **상태**` 줄만 고친다 — 이 표는 따라온다.")


if __name__ == "__main__":
    if "--status" in sys.argv:
        status()
        sys.exit(0)
    check()
