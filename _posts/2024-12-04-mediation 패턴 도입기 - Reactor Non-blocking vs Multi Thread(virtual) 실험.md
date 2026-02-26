---
title: "mediation 패턴 도입기 - Reactor Non-blocking vs Multi Thread(virtual) 실험"
date: 2024-12-04
tags: [미지정]
category:
  - 기타
---


### 시나리오

1. jdk17 + Multi Thread
2. jdk17 + Reactor
3. jdk21 + Multi Thread(non Virtual)
4. jdk21 + Multi Thread(Virtual)
5. jdk21 + Reactor(non Virtual)
6. jdk21 + Reactor(Virtual)
  - 5번 6번 선택지가 분기된 이유는 끄적여보고 있었는데 
  - Reactor면 스레드 이름이 boundedElastic으로 뜸.
  - 근데 virtual thread를 enable 하니 loomBoundedElastic으로 바뀌네?
  - 그래서 혹시 몰라서 선택지에 넣어봄
> Since 3.6.0 [`boundedElastic()`](https://projectreactor.io/docs/core/release/api/reactor/core/scheduler/Schedulers.html#boundedElastic--) can run tasks on `VirtualThread`s if the application runs on a Java 21+ runtime and the [`DEFAULT_BOUNDED_ELASTIC_ON_VIRTUAL_THREADS`](https://projectreactor.io/docs/core/release/api/reactor/core/scheduler/Schedulers.html#DEFAULT_BOUNDED_ELASTIC_ON_VIRTUAL_THREADS) system property is set to `true`.
  - 이거랑 관련있는듯.
  - 근데 실제로 3.6.0 이상으로 reactor를 하면 논블로킹 처리 시 boundedElastic 할당되어있는 스레드를 사용하는게 아니라 그 스레드를 버추얼로 만들어서 loomBoundedElastic을 사용하도록 되어있다.
    - [What new is coming in reactor-core 3.6.0?](https://spring.io/blog/2023/10/31/what-new-is-coming-in-reactor-core-3-6-0)
  - 스케줄링, 컨텍스트 스위칭, 현재 boundedElastic이 없는 경우 신규 스레드 생성하는 경우 이럴 때 버추얼 스레드를 사용하니 아마 조금 더 효과적이긴 할 듯 하다.
[Do Java 21 virtual threads address the main reason to switch to reactive single-thread frameworks?](https://stackoverflow.com/questions/78318131/do-java-21-virtual-threads-address-the-main-reason-to-switch-to-reactive-single)


