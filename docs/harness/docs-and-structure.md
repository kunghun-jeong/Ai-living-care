# 하네스 — 문서 · 구조 · 스펙

> 대상: `CLAUDE.md`(전부), `SOT.md`, `docs/**`, `sot_audit.py`, 디렉터리 이동·신설
>
> 공통 절차는 @docs/harness.md.

## 0. 가장 중요한 규칙

### `CLAUDE.md`와 `docs/**`는 **사람이 직접 유지한다.** 생성기를 쓰지 않는다.

`sot_migrate.py`와 `sot_preserve.py`는 **폐기됐다** (2026-08-06 결정).
이 스크립트들은 42개 `CLAUDE.md`를 내장 문자열 딕셔너리에서 **전면 덮어쓰기** 하는데,
그 템플릿에 구 경로가 박혀 있어 실행하면 방금 고친 문서가 되돌아간다.
**문서 결함의 단일 최대 원인이었다.**

```
❌ python3 sot_migrate.py claudemd     # 실행 금지 — 문서를 되돌린다
❌ python3 sot_preserve.py docs        # 실행 금지 — 멱등하지 않다
✅ 편집기로 .md 를 직접 고친다
```

## 1. 읽을 것

1. `SOT.md` — 명명 규칙(N-*), 정규 구조, 배치 규칙(SP-*), 감사 규칙(R-*)
2. @docs/status.md 의 문서·규범 결함 표 (F-11 ~ F-19)
3. 고칠 문서 자신

## 2. 사전 점검

```bash
python3 sot_audit.py      # 현재 통과 상태인지. 실패한 채로 시작하면 원인 추적 불가
```

## 3. 검증

### D-1. 문서에 적은 경로가 실재하는가 — **가장 자주 깨지는 항목**

> ⚠️ 아래 검사기는 `cd`를 추적하지 않는다. `cd worker_ai_agent/limo-MCP && ros2 launch Simulation/...`
> 처럼 **cd 이후 상대경로**는 오탐으로 잡힌다. 오탐이면 무시하고, 저장소 루트 기준 경로가
> 틀린 것만 고친다. 검사기를 개선하면 이 주석을 지운다. `TODO(확인 필요)`

```bash
python3 - <<'EOF'
import re, os, glob, sys
bad = []
for doc in glob.glob("**/*.md", recursive=True):
    if "_to_delete" in doc or "docs/slides" in doc: continue
    txt = open(doc, encoding="utf-8").read()
    for blk in re.findall(r"```(?:bash|sh)\n(.*?)```", txt, re.S):
        for tok in re.findall(r"(?:^|\s)((?:[\w.-]+/)+[\w.-]+\.(?:py|sh|yaml|json|urdf|rviz|md))", blk):
            if not os.path.exists(tok):
                bad.append((doc, tok))
for d, t in bad: print(f"FAIL {d}: 존재하지 않는 경로 -> {t}")
sys.exit(1 if bad else 0)
EOF
```

### D-2. 금지 경로가 문서에 남아 있지 않은가

```bash
! grep -rn "tools/scenarios\|tools/patrol_viz\|sim/sim_bringup\|(^|[^-])\bsim/" \
    --include='*.md' . | grep -v _to_delete \
  || echo "FAIL: sot_audit.py FORBIDDEN 경로가 문서에 남아 있음"
```

### D-3. 스펙 참조가 단일 규약인가

모든 `CLAUDE.md`의 설계 정본 참조는 **저장소 루트 기준 경로 하나**로 통일한다:
`docs/spec/AI-Care_Unified_Architecture_Spec_v0.2.md`

> 현재 42개 중 39개가 `../` 없이 적혀 있어 그 파일 위치에서는 링크로서 깨진다.
> `sot_audit.py` R8은 `"SOT.md" in s`만 검사해 스펙 참조는 형식·존재 어느 쪽도 검사하지 않는다.

### D-4. 식별자 네임스페이스를 지켰는가

| 접두 | 정의처 | 의미 |
|---|---|---|
| `D-*` | spec §0.2 (설계) / `SOT.md` §6 (구조) | 결정 |
| `U-*` | spec §12 | 미결정 사항 |
| `G-*` | spec §10.3 | 크리티컬 갭 |
| `F-*` | @docs/status.md | 포렌식 결함 |
| `S-*` | spec §11.1 | 표준화 항목 |
| `IF-*` | spec §3 | 인터페이스 |
| `N-*` · `SP-*` · `R-*` | `SOT.md` | 명명 · 배치 · 감사 규칙 |
| `P-*` | spec §1.2 **전용** | 설계 원칙 |
| `0-*` | spec §10.4 | Phase 0 작업 번호 |

> ⚠️ **`P-*`가 두 네임스페이스에서 충돌한다** (F-14). spec §1.2는 설계 원칙, `SOT.md` §4는 배치 규칙.
> 배치 규칙은 **`SP-*`로 개명**해야 한다. 이 문서와 하네스는 이미 `SP-*`를 쓴다.

**규칙: 새 ID를 만들면 정의처에 한 번만 정의하고, 참조는 접두를 반드시 붙인다.**

### D-5. 수치에 출처와 한정어를 붙였는가

| 표기 | 의미 |
|---|---|
| 재현 가능 | "기하 시뮬레이션 기준 93.6% (`patrol_sim.py` 실행 결과)" |
| 1회 실측 | "`turtlebot3_world`에서 1회 측정, `/odom` (0,0)→(0.764, 0.009)" |
| 미측정 가정 | "`CAM_RANGE = 4.0 m` — **미측정 가정**" |
| 외부 인용 | "Duan & Lu, arXiv:2508.15819" |

**상위 문서의 수치를 인용할 때 원문의 한정어를 함께 가져온다.**
"2 m² 이상 사각지대 0" → "사각지대 0"으로 줄이면 거짓이 된다 (F-17).

### D-6. 구조를 바꿨다면

```bash
python3 sot_audit.py           # R1~R10 통과
python3 sot_audit.py --plan    # 남은 이동이 0건인지
```

추가로:
- `SOT.md` §2 정규 구조도를 갱신했는가 — **트리와 `sot_audit.py`의 검사 대상이 일치해야 한다**
- `sot_audit.py`에 새 규칙을 추가했는가
- `MIGRATION.md`에 경로 대응을 추가했는가
- 이동은 `git mv`로 했는가 (`git log --follow`가 이어지는지 확인)

## 4. 알려진 규범 결함 (고칠 때 함께 처리)

| ID | 결함 | 조치 |
|---|---|---|
| **F-13** | `SOT.md` R6/N-5는 `sim/`이 루트에 있어야 한다 하고, `sot_audit.py` FORBIDDEN은 있으면 위반 | **규범을 동시에 만족시킬 수 없다.** R6·N-5에서 `sim/`을 빼야 한다 |
| **F-14** | `P-*`가 spec/SOT 두 네임스페이스에서 충돌 | `SOT.md` §4를 `SP-*`로 개명 |
| **F-15** | 이중 세션 키 검증을 `S-4`라 부르나 실제는 `S-7` | spec §9 오기 → CLAUDE.md 3개로 전파. 함께 정정 |
| **F-19** | D-14가 spec §0.2에 미반영 | spec 결정표에 추가 |
| — | `sot_audit.py` R7의 `sys.path` 검사가 **문자열 포함만** 봐서 공허하다 | 실재 디렉터리 확인으로 강화 |
| — | R9가 루트 한 겹만 봐서 컴포넌트 밖 `.py`를 못 잡는다 | 재귀 검사로 강화 |
| — | `contracts/` 자식 4종이 R1·R4·R6 어디에도 없어 삭제해도 통과한다 | 검사 대상에 추가 |

## 5. 결정 기록 · 리스크

| 변경 | 등급 |
|---|---|
| 문서 내용 수정, 오타·경로 정정 | R0 |
| `CLAUDE.md` 추가·삭제, 문서 구조 변경 | R1 |
| `SOT.md` 명명·배치 규칙 변경, `sot_audit.py` 규칙 추가 | **R2** |
| 디렉터리 이동·신설, 컴포넌트 추가 | **R2** |
| 설계 정본(spec) 수정 | **R3** — 팀 합의 필요 |
| 원본 보존 대상(`limo-MCP/`, `limo-patrol-viz/`) 내부 변경 | **R2** — D-14 위반 여부 판정 |

**구조를 바꾸면 `SOT.md` §6에 결정을 기록하고, 설계에 영향이 있으면 spec §0.2에도 반영한다.**
둘 중 하나만 하면 두 정본이 갈라진다 — 이미 D-14에서 발생했다 (F-19).

## 6. 문서를 쓸 때

- **사실만 쓴다.** 코드에서 확인하지 못한 것은 `TODO(확인 필요)`로 남기고 추측으로 채우지 않는다.
- **"동작한다"와 "동작할 것이다"를 구분한다.** 실행해서 확인한 것만 동작한다고 쓴다.
- **한정어를 지운 채 인용하지 않는다.**
- 루트 `CLAUDE.md`는 **50줄 이내**를 유지한다. 늘어나면 `docs/` 아래로 분리한다.
- 컴포넌트 `CLAUDE.md`는 헤더 외에 **최소 하나의 실행 가능한 항목**(계약 시그니처 / 스키마 /
  갭 ID / 작업 번호)을 갖는다. 헤더만 있으면 그 문서는 없는 것과 같다.
