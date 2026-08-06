#!/bin/bash
# AWS small_house 의 메시/텍스처(약 55MB)를 원본 저장소에서 받아 채운다.
# 저장소에는 우리가 수정한 .sdf/.config/world 만 들어 있고 바이너리는 빠져 있다.
# 이 스크립트는 기존 .sdf 를 덮어쓰지 않는다.
set -e
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEST="$HERE/aws_small_house/models"
REPO=https://github.com/aws-robotics/aws-robomaker-small-house-world.git
BRANCH=gzweb

[ -d "$DEST" ] || { echo "models 디렉터리가 없습니다: $DEST"; exit 1; }

have=$(find "$DEST" -type f -iname '*.dae' | wc -l)
if [ "$have" -gt 0 ]; then
  echo "이미 메시가 $have 개 있습니다. 다시 받으려면 먼저 지우세요."
  exit 0
fi

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
echo "원본 저장소에서 메시를 받는 중... (약 55MB)"
git clone --depth 1 -b "$BRANCH" -q "$REPO" "$TMP/src"

n=0
while IFS= read -r -d '' f; do
  rel="${f#"$TMP/src/models/"}"
  mkdir -p "$DEST/$(dirname "$rel")"
  cp "$f" "$DEST/$rel"
  n=$((n+1))
done < <(find "$TMP/src/models" -type f \
    \( -iname '*.dae' -o -iname '*.stl' -o -iname '*.obj' -o -iname '*.mtl' \
       -o -iname '*.png' -o -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.tga' \) -print0)

echo "완료: $n 개 복사"
echo "우리 수정본 확인:"
echo "  ShoeRack izz : $(grep -c '<izz>' "$DEST/aws_robomaker_residential_ShoeRack_01/model.sdf" 2>/dev/null || echo 0) (1이어야 정상)"
echo "  world static : $(grep -c '<static>true</static>' "$HERE/aws_small_house/worlds/small_house.world")  (56이어야 정상)"
