---
title: HTTP/2 헤더 대소문자 문제 — Netty는 왜 case-insensitive를 포기했나
date: 2026-06-25
tags:
  - Netty
  - HTTP
  - Spring
category:
  - 기술
---

Spring Boot 4.x (Reactor Netty 2.x / Netty 5) 환경에서 `Kbank-Header`로 헤더를 조회했는데 `kbank-header`로 들어온 값을 못 찾는 문제가 생김.

```kotlin
// Kbank-Header 로 저장돼 있으면 찾음, kbank-header 로 저장돼 있으면 못 찾음
exchange.request.headers.getFirst("Kbank-Header") // → null (HTTP/2 경로)
```

처음엔 그냥 잘못 짠줄 알았는데 서블릿과 아닌것 부터의 차이부터 시작 ㄷ

---

## 왜 이렇게 되는가 — 프로토콜 레벨부터

### HTTP/1.1: 헤더 이름은 대소문자 무관

[RFC 7230 §3.2](https://datatracker.ietf.org/doc/html/rfc7230#section-3.2)에 이렇게 나와있음.

> "Each header field consists of a case-insensitive field name…"

HTTP/1.1 텍스트 프로토콜에서는 `Content-Type`, `content-type`, `CONTENT-TYPE`이 다 동일한 헤더로 취급됨. Netty 4의 `DefaultHttpHeaders`는 내부적으로 `AsciiString.equalsIgnoreCase()`를 써서 case-insensitive 조회를 지원한다.

### HTTP/2: 헤더 이름은 반드시 소문자

[RFC 7540 §8.1.2](https://datatracker.ietf.org/doc/html/rfc7540#section-8.1.2)는 아예 강제 규정이라고 나와있다.

> "Header field names MUST be converted to lowercase prior to their encoding in HTTP/2. A request or response containing uppercase header field names MUST be treated as malformed."

HTTP/2는 헤더를 HPACK이라는 바이너리 압축 포맷으로 전송하는데, HPACK 정적 테이블에 등록된 헤더 이름은 전부 소문자이다. 대문자를 허용해버리면 같은 헤더가 두 가지 인코딩으로 표현될 수 있어서 압축 효율이 깨진다고 한다. 그래서 스펙 자체가 대문자를 **프로토콜 위반(malformed)**으로 규정해버림.

---

## Netty 5가 case-insensitive를 제거한 이유

### Spring Boot 버전별 Netty 매핑

| Spring Boot | Reactor Netty | Netty | 헤더 조회 |
|---|---|---|---|
| 3.3.x | 1.1.x | **4.1.x** (io.netty) | case-insensitive ✓ |
| 4.0.x | 2.0.x | **5.0.x** (io.netty5) | HTTP/2 경로 case-sensitive ✗ |

Spring Boot 3.x 기반 WebFlux 프로젝트에서 이 문제가 안 생겼던 건 WebFlux라서가 아니라 **Netty 4를 썼기 때문**임. 스프링 부트 버전을 올리면서 Netty 4 → 5 업그레이드되니깐 이 문제가 드러남

### Netty 4까지의 동작

```
HTTP/1.1 수신 → DefaultHttpHeaders (AsciiString case-insensitive 해시) → getFirst("Kbank-Header") ✓
HTTP/2  수신 → DefaultHttp2Headers (lowercase 강제 저장)              → getFirst("Kbank-Header") ✓ (Netty 4는 여기도 insensitive)
```

Netty 4의 `DefaultHttp2Headers`는 HTTP/1.1 경로랑 같은 `DefaultHeaders<CharSequence, CharSequence>` 기반을 공유하고, 이름 비교에 `AsciiString.CASE_INSENSITIVE_HASHER`를 썼음.

### Netty 5에서 바뀐 것

Netty 5(io.netty5)는 HTTP/2 헤더 구현을 아예 분리해버림.

- HTTP/1.1 경로: 여전히 case-insensitive hasher 유지
- HTTP/2 경로: `Http2Headers`(io.netty5.handler.codec.http2.headers)는 **`CASE_SENSITIVE` hasher**를 사용

이유는 두 가지임.

1. **스펙 준수**: HTTP/2는 소문자를 강제함. 서버가 대문자로 된 HTTP/2 헤더를 받았다면 그 요청은 이미 스펙 위반인 거고, 위반 요청을 암묵적으로 받아주면 클라이언트 버그를 숨기는 셈이 됨.
2. **성능**: 모든 HTTP/2 헤더가 항상 소문자임이 보장되는데, 매 조회마다 `toLowerCase()` + 해시 재계산하는 건 낭비임. case-sensitive 해시는 단순 바이트 비교로 끝나니까 훨씬 빠름.

관련 논의:
- [netty/netty#10747](https://github.com/netty/netty/issues/10747) — HTTP/2 header name validation 강화
- [netty/netty#9985](https://github.com/netty/netty/issues/9985) — Http2Headers lowercase enforcement

---

## Spring Framework 쪽 상황

Spring Framework 6/7은 Reactor Netty의 헤더를 `ReactorNettyHeadersAdapter`로 감싸서 노출함.

```
exchange.request.headers
  └── HttpHeaders (Spring)
        └── ReactorNettyHeadersAdapter.get(key)
              └── io.netty5.handler.codec.http2.headers.Http2Headers.getAll(key)
                    └── CASE_SENSITIVE 해시 조회 → "Kbank-Header" ≠ "kbank-header" → null
```

Spring 자체의 `HttpHeaders(LinkedCaseInsensitiveMap)`를 직접 만들면 당연히 insensitive임. 문제는 **Reactor Netty를 통해 들어온 HTTP/2 요청은 Spring의 `LinkedCaseInsensitiveMap`을 아예 거치지 않는다는 것**. Netty의 native 구조체를 어댑터로만 감싸기 때문에 Netty의 case-sensitive 동작이 그대로 새어나오는 거임.

관련 논의: [spring-projects/spring-framework#29866](https://github.com/spring-projects/spring-framework/issues/29866)

---

## 실제로 소문자로 들어오는 경로

| 발신 클라이언트                                        | 프로토콜         | 헤더 이름 도달 형태             |
| ----------------------------------------------- | ------------ | ----------------------- |
| IntelliJ HTTP Client                            | HTTP/1.1     | `Kbank-Header` (원본 유지)  |
| `curl` (기본)                                     | HTTP/1.1     | `Kbank-Header` (원본 유지)  |
| Java HttpClient (`JdkClientHttpRequestFactory`) | HTTP/2 협상 가능 | `kbank-header` (소문자 변환) |
| Reactor Netty (`ReactorClientHttpConnector`)    | HTTP/2 협상 가능 | `kbank-header` (소문자 변환) |
| Kubernetes Ingress (nginx/envoy) 경유             | 프록시 정규화      | `kbank-header` (정규화됨)   |

RestClient 기본 구현(`SimpleClientHttpRequestFactory`)은 HTTP/1.1이라 케이스가 그대로 보존됨. 근데 다른 서비스가 `JdkClientHttpRequestFactory`나 Reactor Netty 커넥터를 쓰거나, 중간에 nginx/envoy 같은 프록시가 끼어 있으면 소문자로 바뀜.

---

## WebClient vs RestClient — 클라이언트 전환이 원인처럼 보인 이유

### RestClient(`SimpleClientHttpRequestFactory`)는 Netty 기반이 아님 >> 당연한거

실제 코드(`InternalAdapterClientConfig.kt`)를 보면 이렇게 돼있었음.

```kotlin
val factory = SimpleClientHttpRequestFactory().apply { ... }
RestClient.builder().requestFactory(factory).build()
```

`SimpleClientHttpRequestFactory` = `java.net.HttpURLConnection` = **HTTP/1.1 only**. HTTP/2를 아예 지원 안 하고 헤더 케이스를 그대로 보존해서 전송함. 즉 RestClient가 `Kbank-Header`를 설정하면 서버에도 `Kbank-Header`로 도달함.

### WebClient가 괜찮았던 이유 — 사실 클라이언트 문제가 아니었음

WebClient(`ReactorClientHttpConnector`)도 기본 HTTP/1.1에서는 케이스를 보존함. HTTP/2를 협상하려면 TLS + ALPN이나 명시적 h2c 설정이 필요한데, 일반 내부 서비스 호출 환경에서는 WebClient도 그냥 HTTP/1.1로 통신하는 경우가 대부분임.

그러니까 **WebClient → RestClient 전환이 케이스 문제의 직접 원인은 아니었던 것.**

진짜 원인은 **서버 쪽 Netty 5**였다. Netty 5가 HTTP/1.1 헤더도 수신 시 소문자로 정규화해서 저장하는 쪽으로 바뀌었고, 이 때문에 클라이언트가 어떤 케이스로 보내든 서버에서는 `kbank-header`로 저장돼버림.

```
클라이언트 (WebClient/RestClient)  →  Kbank-Header 전송 (HTTP/1.1)
                                         ↓
                              Netty 5 수신 — kbank-header 로 정규화 저장
                                         ↓
              headers["Kbank-Header"]  →  case-sensitive 조회  →  null
```

WebClient가 "괜찮았던" 것처럼 보였다면, 그건 당시 `KbankContextFilter` 자체가 없었거나 다른 경로로 컨텍스트를 처리했기 때문이지, WebClient라서 면제된 게 아니었음.

---

## Tomcat(Spring Boot Web)이었으면 문제없었을까

**결론: 없었을 것.**

### 이유 — Java Servlet 스펙의 강제

Java Servlet 스펙(JSR-340, `javax.servlet.http.HttpServletRequest`)은 명시적으로 이렇게 요구한다고 한다.

> "The header name must be case-insensitive." — Servlet 4.0 Specification §15.1.7

Tomcat은 Servlet 컨테이너라서 이 스펙을 **반드시** 구현해야 함. 내부적으로 `org.apache.tomcat.util.http.MimeHeaders`를 쓰는데, 이 클래스는 헤더 이름을 ASCII 소문자로 정규화해서 저장하고 조회할 때도 소문자 변환 후 비교함. 즉 `getHeader("Kbank-Header")`랑 `getHeader("kbank-header")`는 항상 같은 결과를 반환함.

### Tomcat vs Netty 5 비교

| 구분                         | Tomcat (Servlet)      | Reactor Netty 5 (WebFlux)      |
| -------------------------- | --------------------- | ------------------------------ |
| 헤더 저장 방식                   | 소문자 정규화 후 저장          | HTTP/1.1: 원본 케이스, HTTP/2: 소문자  |
| `getFirst("Kbank-Header")` | 항상 찾음 (Servlet 스펙 보장) | 저장된 케이스와 일치해야 찾음               |
| 근거                         | Java Servlet 스펙 강제    | HTTP/2 스펙 최적화 (Servlet 스펙 비적용) |

### 그럼 왜 Netty는 Servlet 스펙이랑 다르냐

Netty는 범용 네트워크 프레임워크라서 Servlet 스펙이랑 아예 무관하다는걸 알았다. 아니 별도의 스펙이 있다는것을 처음 알았다..
WebFlux는 Servlet 스펙 없이 독자적인 reactive HTTP 추상화(`ServerHttpRequest`)를 쓰고, 그 구현체가 Reactor Netty인 거임. Servlet 스펙의 case-insensitive 보장은 `HttpServletRequest`에만 적용되고 `ServerHttpRequest`에는 그런 보장이 없다.

즉 Spring이 `ServerHttpRequest.headers.getFirst()`를 case-insensitive로 만들려면 스스로 `LinkedCaseInsensitiveMap`으로 감싸야 하는데, Reactor Netty 연동 경로에서는 그걸 안 하고 Netty native 헤더를 어댑터로만 노출하기 때문에 이 간극이 생기는 거.

```
Servlet 스택:
  Tomcat → HttpServletRequest → Servlet 스펙 강제 → case-insensitive 보장

WebFlux 스택:
  Netty  → ServerHttpRequest → 스펙 없음        → Netty 구현에 위임
```

Jetty처럼 두 스택을 다 지원하는 서버도 있는데, 같은 Jetty라도 Servlet 모드로 쓰면 스펙을 따르지만 WebFlux 서버로 쓰면 Servlet 스펙 밖으로 나가버림. 컨테이너 종류가 아니라 **어떤 스택 위에서 동작하느냐**가 기준인 거임.

---

## 결론 및 우회 방법

Netty 5가 case-insensitive를 제거한 건 버그가 아니라 HTTP/2 스펙을 의도적으로 반영한 것 이다. "HTTP/2에서 대문자 헤더는 존재해서는 안 된다"는 전제 하에 설계된 것이고 그걸 내가 몰랐을 뿐..

문제는 **HTTP/1.1과 HTTP/2를 함께 받는 서버**에서 두 경로가 다르게 동작한다는 거고, Spring이 이걸 HttpHeaders 레벨에서 추상화해주지 못한다는 점이다.

### 가장 안전한 우회: `toSingleValueMap()` + `equalsIgnoreCase` 탐색

```kotlin
val rawHeader = exchange.request.headers
    .toSingleValueMap()                              // Map<String, String> 변환
    .entries
    .firstOrNull { it.key.equals("kbank-header", ignoreCase = true) }
    ?.value
```

`toSingleValueMap()`은 Netty의 native 구조에서 Java `HashMap`으로 복사하는데, 이 시점에 실제 저장된 키 이름이 그대로 노출됨. 여기서 `equalsIgnoreCase`로 탐색하면 프로토콜 버전이랑 무관하게 동작함.

---

## + 찾아보다가 알게 된 것들 by Claude

+ **HTTP/2 pseudo-header 문제도 있음.** HTTP/2는 `:method`, `:scheme`, `:authority`, `:path` 같은 pseudo-header를 따로 두는데, [RFC 7540 §8.1.2.1](https://datatracker.ietf.org/doc/html/rfc7540#section-8.1.2.1)은 이걸 "HTTP header field가 아니다"라고 명시한다. Servlet 스펙은 이 pseudo-header들을 `getHeader()`로 노출하지 말고 `getMethod()`, `getRequestURI()` 같은 전용 API로 매핑해서 감춰야 한다는 계약까지 깔고 있음. 근데 이 매핑도 컨테이너 구현이 알아서 해줘야 하는 거라, [Jetty 10에서 `:authority`를 Host 헤더로 안 매핑해서 `getHeader("Host")`가 null 나오는 회귀 버그](https://github.com/jetty/jetty.project/issues/5304)가 실제로 있었다고 한다(Jetty 9에서는 됐었음). 즉 Servlet 컨테이너라고 이 문제에서 완전히 자유로운 것도 아니고, "스펙이 보장한다"랑 "구현체가 항상 지킨다"는 별개라는 걸 알았음.
+ Netty의 `Http2Headers`는 pseudo-header를 일반 헤더랑 **같은 컬렉션에** 담아서 관리한다고 함. `PseudoHeaderName.isPseudoHeader()`로 구분은 해주지만, 걸러내는 건 호출하는 쪽 책임임. Servlet처럼 "너한테는 안 보여줄게"가 기본값이 아니라 "필요하면 네가 걸러라" 쪽에 가까움 — 이것도 Netty가 Servlet 스펙 세계랑 다른 전제로 만들어졌다는 걸 보여주는 지점.
+ Servlet 스펙은 사실 스레드 모델 자체는 강제하지 않는다고 한다. Tomcat/Jetty가 관례적으로 thread-per-request(요청 하나당 스레드 하나 점유)로 구현했던 거고, Servlet 3.0부터 비동기 처리(`AsyncContext`)가 스펙에 들어온 것도 이 blocking 모델의 한계 때문이었음. 반면 Netty는 처음부터 이벤트 루프 기반이라 이 전제 자체가 없음. "Tomcat=블로킹, Netty=논블로킹"이 스펙 차이가 아니라 구현 선택의 차이였다는 게 좀 의외였음.
+ Servlet 스펙은 세션(`HttpSession`), 쿠키, 멀티파트 파싱, 에러 페이지(`web.xml`의 error-page), 필터/리스너 생명주기까지 컨테이너가 지켜야 할 계약으로 강제한다. Netty에는 이런 개념 자체가 없어서, WebFlux가 `WebSession`, `WebFilter` 같은 걸 전부 자체적으로 새로 만들어야 했음. 헤더 케이스 문제는 그중 극히 일부고, 사실 WebFlux 자체가 "Servlet 스펙이 공짜로 주던 걸 하나하나 다시 구현한 결과물"에 가깝다는 느낌.
