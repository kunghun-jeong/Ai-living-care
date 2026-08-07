# AI-Care Edge System — 팀 공용 진입점
#
#   make hooks   최초 1회. 커밋할 때 앵커 검사가 자동으로 돈다
#   make check   커밋 전 검사 (수 초)
#   make test    로봇 없이 도는 회귀 (약 1분)
#
# ROS2 가 필요한 것은 여기 없다 — 시뮬·실기는 각 디렉터리 CLAUDE.md 참조.

PY ?= python3

.DEFAULT_GOAL := help
.PHONY: help hooks check test anchor structure

help:
	@echo "  make hooks   pre-commit 훅 설치 (최초 1회)"
	@echo "  make check   앵커 + 구조 검사 (수 초, 커밋 전)"
	@echo "  make test    회귀 테스트 (로봇 불필요, 약 1분)"

hooks:
	@git config core.hooksPath .githooks
	@chmod +x .githooks/* 2>/dev/null || true
	@echo "pre-commit 훅 설치됨 — 이제 커밋할 때 앵커 검사가 돈다"
	@echo "우회가 필요하면: SKIP_ANCHOR=1 git commit ..."

check: anchor structure

anchor:
	@$(PY) anchor.py

structure:
	@$(PY) sot_audit.py > /dev/null && echo "구조 OK" || ($(PY) sot_audit.py; exit 1)

test:
	@echo "── 안전 경로 회귀 (ROS2 불필요) ─────────────────────────"
	@$(PY) worker_ai_agent/limo-MCP/verify_fixes.py
	@echo ""
	@echo "── 순찰 커버리지 회귀 ───────────────────────────────────"
	@cd tools/limo-patrol-viz && ./run_coverage.sh | tail -4
