---
title: "Gradle Multi Module + Gitlab Submodule 도입기"
date: 2024-07-19
tags: [미지정]
category:
  - 기타
---


## ASIS 문제점

project - Argo CD 1대 1 매핑이라 pod 하나에 프로젝트 하나임
공통모듈 여러 개에 여러 어플리케이션을 붙이고 각각 프로젝트 이미지 만들어서 배포 불가
[Gradle 초기화 시점(settings.gradle → build.gradle,202407)]({% post_url 2025-01-27-Gradle 초기화 시점(settings.gradle → build.gradle,202407) %})
[멀티 모듈의 공통 함정에 대해 깨달은 점(202501)]({% post_url 2025-01-27-멀티 모듈의 공통 함정에 대해 깨달은 점(202501) %})
[멀티 모듈 구성 개선(안, 202502)]({% post_url 2025-02-12-멀티 모듈 구성 개선(안, 202502) %})
[단일 이미지 빌드 환경에서 멀티모듈 빌드(뻘)]({% post_url 2025-02-13-단일 이미지 빌드 환경에서 멀티모듈 빌드(뻘) %})