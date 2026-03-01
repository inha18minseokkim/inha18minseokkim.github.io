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
    python notion_to_obsidian_update_image.py [NOTION_PAGE_URL] [--dry-run]

인자:
    NOTION_PAGE_URL  Notion 페이지 URL (attachment 다운로드에 필요)

옵션:
    --dry-run    실제로 다운로드/수정하지 않고 변경 사항만 출력
"""

import os
import re
import sys
import json
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

# Notion 사이트 URL (attachment 다운로드용)
NOTION_SITE = None


def is_notion_s3_url(url: str) -> bool:
    """URL이 Notion S3 이미지 URL인지 확인"""
    for pattern in NOTION_S3_PATTERNS:
        if re.match(pattern, url):
            return True
    return False


def is_attachment_url(url: str) -> bool:
    """URL이 Notion attachment URL인지 확인"""
    return url.startswith('attachment:')


def parse_notion_url(url: str) -> tuple:
    """Notion URL에서 사이트와 페이지 ID 추출"""
    # https://xxx.notion.site/Page-Title-abc123 형식
    match = re.match(r'https://([^/]+\.notion\.site)/([^?]+)', url)
    if match:
        site = match.group(1)
        path = match.group(2)
        # 페이지 ID는 마지막 하이픈 이후의 32자 또는 URL 끝부분
        page_id_match = re.search(r'([a-f0-9]{32}|[a-f0-9-]{36})$', path.replace('-', ''))
        if page_id_match:
            page_id = page_id_match.group(1)
            # 하이픈 추가된 UUID 형식으로 변환
            if len(page_id) == 32:
                page_id = f"{page_id[:8]}-{page_id[8:12]}-{page_id[12:16]}-{page_id[16:20]}-{page_id[20:]}"
            return site, page_id
    return None, None


def download_attachment(block_id: str, filename: str, dest_path: str, page_id: str = None) -> bool:
    """Notion attachment 다운로드"""
    if not NOTION_SITE:
        print(f"    오류: Notion 사이트 URL이 설정되지 않았습니다.")
        return False

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'image/*,*/*;q=0.8',
        'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
        'Referer': f'https://{NOTION_SITE}/',
    }

    # 여러 URL 패턴 시도
    url_patterns = [
        # 패턴 1: 직접 파일 접근
        f"https://{NOTION_SITE}/file/{block_id}/{urllib.parse.quote(filename)}",
        # 패턴 2: image API with block table
        f"https://{NOTION_SITE}/image/attachment%3A{block_id}%3A{urllib.parse.quote(filename)}?table=block&id={block_id}",
        # 패턴 3: image API with page context
        f"https://{NOTION_SITE}/image/attachment%3A{block_id}%3A{urllib.parse.quote(filename)}?table=block&id={page_id}" if page_id else None,
        # 패턴 4: secure file URL
        f"https://{NOTION_SITE}/signed/{block_id}/{urllib.parse.quote(filename)}",
    ]

    for url in url_patterns:
        if not url:
            continue
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=30) as response:
                content = response.read()

                # 텍스트 응답인지 확인 (에러 메시지)
                if len(content) < 200:
                    try:
                        text = content.decode('utf-8')
                        if 'error' in text.lower() or 'not found' in text.lower():
                            continue
                    except:
                        pass

                if len(content) < 100:
                    continue

                with open(dest_path, 'wb') as f:
                    f.write(content)

                print(f"    다운로드 완료: {dest_path} ({len(content)} bytes)")
                return True

        except urllib.error.HTTPError:
            continue
        except Exception:
            continue

    print(f"    다운로드 실패: 모든 URL 패턴 실패")
    print(f"    수동 다운로드 필요: Notion 페이지에서 이미지를 직접 저장하세요.")
    return False


# 전역 페이지 ID 저장
NOTION_PAGE_ID = None


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
            attachment_match = ATTACHMENT_PATTERN.match(url)
            if attachment_match:
                block_id = attachment_match.group(1)
                orig_filename = attachment_match.group(2)
                print(f"  발견: Notion attachment")
                print(f"    Block ID: {block_id}")
                print(f"    파일명: {orig_filename}")

                # 이미지 파일명 생성
                filename = generate_image_filename(url, orig_filename)
                dest_path = os.path.join(ASSETS_DIR, filename)

                if dry_run:
                    print(f"    [DRY-RUN] 다운로드 예정: {dest_path}")
                    new_url = f"/assets/images/{urllib.parse.quote(filename)}"
                    print(f"    [DRY-RUN] 새 URL: {new_url}")
                else:
                    # attachment 다운로드 시도
                    if download_attachment(block_id, orig_filename, dest_path, NOTION_PAGE_ID):
                        # URL 업데이트
                        new_url = f"/assets/images/{urllib.parse.quote(filename)}"
                        old_tag = match.group(0)
                        new_tag = f"![{alt_text}]({new_url})"
                        content = content.replace(old_tag, new_tag, 1)
                        changes += 1
                        print(f"    변경: {new_url}")
                    else:
                        print(f"    힌트: Notion 페이지 URL을 인자로 전달해주세요.")
                        print(f"    예: python {sys.argv[0]} https://xxx.notion.site/page-id")

    # 변경사항이 있으면 파일 업데이트
    if changes > 0 and not dry_run:
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  파일 업데이트 완료: {changes}개 이미지")

    return changes


def find_matching_file(posts_path: Path, notion_url: str) -> Path:
    """Notion URL에서 제목을 추출하여 매칭되는 마크다운 파일 찾기"""
    # URL에서 제목 부분 추출 (페이지 ID 앞부분)
    # 예: Tech-Talk-MSA-LangChain-MCP-1fe2f38ca9688026b366f483b1c42e59
    match = re.search(r'/([^/]+)-([a-f0-9]{32})(?:\?|$)', notion_url.replace('-', ''))
    if not match:
        # 하이픈 포함 URL 시도
        match = re.search(r'/([^/]+?)-?([a-f0-9-]{32,36})(?:\?|$)', notion_url)

    if match:
        title_part = match.group(1)
        # URL 인코딩된 제목을 디코딩
        title_part = urllib.parse.unquote(title_part)
        # 하이픈을 공백으로, 소문자로 변환하여 검색
        search_term = title_part.replace('-', ' ').lower()

        # 모든 마크다운 파일에서 제목 매칭 시도
        for md_file in posts_path.glob("*.md"):
            filename = md_file.stem.lower()
            # 날짜 부분 제거 (2024-01-01- 형식)
            if len(filename) > 11 and filename[10] == '-':
                filename = filename[11:]

            # 제목 매칭
            if search_term in filename or filename in search_term:
                return md_file

            # 부분 매칭 시도 (첫 몇 단어)
            search_words = search_term.split()[:3]
            if all(word in filename for word in search_words if len(word) > 2):
                return md_file

    return None


def main():
    global NOTION_SITE, NOTION_PAGE_ID

    args = sys.argv[1:]
    dry_run = "--dry-run" in args

    # Notion URL 인자 처리
    notion_url = None
    for arg in args:
        if arg.startswith('https://') and 'notion.site' in arg:
            notion_url = arg
            break

    # 특정 파일 경로 인자 처리
    target_file = None
    for arg in args:
        if arg.endswith('.md') and not arg.startswith('--'):
            target_file = arg
            break

    if notion_url:
        site, page_id = parse_notion_url(notion_url)
        if site:
            NOTION_SITE = site
            NOTION_PAGE_ID = page_id
            print(f"Notion 사이트: {NOTION_SITE}")
            print(f"페이지 ID: {page_id}")
            print()
        else:
            print(f"경고: Notion URL 파싱 실패: {notion_url}")
            print()

    if dry_run:
        print("=== DRY-RUN 모드: 실제 변경 없음 ===\n")

    # assets/images 폴더 생성
    Path(ASSETS_DIR).mkdir(parents=True, exist_ok=True)

    # _posts 폴더 확인
    posts_path = Path(POSTS_DIR)
    if not posts_path.exists():
        print(f"오류: {POSTS_DIR} 폴더를 찾을 수 없습니다.")
        sys.exit(1)

    # 처리할 파일 결정
    if target_file:
        # 특정 파일 지정된 경우
        md_files = [Path(target_file)]
        print(f"지정된 파일 처리: {target_file}\n")
    elif notion_url:
        # Notion URL로 매칭되는 파일 찾기
        matched_file = find_matching_file(posts_path, notion_url)
        if matched_file:
            md_files = [matched_file]
            print(f"매칭된 파일: {matched_file.name}\n")
        else:
            print(f"경고: Notion URL과 매칭되는 파일을 찾을 수 없습니다.")
            print(f"힌트: 파일 경로를 직접 지정하세요.")
            print(f"예: python {sys.argv[0]} {notion_url} _posts/파일명.md")
            sys.exit(1)
    else:
        # 전체 파일 처리
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
