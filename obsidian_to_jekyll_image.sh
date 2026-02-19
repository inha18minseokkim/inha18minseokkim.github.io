#!/bin/bash

# Obsidian 이미지 문법을 Jekyll 표준 마크다운으로 변환하는 스크립트
# 사용법: ./obsidian_to_jekyll_image.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
POSTS_DIR="$SCRIPT_DIR/_posts"
ASSETS_DIR="$SCRIPT_DIR/assets/images"

# assets/images 폴더가 없으면 생성
mkdir -p "$ASSETS_DIR"

echo "=== Obsidian to Jekyll 이미지 변환 스크립트 ==="
echo ""

# 1. 루트 폴더의 "Pasted image*.png" 파일들을 assets/images로 이동
moved_count=0
for img in "$SCRIPT_DIR"/Pasted\ image\ *.png; do
    if [ -f "$img" ]; then
        filename=$(basename "$img")
        mv "$img" "$ASSETS_DIR/"
        echo "이동: $filename -> assets/images/"
        ((moved_count++)) || true
    fi
done

if [ $moved_count -gt 0 ]; then
    echo "총 ${moved_count}개 이미지 파일 이동 완료"
else
    echo "이동할 이미지 파일 없음"
fi
echo ""

# 2. _posts 폴더의 모든 md 파일에서 Obsidian 문법을 Jekyll 문법으로 변환
converted_count=0
for md_file in "$POSTS_DIR"/*.md; do
    if [ -f "$md_file" ]; then
        # Obsidian 문법이 있는지 확인
        if grep -q '!\[\[Pasted image' "$md_file" 2>/dev/null; then
            filename=$(basename "$md_file")
            # ![[Pasted image XXXXX.png]] -> ![이미지](/assets/images/Pasted%20image%20XXXXX.png)
            sed -i '' 's/!\[\[Pasted image \([0-9]*\)\.png\]\]/![이미지](\/assets\/images\/Pasted%20image%20\1.png)/g' "$md_file"
            echo "변환: $filename"
            ((converted_count++)) || true
        fi
    fi
done

if [ $converted_count -gt 0 ]; then
    echo "총 ${converted_count}개 마크다운 파일 변환 완료"
else
    echo "변환할 파일 없음"
fi
echo ""

echo "=== 완료 ==="
