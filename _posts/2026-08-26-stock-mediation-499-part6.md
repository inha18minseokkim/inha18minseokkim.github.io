---
title: CoroutineContext로 traceId 전파하기 — MDC 대신
date: 2026-08-26
tags:
  - Spring
  - WebFlux
  - Reactor
  - Kotlin
  - OpenTelemetry
  - 실무경험
category:
  - 실무경험
---

[이전 글]({% post_url 2026-08-26-stock-mediation-499-part5 %})에서 Proxy 방식(`tracingLogger`)으로 일단 해결했는데, 리뷰받으면서 로그 포맷도 다시 잡고 Proxy도 걷어내고, 결국 traceId 전파 방식 자체를 다르게 다시 짰다.

---

## 로그 포맷부터 다시 잡음

`[traceId=~,spanId=~]` 이렇게 대괄호로 앞에 붙이는 요청을 받음. 근데 5부에서 짠 Proxy는 로그 메시지 자체를 JSON으로 감싸고 있었어서(`{"message": "..."}`) 이 구조로는 "본문 그대로 찍히면서 앞에 메타정보만 붙는" 요구사항을 못 맞춤.

그래서 traceId/spanId 주입 로직을 `LoggerFactory`가 아니라 **logback 패턴 레벨**로 옮김:

```
[traceId=%X{traceId},spanId=%X{spanId}] %logger : %m
```

`LoggerFactory`는 다시 원래대로 얇아지고, Reactive ↔ MDC 간 연동은 `Slf4JEventListener`가 담당하는 구조로 정리됨.

## Proxy 걷어내고 GlobalExceptionHandler에도 확장

로그 포맷 바꾸는 김에 "GlobalExceptionHandler에도 같은 패턴 적용해주고, 기존에 LoggerFactory에 넣었던 Proxy 코드들은 PR 이전으로 원복하고, 공통 로직만 짜서 다시 올려달라"는 요청도 받음. 5부의 `tracingLogger` Proxy 방식이 "동작은 하는데 구조적으로는 마음에 안 든다"는 뜻으로 받아들임 — 로거 자체를 감싸는 것보다, `Span.current()`에서 값 읽어서 MDC 채우는 로직을 별도 헬퍼로 뽑아서 필요한 곳(WebClientManager catch 블록, GlobalExceptionHandler)에서만 쓰는 게 침습이 덜하니까.

그래서 `common/log/TracingContext.kt`에 `Context.restoring { }` 확장 함수를 만들고, `WebClientManager`의 catch 블록들이랑 `GlobalExceptionHandler.handleRunTimeException`에 각각 적용함:

```kotlin
fun <T> Context.restoring(block: () -> T): T {
    val spanContext = Span.fromContext(this).spanContext
    if (spanContext.isValid) {
        MDC.put("traceId", spanContext.traceId)
        MDC.put("spanId", spanContext.spanId)
    }
    return makeCurrent().use { block() }
}
```

호출부마다 메서드 시작 시점에 `Context.current()`를 캡처해두고, catch 블록 안에서 `capturedContext.restoring { log.errorLog(...) }`로 감싸는 식.

### 근데 여기서 두 번째 버그를 하나 더 잡음

`makeCurrent()`가 스코프를 다시 붙이는 이벤트에만 기대면 실패하는 케이스가 있었다. 실측해보니 스레드가 실제로는 안 바뀐 경우(`LoggingWebFilter`의 `doFinally`처럼 요청 처리 내내 같은 스레드) "이미 현재인 Context를 다시 `makeCurrent()`" 하는 건 OTel이 사실상 no-op으로 처리해서 scope-attach 이벤트 자체가 안 뜨고, `Slf4JEventListener`도 안 불려서 MDC가 그대로 안 채워지는 경우가 있었음. 처음 짠 `restoring{}`은 이 이벤트의 부수효과에만 기대고 있었어서 딱 이 케이스에서 조용히 실패했던 것.

고친 버전은 이벤트에 기대지 않고, 주어진 `Context`에서 `Span.fromContext(this)`로 span을 직접 꺼내 MDC에 명시적으로 넣음 - 스레드가 바뀌었든 안 바뀌었든 항상 동작하게. 리뷰 요청 올릴 때 이 버그도 같이 알려드림 - 원래 있던 문제는 아니고 이번에 반복 적용하다가 새로 발견한 거라.

## 근데 이게 정확히 무슨 원리로 되는거임?

나의 순수한 궁금증을 클로드를 통해 문답으로 정리함.

### "OTel이 정보를 가져갈 때 MDC 정보를 가져가는거 아니냐"

내가 처음엔 방향을 반대로 생각하고 있었다. "OTel이 span 만들 때 MDC에 있는 걸 읽어가는 거니까, 읽어가기 직전에 컨텍스트 값으로 MDC를 대체해줘야 하는 거 아니냐"는 식으로 물어봤는데, 반대였음. **OTel Context → MDC**가 실제 흐름이고, Logback은 MDC만 읽지 OTel을 전혀 모른다. `Slf4JEventListener`가 OTel scope 이벤트를 구독하고 있다가 그 순간의 traceId/spanId를 `MDC.put()`으로 밀어넣는 거고, Logback `%X{traceId}`는 그냥 그 시점의 MDC 맵을 읽을 뿐. 방향을 거꾸로 이해하고 있었던 것.

### "그럼 LoggerFactory에서 아예 CoroutineContext의 traceId를 꺼내오면 안 되나?"

logback 패턴이 MDC 기반이니까, 아예 `LoggerFactory` 쪽에서 CoroutineContext 값을 직접 꺼내와서 MDC 대신 쓰면 되지 않냐는 아이디어. 이건 SLF4J `Logger`의 `info()`/`warn()`/`error()`가 전부 일반(non-suspend) 인터페이스 메서드라는 데서 막힘 - `coroutineContext`는 suspend 함수 안이나 CoroutineScope 안에서만 접근 가능한데, `LoggingWebFilter`나 `GlobalExceptionHandler`(당시엔 suspend 아니었음) 같은 non-suspend 경로에서도 로그를 찍어야 해서, 로거 자체를 CoroutineContext 인지하게 만들려면 SLF4J API를 아예 갈아엎어야 함. 커스텀 suspend 전용 로깅 API를 새로 만드는 것도 너무 침습적이라 기각.

### "들어온 요청의 traceparent 헤더를 직접 파싱하면?"

실제로 들어오는 요청엔 `traceparent: 00-{traceId}-{parentSpanId}-01` 헤더가 있으니, 이걸 직접 파싱해서 쓰면 되지 않냐는 아이디어. 괜찮은 방향이긴 한데 몇 가지 짚을 게 있었음 - 헤더의 parent-id는 **호출한 쪽(예: stock-gateway)의 span**이지 우리 서비스 자신의 span이 아니라서 spanId 의미가 다르고, 진짜 OTel span/export를 대체하는 것도 아니고, `traceparent` 헤더가 없는 요청(배치, 내부 스케줄러)엔 fallback이 따로 필요함. 바로 구현하기보단 일단 GitHub 이슈로만 정리해두기로 함(관련 이슈는 뒤에서 다시 나옴).

### "이거 Tempo에 아직도 보이는 499 이랑 관련있는거 아니냐"

4부/5부에서 계속 봐온 그 499랑 이번 MDC 문제가 같은 뿌리 아니냐는 질문. 무관하다고 결론. 지금 붙인 Micrometer 트레이싱 브릿지는 OTLP exporter가 설정 안 돼있어서, span이 로컬 JVM 안에서만 만들어졌다 사라짐 - 어디로도 안 나감. Tempo에 찍히는 499는 여전히 4부에서 다룬 eBPF(Beyla) 관측 노이즈일 확률이 훨씬 높음.

### "OTel의 span 부모-자식 연결도 결국 Span.current() 기반이면, exporter 나중에 붙이면 이것도 같이 끊기는거 아니냐"

로깅 말고 진짜 span 자체의 parent-child 연결도 같은 `Span.current()`/ThreadLocal 메커니즘을 쓰니까, 나중에 exporter를 실제로 붙이면 지금 겪은 것과 똑같은 스레드 hop 문제로 span 트리 자체가 끊길 수 있는 거 아니냐는 지적. 맞는 얘기고, 지금 당장 겪는 문제는 아니지만 exporter를 붙이는 순간 진짜 리스크가 되는 부분. 이것도 나중에 신경 써야 할 것으로 남겨둠.

### "그 두 의존성 정말 로그 찍으려고 넣은거임?"

`micrometer-registry-prometheus`, `micrometer-tracing-bridge-otel` 이 두 개가 결국 로그 찍는 용도로만 쓰인 거 아니냐는 질문. `micrometer-registry-prometheus`는 메트릭 전용이라 로깅이랑 무관하고, `micrometer-tracing-bridge-otel`은 실제로 진짜 OTel SDK를 붙여서 인바운드 `traceparent` 파싱 + 아웃바운드 주입까지 다 하는 물건임 - 지금 로컬 상태에선 exporter가 없어서 눈에 보이는 효과가 로그뿐인 거지, "원래 로깅용"은 아니라고 정정.

### "CoroutineContext propagate 랑 비슷한 맥락인데, 왜 로그 찍을 때 traceId가 안보이는거?"

Reactor의 자체 `Context`(사내 컨텍스트 연동에 쓰는 것)는 Subscriber/subscription 관계를 타고 흐르는 거라 스케줄러 hop이랑 무관하게 안전한데, OTel의 `io.opentelemetry.context.Context`는 근본적으로 **ThreadLocal 기반**이라서 스레드가 바뀔 때마다 명시적으로(혹은 `context-propagation: auto`로 자동) 다시 부착해줘야 함. CoroutineContext는 `Continuation` 객체 자체가 스레드 hop과 무관하게 값을 들고 다니는 구조인데, OTel Context는 그런 보장이 전혀 없다.

## 그러다 나온 아이디어

"내부에서 만들어지는 호출은 헤더에 traceId가 없어서 못 쓴다고 했는데, 게이트웨이에서 받은 요청은 traceId가 있잖아. 그러면 WebFlux/WebFilter에서 요청을 받는 시점에 OTel Context를 까서 그 값을 CoroutineContext에 넣어두면 되는 거 아니냐"

AI를 통해 빠른 검색을 하면서 아이디어들을 모으다 보니 이런 생각이 들었다. `Span.current()`는 WebFilter 진입 시점엔 항상 유효하다는 걸 클로드 시켜서 확인해놨고(`LoggingWebFilter`의 `doFinally`도 마찬가지), 이 패턴은 사내 컨텍스트 연동 방식에서 이미 검증된 패턴이었다. OTel이 "정확한 값을 어디서 읽어야 하는지"를 알려주고, CoroutineContext가 "그 값을 어디까지 들고 다닐지"를 책임지는 조합.

```kotlin
// WebFilter 진입 시점에 딱 한 번
val spanContext = Span.current().spanContext
chain.filter(exchange).contextWrite { ctx ->
    if (spanContext.isValid) ctx.put(TraceContextKey, TraceInfo(spanContext.traceId, spanContext.spanId))
    else ctx
}

// 그 뒤로는 어느 suspend 함수에서든, 캡처/복원 없이 바로
suspend fun currentTraceInfo(): TraceInfo? =
    coroutineContext[TraceContextKey]?.traceInfo
        ?: coroutineContext[ReactorContext]?.context?.getOrEmpty<TraceInfo>(TraceContextKey)?.orElse(null)
```

## 실제로 짜서 검증까지 함

이 아이디어를 master에서 새 브랜치 파서 그대로 구현함. `WebClientManager`/`CoroutineUtil`의 catch 블록에서 `Context.current()` 캡처 + `restoring{}` 하던 걸 전부 `withTraceMdc { currentTraceInfo() }` 호출로 바꿨고, `GlobalExceptionHandler.handleRunTimeException`도 `suspend fun`으로 바꿔서 같은 걸 쓰게 함(Spring WebFlux가 `@ExceptionHandler` suspend fun도 컨트롤러 메서드랑 같은 경로로 지원한다는 것도 이번에 확인함). `async{}`로 넘어갈 때 미리 캡처해두는 코드가 통째로 없어짐 - CoroutineContext는 자식 코루틴한테 자동으로 상속되니까 그럴 필요가 아예 없어짐.

로컬에서 `bootRun`으로 직접 기동해서 검증함(다운스트림 서비스가 로컬엔 없어서 connection-refused로 실제 에러 경로를 태우는 식으로). ~~그러다 백그라운드로 띄운 프로세스를 못 찾아서 `taskkill /F /IM java.exe`로 눈에 보이는 java 프로세스를 다 죽여버렸는데, 다른 서비스 gradle daemon들까지 같이 죽은 건 안 비밀..~~ 아무튼 결과는:

```
traceId=281a7c04cc196189591dd34eca4842d0,spanId=dc89c6a7ddf3c9b3  ← ACCESS_LOG (LoggingWebFilter)
traceId=281a7c04cc196189591dd34eca4842d0,spanId=dc89c6a7ddf3c9b3  ← GlobalExceptionHandler
```

같은 요청 안에서 서로 완전히 다른 두 경로(하나는 OTel Context 기반, 하나는 CoroutineContext 기반)로 읽은 traceId가 정확히 일치함. 그리고 가장 확인하고 싶었던 케이스 - `WebClientManager.getList`가 `DefaultDispatcher-worker-3`(코루틴 워커 스레드, 요청을 처음 받은 `reactor-http-nio-*`가 아님)로 넘어간 뒤에도 traceId/spanId가 그대로 유지됨. 이게 바로 5부에서부터 계속 쫓아온 "스레드 넘어가면 사라지는" 문제 그 자체라서 제일 중요한 검증 포인트였음.

## 정리

- 로그 포맷은 `[traceId=,spanId=]` + `kbankSeverity`/`kbankLogType`을 logback 패턴 레벨로 옮겼고, AccessLog만 JSON 유지
- Proxy 기반 `tracingLogger`는 원복하고, `Context.restoring{}`으로 옮기는 과정에서 `makeCurrent()` no-op 버그를 하나 더 잡음
- OTel Context → MDC라는 방향, CoroutineContext(Continuation 자체가 들고 다님) vs OTel Context(ThreadLocal, 매 hop마다 재부착 필요)라는 구조 차이를 짚고 나니 답이 나왔음
- 결론: 요청 진입 시점에 `Span.current()`를 딱 한 번 읽어서 CoroutineContext로 실어두면, 그 뒤로는 캡처/복원 없이 어디서든 안전하게 꺼내 씀 - 사내 컨텍스트 연동 방식에서 이미 쓰던 패턴 그대로

같은 문제를 두고 "MDC를 억지로 채우는 법"을 찾다가 "애초에 MDC 말고 더 안전한 곳에 값을 실어두면 되지 않나"로 생각이 바뀐 게 이번 편의 핵심이었다. 처음부터 이렇게 짰으면 5부의 Proxy 삽질도 없었을 텐데.. 근데 그 삽질 없이 바로 이 결론에 도달했을 것 같지도 않고.

## 그리고 며칠 뒤 — PR #5는 닫고 #7을 남기기로

대충 구현해놓고 다른 일 하다가, 4~6부에서 다룬 OTel Context capture-restore 방식(PR #5)이랑 이번 편에서 새로 짠 CoroutineContext 방식(PR #7)을 나란히 놓고 뭐가 더 낫냐고 내가 고민했다. 장단점 비교.

**PR #5 (OTel Context capture-restore)**
- 장점: Micrometer/OTel 표준 스택이라, 나중에 진짜 분산 트레이싱 백엔드(Zipkin/Tempo 등)에 span을 export하거나 span 트리·downstream latency 자동 계측이 필요해지면 그 투자를 그대로 이어갈 수 있다.
- 단점: 구현하다보니 안 되는 곳이 많았다 — Reactor 시그널 사이 구간에서 MDC가 비는 문제(5부), `.timeout()` 재시도로 스케줄러가 `Schedulers.parallel()`로 넘어갈 때 `context-propagation:auto` 적용 대상에서 아예 빠지는 문제(6부 초반), `makeCurrent()`가 스코프 재부착 이벤트에 기대다가 스레드가 안 바뀐 경우엔 no-op으로 조용히 실패하는 문제(6부 후반). 커밋 7개 중 절반 가까이가 "안 찍히던 문제 수정"이었다 — 언젠가 나 포함 누군가가 스코프 밖의 스레드나 태스크에 작업을 할당하면 문제가 생길 것이다.

**PR #7 (CoroutineContext)**
- 장점: suspend 함수 체인이라 컴파일러가 CoroutineContext 전달을 강제한다 — "전파가 빠지는 경로" 자체가 존재할 수 없다.
- 단점: suspend 함수로 다 바꿔야 하다보니 영향도가 있다 — `WebClientManager`의 `*WithoutKbankContext` 3종, `EtfService`/`ListedStockService`/`OverseasStockService`의 `*ForJob()` 메서드, `ProductJob`/`PriceJob`까지 총 9개 파일을 건드려야 했고, 순수 Reactor 체인(`Flux.interval().flatMap{}`)과의 경계에서 `mono{}`/`awaitSingle()`로 다리를 놓다 보니 `ProductJob`/`PriceJob`의 실행 스케줄러가 `boundedElastic`에서 `Dispatchers.Default`로 바뀌는 부수효과도 생겼다(지금은 순수 non-blocking WebClient 호출뿐이라 무해하지만, 나중에 블로킹 코드가 들어가면 다시 봐야 함). 그냥 suspend로 다 바꿨다. 아 이래서 사람들이 suspend 쓰면 다 suspend 써야 하는구나를 뼈저리게 느꼈다.
- 단점: 확장성이 없다. 지금 이건 순수 로그를 찍기 위한 목적으로 코루틴 컨텍스트에 박아넣는 건데, 나중에 어떤 개발자(미래 다른 시간속의 나 포함)가 "어 여기는 MDC 전파 되네?" 하고 MDC 기반으로 되어있는 어떤 기능을 이식하는 순간 개판오분전이 될 것 같아서 좀 우려스럽다.

지금 이 서비스가 필요한 건 "요청 하나에 대해 로그들이 같은 traceId로 묶이는 것"이지 진짜 분산 트레이싱 백엔드 연동은 아니라서, 정확성이 라이브러리의 자동전파 가정이 아니라 언어 차원에서 보장되는 PR #7 쪽에 손을 들어줬다. PR #5는 코멘트로 근거를 남기고 닫고, PR #7을 `master`에 머지했다.

이 CoroutineContext 방식이 다음 편(stock-gateway)에서는 아예 못 쓰는 상황을 만나는데, 그 얘기는 [다음 글]({% post_url 2026-08-28-stock-mediation-499-part7 %})에서.
