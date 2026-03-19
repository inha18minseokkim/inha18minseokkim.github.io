---
title: "멀티 모듈 구성 개선(안, 202502)"
date: 2025-02-12
tags:
  - 개발
  - 기술
category:
  - 실무경험
---
드디어 멀티 모듈 구성에 대한 검토가 시작되어 먼저 상장주식 단위 업무를 멀티모듈화 시키면 어떨 까 생각을 해봤다.

위에서 했던 안 기반이긴 한데 몇 가지 개선점이 있음.

![멀티 모듈 구성](/assets/images/Pasted%20image%2020260228165200.png)


# 코어 레벨

app 레벨에서 필요한 기능들을 모아놓음. 최대한 얇게 설계하였고 spring boot 종속성은 제거하였다.

## common

공통 enum, json 관련 자주쓰는 코드 모음. 가급적 순수 자바코드만 들어가있음.

## data

spring-data- 관련 종속성 사용할때 필요한 공통 VO, AuditConfig 선언되어있음
spring-data-commons, spring-data-relation 모듈 관련
해당 모듈 받아 spring-data-jdbc, r2dbc, redis 사용하면 됨.

## jpa

spring-data-jpa 관련 공통 Entity, EnumConverver 등. jakarta.persistence와 spring-data-jpa 모듈을 사용. persistence 관련 로직을 data와 통합하기 힘들어보여서 data와 분리함.

## redis

RedisConnectionFactory와 redisTemplate 공통 정의, Reactive 관련 설정도 있음.
현재는 data DTO도 있지만 이것 또한 data 영역에 포함시킬 수 있지않을까 라는 생각에 data와 합치는 시도중.
모듈이름을 redis로 해야할지, cache로 해야할 지 고민중임.

# app 레벨


## service

was 서버. 위 모듈 받아서 구현

## job

spring batch는 아니지만 job application 형태로 동작하는 것들

## batch

spring batch 사용하는 잡. 현재는 shell 기동 방식이다.