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


def rel(p):
    return os.path.relpath(p, ROOT).replace(os.sep, "/")


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
