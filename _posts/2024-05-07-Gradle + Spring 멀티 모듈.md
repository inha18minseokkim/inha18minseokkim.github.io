---
title: "Gradle + Spring 멀티 모듈"
date: 2024-05-07
tags: [Spring, Gradle, Java, 개발, 1차수정완료]
category: 기술
---

## 필요성

MSA 프로젝트를 회사에서 계속 개발함에 따라 프로젝트 숫자가 늘어남. 중간에 공통 단위 모듈(패키지 및 클래스 파일 모두)들이 늘어나는데 이걸 현재 복붙으로 처리하고 있는 상황.

## 구조

현재 듣고 있는 강의 내용 기준(강의는 Maven 기준이라 들으면서 Gradle로 변환 중)

```
microservices-demo (no bootJar, 소스 없음)
├── docker-compose (카프카 및 아래 프로젝트 배포 도커 파일들)
├── app-config-data (no bootJar)
├── twitter-to-kafka-service
└── kafka (no bootJar, avro gradle 사용)
    ├── kafka-admin
    ├── kafka-producer
    └── kafka-model
```

![](https://prod-files-secure.s3.us-west-2.amazonaws.com/c38aebd7-2834-4fac-b2fc-a2f0c17ce81d/d1788120-6f67-4360-a593-1cfc004f8c6c/Untitled.png)

이런식으로 하나의 루트 프로젝트 아래에 여러 하위 모듈 프로젝트를 넣음. 각각의 프로젝트에 `build.gradle`, `settings.gradle` 이 모두 존재함.

**settings.gradle 예제 (microservices-demo)**

```java
rootProject.name = 'microservices-demo'
include ':twitter-to-kafka-service',':app-config-data'
```

**build.gradle 예제 (twitter-to-kafka-service)**

```java
dependencies {
    implementation 'org.twitter4j:twitter4j-stream:4.0.7'
    implementation project(path: ':app-config-data') // 공통 모듈 import
}
```

도메인 단위로 묶는 경우 공통 모듈들을 참조해서 테이블 엔티티 같은 것들을 가져올 수 있을듯.

```java
@SpringBootApplication
@ComponentScan("com.microservices.demo")
public class KafkaAdminApplication {

    public static void main(String[] args) {
        SpringApplication.run(KafkaAdminApplication.class, args);
    }

}
```

Spring 멀티 모듈 사용 시 프로젝트가 다르기 때문에 `@ComponentScan`의 base package를 루트 공통 패키지로 지정해야 하위 모듈 빈을 인식함.

## 장점

- 공통 모듈을 잘 정의하면 소스코드 중복을 막을 수 있음
- 각 프로젝트마다 IntelliJ를 별도로 켤 필요 없음 (프로젝트 세팅을 분리하면 귀찮고 설정 내용을 가지고 다니기도 번거로움)

## 단점

- 초기 셋팅이 힘듦
- 단일 프로젝트로만 개발해왔기 때문에 처음에 러닝커브가 약간 있을듯
- 현재 케이뱅크 CHA-PKG 브랜치 전략에 적합한지는 의문
- **영향도 문제**: 원래 프로젝트 하나에 파드 하나로 정한 이유는 공통 모듈을 최소화함으로써, 복붙을 하더라도 다른 파드에 영향을 주지 않게 하기 위해서였음
  - 다만 당시 논의는 비즈니스 공통 로직보다는 행내 시스템 관련 공통 로직(EAI 호출 HTTP 메서드, DB 커넥션 관련, GUID 채번 같은)에 관한 것이었음

**업무별로 묶는 예시 (개인적인 생각)**

- 공모주서비스 · 공모주데이터수신배치 · 공모주데이터푸시배치 → 공모주 프로젝트 내 서비스/수신배치/푸시배치로 묶기
- 식품물가서비스 · API배치 · 적재배치 · 푸시배치 · 알림톡배치 → 식품물가 프로젝트 내로 묶기

내부의 공통 entity, configuration을 복붙으로 작업 중이기 때문에 이 정도 단위로 묶는 건 괜찮지 않을까 하는 생각.

## 할일

- **SRE 협의 필요**: 현재 프로젝트 하나에 파드 하나 개념이므로 1:N 구조에 대한 파이프라인 협의 필요
- 공통 모듈 변경 시 배포 대상인 하위 모듈들은 문제없지만, 배포 대상이 아닌 모듈들은 그대로 떠 있다가 다음 배포 시 공통 모듈이 적용될 것
- 또는 해당 프로젝트 하위 모듈들을 모두 같이 배포할 것 — 어느 방식이 맞을지 확인 필요

**2024-05-16 협의 시작**

중간 결과: 투자홈 서비스 프로젝트에 멀티 모듈 구조를 적용시킴. 최선은 아닌 것 같지만 현 상황에서는 최선이라 판단.
