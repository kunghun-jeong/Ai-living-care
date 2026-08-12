#!/usr/bin/env bash
# Gazebo/Nav2 없이 A* 경로를 계산해 시나리오 2를 RViz2에서 재생한다.
set -e

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$HERE/../.." && pwd)"
PATROL_ASSETS="$REPO_ROOT/tools/limo-patrol-viz"

if [ -z "${ROS_DISTRO:-}" ]; then
  # shellcheck disable=SC1091
  source /opt/ros/jazzy/setup.bash 2>/dev/null || {
    echo "ROS2 Jazzy를 찾을 수 없습니다. ROS2와 RViz2를 먼저 설치하세요."
    exit 1
  }
fi

unset GALLIUM_DRIVER
export LIBGL_ALWAYS_SOFTWARE=1
export QT_QPA_PLATFORM=xcb

ros2 run robot_state_publisher robot_state_publisher \
  --ros-args -p robot_description:="$(cat "$PATROL_ASSETS/limo/limo.urdf")" \
  > /tmp/scenario2_rsp.log 2>&1 &
RSP_PID=$!

python3 "$HERE/scenario2_astar_viz.py" > /tmp/scenario2_astar_viz.log 2>&1 &
VIZ_PID=$!

cleanup() {
  kill "$RSP_PID" "$VIZ_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo "A* 경로 계산 및 RViz publisher 준비 중..."
sleep 5
head -4 /tmp/scenario2_astar_viz.log || true

rviz2 -d "$PATROL_ASSETS/patrol.rviz"
