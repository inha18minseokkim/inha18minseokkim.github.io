---
title: Claude Code로 Jekyll 블로그 관리하기
date: 2026-05-10
tags:
  - AI/ML
  - 블로그
  - 자동화
category:
  - 기타
---

about 페이지 개편하면서 Claude Code한테 이것저것 시켜봤는데, 생각보다 블로그 관리용으로 꽤 쓸만해서 정리해봄.

---

## 핵심: CLAUDE.md로 컨텍스트 주입

Claude Code는 프로젝트 루트에 `CLAUDE.md` 파일이 있으면 자동으로 읽어서 컨텍스트로 활용함. 내 블로그에는 이런 내용이 들어있음.

```markdown
# 블로그 포스팅 가이드라인

이 블로그는 Jekyll 기반 GitHub Pages다. `_posts/` 디렉토리에 마크다운 파일로 포스팅한다.
Claude가 포스팅 초안을 받아 포맷팅, 요약, 근거 보충을 수행한다.

## 문체 및 어조
- **반말 구어체**로 작성한다. ("~다", "~임", "~함", "~됨")
- 공식적인 문어체 금지. 자연스럽게 생각을 풀어쓰는 느낌 유지.
- 핵심 개념/키워드는 **볼드** 처리.

## 카테고리 종류
| category | 사용 기준 |
|---|---|
| 기술 | Java, Spring, Redis, Kotlin 등 기술 포스팅 |
| 실무경험 | 실제 업무에서 겪은 이슈, 삽질기 |
| 기타 | 도구, 환경설정, 개인 생각, 비기술 주제 |
```

**이게 있으면 Claude가 포스팅 작성할 때 내 블로그 톤에 맞춰서 알아서 씀.** GPT 특유의 "~입니다", "~하겠습니다" 같은 존댓말 문체가 안 나옴. frontmatter 양식도 알아서 맞춰줌.

---

## 실제로 시킨 작업들

### 1. 깨진 링크 찾아서 수정

about 페이지에 Featured Posts 링크가 5개 있었는데, 포스팅 파일명을 한글에서 영문으로 바꾸면서 전부 404가 떴음.

```
나: about 포스팅에 맨밑 링크가 기존 포스팅의 파일명을 바꿔서 404가 뜨는데
    옵시디언 제목으로 찾으면 다 찾아질거임. 보고 찾아서 링크 바꿔서 푸시해줘
```

Claude가 한 일:
1. about.md 읽어서 깨진 링크 5개 식별
2. `_posts/` 디렉토리에서 grep으로 원본 제목 검색
3. 새 파일명과 매칭해서 링크 일괄 수정
4. git commit & push

| 기존 링크 | 새 파일명 |
|---|---|
| `mediation-패턴-도입기` | `mediation-pattern-introduction` |
| `mediation-패턴-도입기-feignClient-vs-webClient-non-blocking` | `mediation-feign-client-vs-webclient-nonblocking` |
| `BM들에게-보내는-편지-EDA` | `letter-to-business-managers-eda` |

**한글 URL이 영문으로 바뀐 5개 링크를 알아서 찾아서 고침.**

---

### 2. Experience 섹션 전면 개편

경력 사항을 새로 정리해서 넘겨줬음.

```
나: 그냥 이 내용으로 대체해줘

# 케이뱅크 혁신 서비스 백엔드 개발(2023.01~ 현재)

**초기 서비스 개발 및 MSA 전환 (2023.01 ~ 2024.01)**
- 요약: 카드계 프레임워크 서비스 개발, MSA 구조 마이그레이션 참여
...
```

Claude가 한 일:
1. 마크다운 내용을 HTML 구조로 변환
2. 기존 about.md의 Experience 섹션 교체
3. 기술 스택 표시용 CSS 클래스 추가 (`.about-exp-tech`)
4. git commit & push

**날것의 마크다운을 던져주면 기존 HTML 구조에 맞게 변환해서 끼워넣음.**

---

### 3. 삭제된 파일 복원

클라우드 동기화 타이밍 문제로 커밋할 때 포스팅 2개랑 이미지 4개가 날아갔음.

```
나: 2026-04-30-postgresql-partition-pk-deep-dive
    2026-04-26-dev-with-claude 이 포스팅이 여기서 커밋하니깐 사라졌거든?
    깃 커밋 이력을 보면서 누락된 내용들 찾아서 머지해줘
```

Claude가 한 일:
1. `git log --oneline`으로 최근 커밋 확인
2. `git show 8398a7b --stat`으로 삭제된 파일 목록 확인
3. `git checkout 68ce962 -- 파일경로`로 이전 커밋에서 파일 복원
4. 포스팅 3개 + 이미지 4개 복원 후 push

```bash
# Claude가 실행한 명령어
git checkout 68ce962 -- "_posts/2026-04-26-dev-with-claude.md"
git checkout 68ce962 -- "assets/images/Pasted image 20260406151836.png"
```

**git 이력 뒤져서 삭제된 파일 알아서 복원함.** 이건 진짜 편했음.

---

## Obsidian → Jekyll 이미지 변환 스크립트

Obsidian에서 스크린샷 붙여넣기 하면 `![이미지](/assets/images/Pasted%20image%2020260510120000.png)` 형식으로 들어감. Jekyll은 이 문법을 모르니까 변환이 필요함.

```bash
#!/bin/bash
# obsidian_to_jekyll_image.sh

# 1. 루트 폴더의 "Pasted image*.png" 파일들을 assets/images로 이동
for img in "$SCRIPT_DIR"/Pasted\ image\ *.png; do
    mv "$img" "$ASSETS_DIR/"
done

# 2. _posts 폴더의 모든 md 파일에서 Obsidian 문법을 Jekyll 문법으로 변환
# ![[Pasted image XXXXX.png]] -> ![이미지](/assets/images/Pasted%20image%20XXXXX.png)
sed -i 's/!\[\[Pasted image \([0-9]*\)\.png\]\]/![이미지](\/assets\/images\/Pasted%20image%20\1.png)/g' "$md_file"
```

이것도 Claude한테 "Obsidian 이미지 문법을 Jekyll 표준으로 바꾸는 스크립트 만들어줘"라고 해서 만든 거임.

---

## 정리

| 작업 | 지시 방식 | Claude가 한 일 |
|---|---|---|
| 깨진 링크 수정 | "옵시디언 제목으로 찾아서 고쳐줘" | grep 검색 → 링크 일괄 수정 → push |
| Experience 개편 | "이 내용으로 대체해줘" + 마크다운 원문 | HTML 변환 → 섹션 교체 → CSS 추가 |
| 삭제 파일 복원 | "git 이력 보고 복원해줘" | git log → checkout → push |
| 이미지 변환 스크립트 | "Obsidian → Jekyll 변환 스크립트 만들어줘" | sed 기반 쉘 스크립트 생성 |

**CLAUDE.md로 블로그 컨텍스트를 주입해두면, 이후 작업에서 일일이 설명 안 해도 알아서 맞춰서 작업함.** 특히 문체나 포맷 같은 건 한 번 정의해두면 계속 유지되니까 편함.

git 작업도 꽤 잘함. 커밋 메시지도 한글로 적절하게 써주고, 이력 뒤져서 복원하는 것도 됨. 다만 staging area에 이미 올라간 파일이 같이 커밋되는 경우가 있어서 `git status` 확인은 필요함.
