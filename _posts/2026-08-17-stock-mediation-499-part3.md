---
title: stock-mediation 499 트레이싱 일대기 (3부) — 두 가지 원인과 SCG 재시도 추가 중 생긴 에러
date: 2026-08-17
tags:
  - Spring
  - WebFlux
  - Reactor
  - Kubernetes
  - 실무경험
category:
  - 실무경험
---

[1부]({% post_url 2026-08-17-stock-mediation-499-part1 %}), [2부]({% post_url 2026-08-17-stock-mediation-499-part2 %})에서 이것저것 다 확인했는데 전부 아니었다. 이 글에서 진짜 원인들을 확인하고, 그 이후에 한 SCG 재시도 추가 작업이랑 그 과정에서 생긴 에러까지 정리한다.

결론부터: **499는 두 케이스였다.**

- **진짜 499**: SCG `server.netty.idle-timeout: 1s` 설정 버그. 전체 499 중 99%.
- **eBPF 노이즈**: Reactor Netty 내부 재시도를 커널 레벨 계측이 못 봄. 실제 임팩트 없음.

---

## 진짜 원인 — SCG server.netty.idle-timeout: 1s

SCG 방어 작업을 하다가 기존 설정을 정리하는 중에 발견했다.

`server.netty.idle-timeout`이 **1초**로 잡혀 있었다.

1초 idle이면 실제 운영 트래픽에서 keep-alive 커넥션이 거의 항상 서버 쪽에서 끊기는 수준이다. 레거시 → SCG 구간에서 idle이 1초만 넘으면 SCG가 커넥션을 끊어버리고, 클라이언트는 이미 죽은 커넥션으로 요청을 보내게 됨 → premature close. 이게 Tempo에 499로 찍히는 주된 원인이었다.

이 설정을 제거하고 httpclient 풀도 명시적으로 정리했다.

```yaml
spring:
  cloud:
    gateway:
      httpclient:
        connect-timeout: 60000
        response-timeout: 60000
        pool:
          max-connections: 500
          max-idle-time: 45s
          max-life-time: 50s
          acquire-timeout: 5000
          eviction-interval: 55s
```

배포 후 Tempo 499 건수가 확 줄었다. 실제로 에러가 났던 499들이 이게 원인이었다.

---

## 나머지 499 — eBPF 노이즈

1초 설정 제거 이후에도 Tempo에 499가 간헐적으로 찍혔다. 건수가 훨씬 줄긴 했는데 완전히 사라지지는 않음.

결정적 단서는 트레이스의 **리소스 속성**이었다. 클로드가 찾아줬는데 처음에 이게 뭔지 몰랐다.

```
telemetry.sdk.name = beyla
telemetry.sdk.version = 1.44.0
telemetry.distro.name = opentelemetry-ebpf-instrumentation
```

`opentelemetry-ebpf-instrumentation`(구 Grafana Beyla, 현재는 OpenTelemetry에 기증됨 — [공식 발표](https://grafana.com/blog/opentelemetry-ebpf-instrumentation-beyla-donation/))은 **JVM 애플리케이션 코드를 전혀 거치지 않고, 커널 레벨에서 실제 TCP 소켓 syscall(`connect`/`write`/`read`/`close`)을 eBPF 프로브로 직접 관측**해서 HTTP 트랜잭션을 재구성하는 도구다. "애플리케이션 코드의 협조 없이(without any cooperation from the application itself)" 작동한다고 벤더 스스로 명시하고 있다.

Reactor Netty는 풀에서 꺼낸 커넥션이 죽어있다는 걸 감지하면 **JVM 내부에서 조용히 새 커넥션으로 1회 재시도**한다(2부에서 바이트코드로 확인했던 그것). 애플리케이션 레이어에서는 결국 성공 → **최종 응답은 200**.

eBPF는 이 전체 흐름에서 **"죽은 첫 번째 소켓"만 독립된 이벤트로 관측**한다. 그 소켓 위에서 요청은 나갔는데 응답 바이트를 하나도 못 받고 닫혔으니, nginx 컨벤션을 차용해서 **499를 합성해서 기록**한다. 소켓 #1(죽음)과 소켓 #2(재시도 성공)는 eBPF 입장에서 완전히 별개의 이벤트다 — 커널 소켓 레벨에선 JVM 내부에서 재시도로 복구됐다는 걸 알 방법이 없는 것.

그래서:
- 애플리케이션 로그에 안 남음 → JVM 내부에서 처리됨
- 최종 응답 항상 200 → 재시도 성공
- 특정 서비스 국한 없이 무차별적 → 커넥션 재사용은 모든 다운스트림에서 동일하게 발생
- 499 항상 단독으로만 → 애플리케이션 레벨에선 에러가 없으니 희생자가 없는 게 당연

**이 499는 실제 임팩트가 없다.** 알림/대시보드 쪽에서 "자식 span만 499, 최종 응답은 200"인 패턴을 별도 분류/제외하는 게 맞는 방향.

클로드가 reactor-netty 이슈 트래커에서 비슷한 케이스들을 찾아줬는데, 전부 메인테이너가 "status/invalid"로 종료했다 — reactor-netty 자체 버그가 아니라 분산 시스템 커넥션 풀링에서 원래 그렇게 동작하는 것이라는 거 ([#1092](https://github.com/reactor/reactor-netty/issues/1092), [#1296](https://github.com/reactor/reactor-netty/issues/1296), [#1639](https://github.com/reactor/reactor-netty/issues/1639)).

---

## SCG 단 방어 확장

원인을 잡은 김에 레거시 → SCG → stock-mediation 전체 체인에서도 같은 종류의 idle-timeout race가 원리상 똑같이 발생할 수 있어서 hop별로 방어를 맞추는 작업을 추가로 진행했다.

### 각 hop별 idle-timeout 정합

원칙: 각 hop에서 **클라이언트 idle-timeout < 서버 idle-timeout**이어야 서버가 끊기 전에 클라이언트가 먼저 idle 커넥션을 정리해서 race가 안 생긴다.

```
레거시 (HTTP timeout 60~70s, Tomcat)
  → SCG server.netty.idle-timeout: 60s
    → stock-mediation (SCG httpclient pool.max-idle-time: 45s)
      → stock-mediation server.netty.idle-timeout: 60s
        → downstream (WebClientConfig maxIdleTime: 40s)
```

작업하면서 순서 버그를 하나 발견했다 — SCG 클라이언트 idle-time(45s)이 stock-mediation 서버 idle-timeout(당시 설정 자체 없음 → Reactor Netty 기본값)보다 길게 잡혀있던 역전 상태. SCG를 낮추는 대신 **stock-mediation 서버 쪽에 `server.netty.idle-timeout: 60s`를 새로 추가**해서 해결.

그리고 `WebClientConfig.kt`의 `maxIdleTime`/`maxLifeTime`도 재조정했다. 2부에서 설정한 `20s`/`30s` 값이 문제가 있었음 — `maxLifeTime`이 `maxIdleTime`보다 짧으면 idle 여부와 무관하게 `maxLifeTime`에 먼저 걸려서 `maxIdleTime` 설정 자체를 무력화한다. **`maxIdleTime(40s)`, `maxLifeTime(90s)`로 최종 조정**.

### SCG에 GET 요청 premature-close 1회 재시도 추가

stock-mediation에 이미 재시도가 있으니, SCG → stock-mediation 쪽에도 동일하게 달았다. ([issue #1](https://github.com/inha18minseokkim/stock-mirrored/issues/1) / [PR #2](https://github.com/inha18minseokkim/stock-mirrored/pull/2))

```java
// ApiGatewayConfig.java
.retry(retryConfig -> retryConfig
    .setRetries(1)
    .setMethods(HttpMethod.GET)
    .setExceptions(PrematureCloseException.class, IOException.class)
    .setBackoff(Duration.ofMillis(50), Duration.ofMillis(200), 2, false))
```

몇 가지 확인한 것들:

**`exceptions`에 `IOException`까지 넣은 이유**: SCG `Retry` 필터의 매칭은 `Class.isInstance()`(서브타입 포함) 기반이라서 `IOException` 하나만으로도 `PrematureCloseException`(`IOException` 서브클래스)은 이미 커버된다. `PrematureCloseException.class`를 같이 명시한 건 매칭 목적이 아니라 코드만 보고 이 설정이 뭘 겨냥한 건지 알 수 있도록 의도 표시용. `IOException`은 connection reset 등 다른 일시적 네트워크 오류까지 방어 범위를 넓히는 실질적 역할.

**SCG의 `Retry` GatewayFilterFactory는 `statuses`/`series`로 매칭하면 안 된다**: 이건 정상적으로 상태코드가 있는 응답에만 적용된다. premature-close는 응답 자체가 없는 상황이라 이 조건들로는 절대 못 잡는다 — `exceptions` 조건이 필요한 이유.

**필터 배치 순서**: `cacheRequestBody`보다 뒤(재시도 시 요청 바디 재전송 가능), `modifyRequestBody`/`modifyResponseBody`보다 앞(재시도마다 실행, 최종 성공 응답만 변형)에 배치.

---

## 배포하고 생긴 에러 — `NettyDataBuffer cannot be cast to ... JsonNode`

PR #2 배포 직후 `NettyDataBuffer cannot be cast to class com.fasterxml.jackson.databind.JsonNode` 발생. 처음엔 `ApiGatewayConfig.java`만 고쳤는데 같은 에러가 `MciToRestURIFilter.java:26`에서도 또 터졌다. 클로드한테 jar 디컴파일 시켜서 원인을 찾았다.

알고 보니 `CacheRequestBody` + `Retry`를 같이 쓰면 슬롯 충돌이 나는 건 SCG에 알려진 이슈였다 ([#1939](https://github.com/spring-cloud/spring-cloud-gateway/issues/1939), [#2220](https://github.com/spring-cloud/spring-cloud-gateway/issues/2220), [#1873](https://github.com/spring-cloud/spring-cloud-gateway/issues/1873)).

### 수정

`CACHED_REQUEST_BODY_ATTR` 슬롯은 route에 retry가 있는 한 신뢰할 수 없다. 이 슬롯을 읽는 코드를 전부 없애고, 대신 **`cacheRequestBody`가 만들어준 재생 가능한(replayable) 요청 바디**(`exchange.getRequest().getBody()`)를 각자 직접 다시 읽어 파싱하도록 변경했다.

- `ApiGatewayConfig.java`: `modifyRequestBody`의 콜백이 받는 `body` 파라미터를 전용 attribute(`ORIGINAL_REQUEST_BODY_ATTR = "kbankOriginalRequestBody"`)에 저장해두고, `getModifiedResponseBody`가 그걸 읽도록 변경. ([PR #3](https://github.com/inha18minseokkim/stock-mirrored/pull/3))
- `MciToRestURIFilter.java`: `DataBufferUtils.join(exchange.getRequest().getBody())` + `ObjectMapper.readTree(...)` 직접 재파싱으로 변경. ([PR #4](https://github.com/inha18minseokkim/stock-mirrored/pull/4))
- `cacheRequestBody(JsonNode.class)` 필터 자체는 유지 — retry의 재전송 메커니즘을 위해 여전히 필요. 우리 코드에서 그 결과 슬롯을 더 이상 읽지 않는 것.

---

## retry 설정 yml로 이전

retry 값이 Java 코드에 하드코딩돼 있는 게 마음에 걸려서 YAML로 분리했다.

라우트 전체를 YAML로 이전하는 것까지 고려했는데, jar 디컴파일로 두 가지 제약을 확인하고 접었다.

- `spring.cloud.gateway.default-filters`는 `RouteDefinitionRouteLocator`(YAML로 정의된 라우트)에만 적용된다. 이 앱처럼 `RouteLocatorBuilder`(Java DSL)로 만든 라우트에는 아예 적용 안 됨.
- `ModifyRequestBody`/`ModifyResponseBody`의 `setRewriteFunction(...)`은 실제 `RewriteFunction` **객체**만 받는다. MCI 헤더 조립·에러코드 처리·트랜잭션 로깅 같은 커스텀 로직이 이 필터들 안에 있어서 YAML로 표현 자체가 불가능.

**최종 결정**: 필터 배선(어떤 필터를 어떤 순서로)은 Java DSL에 남기고, 튜닝 가능한 값만 yml로 분리.

```kotlin
@ConfigurationProperties(prefix = "stock-gateway.retry")
class StockMediationRetryProperties(
    val retries: Int,
    val methods: List<HttpMethod>,
    val exceptionClassNames: List<String>,
    val backoff: BackoffConfig,
) {
    fun getExceptionClasses(): List<Class<out Throwable>> =
        exceptionClassNames.map { Class.forName(it) as Class<out Throwable> }
    // ...
}
```

`exceptions`를 FQCN 문자열 리스트로 받고 `Class.forName`으로 변환한 이유는, Spring Boot 기본 `ConversionService`에 String→Class 컨버터가 항상 보장되는지 확신이 없어서 안전한 방향을 택했다.

---

## 최종 결론

| | 진짜 499 (99%) | eBPF 노이즈 (나머지) |
|---|---|---|
| **원인** | SCG `server.netty.idle-timeout: 1s` 설정 버그 | `opentelemetry-ebpf-instrumentation` — 커널 소켓 레벨이라 JVM 내부 재시도를 못 봄 |
| **실제 임팩트** | 있음. 실제 premature close 에러 발생 | 없음. stock-mediation 최종 응답은 200, 앱 로그에도 에러 없음 |
| **해결** | `server.netty.idle-timeout` 제거 | 알림/대시보드에서 "자식 span만 499, 최종 응답은 200" 패턴 분류/제외 |

중간에 발견한 커넥션 풀 고갈(`pending acquire queue has reached its maximum size`)도 진짜 문제였다 — `WebClientConfig.kt` `maxConnections`/`pendingAcquireMaxCount`/`pendingAcquireTimeout`/`maxLifeTime` 명시적 설정으로 수정 완료 (2부).

**추가 방어**: 레거시→SCG→stock-mediation 전체 체인 hop별 idle-timeout 정합, SCG에 GET premature-close 1회 재시도 추가.

## 원복된 변경

- `InvestingHomeController.kt`의 `coroutineScope` → `supervisorScope` 변경: 코루틴 연쇄 취소가 원인이 아님을 확인하고 원복. 최종 `coroutineScope` 그대로 유지.

---

처음에 Tempo에 499가 찍혔을 때 뭔가 심각한 버그겠지 했는데, 결론은 설정 버그 하나(1초 idle-timeout)랑 eBPF가 원래 그렇게 보이는 것 두 개였다. eBPF 기반 auto-instrumentation 쓰는 환경이라면 커넥션 재사용 재시도가 일어나는 스택에서는 이런 현상이 항상 나올 수 있다는 걸 알고 있어야 할 것 같다.
