---
title: 옵시디언 {% post_url 링크 %}를 Jekyll post_url로 자동 변환하기
date: 2026-03-20
tags:
  - 자동화
  - 뻘짓
category:
  - 기타
---

옵시디언으로 포스팅 초안 쓰다가 다른 글 링크를 `[[파일명]]` 형식으로 달았는데,
깃허브 블로그에 올리면 링크가 그냥 텍스트로 보임.

---

## 문제 상황

Jekyll에서 내부 포스트 링크는 이렇게 써야 함.

```
{% post_url 2026-03-16-refactoring-overseas-etf-ddd %}
```

근데 옵시디언에서는 `[[2026-03-16-refactoring-overseas-etf-ddd]]` 이렇게 씀.
두 형식이 달라서 옵시디언에서 링크를 달아놓으면 Jekyll 빌드 시 그냥 `[[...]]` 텍스트로 렌더링됨.

그렇다고 포스팅할 때마다 직접 `{% post_url %}` 형식으로 고쳐쓰는 건 번거로움.

---

## 해결 방법 후보

### 후보 A — GitHub Actions 커스텀 빌드

빌드 파이프라인에서 변환 스크립트를 실행하는 방식.

```
push → GitHub Actions → 변환 스크립트 실행 → Jekyll 빌드 → 배포
```

직접 Jekyll을 빌드해야 하기 때문에 기존 GitHub Pages 기본 빌드 방식을 버리고 Actions 기반으로 전환해야 함.
`_config.yml`, `Gemfile`, 빌드 yml 파일까지 손봐야 하는 작업 범위가 있음.

### 후보 B — Git pre-commit 훅

커밋 직전에 `_posts/` 안의 스테이징된 파일을 스캔해서 `[[파일명]]`을 `{% post_url 파일명 %}`으로 치환하고 다시 스테이징하는 방식.

```
git commit → pre-commit 훅 실행 → 변환 → git add → 커밋 완료
```

---

## 후보 B를 선택한 이유

기존 빌드 구조를 건드리지 않아도 됨. GitHub Pages 기본 빌드를 그대로 쓸 수 있음.

변환이 커밋 시점에 일어나기 때문에 레포지터리에 올라가는 파일은 항상 Jekyll이 인식할 수 있는 상태로 유지됨. 빌드 단계에서 변환이 실패할 여지가 없음.

---

## 구현

`.git/hooks/pre-commit` 파일을 생성하고 실행 권한을 부여함.

```bash
#!/bin/bash
POSTS_DIR="_posts"

while IFS= read -r file; do
  if grep -q '\[\[' "$file" 2>/dev/null; then
    python3 - "$file" <<'PYEOF'
import sys, re

filepath = sys.argv[1]
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# 펜스 코드 블록(```...```), 인라인 코드(`...`) 는 건드리지 않음
pattern = re.compile(r'(```[\s\S]*?```|`[^`\n]+`|\[\[([^\[\]\n]+)\]\])')

def replace(m):
    full = m.group(0)
    if full.startswith('`'):
        return full
    return '{% post_url %s %}' % m.group(2)

new_content = pattern.sub(replace, content)
new_content = new_content.replace('{% post_url ', '{% post_url ').replace(' %}', ' %}')

if new_content != content:
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print(f"[pre-commit] wikilink 변환: {filepath}")
PYEOF
    git add "$file"
  fi
done < <(git diff --cached --name-only --diff-filter=ACM | grep "^${POSTS_DIR}/.*\.md$")

exit 0
```

이제 옵시디언에서 `[[파일명]]`으로 링크를 달아도 커밋 시 자동으로 `{% post_url 파일명 %}`으로 바뀜.
코드 블록이나 인라인 코드 안에 있는 `[[...]]`는 변환하지 않아서 이 포스팅처럼 예시 코드를 쓸 때도 문제없음.

---

한 가지 주의할 점은 `.git/` 디렉토리는 git으로 공유되지 않아서 다른 기기에서 클론하면 훅이 없음.
혼자 쓰는 레포라면 문제없고, 공유가 필요하다면 `.githooks/` 디렉토리에 파일을 두고 `git config core.hooksPath .githooks`로 등록하는 방법도 있음.
