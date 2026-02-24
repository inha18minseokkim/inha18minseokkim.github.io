#!/usr/bin/env python3
"""
notion_to_obsidian.py

공개 Notion 페이지(splitbee API 경유)를 Obsidian 마크다운 파일로 변환합니다.
하위 페이지(child page) 및 본문 내 Notion 링크도 DFS로 순회하며 각각 별도 .md 파일로 생성합니다.

사용법:
    python notion_to_obsidian.py <output_dir> <notion_url>

예시:
    python notion_to_obsidian.py ./_posts https://stump-blender-387.notion.site/abc123
"""

import sys
import re
import json
import urllib.request
import os
from pathlib import Path
from datetime import datetime, timezone

SPLITBEE_API = "https://notion-api.splitbee.io/v1/page/"

# page_id → post_slug (변환된 페이지 캐시)
_slug_cache: dict = {}


# ─── URL / ID 파싱 ───────────────────────────────────────────────────────────

def extract_page_id(url: str) -> str:
    """Notion URL에서 페이지 ID(UUID 형식)를 추출합니다."""
    url = url.rstrip('/').split('?')[0]
    last = url.split('/')[-1]

    # slug-{32hex} 또는 순수 32hex
    hex_match = re.search(r'([0-9a-f]{32})$', last.replace('-', ''))
    if hex_match:
        h = hex_match.group(1)
        return f"{h[:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:]}"

    # 이미 UUID 형식
    uuid_match = re.search(
        r'([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})', last
    )
    if uuid_match:
        return uuid_match.group(1)

    raise ValueError(f"URL에서 페이지 ID를 추출할 수 없습니다: {url}")


# ─── API 호출 ─────────────────────────────────────────────────────────────────

def fetch_blocks(page_id: str) -> dict:
    """splitbee API로 페이지 블록 전체를 가져옵니다."""
    url = SPLITBEE_API + page_id
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


# ─── Rich Text → Markdown ─────────────────────────────────────────────────────

def rich_text_to_md(segments) -> str:
    """Notion rich text 세그먼트 배열을 마크다운 문자열로 변환합니다."""
    if not segments:
        return ""

    result = []
    for seg in segments:
        if not seg:
            continue
        text = seg[0] if seg else ""
        annotations = seg[1] if len(seg) > 1 else []

        bold = italic = code = strike = False
        link_url = None

        for ann in annotations:
            if not ann:
                continue
            kind = ann[0] if ann else None
            val = ann[1] if len(ann) > 1 else None
            if kind == "b":
                bold = True
            elif kind == "i":
                italic = True
            elif kind == "c":
                code = True
            elif kind == "s":
                strike = True
            elif kind == "a":
                link_url = val
                if link_url and is_notion_url(link_url):
                    try:
                        pid = extract_page_id(link_url)
                        if pid in _slug_cache:
                            link_url = "{% post_url " + _slug_cache[pid] + " %}"
                    except ValueError:
                        pass
            elif kind == "lm":
                # Link mention (링크 프리뷰)
                if isinstance(val, dict):
                    link_url = val.get("href", "")
                    # 링크 제목이 있으면 텍스트로 사용
                    link_title = val.get("title", "")
                    if link_title and text == "‣":
                        text = link_title
                    if link_url and is_notion_url(link_url):
                        try:
                            pid = extract_page_id(link_url)
                            if pid in _slug_cache:
                                link_url = "{% post_url " + _slug_cache[pid] + " %}"
                        except ValueError:
                            pass

        if code:
            text = f"`{text}`"
        if bold:
            text = f"**{text}**"
        if italic:
            text = f"*{text}*"
        if strike:
            text = f"~~{text}~~"
        if link_url:
            text = f"[{text}]({link_url})"

        result.append(text)

    return "".join(result)


# ─── 블록 → Markdown ──────────────────────────────────────────────────────────

def render_block(bval: dict, blocks: dict, depth: int = 0, number: int = None) -> str:
    """단일 블록을 마크다운 문자열로 변환합니다."""
    btype = bval.get("type", "")
    props = bval.get("properties", {})
    children = bval.get("content", [])
    indent = "  " * depth

    title = rich_text_to_md(props.get("title", []))

    # ── 페이지 (child page) ──────────────────────────────────────────────────
    if btype == "page":
        page_title = title or "Untitled"
        created_time = bval.get("created_time")
        if created_time:
            dt = datetime.fromtimestamp(created_time / 1000, tz=timezone.utc)
            date_prefix = dt.strftime("%Y-%m-%d")
        else:
            date_prefix = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
        post_slug = date_prefix + "-" + sanitize_filename(page_title)
        return "[" + page_title + "]({% post_url " + post_slug + " %})"

    # ── 제목 ────────────────────────────────────────────────────────────────
    elif btype in ("heading_1", "header"):
        return f"\n# {title}\n"
    elif btype in ("heading_2", "sub_header"):
        return f"\n## {title}\n"
    elif btype in ("heading_3", "sub_sub_header"):
        return f"\n### {title}\n"

    # ── 단락 ────────────────────────────────────────────────────────────────
    elif btype == "paragraph":
        formatted_title = f"{indent}- {title}" if (depth > 0 and title) else title
        child_md = render_blocks(children, blocks, depth + 1) if children else ""
        parts = [p for p in [formatted_title, child_md] if p]
        return "\n".join(parts) if parts else ""

    # ── 목록 ────────────────────────────────────────────────────────────────
    elif btype in ("bulleted_list_item", "bulleted_list"):
        line = f"{indent}- {title}"
        child_md = render_blocks(children, blocks, depth + 1) if children else ""
        return "\n".join(p for p in [line, child_md] if p)

    elif btype in ("numbered_list_item", "numbered_list"):
        n = number if number is not None else 1
        line = f"{indent}{n}. {title}"
        child_md = render_blocks(children, blocks, depth + 1) if children else ""
        return "\n".join(p for p in [line, child_md] if p)

    elif btype == "to_do":
        checked = props.get("checked", [["No"]])[0][0] == "Yes"
        cb = "x" if checked else " "
        line = f"{indent}- [{cb}] {title}"
        child_md = render_blocks(children, blocks, depth + 1) if children else ""
        return "\n".join(p for p in [line, child_md] if p)

    # ── 토글 ────────────────────────────────────────────────────────────────
    elif btype == "toggle":
        line = f"{indent}**{title}**"
        child_md = render_blocks(children, blocks, depth + 1) if children else ""
        return "\n".join(p for p in [line, child_md] if p)

    # ── 인용 / 콜아웃 ────────────────────────────────────────────────────────
    elif btype == "quote":
        lines = [f"> {l}" for l in title.split("\n")]
        return "\n".join(lines)

    elif btype == "callout":
        icon = bval.get("format", {}).get("page_icon", "")
        return f"> {icon} {title}".strip()

    # ── 코드 ────────────────────────────────────────────────────────────────
    elif btype == "code":
        lang = ""
        if "language" in props and props["language"]:
            lang = props["language"][0][0].lower()
            if lang == "plain text":
                lang = ""
        return f"\n```{lang}\n{title}\n```\n"

    # ── 이미지 ──────────────────────────────────────────────────────────────
    elif btype == "image":
        source = ""
        if "source" in props and props["source"]:
            source = props["source"][0][0]
        if not source:
            source = bval.get("format", {}).get("display_source", "")
        caption = rich_text_to_md(props.get("caption", []))
        if source:
            return f"\n![{caption}]({source})\n"
        else:
            return f"\n> [이미지 - 권한 필요]\n"

    # ── 구분선 ──────────────────────────────────────────────────────────────
    elif btype == "divider":
        return "\n---\n"

    # ── 링크 / 임베드 ────────────────────────────────────────────────────────
    elif btype == "bookmark":
        link = props.get("link", [[""]])[0][0] if "link" in props else ""
        cap_raw = props.get("caption", [])
        cap = rich_text_to_md(cap_raw) if cap_raw else link
        return f"[{cap or link}]({link})"

    elif btype == "embed":
        source = props.get("source", [[""]])[0][0] if "source" in props else ""
        return f"[임베드]({source})"

    elif btype == "video":
        source = props.get("source", [[""]])[0][0] if "source" in props else ""
        return f"[동영상]({source})"

    # ── 수식 ────────────────────────────────────────────────────────────────
    elif btype == "equation":
        expr = props.get("title", [[""]])[0][0] if "title" in props else ""
        return f"\n$$\n{expr}\n$$\n"

    # ── 테이블 ──────────────────────────────────────────────────────────────
    elif btype == "table":
        fmt = bval.get("format", {}) or {}
        col_order = fmt.get("table_block_column_order", [])
        has_col_header = fmt.get("table_block_column_header", False)

        rows_md = []
        for i, row_id in enumerate(children):
            if row_id not in blocks:
                continue
            row_props = blocks[row_id].get("value", {}).get("properties", {}) or {}

            if col_order:
                cells = [rich_text_to_md(row_props.get(col, [])) for col in col_order]
            else:
                cells = [rich_text_to_md(v) for v in row_props.values()]

            # 셀 안의 줄바꿈은 마크다운 테이블을 깨뜨리므로 공백으로 치환
            cells = [c.replace("\n", " ").strip() for c in cells]

            rows_md.append("| " + " | ".join(cells) + " |")

            # 첫 행이 헤더인 경우 구분선 추가
            if i == 0 and has_col_header:
                rows_md.append("| " + " | ".join(["---"] * len(cells)) + " |")

        # 헤더 지정 없어도 마크다운 테이블은 구분선 필요 — 첫 행 뒤에 추가
        if rows_md and not has_col_header:
            first_cell_count = rows_md[0].count("|") - 1
            rows_md.insert(1, "| " + " | ".join(["---"] * first_cell_count) + " |")

        return "\n" + "\n".join(rows_md) + "\n" if rows_md else ""

    elif btype == "table_row":
        # table 핸들러 안에서 처리되므로 단독 호출 시 fallback
        cells = [rich_text_to_md(v) for v in props.values()]
        return "| " + " | ".join(cells) + " |"

    # ── 컬럼 레이아웃 ────────────────────────────────────────────────────────
    elif btype in ("column_list", "column"):
        return render_blocks(children, blocks, depth) if children else ""

    # ── 목차 (skip) ──────────────────────────────────────────────────────────
    elif btype == "table_of_contents":
        return ""

    # ── 기타 폴백 ────────────────────────────────────────────────────────────
    else:
        formatted_title = f"{indent}- {title}" if (depth > 0 and title) else title
        child_md = render_blocks(children, blocks, depth + 1) if children else ""
        parts = [p for p in [formatted_title, child_md] if p]
        return "\n".join(parts) if parts else ""


def render_blocks(block_ids: list, blocks: dict, depth: int = 0) -> str:
    """블록 ID 목록을 순서대로 마크다운으로 변환합니다."""
    parts = []
    numbered_counter = 0
    for bid in block_ids:
        if bid not in blocks:
            continue
        bval = blocks[bid].get("value", {})
        btype = bval.get("type", "")

        if btype in ("numbered_list_item", "numbered_list"):
            numbered_counter += 1
        else:
            numbered_counter = 0

        md = render_block(
            bval, blocks, depth,
            number=numbered_counter if btype in ("numbered_list_item", "numbered_list") else None
        )
        if md is not None:
            parts.append(md)
    return "\n".join(parts)


# ─── Notion 링크 수집 ────────────────────────────────────────────────────────

NOTION_HOST_RE = re.compile(r'https://(?:[\w-]+\.notion\.site|(?:www\.)?notion\.so)/')

def is_notion_url(url: str) -> bool:
    return bool(url and NOTION_HOST_RE.match(url))

def collect_notion_links(blocks: dict) -> set:
    """모든 블록의 rich text에서 Notion 페이지 링크 ID를 수집합니다."""
    linked_ids = set()
    for bdata in blocks.values():
        val = bdata.get("value", {})
        props = val.get("properties", {})
        for prop_val in props.values():
            if not isinstance(prop_val, list):
                continue
            for seg in prop_val:
                if not isinstance(seg, list) or len(seg) < 2:
                    continue
                for ann in seg[1]:
                    if not ann:
                        continue
                    kind = ann[0] if ann else None
                    ann_val = ann[1] if len(ann) > 1 else None
                    url = None
                    if kind == "a" and isinstance(ann_val, str):
                        url = ann_val
                    elif kind == "lm" and isinstance(ann_val, dict):
                        url = ann_val.get("href", "")
                    if url and is_notion_url(url):
                        try:
                            linked_ids.add(extract_page_id(url))
                        except ValueError:
                            pass
    return linked_ids


# ─── 페이지 변환 메인 로직 ────────────────────────────────────────────────────

def get_page_title(page_id: str, blocks: dict) -> str:
    val = blocks.get(page_id, {}).get("value", {})
    segs = val.get("properties", {}).get("title", [])
    return rich_text_to_md(segs) or "Untitled"


def get_page_date(page_id: str, blocks: dict) -> str:
    """페이지의 created_time(Unix ms)을 YYYY-MM-DD 문자열로 반환합니다."""
    val = blocks.get(page_id, {}).get("value", {})
    created_time = val.get("created_time")
    if created_time:
        dt = datetime.fromtimestamp(created_time / 1000, tz=timezone.utc)
        return dt.strftime("%Y-%m-%d")
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")


def sanitize_filename(title: str) -> str:
    """파일명에 사용할 수 없는 문자를 제거합니다."""
    name = re.sub(r'[<>:"/\\|?*\n\r]', "", title).strip()
    return name or "Untitled"


def convert_page(page_id: str, output_dir: str, visited: set = None, rewrite: bool = False):
    """페이지를 마크다운으로 변환하고, child page 및 본문 내 Notion 링크도 재귀 처리합니다."""
    if visited is None:
        visited = set()
    if page_id in visited:
        return
    visited.add(page_id)

    print(f"페이지 가져오는 중: {page_id}")
    try:
        blocks = fetch_blocks(page_id)
    except Exception as e:
        print(f"  오류: {e}")
        return

    title = get_page_title(page_id, blocks)
    date_str = get_page_date(page_id, blocks)

    Path(output_dir).mkdir(parents=True, exist_ok=True)
    post_slug = f"{date_str}-{sanitize_filename(title)}"
    filename = post_slug + ".md"
    output_path = Path(output_dir) / filename

    # slug 캐시에 등록 (rich text 링크 변환에 사용)
    _slug_cache[page_id] = post_slug

    # 동일 파일 존재 시 스킵 (--rewrite 시 덮어쓰기)
    if output_path.exists():
        if rewrite:
            output_path.unlink()
            print(f"  덮어쓰기: {filename}")
        else:
            print(f"  스킵 (이미 존재): {filename}")
            return

    print(f"  제목: {title} ({date_str})")

    # 루트 페이지의 content 블록들 렌더링
    root_val = blocks.get(page_id, {}).get("value", {})
    content_ids = root_val.get("content", [])
    md_body = render_blocks(content_ids, blocks, depth=0)

    front_matter = f'---\ntitle: "{title}"\ndate: {date_str}\ntags: [미지정]\n---\n'

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(front_matter + md_body)

    print(f"  저장: {output_path}")

    # 1. child page (type="page" 블록) DFS
    for bid in content_ids:
        if bid not in blocks:
            continue
        bval = blocks[bid].get("value", {})
        if bval.get("type") == "page":
            convert_page(bid, output_dir, visited, rewrite=rewrite)

    # 2. 본문 내 Notion 링크 DFS
    for linked_id in collect_notion_links(blocks):
        convert_page(linked_id, output_dir, visited, rewrite=rewrite)


# ─── 진입점 ──────────────────────────────────────────────────────────────────

def main():
    args = sys.argv[1:]
    rewrite = "--rewrite" in args
    args = [a for a in args if a != "--rewrite"]

    if len(args) < 2:
        print("사용법: python notion_to_obsidian.py <output_dir> <notion_url> [--rewrite]")
        print("예시:   python notion_to_obsidian.py ./_posts https://stump-blender-387.notion.site/abc123def456")
        print("        python notion_to_obsidian.py ./_posts https://stump-blender-387.notion.site/abc123def456 --rewrite")
        sys.exit(1)

    output_dir = args[0]
    url = args[1]

    try:
        page_id = extract_page_id(url)
        print(f"페이지 ID: {page_id}")
    except ValueError as e:
        print(f"오류: {e}")
        sys.exit(1)

    convert_page(page_id, output_dir, rewrite=rewrite)
    print("\n완료!")


if __name__ == "__main__":
    main()
