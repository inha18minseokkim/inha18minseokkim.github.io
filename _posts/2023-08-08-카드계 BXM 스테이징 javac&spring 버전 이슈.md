---
title: 카드계 BXM 스테이징 javac&spring 버전 이슈
date: 2023-08-08
tags:
  - Java
  - Spring
  - 개발
  - 이슈정리
  - BXM
  - 케이뱅크
category: 실무경험
---
행내 BX 프레임워크(버전 3.5), openjdk-1.8.0_242 버전에서 람다함수 및 함수형식이 컴파일되지 않거나 컴파일되어도 실행되지 않는 현상 탐지. jdk 1.8버전에서 새로 생성된 라이브러리는 정상작동.

### 경과

1. 개발 서버 내부의 javac 컴파일러(환경변수 기준)로 수동 컴파일 → 컴파일 성공 실행 실패, 디컴파일 정상
2. openjdk 1.8.0_242 버전을 다운받아 로컬에서 빌드 후 실행 및 디컴파일 확인(스프링 x, 자바로만) → 컴파일 성공 실행 성공, 디컴파일 정상
3. 스테이징 서버로 배포 시도 → 실패(컴파일 실패에 따른 배포 실패)
  1. 원인 : 현재까지 형상관리 시스템에서 스테이징 javac 버전이 1.8버전으로 올린 후 현재까지  쭉 1.7로  컴파일 되어있는 현상 발견(즉 컴파일은 1.7버전으로 하고 실행은 1.8버전으로 해왔음)
  2. 해결 : 담당자 연락 후 javac 1.8버전 변경 확인. 배포 성공 but 실행 실패
4. ServiceNotFoundException 컴파일은 성공 but 실행 시 계속 해당 class 파일을 찾을 수 없는 오류 출력


### 결과

원인 : 스프링 버전이 jdk8 문법을 지원하지 않음
[https://spring.io/blog/2013/05/21/spring-framework-4-0-m1-3-2-3-available/](https://spring.io/blog/2013/05/21/spring-framework-4-0-m1-3-2-3-available/)
현  BX 프레임워크 3.5버전은 스프링 3 버전 기반. jdk버전만 1.8버전으로 올린 상황

### 문제상황

> Spring Framework 3.2.x will support **deployment on JDK 8 runtimes for applications compiled against JDK 7** (with -target 1.7) or earlier. Note that it won't support JDK 8's bytecode format (-target 1.8, as needed for lambdas); please upgrade to Spring Framework 4.0 for that purpose.
3.2버전까지는 jdk 1.8 버전 런타임 가능 but 컴파일 환경이 1.7버전까지만 지원함. 따라서 → 나 :: 가 들어있는 JDK 바이트코드 포맷을 지원하지 않음. 즉 jdk의 문제가 아니라 스프링 컨텍스트의 실행 환경에서 jdk 8을 지원하지 않음.

[https://stackoverflow.com/questions/24657418/spring-core-3-2-9-java-8](https://stackoverflow.com/questions/24657418/spring-core-3-2-9-java-8)

asm.jar 관련
asm bytecode manipulation framework
자바 바이트코드와 스프링 사이의 무언가.
**Code Generation and Transformation:** ASM can be used to generate and modify classes at runtime. This is useful for scenarios like creating proxy classes, generating code for specific use cases, or altering existing classes for customization
결론 : 스프링에서 .class파일의 바이트코드 레벨의 무언가를 읽을 때 버전 차이로 생기는 문제

BXM 컨테이너에서 객체를 불러오는 로직을 좀 더 파보기로 함
[카드계 Bxm 자바8 로딩 하는방법(Spring Legacy 3, 부트아님)]({% post_url 2023-11-15-카드계 Bxm 자바8 로딩 하는방법(Spring Legacy 3, 부트아님) %})
[자바 7/8 serializing compatibility의 문제?]({% post_url 2023-11-21-자바 78 serializing compatibility의 문제 %})
