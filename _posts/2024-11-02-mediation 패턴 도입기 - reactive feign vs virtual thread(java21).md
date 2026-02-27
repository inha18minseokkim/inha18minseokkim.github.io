---
title: mediation 패턴 도입기 - reactive feign vs virtual thread(java21)
date: 2024-11-02
tags:
  - 개발
  - 아키텍처
  - Java
  - BFF
  - Webflux
category:
  - 기술
---
Mediation 패턴 구현 시 FeignClient vs WebClient 비교 정리.
[Thread Per Request VS WebFlux VS VirtualThreads](https://medium.com/@sridharrajdevelopment/thread-per-request-vs-virtualthreads-vs-webflux-33c9089d22fb)
[Using Virtual Threads (Project Loom) with Spring WebFlux/Reactor/Reactive libraries](https://stackoverflow.com/questions/75314973/using-virtual-threads-project-loom-with-spring-webflux-reactor-reactive-librar)

[Do Looms Claims Stack Up? Part 2: Thread Pools?](https://webtide.com/do-looms-claims-stack-up-part-2/)

[Java의 미래, Virtual Thread | 우아한형제들 기술블로그](https://techblog.woowahan.com/15398/)
이번 Virtual Thread 기능은 기존 Thread 모델에서 Native 기반으로 동작하던 park/unpark 로직에 대해 Virtual Thread 분기를 추가해, 기존 Thread 방식에서 특별한 코드 수정 없이 Virtual Thread기반의 컨텍스트 스위칭을 가능하게 하였습니다.
[Virtual Thread란 무엇일까? (1)](https://findstar.pe.kr/2023/04/17/java-virtual-threads-1/)
- 높은 처리량을 높이기 위해서 기존에는 Reactive Programming 과 같은 방식을 사용했지만,
- `가상 스레드` 를 사용하면 Reactive Programming 이 추구하는 Non-blocking을 통한 효율적인 자원 사용이 가능해진다.
- `가상 스레드` 가 JVM 내부에서 알아서 스케줄링 해주기 때문에 **가상 스레드 풀** 을 사용하지 않는다.
- Reactive Programming 보다 가독성 좋은 코드를 유지할 수 있고, 기존 스레드와 동일하게 동작하므로 디버깅이 용이하다.
1. `가상 스레드` 기능이 추가되었다고 해서 기존의 스레드(플랫폼 스레드)를 사용하지 못하는 것은 아니다.
  - 기존의 스레드도 사용가능하고, 추가된 `가상 스레드` 도 사용가능하다. 서로 대치되는 것이 아니라 공존하는 것이다.
2. `가상 스레드` 를 사용하더라도 응답속도가 빨라지지는 않는다. (오히려 약간 느려질 수도). 다만 처리량이 늘어날 수 있다.
3. 일반적으로 애플리케이션을 개발할 때 스레드를 직접 다루거나 Executors를 사용하는 코드를 많이 작성하지는 않는다. 오히려 기존의 라이브러리들이 `가상 스레드`를 사용할 수 있도록 개선될 것같다.
4. Reactive Programming 과 같이 높은 처리량을 필요로하는 부분들은 `가상 스레드`를 사용하는 방식으로 전환될 수도 있을것 같다.
[virtual thread + synchronized = X](https://jaeyeong951.medium.com/virtual-thread-synchronized-x-6b19aaa09af1)

그냥 코루틴 쓸까..
[[Project Loom] Virtual Thread에 봄(Spring)은 왔는가 | 카카오페이 기술 블로그](https://tech.kakaopay.com/post/ro-spring-virtual-thread/#as-is-aka-platform-thread)

### 일단 대충 윗글들을 요약 + 내 생각을 정리해보면

1. 현재 webflux nonblocking과 virtual thread는 큰 차이가 없다. 호출하는데 있어서
2. 다만 내가 생각하는 api mediation 서비스는 여러 서비스에 api를 호출하여 데이터를 가져와서 조합, 리턴하는 로직이므로 CompletableFuture나 Runner같은 코드가 덕지덕지 붙는걸 원하지 않음.
3. 그래서 호출할 때는 OpenFeign + Reactor 를 사용하면 선언적인 코드 + openFeign의 가독성을 가져가서 코드가 예뻐지지 않을까 라는 생각
4. Mediation 서비스에서 @RequestMapping시 virtual thread를 사용하여 많은 호출을 받아낼 때 context switching과 같은 스레드 내부 연산에서 고무적인 성능 향상이 있으면 virtual thread를 사용해봐도 좋을 듯.
  - 이건 실험 해보긴해야함. 내부망에서 실험해볼 예정. 맥미니는 무서워
5. mediation의 경우 Network I/O만 있기 때문에 jdbc나 한정된 자원에 접근할 때 발생하는 synchronized 가 없을것이라 생각중임. 따라서 pinning issue는 발생하지 않을 것.
6. 그럼에도 불구하고 결국 api-gateway(db로깅중)> medaition > endpoint service > db에서 db가 하나기 때문에 드라마틱한 성능 향상을 기대하긴 어렵긴함. 
  - 왜냐하면 N개의 뒷 서비스를 콜해서 mediation에서 조합하는데 mediation 이 병목이 될 것을 우려할게 아니라 DB가 병목이 될걸 두려워해야하는 상황임 

7. 그럼에도 불구하고 언젠가는 업무가 확대되어 db가 분리될 것을 생각하면..일단 준비는 해놓자.



### Virtual Thread의 목표

1. Enable **server applications **written in the simple **thread-per-request style **to scale with near-optimal hardware utilization
2. Enable **exsiting(legacy) code **that uses the java.lang.Thread API to adopt virtual threads with minimal change
3. Enable easy troubleshooting, debugging, and profiling of virtual threads with **existing JDK tool**

### Coroutine 목표

1. Make it possible to utilize Kotlin coroutines as wrappers for different exsiting asynchronous APIs (such as Java NIO, different implementations of Futures, etc)
2. No dependency on particular implementation of Futures or such rich library
3. Cover equally the async/await use case and generators block

버추얼 스레드의 경우 스레드를 생성해서 작업을 할 때 생기는 부담을 해결하기 위해 가벼운 스레드를 생성하고, 기존 java.lang.Thread를 사용했던 어플리케이션들도 잘 사용할 수 있게 만들었다는게 골자.
rxjava의 경우 스레드는 일단 차치하고 async 호출을 블로킹해서 스레드가 놀지 않게 프로그래밍 하는 방법을 제시해준게 골자.

결국에는 네트워크 IO가 낀 곳에서 처리량을 늘려주지만 접근하는 방식이 약간 다른 듯 하다.
