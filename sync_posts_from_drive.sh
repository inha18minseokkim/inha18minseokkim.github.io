#!/bin/bash
# Google Drive 동기화 _posts → 저장소 _posts 동기화
# 사용: bash sync_posts_from_drive.sh
#
# 구조:
#   내 노트북/
#   ├── _posts/          ← Google Drive 동기화 폴더 (다른 기기에서 편집)
#   └── minseokkim/      ← git 저장소
#       ├── _posts/      ← 이 스크립트로 위 폴더와 동기화
#       └── sync_posts_from_drive.sh

DRIVE_POSTS="$(dirname "$0")/../_posts"
REPO_POSTS="$(dirname "$0")/_posts"

if [ ! -d "$DRIVE_POSTS" ]; then
  echo "오류: Google Drive _posts 폴더를 찾을 수 없음 ($DRIVE_POSTS)"
  exit 1
fi

echo "동기화: $DRIVE_POSTS → $REPO_POSTS"
rsync -av --delete "$DRIVE_POSTS/" "$REPO_POSTS/"
echo ""
echo "완료: $(ls "$REPO_POSTS" | wc -l | tr -d ' ')개 포스팅"
