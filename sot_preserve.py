#!/usr/bin/env python3
"""limo-MCP / limo-patrol-viz 를 원본 그대로 복원해 적절한 위치에 배치한다.

    python3 sot_preserve.py restore   # 원본 복원 + 배치 + 분해본 격리
    python3 sot_preserve.py docs      # SOT.md / sot_audit.py / CLAUDE.md 갱신

`restructure/sot-v0.2` 브랜치에서 실행. main(27b0f30)은 건드리지 않는다.
"""
import os
import subprocess
import sys

R = os.path.dirname(os.path.abspath(__file__))
BASE = "27b0f30"          # 원본이 온전한 최초 커밋
WA = "worker_ai_agent"
TRASH = "_to_delete/dissolved"


def clr():
    for f in (".git/index.lock", ".git/HEAD.lock", ".git/objects/maintenance.lock"):
        p = os.path.join(R, f)
        if os.path.exists(p):
            os.makedirs(os.path.join(R, "_to_delete/gitlocks"), exist_ok=True)
            try:
                os.replace(p, os.path.join(R, "_to_delete/gitlocks",
                                           os.path.basename(f) + f".{os.getpid()}"))
            except OSError:
                pass


def sh(cmd):
    r = subprocess.run(cmd, shell=True, cwd=R, capture_output=True, text=True)
    clr()
    return r


def trash(rel):
    s = os.path.join(R, rel)
    if not os.path.exists(s):
        return False
    t = os.path.join(R, TRASH)
    os.makedirs(t, exist_ok=True)
    dst = os.path.join(t, rel.replace("/", "__"))
    if os.path.exists(dst):
        dst += f".{os.getpid()}"
    os.replace(s, dst)
    print(f"  격리    {rel}")
    return True


def stage_restore():
    print(f"[restore] {BASE} 에서 원본 복원")
    clr()
    # 1) 분해본을 먼저 격리 (경로 충돌 방지)
    for rel in [f"{WA}/perception/Perceptions.py",
                f"{WA}/reasoning/Reasonings.py",
                f"{WA}/action/Actions.py",
                f"{WA}/mcp_server/MCP_server.py",
                "requirements.txt",
                "sim", "tools/scenarios", "tools/patrol_viz"]:
        trash(rel)
    sh("git add -A")

    # 2) 원본 트리 복원
    r = sh(f'git checkout {BASE} -- limo-MCP limo-patrol-viz')
    if r.returncode != 0:
        return print(f"  ! 복원 실패: {r.stderr.strip()}")
    n = len(sh("git ls-files limo-MCP limo-patrol-viz").stdout.split())
    print(f"  복원    limo-MCP/ + limo-patrol-viz/  ({n} 파일)")

    # 3) 적절한 위치로 통째 이동
    for src, dst in [("limo-MCP", f"{WA}/limo-MCP"),
                     ("limo-patrol-viz", "tools/limo-patrol-viz")]:
        if os.path.exists(os.path.join(R, dst)):
            print(f"  - skip {dst} (이미 존재)")
            continue
        os.makedirs(os.path.dirname(os.path.join(R, dst)), exist_ok=True)
        r = sh(f'git mv "{src}" "{dst}"')
        print(f"  {'git mv ' if r.returncode == 0 else 'mv     '} {src} -> {dst}")
        if r.returncode != 0:
            os.replace(os.path.join(R, src), os.path.join(R, dst))
    sh("git add -A")
    print("  * 원본 파일 내용은 한 글자도 바뀌지 않았다 (경로 참조 수정분도 원복).")


# ─────────────────────────────────────────────────────────────────────────────
SPEC = "docs/spec/AI-Care_Unified_Architecture_Spec_v0.2.md"
HDR = ("> **구조 정본**: `SOT.md` · **설계 정본**: `{spec}`\n"
       "> **상위**: {parent} · **Phase**: {phase} · **구현 상태**: {state}\n")

CLAUDE = {}

CLAUDE[f"{WA}/limo-MCP"] = f"""# limo-MCP — LIMO Worker 구현체 (원본 보존)

{HDR.format(spec="../../" + SPEC, parent=f"`{WA}/`", phase="0", state="동작 — 원본 그대로 보존")}
> **⚠️ 이 디렉터리는 원본을 그대로 보존한다 (D-14).** 내부 구조·파일명·경로를 바꾸지 않는다.
> `github.com/kunghun-jeong/-Ai-living-care` 의 `main/limo-MCP` 와 **내용이 동일**하다.

## 왜 여기 있는가

`limo-MCP`는 프레임워크 컴포넌트가 아니라 **LIMO라는 특정 디바이스의 Worker 실현체**다.
Worker AI Agent의 구현이므로 `{WA}/` 안에 둔다. 다중 Worker로 확장하면 형제로 늘어난다:

```
{WA}/
  limo-MCP/          ← LIMO (현재 유일)
  refrigerator/      ← 향후
  smart_tv/          ← 향후
```

## 내부 구조 (원본)

| 경로 | SOT 컴포넌트 대응 |
|---|---|
| `Worker_functions/Perceptions.py` | Perception Function (PF) → `../perception/` |
| `Worker_functions/Reasonings.py` | Reasoning Function (RF) → `../reasoning/` |
| `Worker_functions/Actions.py` | Action Function (AF) → `../action/` |
| `MCP_server/MCP_server.py` | A2A Server + Agent Executor → `../mcp_server/` |
| `Simulation/` | 시뮬레이션 (비컴포넌트) |
| `Scenarios/` | 검증 클라이언트 (비컴포넌트) |
| `requirements.txt` | 의존성 |
| `SESSION_HANDOFF.md` | 개발 기록 |

각 컴포넌트 디렉터리(`../perception/` 등)의 `CLAUDE.md`에 **설계 규범과 알려진 갭**이 있다.
**구현을 고칠 때는 그 문서를 먼저 읽을 것.**

## 실행 (원본 그대로)

```bash
source /opt/ros/jazzy/setup.bash
./Simulation/fetch_meshes.sh                      # 최초 1회, AWS 메시 ~55MB
ros2 launch Simulation/sim_bringup.launch.py
python3 Scenarios/send_goal.py 1.0 0.0            # 이 디렉터리에서 실행
python3 Scenarios/capture_and_detect.py out.jpg
```

## 알려진 크리티컬 갭

| ID | 갭 | 파일 |
|---|---|---|
| **G-1** | 프레임 pinning 부재 — 최신 1장만 캐시, 과거 `frame_id` 조회 불가 | `Worker_functions/Perceptions.py` |
| **G-2** | `pose`가 항상 `None` | 〃 |
| **G-3** | person-scan API 5종이 MCP tool로 미노출 | `MCP_server/MCP_server.py` |
| **G-4** | `look_around` / patrol 미구현 | `Worker_functions/Actions.py` |
| **G-5** | stale 콜백 가드 없음 | 〃 |

**G-1과 G-2는 시나리오 1의 핵심 경로를 끊는다.** 상세는 `../perception/CLAUDE.md`.

## 주의

- **`Simulation/`의 RTF가 0.04~0.06**이다. 6.3분 시나리오가 벽시계 2시간. 반복 검증은
  `tools/limo-patrol-viz/`로 하고 여기는 최종 확인용으로 쓴다 (U-14).
- **small_house 카메라는 미검증**이다. 검증 실적은 `turtlebot3_world` 기준 (작업 0-0).
- 개발 경위와 함정은 `SESSION_HANDOFF.md`에 누적 기록돼 있다. 새로 합류하면 그것부터 읽을 것.
"""

CLAUDE["tools/limo-patrol-viz"] = f"""# limo-patrol-viz — 순찰 로직 검증 도구 (원본 보존)

{HDR.format(spec="../../" + SPEC, parent="`tools/`", phase="0", state="동작 — 원본 그대로 보존")}
> **⚠️ 이 디렉터리는 원본을 그대로 보존한다 (D-14).** 내부 구조·파일명·경로를 바꾸지 않는다.
> `github.com/kunghun-jeong/-Ai-living-care` 의 `main/limo-patrol-viz` 와 **내용이 동일**하다.

Gazebo·Nav2·YOLO **없이** 순찰 로직을 검증·시연한다. AWS small_house 맵 위에서 A*로 경로를 뽑고
운동학만 적분해 로봇을 움직이며 카메라 1인칭 뷰까지 합성한다.

```bash
./run_coverage.sh    # GUI 없이 커버리지 수치 + patrol_sim.png
./run_patrol.sh      # RViz2 순찰 애니메이션 + 카메라 스트리밍
```

## 왜 존재하는가

Gazebo RTF가 0.04~0.06이라 6.3분 시나리오가 벽시계 2시간이 된다.
**반복 검증이 불가능해 만든 대체 수단**이며, 이 도구의 존재 자체가 U-14 리스크 신호다.

## 결과: 경로점 7개 · 375초 · 스캔 376회 · 주행 50 m · **커버리지 93.6%** · 사각지대 0

**⚠️ 이 수치는 "실측"이 아니라 기하 시뮬레이션 결과다.** 논문·제안서에 반드시 이렇게 표기할 것:

- 물리(바퀴 미끄러짐·충돌)와 Nav2 실제 재계획 없음 → **실소요는 20~30% 더 걸릴 것**
- **YOLO를 돌리지 않음** — "FOV 안 + 시야 확보 = 발견"으로 처리
- `CAM_RANGE = 4.0 m`는 **미측정 가정**이며 커버리지가 여기에 가장 민감
- **수직 FOV 미반영 (U-13)** — 2D 가정이라 4 m 거리에서 **바닥에 누운 사람이 화면 아래로 벗어나는 경우**를
  못 잡는다. 쓰러진 상황이 리빙케어에서 가장 위험한데 바로 그 부분이 미검증이다

## 자산 메모

`limo/limo.urdf` — WeGo `limo_gazebo`(ROS1 xacro)에서 변환한 **실제 LIMO 모델**.
Jazzy 파싱은 통과한다. **Gazebo 플러그인 3블록만 Harmonic 문법으로 재작성하면 시뮬에 투입 가능**하다.
"""

CLAUDE["tools"] = f"""# tools — 검증·시연 도구

{HDR.format(spec=SPEC, parent="저장소 루트", phase="—", state="—")}
**컴포넌트가 아니다.** 비즈니스 로직을 두지 않는다 (P-3).

| 경로 | 용도 | 비고 |
|---|---|---|
| `limo-patrol-viz/` | Gazebo·Nav2·YOLO 없이 순찰 로직 검증 | **원본 보존 (D-14)** |

> **MCP 왕복 검증 클라이언트는 여기 없다.** 원본 보존 원칙에 따라
> `{WA}/limo-MCP/Scenarios/` 안에 그대로 있다.
> ```bash
> cd {WA}/limo-MCP && python3 Scenarios/send_goal.py 1.0 0.0
> ```
"""

CLAUDE[f"{WA}"] = f"""# Worker AI Agent

{HDR.format(spec="../" + SPEC, parent="저장소 루트", phase="0", state="구현체 동작 — 프레임워크 계층 미착수")}
Manager가 만든 **고수준 정책(L2)** 을 받아 디바이스별 **저수준 정책(L3)** 으로 번역하고,
실제로 수행한 뒤 결과를 Report로 되돌린다.

## 두 층으로 구성된다

**① 프레임워크 컴포넌트** — SOT가 정의하는 규범 계층. 설계·인터페이스·갭이 각 `CLAUDE.md`에 있다.

| 디렉터리 | 정규화 명칭 | 상태 |
|---|---|---|
| `worker_ai_core/` | Worker AI Core (WAC) | 미착수 |
| `worker_ai_analyzer/` | Worker AI Analyzer (WAA) | 미착수 |
| `worker_ai_management_system/` | Worker AI Management System (WAMS) | 미착수 |
| `perception/` | Perception Function (PF) | 규범 — 구현은 ② |
| `reasoning/` | Reasoning Function (RF) | 규범 — 구현은 ② |
| `action/` | Action Function (AF) | 규범 — 구현은 ② |
| `mcp_server/` | A2A Server + Agent Executor | 규범 — 구현은 ② |

**② Worker 구현체** — 디바이스별 실현체. **원본 보존 (D-14).**

| 디렉터리 | 디바이스 | 상태 |
|---|---|---|
| `limo-MCP/` | LIMO (현재 turtlebot3 waffle로 시뮬) | **동작** |

다중 Worker로 확장하면 `refrigerator/`, `smart_tv/`가 형제로 늘어난다.

> **왜 나누는가**: 프레임워크는 디바이스와 무관해야 하고(P-2), 구현체는 팀이 이미 돌리고 있는
> 원본이라 손대지 않아야 한다. 규범은 ①에, 코드는 ②에 둔다.
> **컴포넌트 CLAUDE.md가 규범이고, 그 구현이 어디 있는지도 거기 적혀 있다.**

## 인터페이스

**IF-4**(↔MAC, `mcp_server/`) · **IF-5**(→PF/RF/AF) · **IF-6**(←PF/RF/AF) · IF-3(↔WAMS) · IF-7(↔MAMS, P2)

## 주의

**`ReasoningModule`은 ROS2에 의존하지 않는다.** 백엔드를 생성자로 주입받고 미주입 시 no-op으로 동작해
로봇 없이 단독 테스트가 가능하다. **이 저장소에서 가장 잘 분리된 설계이므로 훼손하지 말 것.**
"""

IMPL_NOTE = """
## 구현 위치 (D-14)

원본 보존 원칙에 따라 실제 코드는 **`{impl}`** 에 있다.
이 디렉터리는 **규범(설계·인터페이스·갭)** 을 보유하고, 코드는 두지 않는다.

**구현을 고치기 전에 이 문서의 갭·주의사항을 먼저 읽을 것.**
"""


def stage_docs():
    print("[docs] SOT.md / sot_audit.py / CLAUDE.md 갱신")

    for path, text in CLAUDE.items():
        d = os.path.join(R, path)
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "CLAUDE.md"), "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        print(f"  ~ {path}/CLAUDE.md")

    # 컴포넌트 CLAUDE.md 에 구현 위치 주석 삽입
    impls = {
        f"{WA}/perception": f"{WA}/limo-MCP/Worker_functions/Perceptions.py",
        f"{WA}/reasoning":  f"{WA}/limo-MCP/Worker_functions/Reasonings.py",
        f"{WA}/action":     f"{WA}/limo-MCP/Worker_functions/Actions.py",
        f"{WA}/mcp_server": f"{WA}/limo-MCP/MCP_server/MCP_server.py",
    }
    for d, impl in impls.items():
        p = os.path.join(R, d, "CLAUDE.md")
        if not os.path.exists(p):
            continue
        s = open(p, encoding="utf-8").read()
        if "## 구현 위치 (D-14)" in s:
            continue
        i = s.find("\n## ")
        s = s[:i] + "\n" + IMPL_NOTE.format(impl=impl) + s[i:]
        open(p, "w", encoding="utf-8", newline="\n").write(s)
        print(f"  + {d}/CLAUDE.md : 구현 위치 주석")

    # sot_audit.py — 코드 위치 규칙(R5)과 비컴포넌트 목록 갱신
    p = os.path.join(R, "sot_audit.py")
    s = open(p, encoding="utf-8").read()
    old_code = s[s.find("CODE = {"):s.find("}", s.find("CODE = {")) + 1]
    new_code = f'''CODE = {{
    "{WA}/limo-MCP/Worker_functions/Perceptions.py": "PF 구현 (원본 보존)",
    "{WA}/limo-MCP/Worker_functions/Reasonings.py":  "RF 구현 (원본 보존)",
    "{WA}/limo-MCP/Worker_functions/Actions.py":     "AF 구현 (원본 보존)",
    "{WA}/limo-MCP/MCP_server/MCP_server.py":        "A2A Server / MCP 종단점 (원본 보존)",
    "{WA}/limo-MCP/Simulation/sim_bringup.launch.py": "시뮬 브링업 (원본 보존)",
    "{WA}/limo-MCP/Scenarios/send_goal.py":          "MCP 왕복 클라이언트 (원본 보존)",
    "{WA}/limo-MCP/requirements.txt":                "의존성 (원본 보존)",
    "tools/limo-patrol-viz/patrol_viz.py":           "순찰 검증 도구 (원본 보존)",
    "SOT.md":                                        "구조 정본",
    "CLAUDE.md":                                     "루트 진입점",
}}'''
    s = s.replace(old_code, new_code)
    s = s.replace('NON_COMPONENT = ["docs", "sim", "tools", "contracts"]',
                  'NON_COMPONENT = ["docs", "tools", "contracts"]')
    s = s.replace('"manager", "worker", "a2a",',
                  '"manager", "worker", "a2a", "sim", "tools/scenarios", "tools/patrol_viz",')
    # R5 에 원본 보존 검사 추가
    s = s.replace('ROOT_PY_ALLOW = {"sot_audit.py", "sot_migrate.py"}',
                  'ROOT_PY_ALLOW = {"sot_audit.py", "sot_migrate.py", "sot_preserve.py"}\n\n'
                  '# D-14 원본 보존 대상 — 내부 구조를 바꾸지 않는다\n'
                  f'PRESERVED = ["{WA}/limo-MCP", "tools/limo-patrol-viz"]')
    s = s.replace('    # R9 떠도는 .py',
                  '    # R10 원본 보존\n'
                  '    for d in PRESERVED:\n'
                  '        chk("R10", isdir(d), f"원본 보존: {d}/")\n'
                  f'    chk("R10", exists("{WA}/limo-MCP/Worker_functions") '
                  f'and exists("{WA}/limo-MCP/Simulation"),\n'
                  '        "limo-MCP 내부 구조 원형 유지 (Worker_functions/ · Simulation/)")\n\n'
                  '    # R9 떠도는 .py')
    open(p, "w", encoding="utf-8", newline="\n").write(s)
    print("  ~ sot_audit.py : R5 경로 갱신 + R10(원본 보존) 신설")

    # SOT.md
    p = os.path.join(R, "SOT.md")
    s = open(p, encoding="utf-8").read()
    if "**D-14**" not in s:
        s = s.replace(
            "| **D-13** |",
            f"""| **D-14** | **`limo-MCP/` 와 `limo-patrol-viz/` 는 원본을 그대로 보존한다.** 각각 `{WA}/limo-MCP/`, `tools/limo-patrol-viz/` 에 통째로 배치하고 내부를 분해하지 않는다 | 기존 저장소 작업자가 영향 없이 계속 작업하게 하기 위함. 컴포넌트 디렉터리는 **규범**을 보유하고 코드는 구현체에 둔다 — 규범과 구현의 분리 |
| **D-13** |""")
        s = s.replace(
            "| **R9** |",
            "| **R10** | D-14 원본 보존 대상이 존재하고 내부 구조가 원형인지 |\n| **R9** |")
        s = s.replace("├── sim/                                시뮬레이션 (비컴포넌트)\n", "")
        s = s.replace("""├── tools/                              검증·시연 도구 (비컴포넌트)
│   ├── patrol_viz/
│   └── scenarios/""",
                      """├── tools/                              검증·시연 도구 (비컴포넌트)
│   └── limo-patrol-viz/                ★ 원본 보존 (D-14)""")
        s = s.replace("""│   ├── action/                     AF
│   └── mcp_server/""",
                      """│   ├── action/                     AF
│   ├── mcp_server/                 A2A Server + Agent Executor — IF-4 Worker 측 종단점
│   └── limo-MCP/                   ★ Worker 구현체, 원본 보존 (D-14)
│                                     Worker_functions/ · MCP_server/ · Simulation/ · Scenarios/""")
        s = s.replace("""│   └── mcp_server/                     A2A Server + Agent Executor — IF-4 Worker 측 종단점
""", "")
        open(p, "w", encoding="utf-8", newline="\n").write(s)
        print("  ~ SOT.md : D-14 + R10 추가, 구조도 갱신")
    else:
        print("  - SOT.md 이미 갱신됨")


if __name__ == "__main__":
    st = {"restore": stage_restore, "docs": stage_docs}
    a = sys.argv[1] if len(sys.argv) > 1 else ""
    if a not in st:
        print(__doc__)
        sys.exit(1)
    st[a]()
