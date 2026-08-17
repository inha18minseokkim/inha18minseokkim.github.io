---
title: stock-mediation 499 트레이싱 일대기 (2부) — 커넥션 풀 고갈과 가설들의 무덤
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

[1부]({% post_url 2026-08-17-stock-mediation-499-part1 %})에서 idle-timeout 가설 → SCG 튜닝 → 코루틴 캐스케이드 가설까지 전부 기각됐다. 그래도 하나 건진 게 있는데, 499는 항상 단독으로만 찍힌다는 것. 연쇄 실패의 흔적이 없다.

이 글은 거기서 이어진다.

---

## 재시도 로직에 계측 추가

뭔가를 고치기 전에, 먼저 현상을 제대로 관측할 수 있는 장치를 달았다. `WebClientManager.kt`의 `PREMATURE_CLOSE_RETRY` 재시도 로직에 `.doBeforeRetry { }` 로그를 추가해서, 재시도가 실제로 발동하면 `[WebClientManager][retry]` 로그가 남도록.

이후 발생한 499 건들에서 `[WebClientManager][retry]` 로그는 **총 1건만** 나왔다. 진짜 `PrematureCloseException`이 우리 코드 레이어까지 올라오는 경우는 극히 드물다는 거다. 499가 Tempo에는 계속 찍히는데 애플리케이션 로그에는 거의 안 남는다 — 이것도 나중에 중요한 단서가 된다.

---

## 커넥션 풀 고갈 발견

앱 로그를 더 살펴보다가 별도의 에러를 하나 발견했다.

```
[getList] pending acquire queue has reached its maximum size of 32
```

Reactor Netty의 `PoolAcquirePendingLimitException` — **커넥션 풀 자체가 부족해서 대기열까지 꽉 찬 상황**이다. 이건 499랑은 별개의 진짜 문제.

원인을 추적했다. `WebClientConfig.kt`에서 `ConnectionProvider.builder(...)`에 `maxConnections`를 명시하지 않아서 Reactor Netty 기본값인 `Runtime.availableProcessors() * 2`를 쓰고 있었다. 그리고 이 기본값은 **다운스트림 host별로 적용**된다.

k8s 환경에서 JVM이 파드의 CPU limit이 아니라 **노드 전체 코어 수**를 인식하는 경우가 흔한데, 그러면 이 기본값이 실제 동시 호출량 대비 지나치게 작거나 예측 불가능하게 잡힌다. 거기다 부가 가설도 하나 생겼다 — 풀이 작으면 커넥션이 과도하게 재사용되면서 서버(Tomcat) 쪽의 `maxKeepAliveRequests`(요청 횟수 기반 keep-alive 한도)에 먼저 걸려서 서버가 끊을 수 있다는 것. 이건 idle 시간과 **무관**하기 때문에 `maxIdleTime` 튜닝으로는 막을 수 없다 — 처음부터 가설이 틀렸던 거.

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

배포 후 `PoolAcquirePendingLimitException` 에러 로그는 **완전히 사라졌다**. 그러나 **Tempo에는 여전히 499 이벤트가 계속 잡힌다.** 진짜 원인은 이게 아니라는 뜻.

---

## Reactor Netty 내부 자동 복구 가설

여기서 reactor-netty 소스를 직접 까봤다.

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

이게 원인이라면 설명이 되지 않나? JVM 안에서는 재시도로 성공 → 애플리케이션 로그엔 안 남고 → Tempo에는 첫 번째 죽은 소켓이 499로 찍히는..

로거는 `reactor.netty.resources.DefaultPooledConnectionProvider` (DEBUG 레벨).

### 검증 시도

```yaml
logging:
  level:
    reactor.netty.resources.DefaultPooledConnectionProvider: DEBUG
```

설정 후 Loki로 stdout 확인. 같은 로거의 다른 DEBUG 로그(`Channel Release` 등)는 정상적으로 보임 → 로깅 파이프라인 자체는 문제 없음 확인.

그러나 **`"Immediately aborted pooled channel, re-acquiring new channel"` 메시지는 한 번도 안 찍혔다.** 그 사이에도 Tempo 499는 계속 발생.

이 코드 경로가 원인이 아님. 기각.

---

## 부모 요청 취소 가설

상위(SCG → stock-mediation) 요청에서 타임아웃이나 연결 끊김이 발생해서 그 취소가 아래로 전파된 거 아닐까 하는 가설도 확인했다.

확인 결과: **stock-mediation이 SCG로 보내는 최종 응답은 항상 200.** 인바운드 요청 자체가 비정상 종료된 게 없다.

추가로, 499가 찍히는 호출들이 대부분 말단 로직이라 그 호출에 종속된 하위 호출 자체가 없다는 것도 확인됐다. 취소를 유발할 구조 자체가 없음.

기각.

---

## 캐시/스케줄 잡 가설

`Price.domestic[...]` 같은 캐시성 데이터를 쓰는 `getLatestPriceCached` 계열도 살펴봤는데, 내부를 보면 순수 인메모리 조회(`Price.domestic[key] ?: raise(...)`)라서 **네트워크 호출 자체가 없다.** 이 경로에선 애초에 499 스팬이 생길 수 없음.

실제 관측 결과도 특정 캐시나 특정 서비스에 국한되지 않고, `stock-customer-service`, `overseas-stock-service` 등 **다양한 다운스트림에서 무차별적으로** 나타났다.

기각.

---

여기까지 기각 목록:
- idle-timeout 튜닝 (1차)
- SCG 풀 튜닝 (2차)
- 코루틴 캐스케이드 (3차, 원복)
- Reactor Netty 내부 자동 복구
- 부모 요청 취소 전파
- 캐시/스케줄 잡

근데 단서들이 쌓이고 있다. Tempo에는 계속 찍히는데 애플리케이션 로그에는 없다, 최종 응답은 항상 200이다, 특정 호출에 국한 없이 무차별적으로 나온다, 항상 499 하나만 단독으로..

[3부에서 최종 원인 확정 →]({% post_url 2026-08-17-stock-mediation-499-part3 %})
