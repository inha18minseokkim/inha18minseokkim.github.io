---
title: "stock-customer-service 도메인 통합 테스트 작성기"
date: 2026-03-20
tags:
  - Kotlin
  - Spring
  - 테스트
category:
  - 실무경험
---

stock-customer-service에 도메인 서비스별 통합 테스트 코드를 처음으로 작성했음.
Member, Interest, Push, Hit 네 개 서비스 대상.

---

## DB 설정

`application-local.yml` 기준 실제 DB에 붙는 통합 테스트임.

```
host:     125.186.138.131
port:     5432
database: vectorsample
username: minseokkim
```

로컬 프로파일로 실행해야 함.

---

## 테스트 패턴

기존 `UserJpaEntityServiceImplTest`에서 쓰던 패턴을 그대로 따름.

```kotlin
@SpringBootTest
@Transactional
class XxxServiceTest(...) {

    @BeforeTest
    fun threadLocal_ContextHolder_생성() {
        CommonContextHolder.getContext()  // ThreadLocal 초기화
    }

    @Test
    fun 테스트명() = runBlocking { ... }
}
```

- `@Transactional`: 각 테스트 메서드 종료 시 자동 롤백. DB 오염 방지.
- `CommonContextHolder.getContext()`: 필터를 거치지 않는 테스트 환경에서 ThreadLocal 컨텍스트를 직접 초기화해줘야 함. 안 하면 `getCustomerId()` 호출 시 NPE.
- `runBlocking`: 코루틴 기반 서비스 메서드를 동기적으로 호출.

테스트용 `customerId`는 15자리 고정값 사용:

```kotlin
private const val TEST_CUSTOMER_ID = "202200000000001"
```

---

## MemberServiceTest

| 테스트 | 검증 내용 |
|---|---|
| `사용자_조회_테스트` | 존재하는 customerId 조회 시 동일한 customerId 응답 |
| `존재하지_않는_사용자_조회_테스트` | 미존재 사용자 조회 시 null 대신 기본 User 객체 반환 확인 |

```kotlin
@Test
fun 사용자_조회_테스트() = runBlocking {
    val result = memberService.findMemberInfo(
        MemberFindCriteria(customerId = "20160860")
    )
    assertEquals("20160860", result.customerId)
}
```

---

## InterestServiceTest

### 투자홈 관심종목

| 테스트 | 검증 내용 |
|---|---|
| `투자홈_관심종목_조회_테스트` | 응답 null 여부 |
| `투자홈_관심종목_등록_및_조회_테스트` | 삼성전자(005930) 등록 후 목록에 포함 확인 |
| `투자홈_관심종목_삭제_테스트` | SK하이닉스(000660) 등록 후 `isInterest=false`로 삭제, 목록에서 제거 확인 |

```kotlin
@Test
fun 투자홈_관심종목_등록_및_조회_테스트() = runBlocking {
    interestService.editInterestStock(
        InterestStockEditCriteria(
            customerId = TEST_CUSTOMER_ID,
            nation = Nation.KR,
            symbolId = "005930",
            securities = Securities.STOCK,
            isInterest = true,
            marketCode = "KRX"
        )
    )
    val result = interestService.findInterestStocks(
        InterestStocksFindCriteria(customerId = TEST_CUSTOMER_ID)
    )
    assertContains(result.map { it.symbolId }, "005930")
}
```

### 비상장 관심종목

| 테스트 | 검증 내용 |
|---|---|
| `비상장_관심종목_조회_테스트` | 응답 null 여부 |
| `비상장_관심종목_등록_및_조회_테스트` | 등록 후 `symbols`에 포함 확인 |

> `UnlistedStockInterest`는 `symbols: MutableSet<Interest>` 필드 사용.

### 관심종목 카운트

| 테스트 | 검증 내용 |
|---|---|
| `관심종목_카운트_조회_테스트` | 심볼 기준 관심 카운트 응답 null 여부 |

---

## PushServiceTest

### 조회

| 테스트 | PushType | 검증 내용 |
|---|---|---|
| `IPO_서비스_푸시_조회_테스트` | `IPO_SERVICE` | 응답 null 여부 |
| `비상장_서비스_푸시_조회_테스트` | `UNLISTED_STOCK_SERVICE` | 응답 null 여부 |
| `투자탭_관심종목_푸시_조회_테스트` | `INVESTING_TAB_INTEREST` | 응답 null 여부 |

### 설정

```kotlin
@Test
fun 푸시_동의_설정_및_조회_테스트() = runBlocking {
    pushService.editPushInfo(
        PushInfoEditCriteria(
            customerId = TEST_CUSTOMER_ID,
            type = PushType.IPO_SERVICE,
            isApproved = true,
        )
    )
    val result = pushService.findPushInfo(
        PushInfoFindCriteria(
            customerId = TEST_CUSTOMER_ID,
            type = PushType.IPO_SERVICE,
        )
    )
    assertEquals(true, result.isApproved)
}
```

`isApproved=false` 케이스도 동일 패턴으로 작성했음.

---

## HitServiceTest

### 히트 히스토리 등록

```kotlin
@Test
fun 투자홈_히트_히스토리_등록_테스트() = runBlocking {
    val result = hitService.addHitHistory(
        HitHistoryAddCriteria(
            inquiredAt = LocalDateTime.now(),
            symbolId = "005930",
            nation = Nation.KR,
            marketCode = "KRX",
            securities = Securities.STOCK,
            customerId = TEST_CUSTOMER_ID,
            stockServiceType = StockServiceType.INVESTING_HOME,
        )
    )
    assertNotNull(result)
}
```

`UNLISTED_STOCK_SERVICE` 타입도 동일 패턴으로 작성.

### 히트 랭킹 조회

| 테스트 | 검증 내용 |
|---|---|
| `투자홈_히트랭킹_조회_테스트` | 필터 없이 상위 10개 조회 |
| `투자홈_히트랭킹_국내주식_필터_조회_테스트` | `nation=KR`, `securities=STOCK` 필터 후 응답 항목 nation/securities 검증 |
| `비상장_히트랭킹_기간별_조회_테스트` | `deltaHours=24` |
| `비상장_히트랭킹_기간별_필터_조회_테스트` | `deltaHours=48`, `marketCode=PRIVATE` 필터 |

---

## 실행 방법

IntelliJ에서 Active Profile을 `local`로 설정 후 실행:

```
Run > Edit Configurations > Active profiles: local
```

Gradle로도 실행 가능:

```bash
./gradlew :stock-customer-service:test \
  -Dspring.profiles.active=local \
  --tests "com.kbank.convenience.stock.customer.domain.*"
```
