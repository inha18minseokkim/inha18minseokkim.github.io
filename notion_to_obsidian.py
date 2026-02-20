#!/usr/bin/env python3
"""
notion_to_obsidian.py

공개 Notion 페이지(splitbee API 경유)를 Obsidian 마크다운 파일로 변환합니다.
하위 페이지(child page)도 DFS로 순회하며 각각 별도 .md 파일로 생성합니다.

사용법:
    python notion_to_obsidian.py <notion_url> [output_dir]

예시:
    python notion_to_obsidian.py https://stump-blender-387.notion.site/abc123 ./output
"""

import sys
import re
import json
import urllib.request
import os
from pathlib import Path

SPLITBEE_API = "https://notion-api.splitbee.io/v1/page/"


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

def render_block(bval: dict, blocks: dict, depth: int = 0) -> str:
    """단일 블록을 마크다운 문자열로 변환합니다."""
    btype = bval.get("type", "")
    props = bval.get("properties", {})
    children = bval.get("content", [])
    indent = "  " * depth

    title = rich_text_to_md(props.get("title", []))

    # ── 페이지 (child page) ──────────────────────────────────────────────────
    if btype == "page":
        page_title = title or "Untitled"
        return f"[[{page_title}]]"

    # ── 제목 ────────────────────────────────────────────────────────────────
    elif btype in ("heading_1", "header"):
        return f"\n# {title}\n"
    elif btype in ("heading_2", "sub_header"):
        return f"\n## {title}\n"
    elif btype in ("heading_3", "sub_sub_header"):
        return f"\n### {title}\n"

    # ── 단락 ────────────────────────────────────────────────────────────────
    elif btype == "paragraph":
        child_md = render_blocks(children, blocks, depth) if children else ""
        parts = [p for p in [title, child_md] if p]
        return "\n".join(parts) if parts else ""

    # ── 목록 ────────────────────────────────────────────────────────────────
    elif btype == "bulleted_list_item":
        line = f"{indent}- {title}"
        child_md = render_blocks(children, blocks, depth + 1) if children else ""
        return "\n".join(p for p in [line, child_md] if p)

    elif btype == "numbered_list_item":
        line = f"{indent}1. {title}"
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
        return render_blocks(children, blocks, depth) if children else ""

    elif btype == "table_row":
        cells = props.get("cells", [])
        cell_texts = [rich_text_to_md(cell) for cell in cells]
        return "| " + " | ".join(cell_texts) + " |"

    # ── 컬럼 레이아웃 ────────────────────────────────────────────────────────
    elif btype in ("column_list", "column"):
        return render_blocks(children, blocks, depth) if children else ""

    # ── 목차 (skip) ──────────────────────────────────────────────────────────
    elif btype == "table_of_contents":
        return ""

    # ── 기타 폴백 ────────────────────────────────────────────────────────────
    else:
        child_md = render_blocks(children, blocks, depth) if children else ""
        parts = [p for p in [title, child_md] if p]
        return "\n".join(parts) if parts else ""


def render_blocks(block_ids: list, blocks: dict, depth: int = 0) -> str:
    """블록 ID 목록을 순서대로 마크다운으로 변환합니다."""
    parts = []
    for bid in block_ids:
        if bid not in blocks:
            continue
        bval = blocks[bid].get("value", {})
        md = render_block(bval, blocks, depth)
        if md is not None:
            parts.append(md)
    return "\n".join(parts)


# ─── 페이지 변환 메인 로직 ────────────────────────────────────────────────────

def get_page_title(page_id: str, blocks: dict) -> str:
    val = blocks.get(page_id, {}).get("value", {})
    segs = val.get("properties", {}).get("title", [])
    return rich_text_to_md(segs) or "Untitled"


def sanitize_filename(title: str) -> str:
    """파일명에 사용할 수 없는 문자를 제거합니다."""
    name = re.sub(r'[<>:"/\\|?*\n\r]', "", title).strip()
    return name or "Untitled"


def convert_page(page_id: str, output_dir: str, visited: set = None):
    """페이지를 마크다운으로 변환하고, 하위 페이지도 재귀적으로 처리합니다."""
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
    print(f"  제목: {title}")

    # 루트 페이지의 content 블록들 렌더링
    root_val = blocks.get(page_id, {}).get("value", {})
    content_ids = root_val.get("content", [])
    md_body = render_blocks(content_ids, blocks, depth=0)

    # 파일 저장
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    filename = sanitize_filename(title) + ".md"
    output_path = Path(output_dir) / filename

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(md_body)

    print(f"  저장: {output_path}")

    # 하위 child page 재귀 처리
    for bid in content_ids:
        if bid not in blocks:
            continue
        bval = blocks[bid].get("value", {})
        if bval.get("type") == "page":
            convert_page(bid, output_dir, visited)


# ─── 진입점 ──────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print("사용법: python notion_to_obsidian.py <notion_url> [output_dir]")
        print("예시:   python notion_to_obsidian.py https://stump-blender-387.notion.site/abc123def456 ./output")
        sys.exit(1)

    url = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "."

    try:
        page_id = extract_page_id(url)
        print(f"페이지 ID: {page_id}")
    except ValueError as e:
        print(f"오류: {e}")
        sys.exit(1)

    convert_page(page_id, output_dir)
    print("\n완료!")


if __name__ == "__main__":
    main()
