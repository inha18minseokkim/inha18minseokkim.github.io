#!/usr/bin/env python3
"""
notion_to_obsidian_update_image.py

_posts 폴더의 마크다운 파일을 순회하면서 Notion S3 이미지 URL을 찾아
로컬로 다운로드하고 링크를 업데이트합니다.

지원하는 이미지 URL 패턴:
- https://prod-files-secure.s3.us-west-2.amazonaws.com/...
- https://s3.us-west-2.amazonaws.com/secure.notion-static.com/...
- attachment:xxx:image.png (Notion 내부 첨부파일)

사용법:
    python notion_to_obsidian_update_image.py [--dry-run]

옵션:
    --dry-run    실제로 다운로드/수정하지 않고 변경 사항만 출력
"""

import os
import re
import sys
import hashlib
import urllib.request
import urllib.parse
from pathlib import Path
from datetime import datetime

# 설정
POSTS_DIR = "_posts"
ASSETS_DIR = "assets/images"

# Notion S3 이미지 URL 패턴
NOTION_S3_PATTERNS = [
    r'https://prod-files-secure\.s3\.us-west-2\.amazonaws\.com/[^)\s]+',
    r'https://s3\.us-west-2\.amazonaws\.com/secure\.notion-static\.com/[^)\s]+',
    r'https://prod-files-secure[^)\s]+\.amazonaws\.com/[^)\s]+',
]

# 마크다운 이미지 패턴: ![alt](url)
MD_IMAGE_PATTERN = re.compile(r'!\[([^\]]*)\]\(([^)]+)\)')

# Notion attachment 패턴: attachment:uuid:filename
ATTACHMENT_PATTERN = re.compile(r'attachment:([a-f0-9-]+):([^)]+)')


def is_notion_s3_url(url: str) -> bool:
    """URL이 Notion S3 이미지 URL인지 확인"""
    for pattern in NOTION_S3_PATTERNS:
        if re.match(pattern, url):
            return True
    return False


def is_attachment_url(url: str) -> bool:
    """URL이 Notion attachment URL인지 확인"""
    return url.startswith('attachment:')


def generate_image_filename(url: str, original_name: str = None) -> str:
    """URL에서 고유한 이미지 파일명 생성"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    # URL에서 원본 파일명 추출 시도
    if original_name:
        ext = Path(original_name).suffix or '.png'
        name = Path(original_name).stem
    else:
        # URL에서 파일명 추출
        parsed = urllib.parse.urlparse(url)
        path = urllib.parse.unquote(parsed.path)
        filename = Path(path).name

        if '.' in filename:
            ext = Path(filename).suffix
            name = Path(filename).stem
        else:
            ext = '.png'
            name = 'image'

    # 파일명에 타임스탬프와 해시 추가 (중복 방지)
    url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
    return f"Pasted image {timestamp}_{url_hash}{ext}"


def download_image(url: str, dest_path: str) -> bool:
    """이미지 다운로드"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as response:
            content = response.read()

            # 파일 크기 확인 (최소 100바이트)
            if len(content) < 100:
                print(f"    경고: 파일 크기가 너무 작음 ({len(content)} bytes)")
                return False

            with open(dest_path, 'wb') as f:
                f.write(content)

            print(f"    다운로드 완료: {dest_path} ({len(content)} bytes)")
            return True

    except Exception as e:
        print(f"    다운로드 실패: {e}")
        return False


def process_markdown_file(md_path: str, dry_run: bool = False) -> int:
    """마크다운 파일의 이미지 URL을 처리"""
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content
    changes = 0

    # 모든 이미지 태그 찾기
    for match in MD_IMAGE_PATTERN.finditer(content):
        alt_text = match.group(1)
        url = match.group(2)

        # Notion S3 URL인 경우
        if is_notion_s3_url(url):
            print(f"  발견: Notion S3 이미지")
            print(f"    URL: {url[:80]}...")

            # 이미지 파일명 생성
            filename = generate_image_filename(url)
            dest_path = os.path.join(ASSETS_DIR, filename)

            if dry_run:
                print(f"    [DRY-RUN] 다운로드 예정: {dest_path}")
                new_url = f"/assets/images/{urllib.parse.quote(filename)}"
                print(f"    [DRY-RUN] 새 URL: {new_url}")
            else:
                # 이미지 다운로드
                if download_image(url, dest_path):
                    # URL 업데이트
                    new_url = f"/assets/images/{urllib.parse.quote(filename)}"
                    old_tag = match.group(0)
                    new_tag = f"![{alt_text}]({new_url})"
                    content = content.replace(old_tag, new_tag, 1)
                    changes += 1
                    print(f"    변경: {new_url}")
                else:
                    # 403 에러 등으로 실패한 경우 안내
                    print(f"    힌트: S3 URL이 만료되었습니다.")
                    print(f"    해결: notion_to_obsidian.py --download-images 옵션으로 페이지 재변환")

        # Notion attachment URL인 경우
        elif is_attachment_url(url):
            print(f"  발견: Notion attachment")
            print(f"    URL: {url}")
            print(f"    주의: attachment URL은 Notion 페이지 컨텍스트가 필요합니다.")
            print(f"    수동으로 Notion 페이지에서 이미지를 다운로드하세요.")

    # 변경사항이 있으면 파일 업데이트
    if changes > 0 and not dry_run:
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  파일 업데이트 완료: {changes}개 이미지")

    return changes


def main():
    args = sys.argv[1:]
    dry_run = "--dry-run" in args

    if dry_run:
        print("=== DRY-RUN 모드: 실제 변경 없음 ===\n")

    # assets/images 폴더 생성
    Path(ASSETS_DIR).mkdir(parents=True, exist_ok=True)

    # _posts 폴더의 모든 마크다운 파일 처리
    posts_path = Path(POSTS_DIR)
    if not posts_path.exists():
        print(f"오류: {POSTS_DIR} 폴더를 찾을 수 없습니다.")
        sys.exit(1)

    md_files = sorted(posts_path.glob("*.md"))
    print(f"총 {len(md_files)}개의 마크다운 파일 발견\n")

    total_changes = 0
    files_changed = 0

    for md_file in md_files:
        print(f"처리 중: {md_file.name}")
        changes = process_markdown_file(str(md_file), dry_run)
        if changes > 0:
            total_changes += changes
            files_changed += 1
        print()

    print("=" * 50)
    print(f"완료: {files_changed}개 파일, {total_changes}개 이미지 처리")

    if dry_run:
        print("\n실제로 적용하려면 --dry-run 옵션 없이 실행하세요.")


if __name__ == "__main__":
    main()
