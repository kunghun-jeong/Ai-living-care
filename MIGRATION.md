# MIGRATION — 기존 경로가 어디로 갔는가

> **이 문서는 `restructure/sot-v0.2` 브랜치에만 있다. `main`은 변경되지 않았다.**
>
> 구조 개편의 근거와 규범은 `SOT.md`, 설계는 `docs/spec/AI-Care_Unified_Architecture_Spec_v0.2.md`.
> 검증은 `python3 sot_audit.py` (R1~R9, 99항목).

## main 은 그대로다

`origin/main`은 최초 커밋 `27b0f30`에서 **한 발짝도 움직이지 않았다.**
기존 저장소 작업자는 지금까지 하던 대로 `main`에서 계속 작업하면 되고, 아무 영향도 받지 않는다.

이 개편은 `restructure/sot-v0.2` 브랜치에 격리돼 있다. **병합 시점은 팀이 정한다.**

## 경로 대응표

### limo-MCP/

| 기존 (`main`) | 신규 (`restructure/sot-v0.2`) | 이유 |
|---|---|---|
| `limo-MCP/Worker_functions/Perceptions.py` | `worker_ai_agent/perception/Perceptions.py` | Perception Function (PF) |
| `limo-MCP/Worker_functions/Reasonings.py` | `worker_ai_agent/reasoning/Reasonings.py` | Reasoning Function (RF) |
| `limo-MCP/Worker_functions/Actions.py` | `worker_ai_agent/action/Actions.py` | Action Function (AF) |
| `limo-MCP/MCP_server/MCP_server.py` | `worker_ai_agent/mcp_server/MCP_server.py` | A2A Server + Agent Executor (IF-4 Worker 측) |
| `limo-MCP/Simulation/` | `sim/` | 비컴포넌트 (시뮬레이션) |
| `limo-MCP/Simulation/aws_small_house/` | `sim/aws_small_house/` | 〃 |
| `limo-MCP/Scenarios/` | `tools/scenarios/` | 비컴포넌트 (검증 도구) |
| `limo-MCP/requirements.txt` | `requirements.txt` | 저장소 루트로 |
| `limo-MCP/SESSION_HANDOFF.md` | `docs/handoff/limo-MCP_SESSION_HANDOFF.md` | 문서 정리 |

### limo-patrol-viz/

| 기존 | 신규 |
|---|---|
| `limo-patrol-viz/` 전체 | `tools/patrol_viz/` |
| `limo-patrol-viz/limo/limo.urdf` | `tools/patrol_viz/limo/limo.urdf` |
| `limo-patrol-viz/maps/` | `tools/patrol_viz/maps/` |

`limo-MCP/`와 `limo-patrol-viz/`는 **디렉터리 이름이 아니라 역할로 재배치**됐다.
`limo-MCP`는 "Worker AI Agent 구현 + 시뮬 + 도구"가 한 폴더에 섞여 있던 상태였고,
개편 후에는 컴포넌트(`worker_ai_agent/`)와 비컴포넌트(`sim/`, `tools/`)가 분리됐다.

## 실행 명령 변경

| 기존 | 신규 |
|---|---|
| `ros2 launch limo-MCP/Simulation/sim_bringup.launch.py` | `ros2 launch sim/sim_bringup.launch.py` |
| `cd limo-MCP && python3 Scenarios/send_goal.py 1.0 0.0` | `python3 tools/scenarios/send_goal.py 1.0 0.0` |
| `cd limo-MCP && python3 Scenarios/capture_and_detect.py out.jpg` | `python3 tools/scenarios/capture_and_detect.py out.jpg` |
| `cd limo-patrol-viz && ./run_patrol.sh` | `cd tools/patrol_viz && ./run_patrol.sh` |
| `pip install -r limo-MCP/requirements.txt` | `pip install -r requirements.txt` |

## 코드에서 바뀐 것

파일 내용은 **경로 참조 2곳 외에 손대지 않았다.**

- `MCP_server.py` — `sys.path`가 `worker_ai_agent/{perception,reasoning,action}` 세 곳을 가리키도록 변경.
  **모듈명(`Perceptions`/`Reasonings`/`Actions`)은 그대로라 `import` 문은 바뀌지 않았다.**
- `tools/scenarios/{send_goal,capture_and_detect}.py` — `SERVER_PATH`가 새 위치를 가리키도록 변경.

`sim/`과 `tools/patrol_viz/`는 디렉터리 단위로 통째로 옮겨서 **내부 상대경로가 그대로 유효**하다
(`sim_bringup.launch.py`의 `this_dir`, `run_patrol.sh`의 `HERE`, `patrol_viz.py`의 `MAP` 등).

## 병합할 때 확인할 것

1. `git log --follow <파일>` 로 이력이 이어지는지 — 전부 `git mv`라 rename이 인식된다.
2. `python3 sot_audit.py` 가 99/99 통과하는지.
3. 팀원의 진행 중 브랜치가 있으면 **병합 전에 그쪽을 먼저 main에 넣는다.** 이 개편은 거의 모든 경로를
   바꾸므로, 나중에 리베이스하면 충돌이 크다.
4. 외부 문서·발표자료·이슈에 걸린 `limo-MCP/...` 링크는 이 표를 보고 갱신한다.

## 개행(CRLF) 정규화만 따로 가져가려면

`.gitattributes` 추가 + 개행 정규화 커밋(`58ddc79`)은 구조 개편과 **독립적**이며,
OneDrive/Windows 체크아웃에서 98개 파일이 계속 헛변경으로 잡히던 문제를 없앤다.
구조 개편과 별개로 먼저 반영하고 싶으면 그 커밋만 따로 가져갈 수 있다.

```bash
git checkout main
git cherry-pick 58ddc79
```

**단, 진행 중인 로컬 변경이 있는 팀원은 먼저 커밋하거나 stash한 뒤에 받도록 공지할 것.**
