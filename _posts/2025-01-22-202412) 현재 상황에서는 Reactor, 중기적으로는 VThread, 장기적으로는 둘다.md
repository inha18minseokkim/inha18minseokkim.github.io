---
title: "202412) 현재 상황에서는 Reactor, 중기적으로는 VThread, 장기적으로는 둘다?"
date: 2025-01-22
tags:
  - 개발
  - 아키텍처
  - Java
category:
  - 실무경험
---
Reactor vs VThread 선택 전략과 아키텍처 방향성 정리.
# 글을 쓴 이유

현재 행 내 MSA 환경 기본 자바 버전은 17. api mediation 파드의 병렬 호출 후 조합 처리를 위해 현재 webclient + openfeign 의 논블로킹 조합을 사용하고 있음.
일단 api-gateway를 논블로킹 방식의 SCG를 사용하고 있고(물론 현재는 DB를 쓰긴 하지만) 스레드가 한정되어 있는 상황에 여러 개의 블로킹 호출을 조합하는데에는 reactor 기반의 논블로킹 방식이 적절한 것 같아 논블로킹 함수를 사용하여 api-mediation 패턴을 구현해놓은 상황이다.
다만 만약 앞으로 jdk 21을 사용할 수 있게 된다면? 굳이 reactor를 사용할 필요가 있을까


# 현재 상황

1. jdk 17 사용
2. MCI(무조건블로킹) > api-gateway(SCG-reactor) > mediation(webclient-openfeign) > 업무단 api > jdbc(r2dbc로 바꿀 수 있음) , reactive redis 가능
3. CPU 바운드 작업은 없고 IO 바운드 작업이 90%임

## 현재 잠정 결론 + reactor의 장점

reactor기반 논블로킹 호출이 더 좋음. 
1. mediation api 파드에서 여러 업무단으로 http request를 병렬 호출로 보내고 받을 때 현 jdk 17에서는 Future나 Thread 사용 시 플랫폼 스레드를 사용하기 때문에 컨텍스트 스위칭 비용이 너무 큼.
2. MCI 가 post only이긴 하지만 WAS 성능이 MSA의 단위업무 파드 4개 보다는 월등히 뛰어나고, Spring Cloud Gateway의 논블로킹 호출은 충분히 버티기 때문에 뒷단 mediation 파드가 버틸려면 논블로킹으로 구성하는게 성능상 좋음
3. 혹시 언젠가는 데이터를 스트림으로 제공해서 프론트로 꽂아주는 api를 구성할 일이 있으면 미리 대비해놓는게 괜찮을지도
4. 아무리 virtual thread가 컨텍스트 스위칭과 생성에 비용이 작아진다고 해도 이론적으로는 이벤트 루프를 돌리면서 컨텍스트 스위칭을 하지 않고 시분할로 IO 타고 들어오는 이벤트를 처리하는게 엄밀하게는 퍼포먼스가 좋다.

## 현재 한계 + reactor의 단점

1. reactor 함수 표준 코드 짜는게 익숙하지 않아 다른 사람이 봤을 때 가독성이 떨어지고 디버깅이 힘듬.
2. 뒤에서 아무리 멋드러지게 논블로킹으로 조합을 해줘도 앞에 MCI가 블로킹하기 때문에 성능 향상에는 제한이 있음
3. 과연 데이터를 스트림형식으로 줄만큼 담당업무가 고도화되고 MCI를 거치지 않는 구조가 완성될 수 있을까
4. 현재 DAU 상황에서 과연 버추얼 스레드의 컨텍스트 스위칭 비용을 가지고 퍼포먼스의 이점이라고 할만큼 차이가 날까?

## 앞으로는




[How can Java 21 (Virtual Thread) replace Reactive Framework.](https://www.reddit.com/r/java/comments/1d43rbh/how_can_java_21_virtual_thread_replace_reactive/?rdt=53336)
[Using Virtual Threads (Project Loom) with Spring WebFlux/Reactor/Reactive libraries](https://stackoverflow.com/questions/75314973/using-virtual-threads-project-loom-with-spring-webflux-reactor-reactive-librar)
[Do Java 21 virtual threads address the main reason to switch to reactive single-thread frameworks?](https://stackoverflow.com/questions/78318131/do-java-21-virtual-threads-address-the-main-reason-to-switch-to-reactive-single/78318175#78318175)
