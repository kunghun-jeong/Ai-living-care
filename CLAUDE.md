# AI-Care Edge System

자연어 의도를 고수준 정책으로 번역해 IoT Worker AI Agent에 배포하고, 실행 결과를 해석해
재시도·전환·에스컬레이션을 결정하는 **의도 기반 폐루프 리빙케어 프레임워크**.
IITP RS-2024-00398199 · 산출물: 프로토타입 · 표준화 제안서 · 매거진 논문.

Python 3.10+ · ROS2 Jazzy (rclpy · Nav2 · slam_toolbox) · **MCP SDK ≥2.0** · YOLO(ultralytics) · Gazebo Harmonic
DB 없음 · HTTP API 없음 (외부 인터페이스는 MCP tool 6종)

## ⛔ 소유 경계 (D-17)

`limo-MCP/**` · `limo-patrol-viz/**` 의 **코드는 담당 연구원 소유**다. 다른 사람은
**읽고 `docs/status.md` 에 결함을 기록할 뿐 고치지 않는다.** 각 트리의 `CLAUDE.md` 만 예외.

## 구성

`manager_ai_agent/` · `worker_ai_agent/` (구현체는 `limo-MCP/`) · `interfaces/`(IF-1~IF-8) · `contracts/`(L1~L3·Report 스키마) · `tools/` · `docs/`

## 주요 명령어

- **최초 1회**: `make hooks` (make 없으면 `git config core.hooksPath .githooks`)
- 커밋 전: `make check` (= `python3 anchor.py` + `python3 sot_audit.py`) · 회귀: `make test`
- **전 영역 현황 한 화면**: `make status` — 48개 `CLAUDE.md` 헤더를 읽어 모은다
- 순찰 검증(경량): `cd tools/limo-patrol-viz && ./run_coverage.sh`
- 전체 시뮬: `cd worker_ai_agent/limo-MCP && ros2 launch Simulation/sim_bringup.launch.py`
- MCP 왕복: `cd worker_ai_agent/limo-MCP && python3 Scenarios/send_goal.py 1.0 0.0`
- 빌드 / 린트 / 테스트 프레임워크: **없음**

## 프로젝트 문서 — `@` = 매 세션 자동 로딩 · 무표 = gateway 뒤 lazy

**무표 문서를 습관적으로 열지 않는다.** 아래 세 개로 무엇을 열지 정한 뒤 그것만 연다.

- **문서 라우팅 정본(작업 시작점)**: @docs/doc-map.md — 하려는 일 → 열 문서
- **작업 하네스**: @docs/harness.md — 읽기 · 작업 · 앵커 갱신 · 결정 로그 한 줄
- **현재 상태·갭·선결조건**: @docs/status.md — 건드릴 영역이 지금 깨져 있는지

- 구조 정본: `SOT.md` — **구조를 바꿀 때만.** 명명·배치·감사 규칙
- 설계 정본: `docs/spec/AI-Care_Unified_Architecture_Spec_v0.2.md` (962줄)
  — **통독 금지.** 각 컴포넌트 `CLAUDE.md` 헤더가 지목한 **절만** 읽는다
- 코드 아키텍처: `docs/architecture.md` — ⚠️ 그림의 IF-4·IF-5 종단점에 알려진 불일치 (F-62)
- API 스펙(MCP tool): `docs/api-spec.md` — MCP 작업자만
- 코딩 컨벤션: `docs/conventions.md` · 의사결정 기록: `docs/decisions.md` (쓸 때만 연다)
- 경로 이전 대응: `MIGRATION.md` — 옛 경로로 검색해 못 찾을 때
- **참고 원본 (`REFERENCE-ONLY` · 정본 아님)**: `docs/context/` (1,411줄) · `docs/handoff/`
  — spec v0.2 가 이미 소화한 입력 자료다. **인용하지 말 것** — 정본은 spec

## 작업 규칙

- **작업 전 그 디렉터리의 `CLAUDE.md`만 읽는다.** 절차는 @docs/harness.md.
- 결정은 `docs/decisions.md` 맨 위에 한 줄. 큰 작업은 한 세션에 한 단계만.
- **사실만 기록한다.** 확인 못 한 것은 `TODO(확인 필요)` — 추측으로 채우지 않는다.
- 두 감사 스크립트는 **실행 가능성을 보증하지 않는다.** 크리티컬 갭 6건(G-1~G-6)과
  안전 결함은 @docs/status.md 에 있다.
