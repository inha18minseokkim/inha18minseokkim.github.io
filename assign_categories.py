#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
assign_categories.py

Usage: python assign_categories.py  (from blog root directory)

Scans all _posts/*.md files and adds a 'category' front matter field.
Skips files that already have a 'category' field.

Category priority: 재테크 > 실무경험 > 기술 > 기타 (fallback)
"""

import os
import re

POSTS_DIR = "_posts"

# ── Tag → Category mapping ──────────────────────────────────────────────────
TAG_TO_CATEGORY = {
    "재테크": {
        "주식", "공모주", "부동산", "금융", "경제", "재테크", "가상자산",
        "opendart", "공시", "전문투자자", "도메인지식", "재무",
    },
    "실무경험": {
        "케이뱅크", "이슈정리", "장애분석", "수상", "발표", "인턴", "기획",
    },
    "기술": {
        "java", "spring", "jpa", "kotlin", "webflux", "redis", "cache",
        "msa", "아키텍처", "ai", "llm", "langchain", "rag", "mcp",
        "분산시스템", "saga", "cqrs", "docker", "인프라", "python", "크롤링",
        "백엔드", "http", "알고리즘", "삽질", "디버깅", "공공api", "개발환경",
        "개발", "arm", "windows", "wsl", "macos",
    },
}

CATEGORY_PRIORITY = ["재테크", "실무경험", "기술"]

# ── Title/filename keyword fallback ─────────────────────────────────────────
TITLE_KEYWORDS = {
    "재테크": ["주식", "공모주", "etf", "부동산", "재테크", "금융", "경제",
               "청약", "배당", "아파트", "전문투자자"],
    "실무경험": ["회의록", "케이뱅크", "세미나", "poc", "tf", "인턴", "수상",
                "발표", "야놀자"],
    "기술": ["java", "spring", "jpa", "kotlin", "msa", "ai", "llm",
             "python", "docker", "redis", "http", "알고리즘", "n+1",
             "upsert", "batch", "aws", "macos", "wsl", "surface", "arm"],
}


# ── Helpers ──────────────────────────────────────────────────────────────────

def parse_tags(front_matter: str) -> list:
    """Extract tag list from front matter text (inline or multi-line YAML)."""
    # Inline: tags: [foo, bar]
    m = re.search(r"^tags\s*:\s*\[([^\]]*)\]", front_matter, re.MULTILINE)
    if m:
        return [t.strip().strip("\"'") for t in m.group(1).split(",") if t.strip()]

    # Multi-line:
    #   tags:
    #     - foo
    #     - bar
    m = re.search(r"^tags\s*:", front_matter, re.MULTILINE)
    if m:
        after = front_matter[m.end():]
        tags = []
        for line in after.split("\n"):
            stripped = line.strip()
            if stripped.startswith("- "):
                tags.append(stripped[2:].strip().strip("\"'"))
            elif stripped and not stripped.startswith("#"):
                break  # non-list line → end of tags block
        return tags

    return []


def get_category_from_tags(tags: list) -> str:
    lower_tags = {t.lower() for t in tags}
    for cat in CATEGORY_PRIORITY:
        for expected in TAG_TO_CATEGORY[cat]:
            if expected in lower_tags:
                return cat
    return ""


def get_category_from_text(title: str, filename: str) -> str:
    text = (title + " " + filename).lower()
    for cat in CATEGORY_PRIORITY:
        for kw in TITLE_KEYWORDS[cat]:
            if kw in text:
                return cat
    return "기타"


def extract_title(front_matter: str) -> str:
    m = re.search(r'^title\s*:\s*["\']?(.+?)["\']?\s*$', front_matter, re.MULTILINE)
    return m.group(1).strip().strip("\"'") if m else ""


# ── Main processor ───────────────────────────────────────────────────────────

def process_file(filepath: str) -> tuple:
    """
    Returns (modified: bool, category: str).
    modified=False means the file was skipped (already had category or parse error).
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except UnicodeDecodeError:
        try:
            with open(filepath, "r", encoding="utf-8-sig") as f:
                content = f.read()
        except Exception as e:
            print(f"  [ERROR] Cannot read {filepath}: {e}")
            return False, ""

    if not content.startswith("---"):
        return False, ""

    # Locate end of front matter
    end_idx = content.find("\n---", 3)
    if end_idx == -1:
        return False, ""

    front_matter = content[3:end_idx]      # text between opening and closing ---
    body = content[end_idx + 4:]           # text after closing ---

    # Skip if category already present
    if re.search(r"^\s*category\s*:", front_matter, re.MULTILINE):
        m = re.search(r"^\s*category\s*:\s*(.+)$", front_matter, re.MULTILINE)
        return False, m.group(1).strip() if m else ""

    # Determine category
    tags = [t for t in parse_tags(front_matter) if t and t != "미지정"]
    category = get_category_from_tags(tags)
    if not category:
        title = extract_title(front_matter)
        filename = os.path.basename(filepath)
        category = get_category_from_text(title, filename)

    # Rebuild file content with category appended to front matter
    new_fm = front_matter.rstrip("\n") + f"\ncategory: {category}\n"
    new_content = f"---{new_fm}---{body}"

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new_content)
        return True, category
    except Exception as e:
        print(f"  [ERROR] Cannot write {filepath}: {e}")
        return False, category


def main():
    md_files = []
    for root, _dirs, files in os.walk(POSTS_DIR):
        for fname in files:
            if fname.endswith(".md"):
                md_files.append(os.path.join(root, fname))

    if not md_files:
        print(f"No .md files found in '{POSTS_DIR}/'")
        return

    print(f"Found {len(md_files)} markdown files in '{POSTS_DIR}/'")
    print("─" * 60)

    counts = {"재테크": 0, "실무경험": 0, "기술": 0, "기타": 0}
    modified = 0
    skipped = 0

    for filepath in sorted(md_files):
        changed, category = process_file(filepath)
        if changed:
            modified += 1
            counts[category] = counts.get(category, 0) + 1
            print(f"  [{category}] {os.path.basename(filepath)}")
        else:
            skipped += 1

    print("─" * 60)
    print(f"Done!  Modified: {modified}  |  Skipped: {skipped}")
    print(f"Category breakdown: {counts}")


if __name__ == "__main__":
    main()
