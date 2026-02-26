---
title: "CI - Gradle&Sonar Pipeline 버전 업그레이드"
date: 2025-02-19
tags: [미지정]
category:
  - 기타
---

## 왜?


ResourcelessJobRepository를 사용하기 위해서는 Spring batch 5.2.0-M2버전이 필요했고,
Spring boot 버전 업그레이드가 필요할 것 같기도 하고, JDK 21 을 쓰고 싶은 분이 계심.

다만 현재 CI pipeline 이미지가 gradle 8.3 버전 기준이라 Spring boot 3.4.X 부터는 더 이상 지원하지 않음.
[Spring Boot 3.4 Release Notes](https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-3.4-Release-Notes)
> **Gradle**

그리고 JDK21의 경우도 gradle 8.5버전 부터라서 반입 필요할듯해서 한번에 반입함

### 대상

gradle-8.12-jdk17-corretto
gradle-8.12-jdk21-corretto

반입후 사용중.

### 문제점&개선점

sonarqube pipeline의 경우 gradle 신버전으로 가져오면서 기존 ci image도 gradle 8.12로 업그레이드 하고, 버전 업그레이드까지 했는데,
sonar 버전을 4 에서 6으로 올리려니깐 기존 파이프라인이 돌지 않음.
gradle sonar 시 

```yaml
org.sonar.java.AnalysisException: Your project contains .java files, please provide compiled classes with sonar.java.binaries property, or exclude them from the analysis with sonar.exclusions property.
        at org.sonar.java.classpath.ClasspathForMain.init(ClasspathForMain.java:75)
```

이렇게 뜸.
찾아보니

Gradle 5.0 업그레이드 하면서 SCANGRADLE-124 티켓이 적용되었는데 내용이
Remove implicit dependency of the sonar task on the compile tasks



그래서 gradle sonar > gradle compileJava sonar
로 compileJava task를 선행하는 작업이 필요했음.

요청드리고 정상작동 확인.