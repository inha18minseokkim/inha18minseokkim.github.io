---
title: "mediation 패턴 도입기 - 하지만 100% 코틀린이라면???"
date: 2025-02-06
tags:
  - 개발
  - 아키텍처
  - Java
category:
  - 실무경험
---
client 구현을 신경쓰지 않아도 되어서 feignclient 를 사용하였지만 
Thread 기반 interceptor를 만든다 > 제한된 자원 내에서 동시성 문제가 심함
openfeign-reactive 사용한다(공식) > 내부는 블로킹임 + 스프링 컨텍스트에 포함되지 않음
playtika-reactive 사용한다(비공식) > 스프링 컨텍스트에 포함된 webClient를 사용할 수 있음

그래서 자바를 사용한다면 현재는 playtika-reactive를 사용하면 됨.
문제는 자바에서 reactor를 사용하는데 문법이 너무 힘듬

```java
 @GetMapping("/v1/detail/price")
    public Mono<GetListedStockPriceDetailResponse> getListedStockPriceDetail(GetListedStockPriceDetailRequest request){
        Mono<GetListedStockResponse> listedStock = listedStockService.getListedStock(request.itemCodeNumber);
        Mono<GetListedStockLatestPriceResponse> latestPrice = listedStockService.getListedStockLatestPrice(request.itemCodeNumber);
        Mono<GetListedStockPricesResponse> prices = listedStockService.getListedStockPrices(request.itemCodeNumber,GetListedStockPricesRequest.builder
                .baseDateTime(request.baseDateTime)
                .deltaDay(360L)
                .build);

        return
                Mono.zip(listedStock,latestPrice,prices)
                        .map(it -> GetListedStockPriceDetailResponse.builder
                                .stockKoreanName(it.getT1.stockKoreanName)
                                .itemCodeNumber(it.getT1.itemCodeNumber)
                                .latestPrice(it.getT2.closePrice)
                                .latestRatio(it.getT2.changeRate)
                                .pricesCount(it.getT3.list.stream.count)
                                .prices(it.getT3.list.stream.map(mapper::toSubResponse).collect(Collectors.toList))
                                .previousDayMinPrice(it.getT2.lowPrice)
                                .previousDayMaxPrice(it.getT2.highPrice)
                                .yearlyMinPrice(it.getT3.minPrice)
                                .yearlyMaxPrice(it.getT3.maxPrice)
                                .build);
    }
```


콜백 패턴마냥 함수가 중첩되다보니 가독성문제. 정확하게는 다른 자바 개발자들에게 러닝커브가 클 수도 있다는 생각이 들어 코틀린으로 구현해보기로 함(물론 코틀린도 러닝커브가 있다는 나쁜말은 ㄴㄴ)

feign 관련 dependency 모두 삭제하고 webclient만 사용해봄.


```kotlin
interface ListedStockService {
    //    @RequestLine("GET /v1/listedStock/{itemCodeNumber}")
    suspend fun getListedStock(itemCodeNumber: String): GetListedStockResponse?

    //    @RequestLine("GET /v1/listedStock/{itemCodeNumber}/price/latest")
    suspend fun getListedStockLatestPrice(itemCodeNumber: String): GetListedStockLatestPriceResponse?

    //    @RequestLine("GET /v1/listedStock/{itemCodeNumber}/prices")
    suspend fun getListedStockPrices(
        itemCodeNumber: String,
        request: GetListedStockPricesRequest
    ): GetListedStockPricesResponse?

    //    @RequestLine("GET /v1/listedStock/financial/ratio/{itemCodeNumber}")
    suspend fun getListedStockFinancialRatio(itemCodeNumber: String): GetListedStockFinancialRatioResponse?

    //    @RequestLine("GET /v1/listedStock/financial/statement/latest/{itemCodeNumber}")
    suspend fun getListedStockFinancialStatement(itemCodeNumber: String): GetListedStockFinancialStatementResponse?

    //    @RequestLine("GET /v1/listedStock/summary/{itemCodeNumber}")
    suspend fun getListedStockSummary(itemCodeNumber: String): GetListedStockSummaryResponse?

    //    @RequestLine("GET /v1/listedStock/financial/statement/past/{itemCodeNumber}/{targetFinancialStatement}")
    suspend fun getListedStockPastFinancialStatements(
        itemCodeNumber: String, targetFinancialStatement: String
    ): GetListedStockPastFinancialStatementsResponse?
}

```

Mono 리턴이 아닌 suspend 키워드를 사용하였다.

실제 구현은 다음과 같이 한다

```kotlin
class ListedStockServiceImpl(
    private val webClientBuilder: WebClient.Builder,
    private val objectMapper: ObjectMapper
): ListedStockService {
    val log: Logger = logger

    // ObjectMapper 활용하여 Query String 변환
    fun toQueryParams(request: Any): String {
//        val objectMapper = ObjectMapper
//            .registerKotlinModule
//            .disable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS) // ISO 대신 어노테이션 포맷 유지

        // JSON 직렬화 -> Map 변환
        val jsonString = objectMapper.writeValueAsString(request) // {"baseDateTime":"20240205123456","deltaDay":7}
        val jsonNode = objectMapper.readTree(jsonString) as ObjectNode
        // Query Parameter 생성
        return jsonNode.fields.asSequence
            .joinToString("&") { "${it.key}=${it.value.asText}" }
    }


//    @RequestLine("GET /v1/listedStock/{itemCodeNumber}")
    override suspend fun getListedStock(itemCodeNumber: String): GetListedStockResponse? {
        return webClientBuilder.build
            .get
            .uri("/v1/listedStock/${itemCodeNumber}")
            .retrieve.bodyToMono<GetListedStockResponse>
            .awaitSingle
    }

//    @RequestLine("GET /v1/listedStock/{itemCodeNumber}/price/latest")
    override suspend fun getListedStockLatestPrice(itemCodeNumber: String): GetListedStockLatestPriceResponse? {
        return webClientBuilder.build
            .get
            .uri("/v1/listedStock/${itemCodeNumber}/price/latest")
            .retrieve.bodyToMono<GetListedStockLatestPriceResponse>
            .awaitSingle
    }

//    @RequestLine("GET /v1/listedStock/{itemCodeNumber}/prices")
    override suspend fun getListedStockPrices(
        itemCodeNumber: String,
        request: GetListedStockPricesRequest
    ): GetListedStockPricesResponse? {
        return webClientBuilder.build
            .get
            .uri("/v1/listedStock/${itemCodeNumber}/prices/summary?${toQueryParams(request)}")
            .retrieve.bodyToMono<GetListedStockPricesResponse>
            .awaitSingle
    }

```


관련 빈주입은 수동으로 넣어줬다.

```kotlin
@Configuration
open class ApiClientConfig(
        val log: Logger = logger
) {
    @Bean
    open fun objectMapper: ObjectMapper {
        return jacksonObjectMapper.apply {
            registerModule(JavaTimeModule)
            disable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS)
        }
    }

    @Bean
    open fun webClientBuilder: WebClient.Builder {
        return WebClient.builder
                .filter(kbankHeaderPropagationFilter
                )
    }

    @Bean
    open fun listedStockService: ListedStockService {
        return ListedStockServiceImpl(
            webClientBuilder
                .baseUrl("http://127.0.0.1:38080/listed-stock-service")
            ,objectMapper
        )
    }

    companion object {
        var log = logger
        private fun kbankHeaderPropagationFilter: ExchangeFilterFunction {
            return ExchangeFilterFunction
                    .ofRequestProcessor { request: ClientRequest ->
                        Mono.deferContextual<ClientRequest> { context: ContextView ->
                            //KbankHeaderToContextFilter 에서 ContextWrite 한 헤더 값을 여기서 Context get 함
                            log.debug("WebClient header from Context {}", context.get<Any>("kbank_standard_header").toString)
                            log.debug("{}", request.url)
                            //ClientRequest를 새로 만들어서 헤더갑을 propagate 함. 이러면 종단 파드에 헤더 전달 가능.
                            val build = ClientRequest.from(request)
                                    .header("kbank_standard_header", context.get<Any>("kbank_standard_header").toString)
                                    .build
                            Mono.just<ClientRequest>(build)
                        }
                    }
        }
    }
}

```



실제 service를 사용하는 부분

```kotlin
@RequestMapping(path = ["/stock/listed-stock"])
@RequiredArgsConstructor
@Slf4j
@RestController
class ListedStockController(
    private val listedStockService: ListedStockService,
    private val mapper: ListedStockMapper
) {
    @GetMapping("/v1/detail/price")
    suspend fun getListedStockPriceDetail(request: GetListedStockPriceDetailRequest): GetListedStockPriceDetailResponse =
        coroutineScope {
            val listedStockDeferred = async { listedStockService.getListedStock(request.itemCodeNumber)!! }
            val latestPriceDeferred = async { listedStockService.getListedStockLatestPrice(request.itemCodeNumber)!! }
            val pricesDeferred = async {
                listedStockService.getListedStockPrices(
                    request.itemCodeNumber,
                    GetListedStockPricesRequest(baseDateTime = request.baseDateTime, deltaDay = 360L)
                )
            }

            val listedStock = listedStockDeferred.await
            val latestPrice = latestPriceDeferred.await
            val prices = pricesDeferred.await

            GetListedStockPriceDetailResponse(
                stockKoreanName = listedStock.stockKoreanName,
                itemCodeNumber = listedStock.itemCodeNumber,
                latestPrice = latestPrice.closePrice,
                latestRatio = latestPrice.changeRate,
                pricesCount = prices.list.stream.count,
                prices = prices.list.stream
                    .map { getListedStockPricesSubResponse: GetListedStockPricesSubResponse? ->
                        mapper.toSubResponse(getListedStockPricesSubResponse)
                    }
                    .toList,
                previousDayMinPrice = latestPrice.lowPrice,
                previousDayMaxPrice = latestPrice.highPrice,
                yearlyMinPrice = prices.minPrice,
                yearlyMaxPrice = prices.maxPrice,
            )
        }
}

```


feign이 해주는 일을 공통 로직으로 직접 구현해야 하지만, 코틀린이 그만큼 편리하기 때문에 충분히 고려해볼만한 선택지인 것 같다.

자바 기준으로 압도적인것은, 코루틴스코프 내부에서 suspend 함수를 async 호출을 하면 콜백패턴을 사용하지 않아도 동시성 제어? 라고 해야하나 스케줄링을 알아서 다 해주는게 좋은것같음.
가령 

```kotlin
val listedStockDeferred = async { listedStockService.getListedStock(request.itemCodeNumber)!! }
val latestPriceDeferred = async { listedStockService.getListedStockLatestPrice(request.itemCodeNumber)!! }
val pricesDeferred = async {
    listedStockService.getListedStockPrices(
        request.itemCodeNumber,
        GetListedStockPricesRequest(baseDateTime = request.baseDateTime, deltaDay = 360L)
    )
}

val listedStock = listedStockDeferred.await
val latestPrice = latestPriceDeferred.await
val prices = pricesDeferred.await
```

각 api 호출이 1초가 걸린다면 이 부분은 1초가 걸린다.


```kotlin
val listedStockDeferred = async { listedStockService.getListedStock(request.itemCodeNumber)!! }

val pricesDeferred = async {
    listedStockService.getListedStockPrices(
        request.itemCodeNumber,
        GetListedStockPricesRequest(baseDateTime = request.baseDateTime, deltaDay = 360L)
    )
}

val listedStock = listedStockDeferred.await
val latestPriceDeferred = async { listedStockService.getListedStockLatestPrice(listedStock.itemCodeNumber)!! }
val latestPrice = latestPriceDeferred.await
val prices = pricesDeferred.await
```

이렇게 하면 2초가 걸린다.
이런식으로 스케줄링을 알아서 해주는게 좋음.
