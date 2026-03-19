---
title: 테스트코드 짜기는 싫지만 TDD는 하고 싶어 - 클로드를 시켜
date: 2026-03-04
tags:
  - 개발
  - Java
  - AI/ML
  - Test
category:
  - 기술
---

# 단일 쿼리 조회에서 단순조회 + 캐싱 조합으로

공모주 메이트 서비스의 쿼리를 마이그레이션 진행 중에 있다.

기존(V1) 구조는 MyBatis로 작성된 복잡한 단일 SQL 쿼리가 정렬, 필터링, 페이지네이션까지 모두 처리하는 방식이었다.

```sql
-- V1: SQL이 비즈니스 로직까지 떠안은 경우
ORDER BY
  baseDt ASC,
  CASE WHEN sbscStartYn = 'Y' THEN '1' ELSE '9' END ASC,
  CASE WHEN stckLstnYn  = 'Y' THEN '2' ELSE '9' END ASC,
  CASE WHEN dmdFrcsStartYn = 'Y' THEN '3' ELSE '9' END ASC,
  dmdFrcsRvlrRt DESC,
  stckKorNm ASC,
  itmsCdNbr ASC
```

이걸 왜 바꾸냐? 크게 세 가지 이유가 있다.

1. **SQL이 너무 비대하다**: 정렬 기준이 SQL 안에 박혀 있어서, 비즈니스 로직이 바뀌면 SQL을 손봐야 한다.
2. **캐싱이 불가능하다**: 매 요청마다 DB를 풀스캔한다. 공모주 데이터는 하루에 몇 번 안 바뀌는데.
3. **테스트가 힘들다**: SQL 로직은 DB 없이는 검증하기가 사실상 불가능하다.

TOBE(V2)는 단순하다.

```java
// V2: DB에서 단순 범위 조회만
public List<Ipo> getIpoDatasByStatus(IpoDatasByStatusGetInDto in) {
    return query.selectFrom(tbStkPbofSbscInfoX)
        .where(tbStkPbofSbscInfoX.dmdFrcsStartDt.between(dateFrom, dateTo))
        .fetch().stream()
        .map(ipoJpaMapper::toIpoFromEntity).toList();
}

// 정렬, 필터링, 페이지네이션은 Java 레벨에서
// @Cacheable로 결과를 캐싱
@Cacheable(value = "ipoDatasByStatus",
           key = "{#in.dateFrom(), #in.dateTo(), #in.ipoStatus()}")
public List<Ipo> getIpoDatasByStatus(IpoDatasByStatusGetInDto in) { ... }
```

좋다. 근데 문제가 생겼다.

> "V2가 V1이랑 완전히 같은 결과를 내는지 어떻게 믿냐?"

---

# 연역적 검증 > 귀납적 검증을 섞자

기존에는 이런 식으로 검증했다.

1. SQL 보고 정렬 기준 파악
2. 머릿속에서 로직 트레이싱
3. 실제 데이터로 눈으로 확인
4. 배포 후 문제 생기면 수정

전형적인 **연역적** 방식이다. 원리를 이해하고 → 구현이 맞을 거라 믿는다.

근데 페이지네이션 커서가 4개 필드로 구성된 튜플커서가 되면 얘기가 달라진다.

```
정렬: (eventDate ASC, ratio DESC, name ASC, code ASC)
커서: date > D → 포함
      date = D AND ratio < R → 포함
      date = D AND ratio = R AND name > N → 포함
      date = D AND ratio = R AND name = N AND code > C → 포함
```

이걸 머릿속에서 100% 검증하는 건 사람이 하기 어렵다. 그래서 방향을 바꿨다.

**V1의 결과를 정답으로 놓고, V2가 동일한 결과를 내는지 테스트로 검증하자.**

이게 귀납적 접근이다. 개별 케이스들이 모두 맞으면 → 로직이 맞다고 믿는다.

사실 수학적으로 보면 `y = ax + b` 같은 일차함수도 굳이 "해석적으로" 풀 필요가 없다. 몬테카를로 시뮬레이션으로 수백만 번 샘플링하거나, 매클로린 급수로 전개하거나, 자동 미분으로 기울기를 추정해도 결국 같은 답이 나온다. 단지 엄청나게 비효율적일 뿐.

예전에는 이게 진짜 "미친 짓"이었다. 컴퓨팅 자원이 귀하던 시절엔 `f(x) = x`를 5차 다항식으로 근사하려다가 서버가 뻗었을 것이다. 근데 지금은? GPU 클러스터가 남아돌고, AI가 토큰 수십만 개를 씹어가며 대화하는 시대다. `y = ax + b`를 몬테카를로로 푸는 게 오히려 낭만 있어 보일 지경이다.

V1/V2 동등성 증명도 마찬가지다. 수학적 귀납으로 튜플커서 로직의 완전성을 증명하는 건 논문감이다. 하지만 케이스 128개를 클로드한테 짜게 하고 다 통과시키면 — 공학적으로는 — "맞다"고 믿을 수 있다. 정확한 해보다 충분히 촘촘한 근사가 실용적인 시대가 됐다. 컴퓨팅이 썩어넘치니까.

테스트 플랜을 자연어로 짜고, 테스트 코드 작성은 클로드한테 맡겼다.

---

# 테스트코드 많이 짜야함 > 하기싫음 > 너가 해

재주는 곰이 부리고 돈은 김서방(결혼한 지 두 달 됨, 진짜임)이 챙기는 스킴으로 접근했다.

테스트는 두 레벨로 나눴다.

| 레벨 | 방식 | 목적 | 테스트 수 |
|------|------|------|---------|
| 단위 테스트 | Mock 기반 (Mockito) | ipo-service V1/V2 동등성 | 81개 |
| 통합 테스트 | 실서버 API 비교 | stock-mediation 포함 E2E 검증 | 47개 |

## 월간 조회

공모주 월간 조회가 복잡한 이유가 있다.

공모주 하나에는 세 가지 이벤트가 있다: **수요예측(Book-Building)**, **청약(Subscription)**, **상장(Listing)**.

V1은 이 세 가지 이벤트를 하나의 SQL로 묶어서, 각 이벤트 날짜를 기준으로 정렬했다. V2는 이 세 가지를 별도 API로 3번 호출한 뒤 Java에서 합친다.

```
stock-mediation이 하는 일:
  getIpoDatasByDatePaginated(BB)  ─┐
  getIpoDatasByDatePaginated(SUB) ─┼→ 머지 → 정렬 → 페이지네이션
  getIpoDatasByDatePaginated(LIST)─┘
  +
  getLatestSchedule(BB/SUB/LIST)   → subscriptionMaxDate 계산
```

여기서 페이지네이션 커서가 미묘해진다.

예를 들어 현재 커서가 `date=20240201, status=SUBSCRIPTION`이라면:
- SUB 조회: `date >= 20240201` + 튜플커서 적용
- LIST 조회: `date >= 20240201` (LIST는 SUB보다 이후 이벤트이므로 같은 날짜라도 포함)
- BB 조회: `date >= 20240202` (BB는 SUB보다 이전 이벤트이므로 같은 날짜는 제외)

이 로직을 클로드한테 "이벤트 유형 커서 로직"이라고 설명하고, stock-mediation의 `buildRequest()` 함수로 구현하게 했다.

```kotlin
// stock-mediation: IpoServiceController.kt
fun buildRequest(callOrder: Int): IpoDatasByDatePaginatedGetRequest {
    val isNoCursor = !StringUtils.hasText(baseDateNextKey)
    return IpoDatasByDatePaginatedGetRequest(
        baseDt     = baseDt,
        deltaDay   = deltaDay,
        ipoStatus  = ipoStatus(callOrder),
        pageCount  = pageCount,
        // 커서 없으면 → 전체 조회
        // callOrder > cursorOrder → baseDateNextKey만 (≥ D, 포함)
        // callOrder = cursorOrder → 4-field 튜플커서
        // callOrder < cursorOrder → nextDay(baseDateNextKey) (> D, 제외)
        baseDateNextKey = when {
            isNoCursor                      -> null
            callOrder > cursorOrder         -> baseDateNextKey
            callOrder == cursorOrder        -> baseDateNextKey
            else /* callOrder < cursorOrder */ -> nextDay(baseDateNextKey)
        },
        bookbuildingSubscriptionRatioNextKey = when {
            isNoCursor || callOrder != cursorOrder -> null
            else -> bookbuildingSubscriptionRatioNextKey
        },
        ...
    )
}
```

### 단위 테스트 구조

픽스처는 2024년 Q1 실제 공모주 데이터를 기반으로 만들었다.

```java
// IpoControllerEquivalenceTestBase.java
static final Ipo IPO1_이노스페이스 = Ipo.builder()
    .itemCodeNumber("474900")
    .bookbuildingStartDate("20240108")
    .subscriptionStartDate("20240122")
    .listedDate("20240131")
    .bookbuildingSubscriptionRatio(new BigDecimal("198.50"))
    .build();

static final Ipo IPO2_에이피알 = Ipo.builder()
    .itemCodeNumber("278470")
    .bookbuildingStartDate("20240116")
    .subscriptionStartDate("20240130")
    .listedDate("20240207")
    .bookbuildingSubscriptionRatio(new BigDecimal("251.00"))
    .build();

// ... IPO3_케이엔에스, IPO4_산일전기, IPO5_나우로보틱스
```

각 테스트는 동일한 Mock 데이터를 V1, V2에 각각 주입하고 결과를 비교한다.

```java
// IpoControllerMonthlyEquivalenceTest.java

@Mock IpoReader ipoReader;
@InjectMocks IpoService ipoService;       // 실제 서비스 (V2 로직)
@Spy IpoControllerMapper ipoControllerMapper;

void assertMonthlyEquivalence(...) {
    // V1 mock: SQL이 이미 정렬/필터한 결과를 바로 반환
    given(ipoReader.getIpoMonthlyData(any())).willReturn(v1Result);

    // V2 mock: 각 상태별 raw 데이터 반환 (Java 레벨 로직이 처리)
    given(ipoReader.getIpoDatasByStatus(argThat(
        dto -> dto != null && dto.ipoStatus() == IpoStatus.BOOK_BUILDING)))
        .willReturn(bbIpos);

    // V1 호출
    GetIpoMonthlyDataResponse v1 = ipoController.getIpoMonthlyData(...);

    // V2 조합 결과 (stock-mediation 로직을 Java로 재현)
    GetIpoMonthlyDataResponse tobe = combineV2WithSchedule(...);

    assertThat(v1.pbofStckList()).isEqualTo(tobe.pbofStckList());
}
```

### 통합 테스트 구조

실제 두 서버를 띄우고 같은 파라미터로 API를 호출해서 응답을 비교한다.

```java
// IpoMonthlyEquivalenceTest.java

// V1 서버: http://localhost:36280/stock/ipo-service/v1
// TOBE 서버: http://localhost:38070/stock/ipo-service/v1

@BeforeAll
static void fetchResponses() throws Exception {
    v1Root   = MAPPER.readTree(get(V1_URL));
    tobeRoot = MAPPER.readTree(get(TOBE_URL));
}

@Test void rowCount_동일() {
    assertEquals(v1Root.path("rowCount").asInt(),
                 tobeRoot.path("rowCount").asInt());
}

@Test void 첫번째_아이템_종목코드_동일() {
    assertEquals(
        v1Root.path("pbofStckList").get(0).path("itmsCdNbr").asText(),
        tobeRoot.path("pbofStckList").get(0).path("itmsCdNbr").asText()
    );
}
```

한 가지 주의할 점: V1은 BigDecimal을 JSON string으로 직렬화하고, V2는 JSON number로 직렬화한다. 그래서 단순 `assertEquals`가 아니라 `BigDecimal.compareTo()`로 정규화 비교를 해야 한다.

```java
@Test void 첫번째_아이템_수요예측경쟁률_동일() {
    BigDecimal v1Ratio = new BigDecimal(
        v1Root.path("pbofStckList").get(0).path("dmdFrcsRvlrRt").asText());
    BigDecimal tobeRatio = new BigDecimal(
        tobeRoot.path("pbofStckList").get(0).path("dmdFrcsRvlrRt").asText());
    assertEquals(0, v1Ratio.compareTo(tobeRatio)); // "251.00" == 251.0
}
```

## 주간 조회

주간 조회는 월간보다 단순해 보이지만 함정이 있다.

V1에서 주간 조회는 `inqDate`를 기준으로 해당 주를 계산해서 조회한다. V2는 별도 weekly 엔드포인트가 없고, `/v2/items?ipoStatus=SUBSCRIPTION` 파라미터를 조절해서 사용한다.

```kotlin
// stock-mediation: 주간 = SUBSCRIPTION × ±3개월
val inqLocalDate = LocalDate.parse(inqDate, yyyyMMdd)
val weekStart = inqLocalDate.minusMonths(3).with(DayOfWeek.MONDAY)
val weekEnd   = inqLocalDate.plusMonths(3).with(DayOfWeek.SUNDAY)
val deltaDay  = ChronoUnit.DAYS.between(weekStart, weekEnd)
```

페이지네이션 테스트는 `pageCount=5`로 페이지를 반복 조회하면서 V1/V2 응답을 누적 비교한다.

```java
// IpoWeeklyPaginationEquivalenceTest.java
// 20260303 기준 총 20건 → pageCount=5 → 4페이지 반복
@BeforeAll
static void fetchAllPages() throws Exception {
    while (true) {
        JsonNode v1Page = MAPPER.readTree(get(buildV1Url(nextKey)));
        JsonNode tobePage = MAPPER.readTree(get(buildTobeUrl(nextKey)));

        // 페이지별 아이템 수집
        v1SortedPages.add(sorted(items(v1Page)));
        tobeSortedPages.add(sorted(items(tobePage)));

        if (!"Y".equals(v1Page.path("hasNextYn").asText())) break;
        nextKey = extractNextKey(v1Page); // 마지막 아이템에서 nextKey 추출
    }
}
```

## 테스트 코드 검증 방법

요약하면:

```
[단위 테스트] ipo-service 내부
  Mock IpoReader → 실제 IpoService → 결과 비교
  81개 테스트 / 3개 파일로 분리

[통합 테스트] ipo-equivalence-test (별도 Spring Boot 프로젝트)
  실서버 V1 API ──┐ 같은 파라미터로 호출
  실서버 V2 API ──┘ → 응답 필드 단위 비교
  47개 테스트 / 5개 파일로 분리
    ├── IpoMonthlyEquivalenceTest         (기본 월간 7 tests)
    ├── IpoMonthlyZeroRatioEquivalenceTest (ratio=0 엣지케이스 7 tests)
    ├── IpoMonthlyPaginationEquivalenceTest (월간 페이지네이션 8 tests)
    ├── IpoWeeklyEquivalenceTest           (기본 주간 8 tests)
    └── IpoWeeklyPaginationEquivalenceTest (주간 페이지네이션 9 tests)
```

---

# 클로드가 테스트로 잡아낸 버그들

테스트 코드를 짜고 돌려보니 V1/V2 응답이 다르게 나왔다. 버그가 있다는 뜻이다.

클로드가 테스트를 짜면서 동시에 버그도 잡아줬다. 정확히는, 테스트 실패 → 버그 원인 분석 → 수정 → 테스트 통과를 반복했다.

잡힌 버그는 총 5개다.

### 버그 1: 빈 커서일 때 null 처리 누락

`baseDateNextKey`가 빈 문자열(`""`)로 오면 커서 없는 첫 조회로 처리해야 하는데, `ratio`, `name`, `code` 커서 값도 null로 처리하지 않아서 빈 결과가 반환됐다.

```kotlin
// 수정 전: hasText 체크 없이 ratio 커서 사용
// 수정 후:
val isNoCursor = !StringUtils.hasText(baseDateNextKey)
if (isNoCursor) {
    // ratio/name/code nextKey 모두 무시
}
```

### 버그 2: OR 쿼리로 포함된 잉여 아이템 필터링 누락

V2 QueryDSL에서 SUBSCRIPTION 상태 조회 시 OR 조건을 쓴다.

```java
.where(sbscStartDt.between(from, to)
    .or(sbscClsgDt.between(from, to)))
```

이 때문에 `sbscStartDt`가 조회 범위 이전인데 `sbscClsgDt`만 범위 안에 걸리는 아이템이 포함됐다. 이걸 Java 레벨에서 필터링해야 한다.

### 버그 3: 튜플커서 로직 오류 (date > D 아이템에 불필요한 필터 적용)

```java
// 수정 전: date > D인 아이템에도 ratio/name/code 필터 적용
results.stream().filter(r -> {
    int cmpDate = eventDate.compareTo(baseDateNextKey);
    // date > D면 무조건 포함해야 하는데...
    BigDecimal ratio = r.getBookbuildingSubscriptionRatio();
    return ratio != null && ratio.compareTo(ratioKey) <= 0; // 잘못됨
})

// 수정 후: date > D면 즉시 true 반환
.filter(r -> {
    int cmpDate = eventDate.compareTo(baseDateNextKey);
    if (cmpDate > 0) return true;   // date > D → 무조건 포함
    if (cmpDate < 0) return false;  // date < D → 무조건 제외
    // date = D → 서브커서 적용
    ...
})
```

### 버그 4: 이벤트 유형 커서 로직 미구현

BB/SUB/LIST 세 가지 상태를 각각 조회할 때, 동일한 날짜라도 이벤트 유형에 따라 포함/제외 기준이 달라야 한다 (SUB < LIST < BB 순서).

이 로직이 처음에 아예 없었다. stock-mediation에 `buildRequest(callOrder)` 함수로 추가했다.

### 버그 5: 주간 조회 4-field 튜플커서 미구현

주간 조회 커서가 `subscriptionStartDate > cursor` 단순 비교만 했다. 동일 날짜 내에서 ratio/name/code 서브커서가 없어서 페이지 경계에서 아이템이 누락되거나 중복됐다.

```java
// 수정 후: (date, ratio DESC, name ASC, code ASC) 4-field 튜플커서
.sorted(Comparator
    .comparing(Ipo::getSubscriptionStartDate, nullsLast(naturalOrder()))
    .thenComparing(Ipo::getBookbuildingSubscriptionRatio, nullsLast(reverseOrder()))
    .thenComparing(Ipo::getStockKoreanName, nullsLast(naturalOrder()))
    .thenComparing(Ipo::getItemCodeNumber, nullsLast(naturalOrder())))
```

---

# 후기

TDD의 가장 큰 단점이자 문제점이 테스트 계획 수립하고 테스트 코드 짜는 데 너무 많은 공수가 든다는 것인데, 클로드가 이걸 보완해줬다.

내가 한 일:
- 도메인 설명 ("공모주에는 수요예측/청약/상장 세 가지 이벤트가 있고...")
- 테스트 플랜 자연어로 기술 ("V1과 V2가 같은 결과를 내는지 검증하되, pageCount=5씩 페이지 반복하면서...")
- 버그 발견 시 원인 가설 제시 ("이 케이스에서 date=D AND callOrder<cursorOrder인 아이템이 걸러져야 하는데...")

클로드가 한 일:
- 픽스처 5개 종목 코드 전체 작성
- 81개 단위 테스트 작성
- 47개 통합 테스트 작성
- 버그 수정 코드 작성
- 수정 후 테스트 재실행 및 검증

 **AI를 잘 쓰려면 결국 도메인을 잘 알아야 한다** 고 생각한다. "공모주 페이지네이션 테스트 짜줘"라고 하면 엉터리가 나온다. "4-field 튜플커서에서 date > D인 케이스와 date = D인 케이스를 분리해서 검증해야 하고, 이벤트 유형별 callOrder는 SUB=1, LIST=2, BB=3이야"라고 구체적으로 알려줘야 정확한 테스트가 나온다.

다시 말하면, **도메인을 정의하고 컨텍스트를 촘촘하게 제시**하는 능력이 AI 시대 개발자의 핵심 역량이 된 것 같다. 구현의 모든 세부사항을 개발자가 직접 작성하지 않아도, 테스트 커버리지를 믿고 안정적인 환경에서 운영 배포가 가능하다.

개발자가 설계하고, AI가 구현하고, 테스트가 검증한다. 이게 앞으로의 흐름인 것 같다. 그러니깐 예전에 중간 관리자들이 하던일을 내가 해야하는데,,, 거기에 맞게 아웃풋을 내지 못하면 구조조정 당하지 않을까 라는 생각.
