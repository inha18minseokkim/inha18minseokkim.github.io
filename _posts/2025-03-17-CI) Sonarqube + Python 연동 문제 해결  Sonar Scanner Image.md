---
title: "CI) Sonarqube + Python 연동 문제 해결 : Sonar Scanner Image"
date: 2025-03-17
tags: [미지정]
category: 기술
---

## ASIS

기존 sonar의 경우 gitlab ci pipeline에서 gradle sonar 플러그인을 사용해서 돌고 있었음

```yaml
image: gradle:8.12.1-jdk17-corretto
....
script:
	- gradle compileJava sonar
```

이런식으로 스크립트에서 gradle을 호출하게 되면 자바 중에서 gradle 프로젝트밖에 사용 못하게 됨.


## TOBE

sonar-cli docker image를 활용하여 자바 뿐만 아니라 파이썬까지 coverage를 높이는것이 목표.


```yaml
sonarqube-job:
	rules:
		!reference [.quality_settings:rules:env, rules]
	tags:
		!reference [.default_settings,build_tags}
	stage: dev_quality
	image: sonarsource/sonar-scanner-cli:jdk17
	script:
		- sonar-scanner -Dsonar.projectKey~~~ ..
```

이런식으로 sonar 이미지를 기반으로 sonarqube server에서 지원 가능한 모든 언어 파일을 검사할 수 있도록 바꿈. 즉 특정 language layer → image layer로 전환 완료


# Sonar-Scanner를 파이프라인에서 사용 시 

-Dsonar.qualitygate.wait=true 옵션을 넣어줘야 cod quality fail이 뜨는 경우 return 1을 수행한다.
  - 그래야 다음 파이프라인으로 진행하지 않는다.
쓰지 않는 경우 code quality 검사 요청만 하고 그냥 return 0 job Succeded로 끝난다.


### 추가적인 이점

기존에는 ci 스크립트에서 build.gradle 파일이 있다는 가정 하에

```groovy
plugins {
    id 'java'
    id 'org.jetbrains.kotlin.jvm' version '1.9.22'
    id 'org.springframework.boot' version '3.3.1'
    id 'io.spring.dependency-management' version '1.1.5'
}

```

여기 밑줄에다가 sonar plugin을 직접 sed -i 로 밀어넣어서 build.gradle.kts는 안되었음. 그래서 파이썬 뿐만 아니라 빌드스크립트도 픽스되어있었는데 image에 sonar cli를 사용함으로써 좀 더 유연하게 되었음