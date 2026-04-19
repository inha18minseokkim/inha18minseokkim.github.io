---
title: Reactive에서 Virtual Thread로 전환할 때 주의할 점
date: 2026-04-19
tags:
  - Java
  - Spring
  - Kotlin
  - Reactive
category:
  - 기술
---

## Reactive 방식을 Virtual Thread에 그대로 적용해도 될까?

Java 21의 **Virtual Thread(VT)**가 나오면서, 복잡한 **Reactive(WebFlux/R2DBC)** 스택을 어떻게 전환할지 고민이 많았음.

결론부터 말하면, **기술적으로 가능은 한데 설계를 그대로 가져다 쓰면 위험함**. 우리 프로젝트 특성상 VT + JDBC 조합이 훨씬 유리하다. 단순히 런타임만 바꾸는 게 아니라, 자원 관리 방식과 컨텍스트 전파 메커니즘을 완전히 새로 고쳐야 함.

---

## 무분별한 병렬 호출(awaitAll)과 자원 고갈

Reactive 환경(R2DBC)에서는 여러 비동기 작업을 묶어 병렬로 처리할 때 보통 이런 형태로 작성함.

```kotlin
// 기존 R2DBC + Coroutine 방식의 수도코드
suspend fun getGameData(userId: String) = coroutineScope {
    val profile = async { userRepository.findById(userId) }
    val assets = async { assetRepository.findAllByUserId(userId) }
    val rewards = async { rewardRepository.findAllByUserId(userId) }

    // 비동기 작업들을 병렬로 실행하고 결과를 합침
    awaitAll(profile, assets, rewards)
}
```

이걸 Virtual Thread 환경에서 JDBC로 전환하며 그대로 따라 하면?

- **R2DBC의 경우:** 내부에 **Backpressure(역압)** 메커니즘이 있어서 DB가 감당할 수 있는 수준으로 요청을 조절하거나 이벤트 루프가 효율적으로 스케줄링함
- **Virtual Thread의 경우:** VT는 생성 비용이 거의 제로에 가까움. 수천 개의 요청이 들어왔을 때 각 요청마다 위처럼 3개씩 병렬 쿼리를 던지면, 순간적으로 **DB 커넥션 풀(HikariCP)에 융단폭격**을 가하게 됨. 결국 커넥션을 얻지 못한 쓰레드들이 줄을 서고, 시스템 전체가 타임아웃으로 뻗어버리는 **Connection Pool Starvation** 현상이 생김

---

## Reactive는 언제 쓰는게 좋을까?

리액티브 생태계가 강점을 발휘하는 상황:

- **이벤트 기반 스트리밍:** Flux를 통해 끊임없이 유입되는 이벤트를 리스닝하고 처리해야 할 때
- **복잡한 비동기 파이프라인:** 다수의 외부 API 콜이 복잡하게 얽혀 있는 경우

근데 **단건 호출 위주의 금융 서비스**인 우리 프로젝트에서 R2DBC는 오버스펙임. **단순 단건 요청에 대한 빠른 응답과 높은 처리량**이 핵심인데, 이런 경우 러닝커브가 압도적으로 낮은 VT로 동기식 코드를 유지하는 게 개발 생산성 면에서 훨씬 나음.

---

## 헥사고날 아키텍처에서 JPA 대신 JDBC를 선택한 이유

우리 아키텍처는 **의존성 방향이 도메인 중심**으로 흐르는 헥사고날 구조임.

- **의존성 방향:** `Infrastructure → Domain ← Application`
- **영속성 객체 분리:** 도메인 모델은 순수 Kotlin 클래스로 정의하고, 영속성 계층(Infrastructure)은 이를 모르도록 설계

이 구조에서 JPA를 걷어내고 **Spring Data JDBC**를 선택한 이유가 있음. 헥사고날 아키텍처는 계층 간 의존성을 엄격히 분리하니까, **영속성 컨텍스트를 유지(Dirty Checking 등)할 필요가 없음**. 명시적인 `save()` 호출로 상태를 변경하는 JDBC 방식이 헥사고날의 순수성을 지키기에 더 가볍고 직관적임.

---

## ThreadLocal의 한계와 ScopedValue

기존에 공통 헤더나 인증 정보를 전파할 때 `ThreadLocal`을 썼는데, 수만 개의 VT가 뜨는 환경에서 `ThreadLocal`은 성능과 안정성 면에서 문제가 있음.

### ThreadLocal의 문제점

- 각 VT마다 독립적인 맵을 유지해서 메모리 압박이 큼
- 쓰레드 풀 환경이 아닌데도 습관적으로 `remove()` 누락하면 데이터 오염 위험 있음

### ScopedValue의 장점 (Java 21/25)

- **불변성(Immutability):** 한 번 바인딩되면 범위 내에서 변하지 않아 금융 데이터의 신뢰성 보장
- **메모리 최적화:** 데이터를 쓰레드 객체가 아닌 스택 기반으로 관리해서 메모리 효율이 좋음
- **명시적 생명주기:** 특정 스코프가 끝나면 자동으로 해제됨

### ScopedValue를 이용한 헤더 전파 예시

```kotlin
// 1. 컨텍스트를 담을 홀더 정의
class CommonContextHolder {
    companion object {
        // Java 21+ ScopedValue 선언
        private val CONTEXT: ScopedValue<CommonContext> = ScopedValue.newInstance()

        fun getContext(): CommonContext = if (CONTEXT.isBound) CONTEXT.get()
                                         else throw IllegalStateException("Context not bound")

        // Filter에서 호출할 실행 래퍼
        fun <T> runWithContext(context: CommonContext, action: () -> T): T {
            return ScopedValue.where(CONTEXT, context).call(action)
        }
    }
}

// 2. 필터에서의 적용 (의존성 방향: Infrastructure -> Domain)
@Component
class CommonContextFilter(private val objectMapper: ObjectMapper) : Filter {
    override fun doFilter(request: ServletRequest, response: ServletResponse, chain: FilterChain) {
        val httpRequest = request as HttpServletRequest
        val commonContext = parseHeader(httpRequest) // 헤더 파싱 로직

        // ScopedValue 바인딩: 이 블록 내부의 모든 Service, Repository에서 getContext() 가능
        CommonContextHolder.runWithContext(commonContext) {
            chain.doFilter(request, response)
        }
        // 블록을 벗어나면 별도의 clear() 호출 없이도 자동으로 컨텍스트가 소멸됨
    }
}
```

---

## 정리

리액티브의 복잡함을 피하기 위해 VT로 넘어오는 건 괜찮은 선택임. 근데 **비동기 기술에서 쓰던 습관(awaitAll, ThreadLocal)**을 그대로 가져오면 안 됨.

헥사고날 아키텍처 규칙에 따라 의존성 방향 준수하면서, `ScopedValue`와 **Spring Data JDBC**를 조합해서 단순하면서도 안정적인 시스템을 만들면 됨. Virtual Thread가 주는 진정한 장점은 이런 단순함에 있음.

| 항목 | Reactive (R2DBC) | Virtual Thread (JDBC) |
|------|------------------|----------------------|
| 러닝커브 | 높음 | 낮음 |
| 코드 복잡도 | 높음 (Flux/Mono 체이닝) | 낮음 (동기식 코드) |
| 자원 관리 | Backpressure 내장 | 커넥션 풀 주의 필요 |
| 컨텍스트 전파 | Context API | ScopedValue |
| 적합한 케이스 | 스트리밍, 복잡한 비동기 | 단건 요청, 단순 CRUD |
