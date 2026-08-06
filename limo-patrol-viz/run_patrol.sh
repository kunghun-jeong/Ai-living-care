#!/bin/bash
# RViz2에서 순찰 애니메이션 + 카메라 스트리밍 재생
# 사용: ./run_patrol.sh
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -z "${ROS_DISTRO:-}" ]; then
  # shellcheck disable=SC1091
  source /opt/ros/jazzy/setup.bash 2>/dev/null || {
    echo "ROS2를 찾을 수 없습니다. 'source /opt/ros/<distro>/setup.bash' 후 다시 실행하세요."; exit 1; }
fi

# WSL2에서 RViz2(Ogre)는 d3d12 하드웨어 경로에서 "D3D12: Removing Device"로
# 3D 뷰가 검게 죽는다. 소프트웨어 렌더링으로 우회한다. (README 참고)
unset GALLIUM_DRIVER
export LIBGL_ALWAYS_SOFTWARE=1
export QT_QPA_PLATFORM=xcb

pkill -f patrol_viz.py 2>/dev/null
pkill -f robot_state_publisher 2>/dev/null
pkill rviz2 2>/dev/null
sleep 1

ros2 run robot_state_publisher robot_state_publisher \
    --ros-args -p robot_description:="$(cat "$HERE/limo/limo.urdf")" \
    > /tmp/rsp.log 2>&1 &
RSP=$!

python3 "$HERE/patrol_viz.py" > /tmp/patrol_viz.log 2>&1 &
PV=$!

echo "경로 계산 중... (10초)"
sleep 10
echo "--- patrol_viz ---"; head -4 /tmp/patrol_viz.log

trap 'kill $RSP $PV 2>/dev/null' EXIT
exec rviz2 -d "$HERE/patrol.rviz"
