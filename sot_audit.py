#!/usr/bin/env python3
"""SOT.md 규범에 대한 저장소 구조 감사.

    python3 sot_audit.py            # 검사
    python3 sot_audit.py --plan     # 위반 해소용 git mv 계획 출력

저장소 루트에서 실행. SOT.md §5의 R1~R9를 검사한다.
"""
import os
import re
import sys

R = os.path.dirname(os.path.abspath(__file__))
SPEC = "docs/spec/AI-Care_Unified_Architecture_Spec_v0.2.md"

MANAGER = "manager_ai_agent"
WORKER = "worker_ai_agent"

# ── SOT §2.1 컴포넌트 (정식명칭, 디렉터리, 약칭) ──────────────────────────────
COMPONENTS = [
    ("Manager AI Core",               f"{MANAGER}/manager_ai_core",              "MAC"),
    ("Manager AI Analyzer",           f"{MANAGER}/manager_ai_analyzer",          "MAA"),
    ("Manager AI Management System",  f"{MANAGER}/manager_ai_management_system", "MAMS"),
    ("Knowledge Graph",               f"{MANAGER}/knowledge_graph",              "KG"),
    ("Intent Audit Database",         f"{MANAGER}/intent_audit_database",        "IAD"),
    ("Worker AI Core",                f"{WORKER}/worker_ai_core",                "WAC"),
    ("Worker AI Analyzer",            f"{WORKER}/worker_ai_analyzer",            "WAA"),
    ("Worker AI Management System",   f"{WORKER}/worker_ai_management_system",   "WAMS"),
    ("Perception Function",           f"{WORKER}/perception",                    "PF"),
    ("Reasoning Function",            f"{WORKER}/reasoning",                     "RF"),
    ("Action Function",               f"{WORKER}/action",                        "AF"),
]

CHILDREN = [
    f"{MANAGER}/manager_ai_core/intent_extraction",
    f"{MANAGER}/manager_ai_core/kg_mapping",
    f"{MANAGER}/manager_ai_core/query_composing",
    f"{MANAGER}/manager_ai_core/policy_generation",
    f"{MANAGER}/manager_ai_core/session_key_manager",
    f"{MANAGER}/manager_ai_analyzer/report_interpreter",
    f"{MANAGER}/manager_ai_analyzer/assurance_loop",
    f"{MANAGER}/manager_ai_management_system/agent_registry",
    f"{MANAGER}/manager_ai_management_system/worker_selector",
    f"{MANAGER}/mcp_client",
    f"{WORKER}/worker_ai_core/policy_translator",
    f"{WORKER}/worker_ai_core/session_key_handler",
    f"{WORKER}/worker_ai_management_system/agent_card",
    f"{WORKER}/mcp_server",
]

INTERFACES = [
    ("IF-1", "interfaces/if01_database",           "Database Interface"),
    ("IF-2", "interfaces/if02_analytics",          "Analytics Interface"),
    ("IF-3", "interfaces/if03_registration",       "Registration Interface"),
    ("IF-4", "interfaces/if04_secure_a2a_channel", "Secure A2A Channel"),
    ("IF-5", "interfaces/if05_sf_facing",          "SF-Facing Interface"),
    ("IF-6", "interfaces/if06_agent_monitoring",   "Agent Monitoring Interface"),
    ("IF-7", "interfaces/if07_ams_facing",         "AMS-Facing Interface"),
    ("IF-8", "interfaces/if08_analyzer_facing",    "Analyzer-Facing Interface"),
]

NON_COMPONENT = ["docs", "sim", "tools", "contracts"]

# 금지 별칭 (SOT §5 R2) : 존재하면 위반
FORBIDDEN = [
    "manager", "worker", "a2a",
    f"{WORKER}/service_functions",
    f"{MANAGER}/intent_audit_db",
    f"{MANAGER}/core", f"{MANAGER}/analyzer", f"{MANAGER}/mgmt_system",
    f"{WORKER}/core", f"{WORKER}/analyzer", f"{WORKER}/mgmt_system",
]

# SOT가 정한 코드 위치 (R5)
CODE = {
    f"{WORKER}/perception/Perceptions.py":  "PF 구현",
    f"{WORKER}/reasoning/Reasonings.py":    "RF 구현",
    f"{WORKER}/action/Actions.py":          "AF 구현",
    f"{WORKER}/mcp_server/MCP_server.py":   "A2A Server / MCP 종단점",
    "sim/sim_bringup.launch.py":            "시뮬 브링업",
    "tools/scenarios/send_goal.py":         "MCP 왕복 클라이언트",
    "tools/patrol_viz/patrol_viz.py":       "순찰 검증 도구",
    "requirements.txt":                     "의존성",
    "SOT.md":                               "구조 정본",
    "CLAUDE.md":                            "루트 진입점",
}

# SOT 관리 스크립트는 루트에 두는 것이 규범이다 (SOT.md §5 R9)
ROOT_PY_ALLOW = {"sot_audit.py", "sot_migrate.py"}

# 현재 구조 → SOT (R2/R5 위반 해소용 이동 계획)
MIGRATION = [
    ("manager/core",                        f"{MANAGER}/manager_ai_core"),
    ("manager/analyzer",                    f"{MANAGER}/manager_ai_analyzer"),
    ("manager/mgmt_system",                 f"{MANAGER}/manager_ai_management_system"),
    ("manager/knowledge_graph",             f"{MANAGER}/knowledge_graph"),
    ("manager/intent_audit_db",             f"{MANAGER}/intent_audit_database"),
    ("manager/CLAUDE.md",                   f"{MANAGER}/CLAUDE.md"),
    ("worker/core",                         f"{WORKER}/worker_ai_core"),
    ("worker/analyzer",                     f"{WORKER}/worker_ai_analyzer"),
    ("worker/mgmt_system",                  f"{WORKER}/worker_ai_management_system"),
    ("worker/service_functions/perception",  f"{WORKER}/perception"),
    ("worker/service_functions/reasoning",   f"{WORKER}/reasoning"),
    ("worker/service_functions/action",      f"{WORKER}/action"),
    ("worker/CLAUDE.md",                    f"{WORKER}/CLAUDE.md"),
    ("a2a/server",                          f"{WORKER}/mcp_server"),
    ("a2a/client",                          f"{MANAGER}/mcp_client"),
    ("a2a/binding",                         "interfaces/if04_secure_a2a_channel"),
]

results = []


def chk(rule, ok, msg):
    results.append((rule, ok, msg))


def exists(p):
    return os.path.exists(os.path.join(R, p))


def isdir(p):
    return os.path.isdir(os.path.join(R, p))


def audit():
    # R1 컴포넌트 디렉터리
    for name, d, ab in COMPONENTS:
        chk("R1", isdir(d), f"{name} ({ab}) → {d}/")
    for d in CHILDREN:
        chk("R1", isdir(d), f"child → {d}/")

    # R2 금지 별칭
    for d in FORBIDDEN:
        chk("R2", not exists(d), f"금지 경로 부재: {d}/")

    # R3 인터페이스
    for ifid, d, name in INTERFACES:
        chk("R3", isdir(d), f"{ifid} {name} → {d}/")

    # R4 CLAUDE.md
    for _, d, _ in COMPONENTS:
        chk("R4", exists(f"{d}/CLAUDE.md"), f"{d}/CLAUDE.md")
    for d in CHILDREN:
        chk("R4", exists(f"{d}/CLAUDE.md"), f"{d}/CLAUDE.md")
    for _, d, _ in INTERFACES:
        chk("R4", exists(f"{d}/CLAUDE.md"), f"{d}/CLAUDE.md")
    for d in (MANAGER, WORKER, "interfaces"):
        chk("R4", exists(f"{d}/CLAUDE.md"), f"{d}/CLAUDE.md")

    # R5 코드 위치
    for p, what in CODE.items():
        chk("R5", exists(p), f"{what} → {p}")

    # R6 비컴포넌트
    for d in NON_COMPONENT:
        chk("R6", isdir(d), f"{d}/")

    # R7 경로 참조 무결성
    p = os.path.join(R, WORKER, "mcp_server", "MCP_server.py")
    if os.path.exists(p):
        s = open(p, encoding="utf-8").read()
        m = re.findall(r'os\.path\.join\(_ROOT,\s*([^)]+)\)', s)
        base = os.path.abspath(os.path.join(os.path.dirname(p), "..", ".."))
        hits = [sf for sf in ("perception", "reasoning", "action")
                if os.path.isdir(os.path.join(base, WORKER, sf))]
        chk("R7", len(hits) == 3 and f'"{WORKER}"' in s.replace("'", '"'),
            f"MCP_server.py sys.path → {WORKER}/{{perception,reasoning,action}}")
    else:
        chk("R7", False, "MCP_server.py 부재로 sys.path 검사 불가")

    for n in ("send_goal.py", "capture_and_detect.py"):
        p = os.path.join(R, "tools", "scenarios", n)
        if not os.path.exists(p):
            chk("R7", False, f"tools/scenarios/{n} 부재")
            continue
        s = open(p, encoding="utf-8").read()
        m = re.search(r'SERVER_PATH\s*=\s*os\.path\.join\((.+?)\)\s*$', s, re.M)
        target = None
        if m:
            parts = [x.strip().strip('"\'') for x in m.group(1).split(",")]
            parts = [x for x in parts if x != "os.path.dirname(__file__)"]
            target = os.path.normpath(os.path.join(os.path.dirname(p), *parts))
        chk("R7", bool(target) and os.path.isfile(target),
            f"tools/scenarios/{n} SERVER_PATH → {os.path.relpath(target, R) if target else '?'}")

    # R8 CLAUDE.md가 SOT 참조
    missing = []
    for dirpath, dirnames, filenames in os.walk(R):
        dirnames[:] = [d for d in dirnames if d not in (".git", "_to_delete", "node_modules")]
        if "CLAUDE.md" in filenames:
            rel = os.path.relpath(dirpath, R)
            s = open(os.path.join(dirpath, "CLAUDE.md"), encoding="utf-8").read()
            if "SOT.md" not in s:
                missing.append(rel if rel != "." else "(root)")
    chk("R8", not missing,
        "모든 CLAUDE.md가 SOT.md 참조" + (f" — 미참조 {len(missing)}개: {', '.join(missing[:6])}…" if missing else ""))

    # R9 떠도는 .py
    stray = [f for f in os.listdir(R)
             if f.endswith(".py") and f not in ROOT_PY_ALLOW and os.path.isfile(os.path.join(R, f))]
    chk("R9", not stray, "루트 떠돌이 .py 부재" + (f" — {stray}" if stray else ""))


def report():
    by = {}
    for rule, ok, msg in results:
        by.setdefault(rule, []).append((ok, msg))
    total_ok = sum(1 for _, ok, _ in results if ok)
    print("=" * 74)
    print(f"  SOT AUDIT   기준: SOT.md §5   저장소: {os.path.basename(R)}")
    print("=" * 74)
    for rule in sorted(by):
        items = by[rule]
        nok = sum(1 for ok, _ in items if ok)
        head = "PASS" if nok == len(items) else "FAIL"
        print(f"\n[{head}] {rule}  ({nok}/{len(items)})")
        for ok, msg in items:
            if not ok:
                print(f"    ✗ {msg}")
        if nok == len(items):
            print(f"    ✓ {len(items)}개 항목 모두 통과")
    print("\n" + "-" * 74)
    print(f"  총 {total_ok}/{len(results)} 통과, {len(results) - total_ok} 위반")
    print("-" * 74)
    return len(results) - total_ok


def plan():
    print("# SOT 위반 해소 이동 계획 (git mv)\n")
    n = 0
    for src, dst in MIGRATION:
        if exists(src) and not exists(dst):
            print(f'mkdir -p "$(dirname {dst})" && git mv "{src}" "{dst}"')
            n += 1
    print(f"\n# 신규 생성 필요")
    for ifid, d, name in INTERFACES:
        if not isdir(d):
            print(f'mkdir -p {d}   # {ifid} {name}')
            n += 1
    print(f"\n# 이동 {n}건")


if __name__ == "__main__":
    if "--plan" in sys.argv:
        plan()
    else:
        audit()
        sys.exit(1 if report() else 0)
