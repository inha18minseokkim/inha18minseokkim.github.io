#!/usr/bin/env python3
"""
포스팅 간 유사도 기반 연관 포스팅 데이터 생성 스크립트
Apple Metal(MPS) 가속 사용

사용법: python3 generate_related_posts.py
출력: _data/related_posts.yml
"""

import json
import os
import re
import sys
import yaml
import numpy as np
import frontmatter
from pathlib import Path
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

POSTS_DIR = Path("_posts")
OUTPUT_FILE = Path("_data/related_posts.yml")
BASE_MODEL_NAME = "paraphrase-multilingual-mpnet-base-v2"
FINETUNED_MODEL_DIR = Path("models/finetuned-embedding")
# 검색 모델은 브라우저(_layouts/default.html SEARCH_MODEL)와 반드시 동일해야 한다
# MiniLM(117MB quantized)으로 유지 — mpnet(278MB)은 블로그 첫 방문자가 감당하기 과함
SEARCH_MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
SEARCH_OUTPUT_FILE = Path("assets/search/embeddings.json")
TOP_K = 5
MAX_BODY_CHARS = 1000


def strip_markdown(text: str) -> str:
    text = re.sub(r"```[\s\S]*?```", "", text)
    text = re.sub(r"`[^`]+`", "", text)
    text = re.sub(r"!\[.*?\]\(.*?\)", "", text)
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"\*{1,3}([^*\n]+)\*{1,3}", r"\1", text)
    text = re.sub(r"_{1,3}([^_\n]+)_{1,3}", r"\1", text)
    text = re.sub(r"^[-*_]{3,}$", "", text, flags=re.MULTILINE)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def build_embed_text(meta: dict, body: str) -> str:
    title = str(meta.get("title", ""))
    tags = meta.get("tags", [])
    if isinstance(tags, str):
        tags = [tags]
    tag_str = " ".join(str(t) for t in tags)
    clean_body = strip_markdown(body)[:MAX_BODY_CHARS]
    return " ".join(filter(None, [title, tag_str, clean_body]))


def filename_to_url(filename: str) -> str:
    """YYYY-MM-DD-slug.md → /YYYY/MM/DD/slug/"""
    name = filename[:-3]  # remove .md
    if len(name) >= 11 and name[10] == "-" and name[:10].replace("-", "").isdigit():
        date_str, slug = name[:10], name[11:]
        y, m, d = date_str.split("-")
        return f"/{y}/{m}/{d}/{slug}/"
    return f"/{name}/"


def load_posts() -> list[dict]:
    posts = []
    for md_file in sorted(POSTS_DIR.glob("*.md")):
        try:
            post = frontmatter.load(md_file)
            date_raw = post.metadata.get("date", "")
            date_str = str(date_raw)[:10] if date_raw else ""
            tags = post.metadata.get("tags", [])
            if isinstance(tags, str):
                tags = [tags]
            posts.append({
                "key": md_file.stem,
                "title": str(post.metadata.get("title", md_file.stem)),
                "date": date_str,
                "url": filename_to_url(md_file.name),
                "tags": [str(t) for t in tags],
                "text": build_embed_text(post.metadata, post.content),
            })
        except Exception as e:
            print(f"  skip {md_file.name}: {e}", file=sys.stderr)
    return posts


def main():
    import torch

    posts = load_posts()
    print(f"포스팅 {len(posts)}개 로드 완료")

    device = "mps" if torch.backends.mps.is_available() else "cpu"
    print(f"디바이스: {device}")

    if FINETUNED_MODEL_DIR.exists():
        model_path = str(FINETUNED_MODEL_DIR)
        print(f"파인튜닝 모델 로드: {model_path}")
    else:
        model_path = BASE_MODEL_NAME
        print(f"기본 모델 로드: {model_path}")
        print("  (파인튜닝하려면 python3 finetune_embedding.py 실행)")
    model = SentenceTransformer(model_path, device=device)

    print("임베딩 생성 중...")
    texts = [p["text"] for p in posts]
    embeddings = model.encode(
        texts,
        batch_size=32,
        show_progress_bar=True,
        convert_to_numpy=True,
    )

    print("유사도 행렬 계산 중...")
    sim_matrix = cosine_similarity(embeddings)

    related: dict[str, list] = {}
    for i, post in enumerate(posts):
        sims = sim_matrix[i].copy()
        sims[i] = -1.0
        top_idx = np.argsort(sims)[::-1][:TOP_K]
        related[post["key"]] = [
            {
                "title": posts[j]["title"],
                "url": posts[j]["url"],
                "date": posts[j]["date"],
            }
            for j in top_idx
        ]

    OUTPUT_FILE.parent.mkdir(exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        yaml.dump(related, f, allow_unicode=True, sort_keys=True, default_flow_style=False)

    print(f"완료: {OUTPUT_FILE} ({len(related)}개 항목)")

    # ── 검색용 임베딩 생성 (MiniLM-L12-v2, 브라우저와 동일 모델) ─────────────
    print(f"\n검색 임베딩 생성 중: {SEARCH_MODEL_NAME}")
    search_model = SentenceTransformer(SEARCH_MODEL_NAME, device=device)
    search_embs = search_model.encode(
        texts,
        batch_size=32,
        show_progress_bar=True,
        convert_to_numpy=True,
    )

    # 브라우저에서 dot product = cosine이 되도록 정규화
    norms = np.linalg.norm(search_embs, axis=1, keepdims=True)
    normalized = search_embs / np.maximum(norms, 1e-9)

    search_data = {
        "dim": int(search_embs.shape[1]),
        "posts": [
            {
                "title": p["title"],
                "url": p["url"],
                "date": p["date"],
                "tags": p["tags"],
            }
            for p in posts
        ],
        "vecs": [[round(float(v), 5) for v in vec] for vec in normalized],
    }

    SEARCH_OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SEARCH_OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(search_data, f, ensure_ascii=False, separators=(",", ":"))

    size_kb = SEARCH_OUTPUT_FILE.stat().st_size // 1024
    print(f"완료: {SEARCH_OUTPUT_FILE} ({len(posts)}개, dim={search_data['dim']}, {size_kb}KB)")


if __name__ == "__main__":
    main()
