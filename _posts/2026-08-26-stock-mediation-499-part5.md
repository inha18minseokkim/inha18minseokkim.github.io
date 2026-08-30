---
title: stock-mediation 499 트레이싱 일대기 (5부) — OTel 에이전트 걷어내다가 겪은 MDC 삽질
date: 2026-08-26
tags:
  - Spring
  - WebFlux
  - Reactor
  - Kotlin
  - Kubernetes
  - 실무경험
category:
  - 실무경험
---

[1부]({% post_url 2026-08-17-stock-mediation-499-part1 %}), [2부]({% post_url 2026-08-17-stock-mediation-499-part2 %}), [3부]({% post_url 2026-08-17-stock-mediation-499-part3 %}), [4부]({% post_url 2026-08-20-stock-mediation-499-part4 %})에서 499 원인 규명이랑 eBPF 노이즈까지 정리했는데, 4부 Q3에서 "eBPF(opentelemetry-ebpf-instrumentation) 대신 바이트코드 계측(java agent) 썼으면 이 노이즈 자체가 안 생겼을 것"이라고 적었었다. 근데 실제로는 반대 방향으로 가고 있었음 — `stock-mediation`에 이미 붙어있던 OTel java agent를 걷어내고 Micrometer 기반으로 갈아타는 작업이 진행 중이었고, 그 과정에서 traceId/spanId가 로그에 안 찍히는 문제로 한참 삽질했다. 이번 편은 그 얘기.

---

## 시작은 동료 질문 하나였다

`micrometer-registry-prometheus`, `micrometer-tracing-bridge-otel` 이 두 개 넣고 `spring.reactor.context-propagation: auto` 설정하면 되냐는 질문에서 출발했음. 그리고 로그에 traceId/spanId를 key=value로 남기고 싶다길래 적용해주기로 함.

먼저 연습 삼아 별도 레포에서 검증부터 했는데 여기서부터 이미 삽질이 시작됐다.

### 로그에 아무것도 안 찍힘 → 근데 문법 오타였다

MDC 찍는 패턴을 `%X{traceId:-} spanId:%X{spanId:-}` 이런 식으로 썼는데 (Logback에서 흔히 보던 문법이라 별 생각 없이 그대로 씀) 아무리 해도 traceId가 안 찍혔다. 그래서 `Slf4JEventListener`, OTel `ContextStorage` 래퍼, coroutine 스레드 홉 이런 것들을 한참 팠는데 전부 정상이었고, 알고보니 이 레포는 Log4j2 썼는데 `%X{key:-default}` 문법은 **Logback 전용**이고 Log4j2는 지원을 안 함 — `"traceId:-"`를 통째로 (존재하지도 않는) 리터럴 키 이름으로 취급해서 항상 빈 값이 찍히는 거였음. `%X{traceId}`로 고치니 바로 됨. 삽질의 8할이 오타 하나 때문이었다..

## 엉뚱한 레포에 PR 올림

검증 끝나고 실제 `stock-mediation`에 적용해서 PR을 올렸는데 — ~~그 실제 레포가 어딘지도 제대로 확인 안 하고~~ 독립적으로 떠도는 다른 레포에다 올려버림. "이 프로젝트의 remote는 stock-mirrored 하위 stock-mediation 폴더"라는 지적을 받고서야 알았다. 확인해보니 실제로 작업하던 폴더(`ai-stock-poc/stock`)에 이미 `stock-mirrored`를 가리키는 remote가 잡혀있었는데 그걸 못 보고 딴 데다 clone 떠서 작업한 거. 엉뚱한 PR은 닫고 제대로 된 위치에서 다시 시작함.

## 진짜 레포는 상황이 완전히 달랐다

제대로 된 `stock-mediation`을 열어보니 검증했던 연습 레포랑 상황이 많이 달랐음:

- Logback이 아니라 **이미 OTel java agent가 붙어있었음** (`Dockerfile`에 `-javaagent:.../opentelemetry-javaagent.jar`)
- `opentelemetry-logback-appender-1.0`, `opentelemetry-logback-mdc-1.0` 의존성이 있는데 코드 어디서도 참조를 안 함 — 죽은 의존성

이 상태에서 Micrometer tracing bridge를 그냥 추가하면 에이전트가 이미 잡아놓은 `GlobalOpenTelemetry`랑 충돌할 수 있어서, 에이전트 여전히 붙어있는 거 맞냐고 확인부터 물어봤다. 돌아온 답은 "이 작업 자체가 에이전트 걷어내는 과정"이라는 것 — 그러니까 순서가 반대였던 거고, 나만 몰랐던 거였다. 그래서 죽어있던 두 의존성도 같이 정리(제거)하고 Micrometer 쪽으로 마저 진행함.

버전도 하나 걸림 — Boot 3.3.1 기본 BOM이 관리하는 micrometer/micrometer-tracing/opentelemetry 버전이 내가 넣으려는 버전보다 낮아서, 명시적으로 넣은 dependency는 원하는 버전으로 뜨는데 걔들이 끌고오는 전이 의존성은 구버전으로 내려가는 스큐가 생겼다. `ext`에 BOM 프로퍼티(`micrometer.version`, `micrometer-tracing.version`, `opentelemetry.version` 등)를 같이 올려서 해결.

## PR 올리고 나서 리포트받은 것

여기까지 하고 PR 올렸는데, 실제로 써보니 **traceId=/spanId=가 그냥 빈 값**으로 찍힌다는 리포트를 받음. 로컬에서 재현해보려는데 이것도 순탄치 않았다.

`stock-mediation`은 기동될 때 `@PostConstruct`에서 다운스트림 서비스들(가격/상품 정보)을 받아올 때까지 **busy-wait로 무한 대기**하는 코드가 있었음:

```kotlin
@PostConstruct
private fun init() {
    priceJob.init()
    productJob.init()
    while (!hasPrice || !hasProduct) {
        // 다운스트림 응답 받을 때까지 계속 돎
        Thread.sleep(100L)
    }
}
```

로컬엔 저 다운스트림들이 없으니 서버가 영원히 안 뜬다. 이거 원래 있던 코드고 내가 건드린 것도 아닌데, 로컬 검증을 위해 잠깐 빼고 (당연히 커밋은 안 함) 실제 요청을 날려봤다.

## Span.current()는 맞는데 MDC는 비어있음

```
DIAGNOSTIC span=ImmutableSpanContext{traceId=4c7843b28c44457d38eb3e0e90c491a3, ...}
DIAGNOSTIC MDC.get(traceId)=null
```

`Span.current()`(OTel 원시 API)는 정확한 값을 주는데 `MDC.get("traceId")`는 `null`. 리포트 그대로 재현됨. 여기서부터 가설을 하나씩 세우고 지웠다:

| 가설 | 확인 결과 |
|---|---|
| java agent가 아직 붙어있어서 GlobalOpenTelemetry 충돌 | 에이전트 없다고 확인받음 → 기각 |
| 백그라운드 job(가격/상품 폴링)들이 동시에 span 만들면서 서로 간섭 | job 완전히 꺼도 동일하게 재현 → 기각 |
| ContextStorage wrapper가 아예 설치 안 됨 | `ContextStorage.get()` 찍어보니 `EventPublishingContextWrapper$1` — 정상 설치돼있음 → 기각 |
| MDC 자체가 고장(다른 바인딩 잡혔거나) | 직접 `MDC.put("test", "123")` 하고 바로 `get` 해보니 정상 왕복됨 → 기각 |

전부 아니었다. 그럼 대체 뭐지..

## Slf4JEventListener에 TRACE 로그를 켜봤다

`micrometer-tracing-bridge-otel`이 MDC를 채워주는 실제 담당은 `Slf4JEventListener`인데, 여기에 TRACE 레벨 로그를 켜서 뭘 하는지 직접 봄:

```
Got scope changed event [ScopeAttached{... SdkSpan{traceId=2386c3b2..., spanId=57b98c35...}}]
Got scope changed event [ScopeAttached{context: [span: null] [baggage: null]}]
Got scope changed event [ScopeAttached{... SdkSpan{traceId=2386c3b2..., ...}}]
traceId=2386c3b2... spanId=57b98c35... Got scope closed event [...]
Got scope restored event [ScopeRestored{context: [span: null] [baggage: null]}]
Got scope closed event [...]
Got scope restored event [ScopeRestored{... SdkSpan{traceId=2386c3b2..., ...}}]
```

이거 보고 이해했다. **scope가 열렸다 닫혔다 하는 게 Reactor 시그널(onNext/onComplete 등) 하나 처리하는 밀리초 단위로 아주 짧게** 일어난다. MDC.put()은 scope attach 될 때, MDC.remove()는 close/restore 사이에 일어나는데, 이 구간이 너무 좁아서 **그 사이에 실행되는 일반 애플리케이션 코드(우리가 로그 찍는 지점 대부분)는 scope가 닫혀서 MDC가 비어있는 타이밍에 걸린다.** 표로 보면:

```
[scope attach → MDC.put(traceId=X)] → (아주 짧은 처리) → [scope close → MDC.remove()]
                                                              ↑
                                        우리 로그 대부분은 이 바깥에서 실행됨
```

`Span.current()`는 이 scope 개폐 타이밍이랑 무관하게 요청 처리 내내 정확한 걸 주는데, MDC는 딱 그 짧은 창 안에서만 정확하다는 게 핵심. `context-propagation: auto`는 스레드 넘어갈 때 "지금 있는 ThreadLocal 값"을 옮겨주는 역할만 하지, 옮길 시점에 MDC가 이미 비어있으면 빈 걸 그대로 옮기니까 이 문제엔 무력함.

## 해결: 로그 찍는 순간마다 직접 물어보기

MDC가 채워져 있길 기다리는 대신, 공용 `logger()` 헬퍼가 반환하는 `Logger`를 Proxy로 감싸서 **로그를 실제로 남기는 그 순간마다 `Span.current()`를 직접 읽어 MDC를 채우고 위임**하도록 바꿈:

```kotlin
inline fun <reified T> T.logger(): Logger = tracingLogger(LoggerFactory.getLogger(T::class.java))

fun tracingLogger(delegate: Logger): Logger {
    return Proxy.newProxyInstance(
        Logger::class.java.classLoader,
        arrayOf(Logger::class.java)
    ) { _, method, args ->
        val spanContext = Span.current().spanContext
        if (spanContext.isValid) {
            MDC.put("traceId", spanContext.traceId)
            MDC.put("spanId", spanContext.spanId)
        } else {
            MDC.remove("traceId")
            MDC.remove("spanId")
        }
        try {
            if (args == null) method.invoke(delegate) else method.invoke(delegate, *args)
        } catch (e: InvocationTargetException) {
            throw e.targetException
        }
    } as Logger
}
```

`logger()`가 앱 전체에서 이미 쓰이던 공용 헬퍼라 이거 하나만 고치면 개별 로그 호출부는 손 안 대도 됨. 다시 검증해보니:

```
traceId=afbcc821ad0d479c85b3ffc1b7de1904 spanId=e6516a9945f0074f ... [ACCESS] {...}
```

실제 요청, 실제 다운스트림 호출 있는 컨트롤러 둘 다 정상 확인.

## 정리

- CGLIB 생성자 문제, Log4j2/Logback `%X{key:-default}` 문법 헷갈림 — 둘 다 검증 단계에서 시간 잡아먹은 오타/설정 실수
- 엉뚱한 레포에 PR 올린 것도 remote 확인 안 한 내 실수
- 진짜 문제는 `Slf4JEventListener`가 MDC를 채워주긴 하는데, 그 유효 구간이 Reactor 시그널 하나 처리하는 만큼만 아주 짧다는 것 — `Span.current()`는 항상 맞고 MDC만 좁은 창에서만 맞는다는 게 핵심
- `context-propagation: auto`는 "있는 값을 스레드 넘어 옮겨주는" 역할이지 "값을 채워주는" 역할이 아니라서, 이 문제 자체는 못 고쳐줌
- 결국 MDC가 채워지길 기다리지 않고 로그 시점마다 `Span.current()`를 직접 읽는 쪽으로 우회

에이전트 없이 순수 Micrometer로 트레이싱 계측할 때 이런 "MDC는 signal 단위로만 잠깐 채워진다"는 게 생각보다 덜 알려진 함정인 것 같다. 검색해봐도 딱 이 케이스로 정리된 글을 못 찾았는데.. 다음에 비슷한 거 또 겪으면 바로 `Span.current()` 직접 읽는 쪽으로 갈 듯.
