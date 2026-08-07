# MIGRATION — 기존 저장소 작업자를 위한 안내

> **옛 경로 ↔ 새 경로 대응표.** 기존 클론에서 경로를 못 찾을 때 여기서 찾는다.
>
> 구조 규범은 `SOT.md`, 설계는 `docs/spec/AI-Care_Unified_Architecture_Spec_v0.2.md`.
> 검증은 `python3 sot_audit.py` (R1~R10, 104항목).

## 한 줄 요약

**`limo-MCP/` 와 `limo-patrol-viz/` 는 내용이 하나도 바뀌지 않았다. 부모 디렉터리만 바뀌었다.**

| 옛 경로 (`27b0f30`) | 현재 경로 |
|---|---|
| `limo-MCP/` | `worker_ai_agent/limo-MCP/` |
| `limo-patrol-viz/` | `tools/limo-patrol-viz/` |

내부 파일·폴더 구조·파일명·코드 내용 **전부 그대로**다. 검증 결과:

```
limo-MCP        : 원본 157개 → 157개 | 누락 0 | 추가 0 | 내용상이 0
limo-patrol-viz : 원본  10개 →  10개 | 누락 0 | 추가 0 | 내용상이 0
```

blob 해시가 원본과 일치한다. 각 디렉터리에 `CLAUDE.md` 한 개만 추가됐다.

## 저장소가 옮겨졌다

이 개편은 **새 저장소 `github.com/kunghun-jeong/Ai-living-care`** 의 `master` 로 들어간다.

원본 저장소 `github.com/kunghun-jeong/-Ai-living-care` 의 `main` 은 최초 커밋 `27b0f30`
그대로이며 **건드리지 않았다.** 거기 걸린 `tree/main/limo-MCP` 링크도 그대로 산다.
다만 앞으로의 작업은 새 저장소에서 한다.

**기존 클론을 갖고 있다면:**

```bash
git remote set-url origin https://github.com/kunghun-jeong/Ai-living-care.git
git fetch origin
git checkout master        # 경로가 크게 바뀐다 — 위 대응표 참조
```

**진행 중인 로컬 변경이 있으면 먼저 커밋하거나 stash 한 뒤 받는다.**

## 실행 명령 — `cd` 한 줄만 바뀐다

```bash
# 기존
cd limo-MCP
ros2 launch Simulation/sim_bringup.launch.py
python3 Scenarios/send_goal.py 1.0 0.0

# 신규 — 디렉터리 위치만 다르고 그 안은 동일
cd worker_ai_agent/limo-MCP
ros2 launch Simulation/sim_bringup.launch.py
python3 Scenarios/send_goal.py 1.0 0.0
```

```bash
cd tools/limo-patrol-viz   # 기존: cd limo-patrol-viz
./run_coverage.sh
./run_patrol.sh
```

`Simulation/sim_bringup.launch.py`의 `this_dir`, `run_patrol.sh`의 `HERE`,
`patrol_viz.py`의 `MAP`, `MCP_server.py`의 `sys.path`, `Scenarios/*.py`의 `SERVER_PATH` —
**전부 디렉터리 내부 상대경로라 통째로 옮겨도 그대로 동작한다.** 손대지 않았다.

## 왜 이 위치인가

- **`worker_ai_agent/limo-MCP/`** — `limo-MCP`는 프레임워크 컴포넌트가 아니라
  **LIMO라는 특정 디바이스의 Worker 실현체**다. 다중 Worker로 확장하면 형제로 늘어난다:
  `worker_ai_agent/{limo-MCP, refrigerator, smart_tv}/`
- **`tools/limo-patrol-viz/`** — `SOT.md`가 `tools/`를 검증·시연 도구 자리로 정의한다.

`SOT.md` 결정 **D-14**로 기록했고, 감사 규칙 **R10**이 두 디렉터리의 존재와 내부 구조
(`Worker_functions/` · `Simulation/` · `Scenarios/` · `MCP_server/`)가 원형인지 검사한다.
**누가 이걸 다시 분해하면 `sot_audit.py`에서 잡힌다.**

## 새로 추가된 것 (기존 코드에 영향 없음)

전부 **추가**이고, 기존 파일을 고치지 않는다.

| 경로 | 내용 |
|---|---|
| `SOT.md` · `sot_audit.py` | 구조 규범 + 기계 검사 (R1~R10) |
| `manager_ai_agent/` | Manager 컴포넌트 5종 + `mcp_client/` — **규범만, 코드 없음** |
| `worker_ai_agent/{worker_ai_core,worker_ai_analyzer,…,perception,reasoning,action,mcp_server}/` | Worker 컴포넌트 — **규범만, 코드 없음** |
| `interfaces/if01…if08/` | 인터페이스 카탈로그 IF-1~IF-8 |
| `contracts/` | L1~L3 · Report 페이로드 스키마 자리 |
| `docs/` | spec · context · handoff · audit · slides |
| 각 디렉터리 `CLAUDE.md` | 설계·인터페이스·알려진 갭 |

### 규범과 구현의 분리

컴포넌트 디렉터리는 **코드를 두지 않는다.** 설계 규범과 알려진 갭만 갖고,
실제 구현이 어디 있는지 가리킨다.

| 규범 (읽을 곳) | 구현 (고칠 곳) |
|---|---|
| `worker_ai_agent/perception/CLAUDE.md` | `worker_ai_agent/limo-MCP/Worker_functions/Perceptions.py` |
| `worker_ai_agent/reasoning/CLAUDE.md` | `worker_ai_agent/limo-MCP/Worker_functions/Reasonings.py` |
| `worker_ai_agent/action/CLAUDE.md` | `worker_ai_agent/limo-MCP/Worker_functions/Actions.py` |
| `worker_ai_agent/mcp_server/CLAUDE.md` | `worker_ai_agent/limo-MCP/MCP_server/MCP_server.py` |

**구현을 고치기 전에 대응하는 규범 문서를 먼저 읽을 것.** G-1~G-6(크리티컬 갭)과
검증 실적의 한계가 거기 적혀 있다.

## 병합할 때

1. **팀원의 진행 중 브랜치를 먼저 넣는다.** 이 개편은 rename이 대부분이라
   충돌이 크지 않지만, 순서를 지키면 더 깔끔하다.
2. `python3 sot_audit.py` 가 104/104 통과하는지 확인.
3. `git log --follow <파일>` 로 이력이 이어지는지 확인 — 전부 `git mv`라 rename이 인식된다.
4. 외부 문서·발표자료·이슈에 걸린 `limo-MCP/...` 링크에 `worker_ai_agent/` 접두사를 붙인다.

## 개행(CRLF) 정규화만 먼저 가져가려면

`.gitattributes` 추가 + 개행 정규화 커밋(`58ddc79`)은 구조 개편과 **독립적**이며,
OneDrive/Windows 체크아웃에서 98개 파일이 계속 헛변경(5,839줄)으로 잡히던 문제를 없앤다.

```bash
git checkout master
git cherry-pick 58ddc79
```

**진행 중인 로컬 변경이 있는 팀원은 먼저 커밋하거나 stash한 뒤 받도록 공지할 것.**
