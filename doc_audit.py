#!/usr/bin/env python3
"""문서 정합성 감사 — doc-map §1 「정본 소유권」의 기계 집행기.

    python3 doc_audit.py           # 전체 검사
    python3 doc_audit.py DA-2      # 특정 장치만
    python3 doc_audit.py --list    # 장치 목록

`sot_audit.py`는 **구조**(디렉터리·파일이 있는가)를 본다.
`doc_audit.py`는 **정합성**(같은 사실을 적은 여러 곳이 갈라졌는가)을 본다.

두 개가 같이 통과해야 커밋한다. 하네스 2단계·3단계(V-5)에서 호출된다.

── 왜 있는가 ────────────────────────────────────────────────────────────────
하네스는 "부모 CLAUDE.md도 같이 고쳐라"라고 **적어만** 두었다. 그 결과
하네스 출하 시점에 이미 `SOT.md` §2 트리에서 `worker_ai_agent/mcp_server/`와
`worker_ai_agent/limo-MCP/`가 사라져 있었고, `sot_audit.py`는 104/104를 냈다.
**사람에게 시키는 전파는 지켜지지 않는다.** 이 파일은 그것을 기계로 옮긴 것이다.

── 장치 ↔ doc-map 대응 ──────────────────────────────────────────────────────
DA-1  MCP tool 집합       doc-map §1 「MCP tool 시그니처」 — 코드가 정본
DA-2  부모 ↔ 자식 구성표   doc-map §2 구조 ① 「부모 CLAUDE.md의 구성 표」
DA-3  SOT 트리 3자 일치    doc-map §1 「디렉터리 배치·명명 규칙」 — 집합 일치
DA-4  「N종」 리터럴        doc-map §1 전반 — 개수를 세는 문장은 전부 파생물
DA-5  식별자 무결성        doc-map §1 「갭 G-*」「결함 F-*」「표준화 S-*」 등
DA-6  원본 보존 무변경     doc-map §1 「원본 보존 대상」 — D-14
DA-7  문서 경로 실재       구 하네스 D-1 재작성 (인라인 코드까지 본다)
DA-8  폐기 생성기 봉인     하네스 docs-and-structure §0
DA-9  CLAUDE.md 규약       하네스 docs-and-structure §6 · HD-1
DA-10 architecture 정합    doc-map §3 DM-5
"""
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SPEC = "docs/spec/AI-Care_Unified_Architecture_Spec_v0.2.md"
SOT = "SOT.md"
MCP_SERVER = "worker_ai_agent/limo-MCP/MCP_server/MCP_server.py"
BASE_COMMIT = "27b0f30"

# 감사 대상에서 제외 — 기록물이거나 저장소 외부에서 온 것
SKIP_DIRS = ("_to_delete", "_bundle", ".git", "node_modules", "docs/slides")
# 과거 시점의 기록이라 현재 사실과 달라도 정상인 문서
HISTORICAL = ("docs/audit/", "docs/handoff/", "docs/context/", "MIGRATION.md")

# doc-map §1 「MCP tool 시그니처」가 복제를 허용한 위치 — 여기만 전수 열거 의무
TOOL_MIRRORS = ["docs/api-spec.md", "worker_ai_agent/mcp_server/CLAUDE.md"]

results = []


def chk(dev, ok, msg, detail=""):
    results.append((dev, bool(ok), msg, detail))


def rel(p):
    return os.path.join(ROOT, p)


def read(p):
    with open(rel(p), encoding="utf-8") as f:
        return f.read()


def all_md(include_historical=False):
    out = []
    for dp, dns, fns in os.walk(ROOT):
        dns[:] = [d for d in dns if d not in ("_to_delete", "_bundle", ".git", "node_modules")]
        for fn in fns:
            if not fn.endswith(".md"):
                continue
            r = os.path.relpath(os.path.join(dp, fn), ROOT).replace(os.sep, "/")
            if any(s in r for s in ("docs/slides",)):
                continue
            if not include_historical and any(r.startswith(h) or r == h for h in HISTORICAL):
                continue
            out.append(r)
    return sorted(out)


def dirs_with_claude():
    out = []
    for dp, dns, fns in os.walk(ROOT):
        dns[:] = [d for d in dns if d not in ("_to_delete", "_bundle", ".git", "node_modules")]
        if "CLAUDE.md" in fns:
            r = os.path.relpath(dp, ROOT).replace(os.sep, "/")
            out.append("." if r == "." else r)
    return sorted(out)


def git(*args):
    try:
        p = subprocess.run(["git"] + list(args), cwd=ROOT, capture_output=True, text=True, timeout=30)
        return p.stdout if p.returncode == 0 else None
    except Exception:
        return None


# ═══ DA-1 · MCP tool 집합 — 코드가 정본 ═══════════════════════════════════════
def da1():
    if not os.path.exists(rel(MCP_SERVER)):
        chk("DA-1", False, f"정본 부재: {MCP_SERVER}")
        return None
    src = read(MCP_SERVER)
    truth = re.findall(r"@mcp\.tool\(\)\s*\n\s*(?:async\s+)?def\s+(\w+)", src)
    tools = set(truth)
    chk("DA-1", len(truth) == len(tools), f"코드에 tool {len(truth)}종 — 이름 중복 없음")

    # doc-map §1이 「복제 허용」으로 선언한 두 곳만 전수 열거 의무를 진다.
    # 그 외 문서가 일부 tool만 언급하는 것은 정상이다 (문맥상 인용).
    for md in TOOL_MIRRORS:
        if not os.path.exists(rel(md)):
            chk("DA-1", False, f"복제 허용처 부재: {md}")
            continue
        txt = read(md)
        found = {t for t in tools if re.search(rf"`{re.escape(t)}`|\b{re.escape(t)}\(", txt)}
        missing = tools - found
        chk("DA-1", not missing, f"{md} — tool 전수 열거 (doc-map 복제 허용처)",
            f"누락: {sorted(missing)}" if missing else "")
    # 코드에 없는 이름을 tool처럼 부르는 문서
    for md in all_md():
        txt = read(md)
        claimed = set(re.findall(r"`(\w+)`\s*(?:tool|툴)\b", txt)) | set(
            re.findall(r"(?:tool|툴)\s*`(\w+)`", txt))
        ghost = {c for c in claimed if c not in tools and c.islower() and "_" in c}
        chk("DA-1", not ghost, f"{md} — 존재하지 않는 tool 참조 없음",
            f"코드에 없음: {sorted(ghost)}" if ghost else "")
    return tools


# ═══ DA-2 · 부모 CLAUDE.md ↔ 실제 자식 디렉터리 ═══════════════════════════════
# 팀이 하위 컴포넌트에서 일할 때 상위가 낡는 것을 직접 막는 장치.
EXEMPT_PARENT = {".", "docs"}   # 루트는 목차(50줄 규약), docs는 문서 분류


def da2():
    have = set(dirs_with_claude())
    for parent in sorted(have):
        if parent in EXEMPT_PARENT:
            continue
        kids = sorted(c.split("/")[-1] for c in have
                      if c != parent and c.startswith(parent + "/")
                      and "/" not in c[len(parent) + 1:])
        if not kids:
            continue
        txt = read(f"{parent}/CLAUDE.md")
        # 부모 문서가 자식 디렉터리 이름을 `xxx/` 형태로 언급하는가
        named = set(re.findall(r"`([\w.-]+)/`", txt))
        missing = [k for k in kids if k not in named]
        chk("DA-2", not missing,
            f"{parent}/CLAUDE.md ← 자식 {len(kids)}개 전부 등재",
            f"부모 문서에 없는 자식: {missing}  ← 상위 노후화" if missing else "")
        # 표에 적혀 있으나 실재하지 않는 자식 (삭제 후 부모 미갱신)
        phantom = [n for n in sorted(named)
                   if n not in kids and os.path.isdir(rel(parent)) is True
                   and not os.path.exists(rel(f"{parent}/{n}"))
                   and n not in ("docs", "interfaces", "contracts", "tools", "spec")
                   and re.search(rf"^\|\s*`{re.escape(n)}/`", txt, re.M)]
        chk("DA-2", not phantom, f"{parent}/CLAUDE.md — 구성 표에 유령 항목 없음",
            f"실재하지 않음: {phantom}" if phantom else "")


# ═══ DA-3 · SOT §2 트리 ↔ sot_audit.py ↔ 파일시스템 3자 집합 일치 ═════════════
TREE_SCOPE = ("manager_ai_agent", "worker_ai_agent", "interfaces", "contracts", "tools")


def parse_sot_tree():
    txt = read(SOT)
    m = re.search(r"^## 2\.\s.*?```\n(.*?)```", txt, re.S | re.M)
    if not m:
        return None
    stack, out = [], set()
    for line in m.group(1).splitlines():
        c = max(line.find("├── "), line.find("└── "))
        if c < 0:
            continue
        depth = c // 4
        names = re.findall(r"([\w.-]+)/", line[c + 4:].split("  ")[0] + " ")
        if not names:
            continue
        stack = stack[:depth]
        stack.append(names[0])
        out.add("/".join(stack))
        for extra in names[1:]:          # `├── spec/ context/ audit/` 형태
            out.add("/".join(stack + [extra]))
    return out


def sot_audit_targets():
    txt = read("sot_audit.py")
    ns = {}
    try:
        exec(compile(re.sub(r"^if __name__.*", "", txt, flags=re.S | re.M), "sot_audit.py", "exec"),
             {"os": os, "re": re, "sys": sys, "__file__": rel("sot_audit.py")}, ns)
    except Exception as e:
        chk("DA-3", False, "sot_audit.py 구조 추출 실패", str(e))
        return None
    t = set()
    t |= {d for _, d, _ in ns.get("COMPONENTS", [])}
    t |= set(ns.get("CHILDREN", []))
    t |= {d for _, d, _ in ns.get("INTERFACES", [])}
    t |= set(ns.get("NON_COMPONENT", []))
    t |= set(ns.get("PRESERVED", []))
    t |= {os.path.dirname(p) for p in ns.get("CODE", {}) if "/" in p}
    t |= {"manager_ai_agent", "worker_ai_agent", "interfaces"}
    return t


def in_scope(p):
    return p.split("/")[0] in TREE_SCOPE


def da3():
    tree = parse_sot_tree()
    if tree is None:
        chk("DA-3", False, "SOT.md §2 트리 블록을 찾지 못함")
        return
    targets = sot_audit_targets()
    if targets is None:
        return
    fs = {d for d in dirs_with_claude() if in_scope(d)}
    fs |= {p for p in ("worker_ai_agent/limo-MCP", "tools/limo-patrol-viz") if os.path.isdir(rel(p))}
    tree_s = {p for p in tree if in_scope(p)}
    tgt_s = {p for p in targets if in_scope(p)}

    miss = sorted(fs - tree_s)
    chk("DA-3", not miss, "SOT.md §2 트리가 실재 디렉터리를 전부 담는가",
        f"트리에 없는 실재 디렉터리: {miss}  ← 정본이 파생물보다 낡음" if miss else "")
    gone = sorted(p for p in tree_s - fs if not os.path.isdir(rel(p)))
    chk("DA-3", not gone, "SOT.md §2 트리에 유령 경로 없음",
        f"실재하지 않음: {gone}" if gone else "")
    untracked = sorted(fs - tgt_s)
    chk("DA-3", not untracked, "sot_audit.py 검사 대상이 실재 디렉터리를 전부 담는가",
        f"감사 사각지대: {untracked}" if untracked else "")
    only_tgt = sorted(p for p in tgt_s - tree_s if os.path.isdir(rel(p)))
    chk("DA-3", not only_tgt, "sot_audit.py 대상 ⊆ SOT.md 트리",
        f"트리 미등재: {only_tgt}" if only_tgt else "")

    # §2.1 대응표의 디렉터리도 실재해야 한다
    txt = read(SOT)
    for d in set(re.findall(r"`((?:manager_ai_agent|worker_ai_agent)/[\w/-]+)/`", txt)):
        chk("DA-3", os.path.isdir(rel(d)), f"SOT §2.1 대응표 경로 실재: {d}/")


# ═══ DA-4 · 「N종」 리터럴 ↔ 정본 개수 ════════════════════════════════════════
def da4(tools):
    counts = {}
    if tools is not None:
        counts["tool"] = (len(tools), f"{MCP_SERVER}의 @mcp.tool()")
    spec = read(SPEC) if os.path.exists(rel(SPEC)) else ""
    m = re.search(r"### 5\.2 `status` 열거값.*?\n((?:\|.*\n)+)", spec)
    if m:
        vals = re.findall(r"^\|\s*`(\w+)`\s*\|", m.group(1), re.M)
        if vals:
            counts["status"] = (len(vals), "spec §5.2 열거표")
    m = re.search(r"^\s*(?:or-race|and-all)[\s\S]{0,400}", spec, re.M)
    modes = set(re.findall(r"\b(and-all|or-race|or-fallback|sequential|split)\b", spec))
    if modes:
        counts["dispatch-mode"] = (len(modes), "spec §7.1 모드 이름")
    ifn = len(re.findall(r"^\|\s*\*{0,2}IF-\d+", read(SOT), re.M))
    if ifn:
        counts["인터페이스"] = (ifn, "SOT.md §3 표")

    # 「없는 tool 3종」처럼 부재를 세는 문장은 정본 개수와 무관하다
    pat = re.compile(r"(?P<neg>없는|미구현|존재하지 않는|누락된)?\s*"
                     r"(?P<label>tool|status|dispatch-mode|인터페이스|툴)\s*(?P<n>\d+)\s*종")
    hits = 0
    for md in all_md():
        txt = read(md)
        for m in pat.finditer(txt):
            if m.group("neg"):
                continue
            label = m.group("label")
            label = "tool" if label == "툴" else label
            if label not in counts:
                continue
            want, src = counts[label]
            hits += 1
            n = int(m.group("n"))
            chk("DA-4", n == want, f"{md} — 「{label} {n}종」",
                f"정본({src})은 {want}종" if n != want else "")
    chk("DA-4", hits > 0, f"「N종」 리터럴 {hits}건 대조 (정본 {len(counts)}종 등록)")


# ═══ DA-5 · 식별자 무결성 ════════════════════════════════════════════════════
# doc-map §1 · 하네스 D-4 식별자 표를 그대로 옮긴 것.
# 하네스 파일 내부의 체크 번호는 `H*-n`(HM/HW/HG/HS/HD)이라 여기 걸리지 않는다 —
# 접두가 한 글자 더 붙어 단어 경계가 생기지 않기 때문이다. 그것이 네임스페이스 분리다.
OWNERS = {
    "F": ["docs/status.md"],
    "G": [SPEC],
    "U": [SPEC],
    "S": [SPEC],
    "IF": [SPEC, SOT],
    "D": [SPEC, SOT],
    "N": [SOT],
    "SP": [SOT],
    "AR": [SOT],
    "P": [SPEC],
    "V": ["docs/harness.md"],
    "DA": ["doc_audit.py"],
}


def da5():
    for pre, owners in OWNERS.items():
        defined = set()
        for o in owners:
            if not os.path.exists(rel(o)):
                continue
            defined |= set(re.findall(rf"\b{pre}-(\d+)\b", read(o)))
        if not defined:
            chk("DA-5", False, f"{pre}-* 정의처에서 ID를 하나도 찾지 못함 ({owners})")
            continue
        bad = {}
        for md in all_md():
            if md in owners:
                continue
            used = set(re.findall(rf"\b{pre}-(\d+)\b", read(md)))
            undef = used - defined
            if undef:
                bad[md] = sorted(undef, key=int)
        chk("DA-5", not bad,
            f"{pre}-* 참조가 전부 정의처({'/'.join(os.path.basename(o) for o in owners)})에 존재",
            "; ".join(f"{k}: {[pre + '-' + v for v in vs]}" for k, vs in bad.items()) if bad else "")


# ═══ DA-6 · 원본 보존 무변경 (D-14) ══════════════════════════════════════════
PRESERVE_MAP = {"limo-MCP": "worker_ai_agent/limo-MCP",
                "limo-patrol-viz": "tools/limo-patrol-viz"}
# 보존 대상 안에 우리가 새로 넣어도 되는 것 — 규범 문서만
ALLOWED_ADD = ("CLAUDE.md",)


def blobs(ref, path):
    out = git("ls-tree", "-r", ref, "--", path)
    if out is None:
        return None
    d = {}
    for line in out.splitlines():
        meta, name = line.split("\t", 1)
        d[name[len(path):].lstrip("/")] = meta.split()[2]
    return d


def norm(sha):
    raw = subprocess.run(["git", "cat-file", "blob", sha], cwd=ROOT, capture_output=True, timeout=30)
    return raw.stdout.replace(b"\r\n", b"\n")


def on_disk(d):
    """작업 트리의 실제 파일 목록. 커밋 전에 걸러야 의미가 있으므로 HEAD가 아니라 디스크를 본다."""
    out = {}
    base = rel(d)
    for dp, dns, fns in os.walk(base):
        dns[:] = [x for x in dns if x not in (".git", "__pycache__")]
        for fn in fns:
            p = os.path.join(dp, fn)
            out[os.path.relpath(p, base).replace(os.sep, "/")] = p
    return out


def da6():
    if git("rev-parse", "--git-dir") is None:
        chk("DA-6", True, "git 없음 — 보존 검사 SKIP")
        return
    if git("cat-file", "-e", BASE_COMMIT) is None and git("rev-parse", BASE_COMMIT) is None:
        chk("DA-6", True, f"기준 커밋 {BASE_COMMIT} 없음 — SKIP")
        return
    for old, new in PRESERVE_MAP.items():
        a = blobs(BASE_COMMIT, old)
        if a is None or not os.path.isdir(rel(new)):
            chk("DA-6", False, f"{new} — 기준 blob 또는 디렉터리 부재")
            continue
        b = on_disk(new)          # HEAD가 아니라 작업 트리 — 커밋 전에 걸러야 한다
        removed = sorted(set(a) - set(b))
        added = sorted(f for f in set(b) - set(a) if os.path.basename(f) not in ALLOWED_ADD)
        changed = sorted(f for f in set(a) & set(b)
                         if norm(a[f]) != open(b[f], "rb").read().replace(b"\r\n", b"\n"))
        chk("DA-6", not removed, f"{new} — 원본 파일 삭제 없음", f"{removed}" if removed else "")
        chk("DA-6", not changed, f"{new} — 원본 내용 변경 없음 (개행 정규화 제외)",
            f"{changed}  ← D-14 위반" if changed else "")
        chk("DA-6", not added, f"{new} — 허용 외 파일 추가 없음", f"{added}" if added else "")
        chk("DA-6", True, f"{new} — 원본 {len(a)}개 파일 대조 완료")


# ═══ DA-7 · 문서 경로 실재 (하네스 D-1 재작성) ════════════════════════════════
# 구 D-1은 ```bash 펜스만 봐서 루트 CLAUDE.md(인라인 불릿)에서 0개를 검사했다.
TOPS = None
EXT = r"py|sh|yaml|yml|json|urdf|rviz|md|txt|pgm|xml|launch\.py"
FUTURE = ("TODO", "예정", "미구현", "신설", "만든다", "작성한다", "될 것", "추가한다", "생성한다")
# 금지 경로를 "금지"라고 적은 문장은 그 경로가 없어야 정상이다
NEGATED = ("금지", "❌", "FORBIDDEN", "없다", "부재", "삭제", "아니라")
# 원본 보존 대상(D-14) 안의 원본 문서는 우리가 고칠 수 없다 — CLAUDE.md만 우리 것
PRESERVED_ROOTS = ("worker_ai_agent/limo-MCP/", "tools/limo-patrol-viz/")


def shell_paths(cmd):
    """`cd A && python3 B/c.py` 처럼 **cwd가 바뀌는 명령**을 실제 저장소 경로로 해석한다.

    구 하네스 D-1이 놓쳤던 두 형태를 여기서 잡는다:
      ① 확장자 없는 `cd tools/limo-patrol-viz`  ② `cd` 이후의 상대경로 `Scenarios/send_goal.py`
    """
    out, cwd = set(), ""
    for seg in re.split(r"&&|\|\||;|\n", cmd):
        seg = seg.strip()
        m = re.match(r"cd\s+([^\s;&|]+)", seg)
        if m:
            d = m.group(1).strip("\"'")
            cwd = d if d.split("/")[0] in TOPS else os.path.normpath(os.path.join(cwd, d))
            out.add(cwd.rstrip("/") + "/")
            continue
        for tok in re.findall(rf"((?:\./)?(?:[\w.-]+/)*[\w.-]+\.(?:{EXT}))", seg):
            t = tok[2:] if tok.startswith("./") else tok
            if "/" not in t and not cwd:
                continue                       # 맨 파일명 + cwd 미상 → 판정 불가
            out.add(t if t.split("/")[0] in TOPS else os.path.normpath(os.path.join(cwd, t)))
        for tok in re.findall(r"(?:^|\s)((?:[\w.-]+/)+)(?:\s|$)", seg):
            out.add(tok if tok.split("/")[0] in TOPS else os.path.normpath(os.path.join(cwd, tok)) + "/")
    return out


def path_tokens(text):
    toks = set()
    for blk in re.findall(r"```(?:bash|sh|console)?\n(.*?)```", text, re.S):
        toks |= shell_paths(blk)
    # 인라인 코드 스팬 — 루트 CLAUDE.md의 실행 명령이 여기 있고, 구 D-1은 이걸 안 봤다
    for span in re.findall(r"`([^`\n]+)`", text):
        if re.search(r"(^|\s)(cd|python3?|bash|ros2|test -[fdx]|source|\./)\s", span):
            toks |= shell_paths(span)
        elif "/" in span:
            toks |= set(re.findall(rf"((?:[\w.-]+/)+[\w.-]+\.(?:{EXT}))", span))
            toks |= set(re.findall(r"^((?:[\w.-]+/)+)$", span))
    for m in re.findall(r"@((?:[\w.-]+/)*[\w.-]+\.md)", text):
        toks.add(m)
    return toks


def da7():
    global TOPS
    TOPS = {d for d in os.listdir(ROOT) if os.path.isdir(rel(d))} | {
        f for f in os.listdir(ROOT) if os.path.isfile(rel(f))}
    for md in all_md():
        if any(md.startswith(p) for p in PRESERVED_ROOTS) and os.path.basename(md) != "CLAUDE.md":
            continue                        # D-14 원본 — 손대지 않는다
        txt = read(md)
        lines = txt.splitlines()
        bad = []
        for tok in sorted(path_tokens(txt)):
            head = tok.split("/")[0]
            if head not in TOPS:            # 저장소 루트 기준 경로만 검사
                continue
            if os.path.exists(rel(tok.rstrip("/"))):
                continue
            ctx = next((l for l in lines if tok in l), "")
            if any(k in ctx for k in FUTURE) or any(k in ctx for k in NEGATED):
                continue
            bad.append(tok)
        chk("DA-7", not bad, f"{md} — 언급 경로 실재", f"없는 경로: {bad}" if bad else "")


# ═══ DA-8 · 폐기 생성기 봉인 ═════════════════════════════════════════════════
RETIRED = ("sot_migrate.py", "sot_preserve.py", "sot_restructure.py")


def da8():
    for g in RETIRED:
        if os.path.exists(rel(g)):
            src = read(g)[:2000]
            guarded = "폐기" in src and ("sys.exit" in src or "raise SystemExit" in src)
            chk("DA-8", guarded, f"{g} — 저장소에 존재하면 폐기 가드 필수",
                "가드 없음: 실행하면 42개 CLAUDE.md를 되돌린다" if not guarded else "")
        else:
            chk("DA-8", True, f"{g} — 저장소에 없음")
    txt = read("sot_audit.py")
    m = re.search(r"ROOT_PY_ALLOW\s*=\s*\{([^}]*)\}", txt)
    allow = set(re.findall(r"[\"']([^\"']+)[\"']", m.group(1))) if m else set()
    leak = sorted(allow & set(RETIRED))
    chk("DA-8", not leak, "sot_audit.py ROOT_PY_ALLOW에 폐기 생성기 없음",
        f"{leak} ← 되살려 놔도 R9가 통과시킨다" if leak else "")
    for md in all_md():
        txt = read(md)
        for g in RETIRED:
            for line in txt.splitlines():
                if f"python3 {g}" in line or f"python {g}" in line:
                    ok = any(k in line for k in ("❌", "금지", "실행하지", "폐기"))
                    chk("DA-8", ok, f"{md} — 폐기 생성기 실행 예시에 금지 표시",
                        line.strip()[:90] if not ok else "")


# ═══ DA-9 · CLAUDE.md 규약 ═══════════════════════════════════════════════════
def da9():
    n = len(read("CLAUDE.md").splitlines())
    chk("DA-9", n <= 50, f"루트 CLAUDE.md ≤ 50줄 (현재 {n}줄)")
    for d in dirs_with_claude():
        p = "CLAUDE.md" if d == "." else f"{d}/CLAUDE.md"
        txt = read(p)
        body = [l for l in txt.splitlines() if l.strip() and not l.lstrip().startswith(("#", ">"))]
        chk("DA-9", len(body) >= 3, f"{p} — 헤더 외 실질 내용 존재")
        if d == ".":
            continue
        m = re.search(r"\*\*설계 정본\*\*:\s*`([^`]+)`", txt)
        chk("DA-9", bool(m), f"{p} — 설계 정본 헤더 존재")
        if m:
            chk("DA-9", m.group(1) == SPEC, f"{p} — 설계 정본 참조가 루트 기준 단일 규약 (D-3)",
                f"'{m.group(1)}' ≠ '{SPEC}'")
    # @참조 실재
    for md in all_md():
        bad = [t for t in re.findall(r"@((?:[\w.-]+/)*[\w.-]+\.md)", read(md))
               if not os.path.exists(rel(t))]
        chk("DA-9", not bad, f"{md} — @참조 실재", f"{bad}" if bad else "")


# ═══ DA-10 · architecture.md ↔ 실제 컴포넌트 (doc-map DM-5) ══════════════════
ARCH = "docs/architecture.md"


def da10():
    if not os.path.exists(rel(ARCH)):
        chk("DA-10", False, f"{ARCH} 부재")
        return
    txt = read(ARCH)
    for agent in ("manager_ai_agent", "worker_ai_agent"):
        kids = sorted(d.split("/")[-1] for d in dirs_with_claude()
                      if d.startswith(agent + "/") and "/" not in d[len(agent) + 1:])
        missing = [k for k in kids if k not in txt]
        chk("DA-10", not missing, f"{ARCH} ← {agent}/ 자식 {len(kids)}개 전부 등장",
            f"다이어그램·표 어디에도 없음: {missing}" if missing else "")
    for top in ("interfaces", "contracts", "tools"):
        chk("DA-10", top in txt, f"{ARCH} — 비컴포넌트 `{top}/` 언급")


DEVICES = [("DA-1", "MCP tool 집합 (코드가 정본)", None),
           ("DA-2", "부모 CLAUDE.md ↔ 실제 자식 디렉터리", da2),
           ("DA-3", "SOT §2 트리 ↔ sot_audit.py ↔ 파일시스템", da3),
           ("DA-4", "「N종」 리터럴 ↔ 정본 개수", None),
           ("DA-5", "식별자 무결성 (정의처 존재)", da5),
           ("DA-6", "원본 보존 무변경 (D-14)", da6),
           ("DA-7", "문서 언급 경로 실재", da7),
           ("DA-8", "폐기 생성기 봉인", da8),
           ("DA-9", "CLAUDE.md 규약 · @참조", da9),
           ("DA-10", "architecture.md ↔ 실제 컴포넌트", da10)]


def run(only=None):
    tools = None
    if only in (None, "DA-1", "DA-4"):
        tools = da1()
        if only == "DA-1":
            return
    for dev, _, fn in DEVICES:
        if dev == "DA-4":
            if only in (None, "DA-4"):
                da4(tools)
            continue
        if fn and only in (None, dev):
            fn()


def report():
    by = {}
    for dev, ok, msg, det in results:
        by.setdefault(dev, []).append((ok, msg, det))
    names = dict((d, n) for d, n, _ in DEVICES)
    nok = sum(1 for _, ok, _, _ in results if ok)
    print("=" * 78)
    print("  DOC AUDIT   기준: docs/doc-map.md §1 정본 소유권")
    print("=" * 78)
    for dev in sorted(by):
        items = by[dev]
        p = sum(1 for ok, _, _ in items if ok)
        print(f"\n[{'PASS' if p == len(items) else 'FAIL'}] {dev} {names.get(dev,'')}  ({p}/{len(items)})")
        for ok, msg, det in items:
            if not ok:
                print(f"    ✗ {msg}")
                if det:
                    print(f"      → {det}")
        if p == len(items):
            print(f"    ✓ {len(items)}개 항목 모두 통과")
    print("\n" + "-" * 78)
    print(f"  총 {nok}/{len(results)} 통과, {len(results) - nok} 위반")
    print("-" * 78)
    return len(results) - nok


if __name__ == "__main__":
    if "--list" in sys.argv:
        for d, n, _ in DEVICES:
            print(f"{d}  {n}")
        sys.exit(0)
    sel = next((a for a in sys.argv[1:] if a.startswith("DA-")), None)
    run(sel)
    sys.exit(1 if report() else 0)
