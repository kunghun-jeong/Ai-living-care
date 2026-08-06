#!/bin/bash
# GUI 없이 순찰 커버리지만 계산하고 patrol_sim.png 를 남긴다.
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$HERE/patrol_sim.py"
