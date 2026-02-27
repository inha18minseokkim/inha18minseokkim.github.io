---
title: "Gitlab SAML 환경에서 clone (1)"
date: 2025-01-27
tags:
  - Git
  - CI/CD
  - 개발
category:
  - 실무경험
---
1. gitlab-ci 스크립트 뜯어봤는데 현재 submodule clone 하는 스크립트가 구성되어있지않음
2. 그래서 임시로 dockerfile 내부에서 clone 후 gradle build 하는 방식을 사용
3. SAML SSO를 사용하고 프로젝트가 private이기 때문에 docker 내부에서 kbank git으로 찌르는건 가능하지만 SSO id pw 인증 불가
4. 