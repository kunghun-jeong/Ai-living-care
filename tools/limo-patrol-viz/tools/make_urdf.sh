#!/bin/bash
# WeGo limo_gazebo (ROS1 / Gazebo Classic) 에서 ROS2용 평문 URDF 를 뽑는다.
# 원본 저장소는 건드리지 않고 작업 사본에서만 고친다.
#
#   1) $(find limo_description)  -> 절대경로
#   2) .gazebo include 제거       (Classic 플러그인. RViz엔 불필요하고
#                                  $(arg robot_namespace) 때문에 변환이 막힘)
set -e
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT="$HERE/../limo"
WORK=$(mktemp -d)

: "${LIMO_SRC:=}"
if [ -z "$LIMO_SRC" ]; then
  echo "WeGo limo_gazebo 를 받는 중..."
  git clone --depth 1 -q https://github.com/WeGo-Robotics/limo_gazebo.git "$WORK/repo"
  LIMO_SRC="$WORK/repo/limo_description"
fi

cp -r "$LIMO_SRC/urdf" "$WORK/"
[ -d "$LIMO_SRC/meshes" ] && cp -r "$LIMO_SRC/meshes" "$WORK/"

sed -i "s|\$(find limo_description)|$WORK|g" "$WORK"/urdf/*.xacro "$WORK"/urdf/*.gazebo 2>/dev/null || true
sed -i '/xacro:include[^>]*\.gazebo/d' "$WORK"/urdf/*.xacro

source /opt/ros/jazzy/setup.bash 2>/dev/null || true
mkdir -p "$OUT"
xacro "$WORK/urdf/limo_four_diff.xacro" -o "$OUT/limo.urdf"

echo "생성: $OUT/limo.urdf  ($(wc -l < "$OUT/limo.urdf") 줄)"
grep -oE '<link name="[^"]+"' "$OUT/limo.urdf" | sed 's/<link name=//' | tr -d '"' | sed 's/^/  /'
rm -rf "$WORK"
