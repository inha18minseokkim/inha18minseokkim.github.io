---
title: Spring Cloud Gateway에서 traceId 전파 — ServerWebExchange attribute
date: 2026-08-28
tags:
  - Spring
  - WebFlux
  - Reactor
  - Spring Cloud Gateway
  - Kotlin
  - OpenTelemetry
  - 실무경험
category:
  - 실무경험
---

[이전 글]({% post_url 2026-08-26-stock-mediation-499-part6 %})에서 stock-mediation은 CoroutineContext로 해결했는데, 같은 로그 포맷을 stock-gateway에도 적용해달라는 요청이 왔다. gateway는 코루틴을 아예 안 쓰는 순수 Reactor(WebFlux + Spring Cloud Gateway) 앱이라 같은 방식을 그대로 쓸 수가 없었다. 대안을 짜고 실제로 붙이면서 버그 세 개를 잡은 이야기.

---

## CoroutineContext를 못 쓰는 이유

6부의 결론은 "요청 진입 시점에 `Span.current()`를 한 번 읽어서 CoroutineContext로 실어두면, 그 뒤로는 캡처/복원 없이 어디서든 안전하게 꺼내 쓴다"였다. 이게 되는 이유는 `suspend fun` 체인을 컴파일러가 강제하기 때문이다 — `CoroutineContext`는 `Continuation` 객체 자체가 들고 다니는 구조라, 스레드가 몇 번을 넘어가든 재부착 없이 안전하다.

이건 코틀린 기반이 아니라 reactor에서 제공하는 context를 써야 한다. 심지어 이건 내가 3년 전에 짠 코드야 ㅋㅋ. 그리고 이 코드가 팀내 여러 게이트웨이의 레퍼런스라서 나 혼자 갑자기 코틀린 코루틴으로 감 ㅅㄱ 이러고 갈 수도 없는 상황이다. `WebFilter.filter()`도, `GatewayFilter.filter()`도 전부 `Mono<Void>`를 반환하는 순수 Reactor 인터페이스 메서드다. CoroutineContext는 코루틴 빌더(`launch`, `async`, suspend 함수 체인) 없이는 애초에 존재하지 않는 개념이라, "여기에 값을 실어두자"고 할 대상 자체가 없다.

그럼 mediation이 5~6부에서 겪었던 것처럼 Reactor Context 자동전파(`spring.reactor.context-propagation: auto`)에 기대는 방식으로 가면 되지 않냐 싶었는데, 이것도 안 맞았다. gateway는 mediation보다 스케줄러가 바뀌는 지점(hop)이 오히려 더 많다:

- `LoggingWebFilter`의 요청/응답 바디 캡처가 `.publishOn(Schedulers.boundedElastic())`을 씀
- 라우트에 `.modifyRequestBody`/`.modifyResponseBody`가 각자 독립적인 디코딩 경로를 탐
- (이 시점엔 아직 있었던) GET premature-close 재시도용 `.retry()`

mediation의 PR #5가 "자동 전파는 새 hop을 만날 때마다 실측으로 빈 값을 찾아 패치해야 한다"는 걸 이미 세 번이나 증명했는데(6부), gateway에서 그 방식을 또 쓰면 같은 클래스의 버그를 더 자주 겪을 게 뻔했다.

## 그래서 택한 방식: ServerWebExchange attribute

gateway 코드를 실제로 보면, 로그를 남기는 지점이 전부 `ServerWebExchange`를 이미 파라미터로 들고 있었다 — `LoggingWebFilter.filter(exchange, chain)`, `LogService.saveTransactionLog(body, exchange)`, `ApiGatewayConfig`의 `getModifiedRequestBody`/`getModifiedResponseBody(exchange, ...)`. 그래서 traceId/spanId를 CoroutineContext 대신 `exchange`의 attribute에 담아두고, 로그를 남기는 모든 지점이 그 `exchange`에서 명시적으로 꺼내 쓰는 방식으로 갔다.

```kotlin
@Component
class TraceContextFilter : WebFilter {
    override fun filter(exchange: ServerWebExchange, chain: WebFilterChain): Mono<Void> {
        val spanContext = Span.current().spanContext
        if (spanContext.isValid) {
            exchange.attributes[TRACE_INFO_ATTR] = TraceInfo(spanContext.traceId, spanContext.spanId)
        }
        return chain.filter(exchange)
    }
}
```

## CoroutineContext vs exchange attribute, 뭐가 다른가

클로드가 찾아준 구분인데, 둘 다 "스레드가 바뀌어도 값이 안 깨진다"는 결과는 같은데, 그 보장이 나오는 방식이 완전히 다르다.

**CoroutineContext**는 값이 `Continuation` 객체를 타고 흐른다. suspend 함수를 호출하는 순간 컴파일러가 CPS(continuation-passing style) 변환을 해주기 때문에, 어느 스레드/디스패처에서 재개되든 그 값은 항상 같이 붙어 있다. "이 함수가 CoroutineContext를 볼 수 있느냐"는 컴파일 타임에 `suspend` 키워드로 강제된다 — 실수로 빠뜨리면 컴파일이 안 된다.

**exchange attribute**는 값이 `ServerWebExchange` 객체 하나의 `Map<String, Object>`에 들어있고, 그 객체 참조가 WebFilter/GatewayFilter 체인 전체를 프레임워크가 보장하는 방식으로 넘어간다. 스레드가 몇 번을 넘어가든 상관없는 이유가 애초에 스레드 얘기가 아니기 때문이다 — "이 코드가 `exchange`를 들고 있느냐"의 문제일 뿐이고, WebFlux/SCG 필터 체인에 참여하는 코드는 설계상 전부 `exchange`를 들고 있다. 대신 이건 컴파일러가 강제해주는 게 아니라, "로그를 남기려는 지점이 실제로 `exchange` 파라미터를 받고 있느냐"를 사람이 챙겨야 한다 — 이번에 발견한 버그들 중 하나가 정확히 이 지점(뒤에서 다룸)에서 났다.

정리하면: CoroutineContext는 "언어가 보장하는 전파", exchange attribute는 "프레임워크가 보장하는 참조 공유". 코루틴이 없는 앱에서는 후자가 유일한 선택지였는데, 스레드로컬·코루틴 컨텍스트 같은 기능이 없어서 리액티브 라이브러리에서 제공하는 프레임워크 기능을 활용해야 했던 거고, 결과적으로 mediation이 5~6부 내내 겪은 자동 전파가 안 되는 클래스의 버그 자체가 발생할 수 없는 설계이기도 했다.

## 실제로 붙이면서 잡은 버그 세 개

설계까지는 깔끔했는데, 실제로 붙여서 테스트해보니 세 가지가 순서대로 터졌다.

### 1. traceId/spanId가 항상 비어있었음

가장 먼저 나온 리포트는 "gateway 로그엔 traceId/spanId가 아예 안 찍히는데 mediation은 잘 찍힌다"였다. gateway의 `application-stg.yml`에 `spring.reactor.context-propagation: auto` 설정이 빠져 있었다(mediation엔 있었음). tracing 필터가 만든 span이 WebFilter 체인 안의 스레드/비동기 경계를 못 넘어가면 그다음 필터에서 `Span.current()`가 비어버리기 때문. mediation과 동일하게 추가해서 해결.

### 2. gateway의 traceId가 mediation으로 안 이어짐

두 가지를 고치고 나니 gateway 자체 로그는 정상이었는데, gateway가 stock-mediation으로 보낸 요청의 traceId가 mediation 쪽에서는 완전히 다른 값으로 찍혔다. mediation의 ACCESS 로그를 보면 요청 헤더 안에 `traceparent`가 **두 개** 들어있었다 — 하나는 gateway 자신이 로그에 찍는 값과 일치했고, 다른 하나는 mediation이 새로 만든, gateway와는 무관한 값이었다.

원인은 POST 요청을 받아 새로운 RESTful 요청(GET, POST, PUT, DELETE, PATCH)으로 매핑하는 필터였다.

```java
ServerHttpRequest newServerHttpRequest = exchange.getRequest().mutate()
        .path(...)
        .method(...)
        .headers(h -> h.addAll(this.getModifiedHeaders(exchange, headerJson)))
        .build();
```

```java
public HttpHeaders getModifiedHeaders(ServerWebExchange exchange, JsonNode kBankHeaderJson) {
    HttpHeaders modifiedHeaders = new HttpHeaders();
    modifiedHeaders.putAll(exchange.getRequest().getHeaders());  // 원본 헤더 전체 복사
    modifiedHeaders.set("Kbank-Header", kBankHeaderJson.toString());
    return modifiedHeaders;
}
```

`.mutate().headers(h -> ...)`가 넘겨주는 `h`는 이미 원본 요청 헤더로 초기화된 상태로 들어온다. 그런데 `getModifiedHeaders()`도 원본 헤더를 통째로 복사한 사본을 새로 만들어 반환하니, `h.addAll(modifiedHeaders)`는 "이미 원본 헤더가 들어있는 h" 위에 "원본 헤더를 복사한 사본"을 한 번 더 얹는 꼴이었다. 이 필터를 거치는 모든 요청에서 헤더가 전부 두 벌씩 찍히고 있었던 거다.

대부분의 헤더는 값이 중복돼도 어차피 서버가 대충 첫 값만 쓰거나 넘어가서 티가 안 났는데, W3C Trace Context 스펙은 "한 요청에 `traceparent`가 두 개 이상 있으면 파싱하지 말고 아예 없는 것으로 취급"하도록 정해져 있다. gateway가 SCG 자체 계측으로 붙인 `traceparent`가 이 필터를 거치며 중복됐고, mediation의 tracing 라이브러리가 스펙대로 그 중복을 통째로 무시하고 새 trace를 시작해버린 것이었다.

처음엔 `h.clear()`로 싹 비운 뒤 다시 채우는 식으로 고쳤는데, 실사용 중 이번엔 `415 Unsupported Media Type` 에러가 났다. `Content-Type`처럼 이 필터가 건드릴 필요 없는 헤더까지 같이 날아간 뒤 `addAll`만으로는 온전히 복구되지 않는 것으로 보였다(`ServerHttpRequest.Builder` 내부에서 `Content-Type`을 별도 필드로 캐싱해두는 구현일 가능성이 있는데, 정확한 내부 동작까지는 추적하지 않았다). 그래서 전부 비우는 대신, `modifiedHeaders`에 실제로 들어있는 키만 골라 지운 뒤 다시 채우는 방식으로 바꿨다:

```java
.headers(h -> {
    HttpHeaders modifiedHeaders = this.getModifiedHeaders(exchange, headerJson);
    modifiedHeaders.keySet().forEach(h::remove);
    h.addAll(modifiedHeaders);
})
```

손대지 않는 헤더는 원본 그대로 남고, 중복될 헤더만 정확히 한 벌로 덮어써지는 방식.

## 정리

- gateway는 CoroutineContext가 아예 없는 앱이라 mediation의 방식을 그대로 못 가져왔고, Reactor Context 자동전파도 hop이 많아서 안 맞았다 — 그래서 `ServerWebExchange` attribute로 값을 옮기는 방식을 택함
- CoroutineContext는 언어(컴파일러)가 전파를 보장하고, exchange attribute는 프레임워크가 보장한다 — 둘 다 "스레드 hop에 안전"하다는 결론은 같음
- 실제로 붙이면서 버그 세 개를 잡음: `context-propagation:auto` 누락, 헤더 중복으로 W3C `traceparent` 스펙을 위반해 mediation이 새 trace를 시작해버리던 문제(+ 그 수정이 415를 유발해서 다시 고친 것까지)

BFF(mediation)서버는 코틀린 코루틴을 활용해서 MDC 로그를 찍었고 SCG는 reactor 스택이므로 spring cloud gateway 프레임워크에서 제공해주는 기능으로 로그를 찍었다.

스레드로컬 기반 MDC를 coroutine이나 Reactor context로 전파시키려니 쉽지 않지만 행내에서 로깅이나 관제 표준이 MDC 기반으로 되어있어 불가피하게 이런 행위를 하였다. 하지만 이 로직들은 단순히 Logback을 concurrent 스택에 호환시킬 목적으로 만든 것이므로 확장성은 없다고 볼 수 있지만, 로그 목적 외에 MDC를 해당 프로젝트에서 쓸 이유가 없기 때문에 일단 이쯤에서 그만하기로 하였다.
