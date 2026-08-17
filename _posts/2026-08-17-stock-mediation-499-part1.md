---
title: stock-mediation 499 트레이싱 일대기 (1부) — idle 커넥션 이슈에서 코루틴까지
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

Grafana Tempo 트레이스에 `499 connection prematurely closed BEFORE response`가 간헐적으로 찍히기 시작했다. 대상 구간은 `istio-gateway → SCG(Spring Cloud Gateway) → stock-mediation → (listed-stock-service / overseas-stock-service / stock-customer-service / etf-service 등)` 체인 중 stock-mediation이 뒷단을 WebClient로 호출하는 hop.

결론부터 말하면 이 499는 **eBPF 계측 도구가 원래 그렇게 보이는 것**이었다. 실제 애플리케이션에는 아무 영향이 없었음. 근데 그 결론까지 오는 데 조사 과정이 꽤 길었고, 중간에 진짜 문제(커넥션 풀 고갈)도 하나 발견했고, SCG에 재시도 붙이다가 에러도 하나 터졌다. 3부로 나눠서 적는다.

- **1부 (이 글)**: idle 커넥션 이슈 → SCG 튜닝 → 코루틴 연쇄 취소 원인 아님
- [**2부**]({% post_url 2026-08-17-stock-mediation-499-part2 %}): 재시도 계측 → 커넥션 풀 고갈 → Reactor Netty 내부 → 전부 아님
- [**3부**]({% post_url 2026-08-17-stock-mediation-499-part3 %}): SCG 1초 설정 버그가 99% 원인 → eBPF 노이즈 → SCG에 재시도 추가 → 생긴 에러 → 결론

---

## 최초 증상

관측 도구는 Grafana Tempo(트레이스)와 Loki(stdout 로그).

stock-mediation이 downstream 서비스들을 호출할 때 `499 connection prematurely close BEFORE response`가 반복적으로 찍힘. 처음엔 이걸 전형적인 **idle 커넥션 race** 문제로 봤다 — 커넥션 풀에 남아있던 idle 커넥션을, 다운스트림 LB/nginx이 자기 idle timeout으로 이미 끊어버린 뒤에 클라이언트가 그걸 모르고 재사용하는 패턴.

### 1차 조치: 커넥션 풀 idle timeout 설정

`WebClientConfig.kt`를 고쳤다.

- 기존: Reactor Netty 기본 전역 풀 사용 (커스터마이징 전혀 없음)
- 변경: `ConnectionProvider.builder("stock-mediation-http")`로 명시적 풀을 만들고, `maxIdleTime(20s)` + `evictInBackground(30s)` 적용. 다운스트림이 끊기 전에 클라이언트가 먼저 idle 커넥션을 정리하도록.

`WebClientManager.kt`에는 GET 계열 6개 메서드(`get`, `getWithoutKbankContext`, `getListWithoutKbankContext`, `getList`, `getFlux`, `getFluxWithoutKbankContext`)에 `PrematureCloseException` 전용 1회 재시도(`retryWhen`)를 추가했다. POST/PUT은 non-idempotent라 제외.

```kotlin
// WebClientManager.kt — GET 계열 공통 패턴 (단순화)
fun get(...): Mono<T> =
    webClient.get()
        ...
        .retryWhen(
            Retry.max(1)
                .filter { it is PrematureCloseException }
        )
```

배포·재기동 후에도 **499 지속**.

---

## SCG도 튜닝

stock-mediation만 잡아서 될 문제가 아닌가 싶어서, SCG의 httpclient 풀 설정도 손봤다.

```yaml
spring:
  cloud:
    gateway:
      httpclient:
        pool:
          max-connections: 500
          max-idle-time: 10s
          max-life-time: 15s
          acquire-timeout: 5000
          eviction-interval: 20s
```

재기동 직후엔 499가 잠깐 없다가, **얼마 안 가 다시 몰려서 발생**. idle-timeout 가설이 맞다면 설정 반영 직후부터 효과가 있어야 하는데, 재기동 후 잠깐 조용하다가 다시 터지는 패턴은 이 가설로 설명이 안 된다는 걸 여기서 처음 인지했다.

---

## 코루틴 연쇄 취소가 원인일까

트레이스를 더 들여다봤다. `stock-mediation`이 `GET /stock-customer-service/interests/v1/investing-home`을 호출한 케이스에서 이상한 게 보였다.

- stock-mediation 쪽 span: **22.25ms에 끊김**
- stock-customer-service 쪽 span: **25.71ms에 정상 완료**

서버가 응답을 만들기 직전에 **클라이언트가 먼저 끊은 패턴**이다. 서버 쪽이 먼저 끊은 게 아님.

클로드가 `InvestingHomeController.kt`를 분석했더니 `CoroutineUtil.kt` 구조를 문제라고 했다.

```kotlin
// 단순화한 구조 (실제 코드와 약간 다름)
coroutineScope {
    val prices  = tryCatchAsync { ... }          // 예외 → 그대로 throw
    val interests = tryCatchAsyncOrNull { ... }  // 예외 → null 반환
    val ranks     = tryCatchAsyncOrDefault { ... }// 예외 → default 반환
    // ...
}
```

**Kotlin 구조적 동시성 규칙**: `coroutineScope` 안에서 형제 코루틴 하나가 예외를 던지면 나머지 형제 전부가 즉시 취소된다. `prices` 같은 필수 데이터 호출이 실패하면, 아무 잘못도 없이 진행 중이던 `interests`(stock-customer-service 호출)도 강제 취소 → 이미 보낸 TCP 커넥션이 응답 오기 전에 끊겨서 499처럼 보인다는 이론.

### 2차 조치: supervisorScope (이후 원복됨)

`InvestingHomeController.kt`의 모든 `coroutineScope { }` → `supervisorScope { }`로 변경. 형제 하나가 실패해도 나머지 형제는 계속 실행되도록.

### 근데 트레이스가 이걸 반박함

클로드가 세운 가설인데, 코드 원작자인 내가 두 가지를 정정했다.

첫째, `tryCatchAsync`가 필수 데이터 없을 때 500을 주는 건 **의도된 설계**임. 그게 문제가 아니다.

둘째가 결정적이었는데 — 실제 트레이스를 보면 detail/rank 등 **다른 엔드포인트**에서도 똑같이 "정상 호출들 중 딱 하나만 499, 나머지는 전부 정상"이 **100%** 관측된다. 이 이론이 맞다면 "진짜 원인이 된 실패 호출(에러 상태) + 그로 인해 끊긴 희생자(499)"가 최소 2개는 트레이스에 같이 찍혀야 한다. 근데 실제로는 **원인이 될 만한 실패가 트레이스 어디에도 없이 499 하나만 단독으로** 나온다.

이론이 틀렸다. `InvestingHomeController.kt` `coroutineScope`로 원복.

---

여기서 확보한 단서가 하나 있다. **499는 항상 단독으로만 나온다.** 연쇄 실패의 흔적이 없다. 이게 나중에 중요해진다.

[2부로 →]({% post_url 2026-08-17-stock-mediation-499-part2 %})
