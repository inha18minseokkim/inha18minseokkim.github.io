# minseokkim.github.io

개발하면서 공부하고 경험한 것들을 정리하는 Jekyll 기반 블로그.
Obsidian을 에디터로 사용하고 GitHub Pages로 배포한다.

- **블로그 주소**: https://inha18minseokkim.github.io
- **스택**: Jekyll + kramdown + GitHub Pages
- **에디터**: Obsidian (같은 폴더를 vault로 사용)

---

## 디렉토리 구조

```
.
├── _config.yml                  # Jekyll 설정
├── _layouts/
│   ├── default.html             # 전체 페이지 공통 레이아웃 (header, nav, footer)
│   └── post.html                # 포스팅 페이지 레이아웃
├── _posts/                      # 포스팅 마크다운 파일
├── assets/
│   ├── css/style.css            # 전체 스타일
│   └── images/                  # 포스팅에 사용되는 이미지
├── index.html                   # 메인 페이지 (포스팅 목록 + 태그 필터)
└── obsidian_to_jekyll_image.sh  # Obsidian 이미지 문법 → Jekyll 변환 스크립트
```

---

## 포스팅 작성

### 파일 위치 및 이름 규칙

`_posts/` 폴더에 `YYYY-MM-DD-slug.md` 형식으로 저장한다.

```
_posts/2025-01-01-my-post-title.md
```

### front matter

모든 포스팅 상단에 반드시 포함해야 한다.

```yaml
---
title: "포스팅 제목"
date: 2025-01-01
tags: [태그1, 태그2, 태그3]
---
```

- `layout`은 `_config.yml`의 `defaults`에서 `_posts` 전체에 `post`로 자동 지정되므로 생략 가능
- `tags`는 메인 페이지의 필터 버튼에 자동으로 반영됨

### 퍼머링크

`_config.yml`에 `permalink: /:year/:month/:day/:title/`로 설정되어 있어 아래 형식으로 접근한다.

```
https://inha18minseokkim.github.io/2025/01/01/my-post-title/
```

---

## 이미지 관리

### 이미지 저장 위치

모든 이미지는 `assets/images/`에 저장한다.

```
assets/images/Pasted image 20260220085511.png
assets/images/redis-cache-diagram.png
```

### 마크다운에서 이미지 참조

```markdown
![이미지](/assets/images/파일명.png)
```

파일명에 공백이 있으면 `%20`으로 인코딩한다.

```markdown
![이미지](/assets/images/Pasted%20image%2020260220085511.png)
```

### Obsidian → Jekyll 이미지 변환 스크립트

Obsidian에서 붙여넣은 이미지는 `![[Pasted image XXXXX.png]]` 문법으로 저장되는데, Jekyll은 이 문법을 지원하지 않는다.

`obsidian_to_jekyll_image.sh`를 실행하면 두 가지 작업을 자동으로 수행한다.

1. 레포 루트의 `Pasted image *.png` 파일을 `assets/images/`로 이동
2. `_posts/` 내 모든 `.md` 파일의 Obsidian 문법을 Jekyll 문법으로 변환

```bash
bash obsidian_to_jekyll_image.sh
```

> **주의**: `sed -i ''`는 macOS 전용 문법이다. 이 스크립트는 GNU sed(Windows Git Bash / Linux) 기준으로 `sed -i`를 사용한다. macOS에서 실행 시 `sed -i ''`로 수정 필요.

---

## CSS 커스텀 클래스

`assets/css/style.css`에 정의된 포스팅 전용 클래스.

### `.image-row` — 이미지 가로 배열

감싼 이미지 N개를 한 줄에 균등하게 배열한다. 2개면 2열, 3개면 3열, N개면 N열.
모바일(600px 이하)에서는 자동으로 세로 1열로 전환된다.

```html
<div class="image-row" markdown="1">

![이미지](/assets/images/a.png)

![이미지](/assets/images/b.png)

![이미지](/assets/images/c.png)

</div>
```

- `markdown="1"` 속성이 있어야 div 내부에서 마크다운 이미지 문법이 렌더링된다 (kramdown 사양)
- 이미지 사이에 빈 줄을 넣어야 각각 별도 `<p><img>` 블록으로 파싱되어 flex 아이템이 된다
- Obsidian에서는 일렬로 보이는 것이 정상 — 웹에서만 가로 배열된다

---

## 레이아웃 파일

### `_layouts/default.html`

모든 페이지에 공통으로 적용되는 기본 레이아웃.

- `<head>`: Pretendard 웹폰트, `assets/css/style.css` 로드
- `<header class="site-header">`: 사이트 제목(홈 링크) + nav(글 목록, GitHub)
- `<main>`: `{{ content }}` 삽입 위치
- `<footer class="site-footer">`: 저작권 표시

### `_layouts/post.html`

`default.html`을 상속(`layout: default`)하는 포스팅 전용 레이아웃.

- `<article class="post-page">` 래퍼
- `<header class="post-header">`: 날짜, 태그 뱃지, 포스팅 제목
- `<div class="post-content">`: 본문 (`{{ content }}`)
- `<div class="post-footer">`: 목록으로 돌아가기 링크

---

## 메인 페이지 (`index.html`)

### 태그 필터

`site.tags`(Jekyll 내장 변수)를 사용해 모든 태그 버튼을 렌더링한다.
태그 버튼은 `data-count` 속성(해당 태그 포스팅 수)을 가지며, 페이지 로드 시 JavaScript가 언급 횟수 내림차순으로 정렬한다.

```javascript
// 태그 버튼을 data-count 기준 내림차순 정렬
const tagBtns = Array.from(tagFilter.querySelectorAll('.tag-filter-btn[data-count]'));
tagBtns.sort((a, b) => parseInt(b.dataset.count) - parseInt(a.dataset.count));
tagBtns.forEach(btn => tagFilter.appendChild(btn));
```

### 포스팅 필터링

태그 버튼 클릭 시 각 포스팅 `<li>`의 `data-tags` 속성과 비교해 show/hide 처리한다. 별도 페이지 이동 없이 클라이언트 사이드에서 동작한다.

---

## `_config.yml` 주요 설정

| 항목 | 값 | 설명 |
|------|-----|------|
| `markdown` | `kramdown` | 마크다운 파서 |
| `highlighter` | `rouge` | 코드 블록 하이라이터 |
| `permalink` | `/:year/:month/:day/:title/` | URL 형식 |
| `kramdown.input` | `GFM` | GitHub Flavored Markdown 허용 |
| `exclude` | `.obsidian/`, `Pasted image*.png` 등 | 빌드에서 제외할 파일 |
| `defaults` | `_posts` → `layout: post` | 포스팅 레이아웃 자동 지정 |
