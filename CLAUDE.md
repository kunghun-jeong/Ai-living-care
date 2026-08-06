# AI-Care Edge System

## 개요

스마트홈 거주자의 자연어 의도를 고수준 정책으로 번역해 IoT Worker AI Agent에 배포하고,
실행 결과를 해석해 재시도·전환·에스컬레이션을 결정하는 **의도 기반 폐루프 리빙케어 프레임워크**.
IITP RS-2024-00398199 과제 · 산출물 3종: 프로토타입 · IITP 표준화 제안서 · 매거진 논문.

## 기술 스택

Python 3.10+ · ROS2 Jazzy (rclpy · Nav2 · slam_toolbox) · **MCP SDK ≥2.0** · YOLO(ultralytics) · Gazebo Harmonic
DB 없음 · HTTP API 없음 (외부 인터페이스는 MCP tool 6종)

## 주요 명령어

- 구조 감사: `python3 sot_audit.py`
- 문서 정합성 감사: `python3 doc_audit.py`
- 순찰 검증(경량, ROS2만 필요): `cd tools/limo-patrol-viz && ./run_coverage.sh`
- 전체 시뮬: `cd worker_ai_agent/limo-MCP && ros2 launch Simulation/sim_bringup.launch.py`
- MCP 왕복: `cd worker_ai_agent/limo-MCP && python3 Scenarios/send_goal.py 1.0 0.0`
- 빌드 / 테스트 / 린트: **없음** — `TODO(확인 필요)`, @docs/status.md 참조

## 프로젝트 문서 (필요할 때만 읽을 것)

- 아키텍처: @docs/architecture.md
- API 스펙(MCP tool): @docs/api-spec.md
- 코딩 컨벤션: @docs/conventions.md
- 의사결정 기록: @docs/decisions.md
- 현재 상태·갭·선결조건: @docs/status.md
- **작업 하네스**: @docs/harness.md
- 문서 소유권·전파: @docs/doc-map.md
- 구조 정본: @SOT.md
- 설계 정본: @docs/spec/AI-Care_Unified_Architecture_Spec_v0.2.md

## 작업 규칙

- **작업 시작 전 @docs/harness.md 에서 해당 작업의 하네스를 읽는다.** 하네스가 사전 점검·검증·결정 기록·리스크 판정 절차를 정한다.
- 중요한 설계·기술 결정을 내리면 즉시 @docs/decisions.md 맨 위에 날짜와 함께 기록한다.
- 이 파일에는 참조와 규칙만 추가한다. 상세 내용은 docs/ 아래 파일로 분리한다.
- 팀 공유 지식은 CLAUDE.md와 docs/에, 개인 학습 내용은 /memory에 저장한다.
- 큰 작업은 먼저 계획을 단계로 나누고, 한 세션에서는 한 단계(피처)만 구현한다.
- **사실만 기록한다.** 코드에서 확인하지 못한 것은 `TODO(확인 필요)`로 남기고 추측으로 채우지 않는다.

## ⚠️ 착수 전 필독

`sot_audit.py`는 **구조**를, `doc_audit.py`는 **문서 정합성**을 본다 — 둘 다 초록이어도 **실행 가능성은 전혀 보증되지 않는다.**
크리티컬 갭 6건(G-1~G-6), 안전 결함, 선결 조건은 @docs/status.md 에 있다.
