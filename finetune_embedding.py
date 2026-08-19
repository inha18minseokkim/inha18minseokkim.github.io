#!/usr/bin/env python3
"""
블로그 포스팅 기반 임베딩 모델 파인튜닝

사용법: python3 finetune_embedding.py
출력: ./models/finetuned-embedding/ (fine-tuned 모델)

이후 generate_related_posts.py를 실행하면 파인튜닝된 모델로 임베딩을 갱신한다.
"""

import json
import random
import re
from collections import defaultdict
from itertools import combinations
from pathlib import Path

import frontmatter
import torch
from sentence_transformers import InputExample, SentenceTransformer, losses
from torch.utils.data import DataLoader

POSTS_DIR = Path("_posts")
BASE_MODEL = "paraphrase-multilingual-mpnet-base-v2"
OUTPUT_DIR = Path("models/finetuned-embedding")
CHECKPOINT_DIR = OUTPUT_DIR / "checkpoints"

# 파인튜닝 하이퍼파라미터
EPOCHS = 3
BATCH_SIZE = 16
MAX_TAG_PAIRS = 3000  # 태그 공유 쌍 상한

# 학습 데이터 마이닝에서 제외할 범용 태그 (너무 넓어서 의미 없는 쌍이 생김)
GENERIC_TAGS = {"개발", "기술", "이슈정리", "삽질", "기타"}

# 자동 마이닝으로 연결이 약한 시리즈/연관 포스팅을 명시적으로 지정
# 코드 블록 위주 포스팅은 strip 후 텍스트가 적어 임베딩이 약해지는 문제를 보완
MANUAL_SERIES: list[tuple[str, str]] = [
    (
        "2025-01-21-netty-native-memory-issue",
        "2025-02-16-netty-phantom-reference-gc",
    ),
    (
        "2025-01-21-netty-native-memory-issue",
        "2025-09-08-java-committed-memory-increase-investigation",
    ),
    (
        "2025-02-16-netty-phantom-reference-gc",
        "2025-09-08-java-committed-memory-increase-investigation",
    ),
]


def strip_markdown(text: str) -> str:
    text = re.sub(r"```[\s\S]*?```", "", text)
    text = re.sub(r"`[^`]+`", "", text)
    text = re.sub(r"!\[.*?\]\(.*?\)", "", text)
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"\*{1,3}([^*\n]+)\*{1,3}", r"\1", text)
    text = re.sub(r"_{1,3}([^_\n]+)_{1,3}", r"\1", text)
    text = re.sub(r"~~[^~]+~~", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_sections(content: str) -> list[tuple[str, str]]:
    """## / ### 헤더와 그 아래 내용을 (헤더, 내용) 쌍으로 추출"""
    sections: list[tuple[str, str]] = []
    current_header: str | None = None
    current_lines: list[str] = []

    for line in content.split("\n"):
        m = re.match(r"^(#{2,3})\s+(.+)", line)
        if m:
            if current_header and current_lines:
                body = strip_markdown("\n".join(current_lines)).strip()
                if len(body) > 80:
                    sections.append((current_header, body[:500]))
            current_header = m.group(2).strip()
            current_lines = []
        else:
            current_lines.append(line)

    if current_header and current_lines:
        body = strip_markdown("\n".join(current_lines)).strip()
        if len(body) > 80:
            sections.append((current_header, body[:500]))

    return sections


def load_posts() -> list[dict]:
    posts = []
    for md_file in sorted(POSTS_DIR.glob("*.md")):
        try:
            p = frontmatter.load(md_file)
            title = str(p.metadata.get("title", md_file.stem))
            tags_raw = p.metadata.get("tags", [])
            if isinstance(tags_raw, str):
                tags_raw = [tags_raw]
            tags = [str(t) for t in tags_raw]
            meaningful_tags = {t for t in tags if t not in GENERIC_TAGS}

            clean_body = strip_markdown(p.content)
            paragraphs = [
                para.strip()
                for para in clean_body.split("\n\n")
                if len(para.strip()) > 60
            ]
            sections = extract_sections(p.content)

            summary = title
            if paragraphs:
                summary = title + ". " + paragraphs[0][:250]

            posts.append(
                {
                    "key": md_file.stem,
                    "title": title,
                    "tags": set(tags),
                    "meaningful_tags": meaningful_tags,
                    "body": clean_body,
                    "paragraphs": paragraphs,
                    "sections": sections,
                    "summary": summary,
                }
            )
        except Exception as e:
            print(f"  skip {md_file.name}: {e}")

    return posts


def mine_pairs(posts: list[dict]) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []

    # Type A: 포스팅 제목 → 본문 첫 단락 (강한 직접 연관)
    type_a = 0
    for post in posts:
        if post["paragraphs"]:
            pairs.append((post["title"], post["paragraphs"][0][:400]))
            type_a += 1
        if len(post["body"]) > 300 and len(post["paragraphs"]) > 1:
            pairs.append((post["title"], post["body"][:500]))
            type_a += 1

    # Type B: 섹션 헤더 → 섹션 내용 (포스팅 내 구조 학습)
    type_b = 0
    for post in posts:
        for header, content in post["sections"]:
            # 포스팅 제목 + 섹션 헤더 → 섹션 내용 (더 강한 문맥)
            pairs.append((post["title"] + " — " + header, content))
            pairs.append((header, content))
            type_b += 2

    # Type C: 의미 있는 공통 태그 보유 포스트 쌍 (유사 주제 포스팅)
    tag_to_idxs: dict[str, list[int]] = defaultdict(list)
    for i, post in enumerate(posts):
        for tag in post["meaningful_tags"]:
            tag_to_idxs[tag].append(i)

    # 쌍별 공유 태그 수 집계
    pair_shared: dict[tuple[int, int], int] = defaultdict(int)
    for tag, idxs in tag_to_idxs.items():
        if len(idxs) < 2:
            continue
        # 같은 태그를 너무 많이 가진 클러스터는 상위 50개만 참여
        for a, b in combinations(idxs[:50], 2):
            pair_shared[(min(a, b), max(a, b))] += 1

    # 공유 태그 수 내림차순, MAX_TAG_PAIRS 선택
    sorted_pairs = sorted(pair_shared.items(), key=lambda x: -x[1])[:MAX_TAG_PAIRS]
    type_c = 0
    for (a, b), _ in sorted_pairs:
        pairs.append((posts[a]["summary"], posts[b]["summary"]))
        type_c += 1

    # Type D: 수동 지정 시리즈 페어 (코드 위주 포스팅 임베딩 보완)
    post_map = {p["key"]: p for p in posts}
    type_d = 0
    for key_a, key_b in MANUAL_SERIES:
        pa, pb = post_map.get(key_a), post_map.get(key_b)
        if not pa or not pb:
            continue
        # 제목↔제목, 요약↔요약, 본문↔본문 세 가지 표현으로 반복 학습
        # body를 넉넉히 써야 코드 블록 위주 포스팅의 핵심 키워드가 학습에 반영됨
        pairs.append((pa["title"], pb["title"]))
        pairs.append((pa["summary"], pb["summary"]))
        pairs.append((pa["body"][:1500], pb["body"][:1500]))
        type_d += 3

    print(f"  Type A (제목→본문):    {type_a:4d}쌍")
    print(f"  Type B (섹션 구조):    {type_b:4d}쌍")
    print(f"  Type C (태그 공유):    {type_c:4d}쌍")
    print(f"  Type D (수동 시리즈):  {type_d:4d}쌍")

    return pairs


def deduplicate(pairs: list[tuple[str, str]]) -> list[tuple[str, str]]:
    seen: set[tuple[str, str]] = set()
    out = []
    for a, b in pairs:
        key = (a[:120], b[:120])
        if key not in seen:
            seen.add(key)
            out.append((a, b))
    return out


def run_finetune(pairs: list[tuple[str, str]], device: str) -> None:
    print(f"\n기본 모델 로드 중: {BASE_MODEL}")
    model = SentenceTransformer(BASE_MODEL, device=device)

    train_examples = [InputExample(texts=[a, b]) for a, b in pairs]
    train_dataloader = DataLoader(train_examples, shuffle=True, batch_size=BATCH_SIZE)
    train_loss = losses.MultipleNegativesRankingLoss(model)

    warmup_steps = max(1, int(len(train_dataloader) * EPOCHS * 0.1))
    print(
        f"파인튜닝: {EPOCHS} epochs / {len(pairs)}쌍 / "
        f"배치 {BATCH_SIZE} / warmup {warmup_steps}스텝"
    )

    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    model.fit(
        train_objectives=[(train_dataloader, train_loss)],
        epochs=EPOCHS,
        warmup_steps=warmup_steps,
        show_progress_bar=True,
        checkpoint_path=str(CHECKPOINT_DIR),
        checkpoint_save_steps=len(train_dataloader),
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    model.save(str(OUTPUT_DIR))

    meta = {
        "base_model": BASE_MODEL,
        "n_pairs": len(pairs),
        "epochs": EPOCHS,
        "batch_size": BATCH_SIZE,
        "warmup_steps": warmup_steps,
    }
    with open(OUTPUT_DIR / "training_meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    print(f"\n저장 완료: {OUTPUT_DIR}")
    print("이제 generate_related_posts.py를 실행하면 파인튜닝 모델로 임베딩을 갱신합니다.")


def main() -> None:
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    print(f"디바이스: {device}")

    print("\n포스팅 로드 중...")
    posts = load_posts()
    print(f"로드 완료: {len(posts)}개")

    print("\n학습 데이터 마이닝 중...")
    raw_pairs = mine_pairs(posts)

    random.shuffle(raw_pairs)
    pairs = deduplicate(raw_pairs)
    print(f"중복 제거 후 총: {len(pairs)}쌍")

    run_finetune(pairs, device)


if __name__ == "__main__":
    main()
