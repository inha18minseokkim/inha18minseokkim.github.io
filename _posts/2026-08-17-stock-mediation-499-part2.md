---
title: stock-mediation 499 트레이싱 일대기 (2부) — 커넥션 풀 고갈과 여러 이슈들
date: 2026-08-17
tags:
  - Spring
  - WebFlux
  - Reactor
  - Kotlin
  - 실무경험
category:
  - 실무경험
---

[1부]({% post_url 2026-08-17-stock-mediation-499-part1 %})에서 idle-timeout → SCG 튜닝 → 코루틴 연쇄 취소가 원인이 아닌 것까지 확인됐다. 그래도 하나 건진 게 있는데, 499는 항상 단독으로만 찍힌다는 것. 연쇄 실패의 흔적이 없다.

이 글은 거기서 이어진다.

---

## 재시도 로직에 계측 추가

뭔가를 고치기 전에, 먼저 현상을 제대로 관측할 수 있는 장치를 달았다. `WebClientManager.kt`의 `PREMATURE_CLOSE_RETRY` 재시도 로직에 `.doBeforeRetry { }` 로그를 추가해서, 재시도가 실제로 발동하면 `[WebClientManager][retry]` 로그가 남도록.

이후 발생한 499 건들에서 `[WebClientManager][retry]` 로그는 **총 1건만** 나왔다. 진짜 `PrematureCloseException`이 우리 코드 레이어까지 올라오는 경우는 극히 드물다는 거다. 499가 Tempo에는 계속 찍히는데 애플리케이션 로그에는 거의 안 남는다 — 이것도 나중에 중요한 단서가 된다.

---

## 커넥션 풀 고갈 발견

그냥 목표 TPS 테스트가 아니라 **의도적으로 시스템을 터뜨릴려고** 부하 테스트를 수행하다가 앱 로그에서 우연히 발견한 에러.

```
[getList] pending acquire queue has reached its maximum size of 32
```

Reactor Netty의 `PoolAcquirePendingLimitException` — **커넥션 풀 자체가 부족해서 대기열까지 꽉 찬 상황**이다. 499랑은 별개지만 모르고 있었던 이슈.

원인을 추적했다. `WebClientConfig.kt`에서 `ConnectionProvider.builder(...)`에 `maxConnections`를 명시하지 않아서 Reactor Netty 기본값인 `Runtime.availableProcessors() * 2`를 쓰고 있었다. 그리고 이 기본값은 **다운스트림 host별로 적용**된다.

k8s 환경에서 JVM이 파드의 CPU limit이 아니라 **노드 전체 코어 수**를 인식하는 경우가 흔한데, 그러면 이 기본값이 실제 동시 호출량 대비 지나치게 작거나 예측 불가능하게 잡힌다. 그리고 풀이 작으면 커넥션이 과도하게 재사용되면서 서버(Tomcat) 쪽의 `maxKeepAliveRequests`(요청 횟수 기반 keep-alive 한도)에 먼저 걸려서 서버가 끊을 수 있다. 이건 idle 시간과 **무관**하기 때문에 `maxIdleTime` 튜닝으로는 막을 수 없다 — 애초에 다른 종류의 문제였던 거.

지금까지 이 이슈가 안 터진 건, 클라이언트 사이드 캐싱 요청도 있었고 서버사이드에서도 처리성 업무 제외하고 캐싱을 하고 있었어서 실제 동시 요청이 그렇게 많지 않았던 것. 부하가 좀 심한 상황이었으면 진작 터졌을 이슈.

[Reactor Netty 공식 FAQ](https://projectreactor.io/docs/netty/release/reference/faq.html)에도 499 디버깅 체크리스트로 "서버의 최대 keep-alive 요청 수 제한"을 명시적으로 언급하고 있다.

### 3차 조치: 커넥션 풀 명시적 설정

`WebClientConfig.kt`의 `ConnectionProvider`에 명시적으로 추가했다.

```kotlin
ConnectionProvider.builder("stock-mediation-http")
    .maxConnections(500)
    .pendingAcquireMaxCount(1000)
    .pendingAcquireTimeout(Duration.ofSeconds(5))
    .maxIdleTime(Duration.ofSeconds(20))
    .maxLifeTime(Duration.ofSeconds(30))
    .evictInBackground(Duration.ofSeconds(30))
    .build()
```

**`maxLifeTime`을 명시한 이유**: 커넥션을 시간 기준으로 강제 순환시켜서 서버 쪽 요청-횟수 한도에 걸리기 전에 클라이언트가 선제적으로 커넥션을 교체할 수 있도록.

배포 후 `PoolAcquirePendingLimitException` 에러 로그는 **완전히 사라졌다**. 그런데 **Tempo에는 여전히 499 이벤트가 계속 잡힌다.** 이 이슈 외에 다른 원인으로도 발생하고 있었던 것.

---

## Reactor Netty 내부 자동 복구 이슈인가

클로드한테 reactor-netty jar를 직접 까보라고 했다.

의존성 버전 확인: Spring Boot 3.3.1 관리 버전에서 `reactor-netty 1.1.20`. jar를 직접 디컴파일(`javap`)해서 `DefaultPooledConnectionProvider$DisposableAcquire.run()` 내부를 확인했더니 이런 로직이 있었다.

```java
// 바이트코드로 확인한 내용을 의사코드로
if (!channel.isActive()) {
    pooledRef.invalidate();
    // 새 채널로 재구독 (최대 1회, retried 플래그로 재귀 방지)
    if (!retried && log.isDebugEnabled()) {
        log.debug("Immediately aborted pooled channel, re-acquiring new channel");
    }
}
```

풀에서 꺼낸 커넥션이 **이미 죽어있으면**, 애플리케이션에 에러를 던지지 않고 조용히 새 커넥션으로 1회 재시도하는 게 라이브러리 자체 기능이었다. 아니 이게 있는 줄 몰랐다..

어, 근데 이게 되지 않나. JVM 안에서는 재시도로 성공해서 로그에 안 남고, Tempo에는 첫 번째 죽은 소켓이 499로 찍히는 그림..

로거는 `reactor.netty.resources.DefaultPooledConnectionProvider` (DEBUG 레벨).

### 검증 시도

```yaml
logging:
  level:
    reactor.netty.resources.DefaultPooledConnectionProvider: DEBUG
```

설정 후 Loki로 stdout 확인. 같은 로거의 다른 DEBUG 로그(`Channel Release` 등)는 정상적으로 보임 → 동작 자체에는 문제 없음 확인.

그러나 **`"Immediately aborted pooled channel, re-acquiring new channel"` 메시지는 한 번도 안 찍혔다.** 그 사이에도 Tempo 499는 계속 발생.

원인이 아니었다.

---

## 부모 요청 취소 이슈인가

상위(SCG → stock-mediation) 요청에서 타임아웃이나 연결 끊김이 발생해서 그 취소가 아래로 전파된 거 아닐까 하는 것도 확인했다.

확인 결과: **stock-mediation이 SCG로 보내는 최종 응답은 항상 200.** 인바운드 요청 자체가 비정상 종료된 게 없다.

추가로, 499가 찍히는 호출들이 대부분 말단 로직이라 그 호출에 종속된 하위 호출 자체가 없다는 것도 확인됐다. 연쇄 취소가 발생할 구조 자체가 없음.

아니었다.

---

## 캐시/스케줄 잡 이슈인가

`Price.domestic[...]` 같은 캐시성 데이터를 쓰는 `getLatestPriceCached` 계열도 살펴봤는데, 내부를 보면 순수 인메모리 조회(`Price.domestic[key] ?: raise(...)`)라서 **네트워크 호출 자체가 없다.** 애초에 499 스팬이 생길 수 없음.

클로드가 `Flux.interval`로 구현된 Job도 의심했는데, 내부 보면 네트워크 호출이 없다고 정정했음.

실제 관측 결과도 특정 캐시나 특정 서비스에 국한되지 않고, `stock-customer-service`, `overseas-stock-service` 등 **다양한 다운스트림에서 무차별적으로** 나타났다.

아니었다.

---

여기까지 안 된 것들:
- idle-timeout 튜닝 (1차)
- SCG 풀 튜닝 (2차)
- 코루틴 연쇄 취소 (3차, 원복)
- Reactor Netty 내부 자동 복구
- 부모 요청 취소 전파
- 캐시/스케줄 잡

근데 단서들이 쌓이고 있다. Tempo에는 계속 찍히는데 애플리케이션 로그에는 없다, 최종 응답은 항상 200이다, 특정 호출에 국한 없이 무차별적으로 나온다, 항상 499 하나만 단독으로..

[3부에서 최종 원인 확정 →]({% post_url 2026-08-17-stock-mediation-499-part3 %})
