---
title: stock-customer-service RESTful 리팩토링 — customerId를 URI에서 뺀 이유
date: 2026-03-20
tags:
  - Kotlin
  - Spring
  - 아키텍처
  - Refactoring
  - HTTP
category:
  - 실무경험
  - MSA표준
---

커밋 `77b272f`, `75d5775` 기준.

기존 컨트롤러에서 `customerId`를 `@PathVariable`이나 `@RequestParam`으로 직접 받고 있었음.
이게 여러모로 불편했음.

---

## 문제 상황

```kotlin
// 이런 게 모든 엔드포인트에 붙어있었음
fun getInterests(@PathVariable customerId: String) { ... }
fun getMember(@PathVariable customerId: String) { ... }
fun getPushInfo(@PathVariable customerId: String, @PathVariable pushType: String) { ... }
```

문제는 두 가지였음:
1. `customerId`는 이미 헤더의 공통 컨텍스트(`CommonContext`)에 들어있는데, 굳이 URI에도 넣고 있었음
2. URI가 RESTful하지 않았음 — 리소스 경로에 사용자 ID를 박아넣는 건 별로임

---

## 해결 방법

### 1. customerId → CommonContextHolder로 대체

`CommonContextHolder.getContext().getCustomerId()`로 ThreadLocal에서 꺼내는 방식으로 전환했음.

```kotlin
// Before
fun getInterests(@PathVariable customerId: String) {
    interestService.findInterestStocks(InterestStocksFindCriteria(customerId = customerId))
}

// After
fun getInterests() {
    val customerId = CommonContextHolder.getContext().getCustomerId()
    interestService.findInterestStocks(InterestStocksFindCriteria(customerId = customerId))
}
```

`getCustomerId()`에서 custId가 없거나 15자리가 아니면 `CustomerIdNotValidException`을 던지도록 했음.
기존 `GlobalExceptionHandler`가 `RuntimeException`을 처리하고 있어서 별도 어드바이스 추가 없이 동작함.

```kotlin
@JsonIgnore  // 이거 빠뜨리면 직렬화 때 터짐 (아래 설명)
fun getCustomerId(): String {
    if (custId == null || custId.length != 15) throw CustomerIdNotValidException()
    return custId
}
```

> **`@JsonIgnore` 이유**: Kotlin의 `fun getXxx()`는 JVM 바이트코드에서 `public getXxx()` 메서드로 컴파일됨.
> Jackson이 이걸 `customerId` 프로퍼티로 인식해서 직렬화 시 호출해버림.
> `CommonContext`가 응답에 섞이는 걸 막으려면 `@JsonIgnore` 필수.

### 2. URI 변경

**MemberController**

| 변경 전 | 변경 후 |
|---|---|
| `GET /members/v1/{customerId}` | `GET /members/v1/me` |

**InterestController**

| 변경 전 | 변경 후 |
|---|---|
| `GET /interests/v1/{customerId}/investing-home` | `GET /interests/v1/investing-home` |
| `GET /interests/v1/{customerId}/unlisted-stock-service` | `GET /interests/v1/unlisted-stocks` |

**PushController**

| 변경 전 | 변경 후 | 비고 |
|---|---|---|
| `GET /pushes/v1/{customerId}/{pushType}` | `GET /pushes/v1/{pushType}` | |
| `POST /pushes/v1/{customerId}/{pushType}` | `PUT /pushes/v1/{pushType}` | 멱등 갱신이니 PUT |

**HitController**

| 변경 전 | 변경 후 |
|---|---|
| `GET /hit-ranks/v1/INVESTING_HOME` | `GET /hit-ranks/v1?serviceType=INVESTING_HOME` |
| `GET /hit-ranks/v1/UNLISTED_STOCK_SERVICE` | `GET /hit-ranks/v1?serviceType=UNLISTED_STOCK_SERVICE` |

`serviceType`은 리소스 식별자가 아니라 필터 조건임. 경로 세그먼트보다 쿼리 파라미터가 맞는 자리.
Spring의 `params` 속성으로 같은 경로를 분기했음:

```kotlin
@GetMapping("/v1", params = ["serviceType=INVESTING_HOME"])
@GetMapping("/v1", params = ["serviceType=UNLISTED_STOCK_SERVICE"])
```

---

## stock-mediation 동기화

API 변경에 맞춰 stock-mediation 클라이언트 코드도 함께 수정했음.

```kotlin
// Before
INVESTING_HOME_CUSTOMER_INTEREST_STOCKS_V1 = "/interests/v1/investing-home/{customerId}"
CUSTOMER_V1                                = "/members/v1/{customerId}"
CUSTOMER_PUSH_V1                           = "/pushes/v1/{customerId}/{type}"
CUSTOMER_HIT_RANKS_V1                      = "/hit-ranks/v1/INVESTING_HOME"

// After
INVESTING_HOME_CUSTOMER_INTEREST_STOCKS_V1 = "/interests/v1/investing-home"
CUSTOMER_V1                                = "/members/v1/me"
CUSTOMER_PUSH_V1                           = "/pushes/v1/{type}"
CUSTOMER_HIT_RANKS_V1                      = "/hit-ranks/v1"
```

서비스 인터페이스에서도 `customerId` 파라미터를 전부 제거했음.

```kotlin
// Before
fun getMember(customerId: String, request: MemberGetRequest): MemberGetResponse

// After
fun getMember(request: MemberGetRequest): MemberGetResponse
```

`HitRankPutRequest`의 `val customerId: String` 필드도 제거했음 — 서버 컨텍스트에서 꺼내니까 요청 body에 있을 이유가 없음.

---

이번 작업의 핵심은 "공통 컨텍스트에 이미 있는 걸 왜 URI에 또 넣나"라는 질문이었음.
customerId가 헤더 기반 컨텍스트로 넘어오는 구조에서는 URI에서 빼는 게 맞음.
