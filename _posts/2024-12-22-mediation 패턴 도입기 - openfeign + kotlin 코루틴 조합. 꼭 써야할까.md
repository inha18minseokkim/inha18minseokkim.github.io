---
title: "mediation 패턴 도입기 - openfeign + kotlin 코루틴 조합. 꼭 써야할까?"
date: 2024-12-22
tags: [미지정]
category: 기술
---
openfeign의 경우 suspend 아직까지는 인식못하기 때문에 adapter 패턴으로 한 벌 감싸줘야 한다.
ListedStockService.kt

```java
interface ListedStockService {
    @RequestLine("GET /v1/listedStock/{itemCodeNumber}")
    fun getListedStock(@Param("itemCodeNumber") itemCodeNumber: String?): GetListedStockResponse

    @RequestLine("GET /v1/listedStock/{itemCodeNumber}/price/latest")
    fun getListedStockLatestPrice(@Param("itemCodeNumber") itemCodeNumber: String?): GetListedStockLatestPriceResponse

    @RequestLine("GET /v1/listedStock/{itemCodeNumber}/prices")
    fun getListedStockPrices(@Param("itemCodeNumber") itemCodeNumber: String?, @QueryMap request: GetListedStockPricesRequest?): GetListedStockPricesResponse
```

ListedStockServiceAdapter.kt

```java
suspend fun getListedStock(@Param("itemCodeNumber") itemCodeNumber: String?): GetListedStockResponse {
    log.info("getListedStock")
    return withContext(Dispatchers.IO){ listedStockService.getListedStock(itemCodeNumber)}
}

suspend fun getListedStockLatestPrice(@Param("itemCodeNumber") itemCodeNumber: String?): GetListedStockLatestPriceResponse {
    log.info("getListedStockLatestPrice")
    return withContext(Dispatchers.IO) {listedStockService.getListedStockLatestPrice(itemCodeNumber)}
}

suspend fun getListedStockPrices(@Param("itemCodeNumber") itemCodeNumber: String?, @QueryMap request: GetListedStockPricesRequest?):GetListedStockPricesResponse {
    log.info("getListedStockPrices")
    return withContext(Dispatchers.IO) {listedStockService.getListedStockPrices(itemCodeNumber,request)}
}
```



```java
@GetMapping("/v1/detail/price")
suspend fun getListedStockPriceDetail(request: GetListedStockPriceDetailRequest): GetListedStockPriceDetailResponse {
    val listedStock = listedStockService.getListedStock(request.itemCodeNumber)
    val latestPrice = listedStockService.getListedStockLatestPrice(request.itemCodeNumber)
    val prices = listedStockService.getListedStockPrices(request.itemCodeNumber, GetListedStockPricesRequest(request.baseDateTime, 360L))
    return GetListedStockPriceDetailResponse(
            stockKoreanName = listedStock.stockKoreanName,
            itemCodeNumber = listedStock.itemCodeNumber,
            latestPrice = latestPrice.closePrice,
            latestRatio = latestPrice.changeRate,
            pricesCount = prices.list.stream().count(),
            prices = prices.list.stream().map {
                GetListedStockPriceDetailResponse.PriceElement(
                        baseDate = it.baseDate,
                        closePrice = it.closePrice,
                        changePrice = it.changePrice,
                        changeRate = it.changeRate
                )
            }.toList(),
            previousDayMinPrice = latestPrice.lowPrice,
            previousDayMaxPrice = latestPrice.highPrice,
            yearlyMinPrice = prices.minPrice,
            yearlyMaxPrice = prices.maxPrice
    )
}
```

다만 이렇게 두면 같은 코루틴 스코프내에서 3번 블로킹 되기 때문에

```java
suspend fun getListedStockLatestPrice(@Param("itemCodeNumber") itemCodeNumber: String?): Deferred<GetListedStockLatestPriceResponse> {
    log.info("getListedStockLatestPrice")
    return CoroutineScope(Dispatchers.IO).async {listedStockService.getListedStockLatestPrice(itemCodeNumber)}
}

suspend fun getListedStockPrices(@Param("itemCodeNumber") itemCodeNumber: String?, @QueryMap request: GetListedStockPricesRequest?): Deferred<GetListedStockPricesResponse> {
    log.info("getListedStockPrices")
    return CoroutineScope(Dispatchers.IO).async {listedStockService.getListedStockPrices(itemCodeNumber,request)}
}
```


```java
@GetMapping("/v1/detail/price")
suspend fun getListedStockPriceDetail(request: GetListedStockPriceDetailRequest): GetListedStockPriceDetailResponse {
    val listedStock = listedStockService.getListedStock(request.itemCodeNumber)
    val latestPrice = listedStockService.getListedStockLatestPrice(request.itemCodeNumber)
    val prices = listedStockService.getListedStockPrices(request.itemCodeNumber, GetListedStockPricesRequest(request.baseDateTime, 360L))
    return GetListedStockPriceDetailResponse(
            stockKoreanName = listedStock.await().stockKoreanName,
            itemCodeNumber = listedStock.await().itemCodeNumber,
            latestPrice = latestPrice.await().closePrice,
            latestRatio = latestPrice.await().changeRate,
            pricesCount = prices.await().list.stream().count(),
            prices = prices.await().list.stream().map {
                GetListedStockPriceDetailResponse.PriceElement(
                        baseDate = it.baseDate,
                        closePrice = it.closePrice,
                        changePrice = it.changePrice,
                        changeRate = it.changeRate
                )
            }.toList(),
            previousDayMinPrice = latestPrice.await().lowPrice,
            previousDayMaxPrice = latestPrice.await().highPrice,
            yearlyMinPrice = prices.await().minPrice,
            yearlyMaxPrice = prices.await().maxPrice
    )
}
```

이런식으로 되어야하는데..
아직 feign이 코루틴을 공식적으로 지원하지 않아서 suspend 처리가 잘 안됨.
코틀린으로 mediation 조합을 사용하면 다음과 같은 장점이 있다
1. 롬복 무필요(코틀린이라서)
2. 매핑로직 간결(코틀린이라서)
3. 코루틴 사용가능(코틀린이라서)
다음과 같은 단점이 있다
1. openfeign이 코루틴을 지원하지 않아서 논블로킹 구간을 Adapter를 통해서 만들어줘야함
2. jackson 관련 코틀린 모듈이 필요함(코틀린이라서)


### 결론

1. openfeign과 코틀린은 맞지 않다. 코틀린 지원해달라는 공식문서를 찾아봤는데 PO 선생님께서는 코틀린 네이티브 코드가 feign에 들어가는걸 리스크라고 판단하시는듯
2. 그러면 feignclient 말고 webclient를 써야하는데 코드가 조금 더 복잡해지지 않을까 싶다
3. feignclient는 현재까지(202501) 자바만 쓰고 코틀린쓸거면 webclient 씁시다
