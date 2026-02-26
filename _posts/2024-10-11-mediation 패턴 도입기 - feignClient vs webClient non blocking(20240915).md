---
title: "mediation 패턴 도입기 - feignClient vs webClient non blocking(20240915)"
date: 2024-10-11
tags: [미지정]
category:
  - 기타
---

이 포스팅 이후 아쉬운 내용들을 해결해보고자 작성시작함.

### 현재 상황


![](https://prod-files-secure.s3.us-west-2.amazonaws.com/c38aebd7-2834-4fac-b2fc-a2f0c17ce81d/a6e52407-67d7-4315-a81a-b73ed55d0fb2/image.png)

이 구간에서 mediation > 각 단위 서비스들로 서비스가 찢어지는데, mediation의 컨트롤러에서 보통 3~5개 정도 작은 api 단위의 api를 조합한다.
그래서 현재는 가독성이 좋은 feignClient를 사용중. 

```java
@FeignClient(value = "listed-stock-web-service", url = "http://127.0.0.1:8088/listed-stock-web-service")
public interface ListedStockService {
    @GetMapping(path= "/v1/listedStock/{itemCodeNumber}")
    GetListedStockResponse getListedStock(@PathVariable("itemCodeNumber") String itemCodeNumber);
    @GetMapping(path="/v1/listedStock/latestPrice/{itemCodeNumber}")
    GetListedStockLatestPriceResponse getListedStockLatestPrice(@PathVariable("itemCodeNumber")String itemCodeNumber);
    @GetMapping(path="/v1/listedStock/outline/{itemCodeNumber}")
    GetListedStockOutlineResponse getListedStockOutline(@PathVariable("itemCodeNumber")String itemCodeNumber);
    @GetMapping(path = "/v1/listedStockPrices")
    GetListedStockPricesResponse getListedStockPrices(@SpringQueryMap GetListedStockPricesRequest request);
    @GetMapping(path= "/v1/listedStock/financial/ratio/{itemCodeNumber}")
    GetListedStockFinancialRatioResponse getListedStockFinancialRatio(@PathVariable("itemCodeNumber")String itemCodeNumber);
    @GetMapping(path= "/v1/listedStock/financial/statement/latest/{itemCodeNumber}")
    GetListedStockFinancialStatementResponse getListedStockFinancialStatement(@PathVariable("itemCodeNumber")String itemCodeNumber);
    @GetMapping(path="/v1/listedStock/summary/{itemCodeNumber}")
    GetListedStockSummaryResponse getListedStockSummary(@PathVariable("itemCodeNumber")String itemCodeNumber);
    @GetMapping(path="/v1/listedStock/financial/statement/past/{itemCodeNumber}/{targetFinancialStatement}")
    GetListedStockPastFinancialStatementsResponse getListedStockPastFinancialStatements(@PathVariable("itemCodeNumber") String itemCodeNumber
            , @PathVariable("targetFinancialStatement") String targetFinancialStatement);
}
```

이런식으로
다만 feignClient 그 자체로는 동기식이기 때문에 호출 하나 하나마다 Blocking으로 작동함.
그래서 현재는 CompletableFuture를 사용해서 비동기호출을 사용하는 중이다.

```java
    @GetMapping("/v1/detail")
    public ResponseEntity<GetListedStockPriceDetailResponse> getListedStockPriceDetail(GetListedStockPriceDetailRequest request) throws InterruptedException, ExecutionException {
        AtomicReference<GetListedStockPriceDetailResponse.GetListedStockPriceDetailResponseBuilder> builder = new AtomicReference<>(GetListedStockPriceDetailResponse.builder());

        CompletableFuture.allOf(
                CompletableFuture.supplyAsync(() ->{
                GetListedStockResponse response = listedStockService.getListedStock(request.itemCodeNumber());
                builder.set(builder.get().stockKoreanName(response.stockKoreanName())
                        .itemCodeNumber(response.itemCodeNumber())
                        .representativeName(response.representativeName())
                        .establishDate(response.establishDate())
                        .companyDetail(response.companyDetail())
                        .companyScale(response.companyScale())
                        .businessRegistrationNumber(response.businessRegistrationNumber())
                        .corporationNumber(response.corporationNumber())
                        .telephoneNumber(response.telephoneNumber())
                        .landAddress(response.landAddress())
                        .industryName(response.industryName())
                        .businessScope(response.businessScope()));
                return response;
                }),
                CompletableFuture.supplyAsync(() -> {
                    GetListedStockLatestPriceResponse response = listedStockService.getListedStockLatestPrice(request.itemCodeNumber());
                    builder.set(builder.get()
                            .latestPrice(response.closePrice())
                            .latestRatio(response.changeRate())
                            .marketPriceTotal(response.marketPriceTotal())
                            .changeRate(response.changeRate())
                            .closePrice(response.closePrice())
                            .volume(response.volume())
                    );
                    return response;
                }),
```


이거랑 Webflux를 활용한 Nonblocking 조합 중 뭐가 더 효과가 좋을지 궁금함.
일단 지금도 TPS 200정도는 버티니깐 시간나면 한번 알아보고 개선포인트면 개선 해보자.


# openFeign도 reactive feign이 있다.

현재상황은 OpenFeign 블로킹 + CompletableFuture 활용 논블로킹인데 이걸 논블로킹으로 바꾸고싶다.
다음과 같은 장점과 한계를 고려하며 도입 고민중.
1. Webflux의 retry 관련 설정 활용하고싶음
2. non blocking 쓰고싶긴한데 어차피 MCI에 줄 때 다 조립해서 줘야하서 싹 블로킹이긴 함.
3. feign을 사용해서 가독성을 높이고 싶음

```java
public interface ListedStockService {
    @RequestLine("GET /v1/listedStock/{itemCodeNumber}")
    Mono<GetListedStockResponse> getListedStock(@Param("itemCodeNumber") String itemCodeNumber);
    @RequestLine("GET /v1/listedStock/{itemCodeNumber}/price/latest")
    Mono<GetListedStockLatestPriceResponse> getListedStockLatestPrice(@Param("itemCodeNumber")String itemCodeNumber);
    @RequestLine("GET /v1/listedStock/{itemCodeNumber}/prices")
    Mono<GetListedStockPricesResponse> getListedStockPrices(@Param("itemCodeNumber") String itemCodeNumber,@QueryMap GetListedStockPricesRequest request);
    @RequestLine("GET /v1/listedStock/financial/ratio/{itemCodeNumber}")
    Mono<GetListedStockFinancialRatioResponse> getListedStockFinancialRatio(@Param("itemCodeNumber")String itemCodeNumber);
    @RequestLine("GET /v1/listedStock/financial/statement/latest/{itemCodeNumber}")
    Mono<GetListedStockFinancialStatementResponse> getListedStockFinancialStatement(@Param("itemCodeNumber")String itemCodeNumber);
    @RequestLine("GET /v1/listedStock/summary/{itemCodeNumber}")
    Mono<GetListedStockSummaryResponse> getListedStockSummary(@Param("itemCodeNumber")String itemCodeNumber);
    @RequestLine("GET /v1/listedStock/financial/statement/past/{itemCodeNumber}/{targetFinancialStatement}")
    Mono<GetListedStockPastFinancialStatementsResponse> getListedStockPastFinancialStatements(@Param("itemCodeNumber") String itemCodeNumber
            , @Param("targetFinancialStatement") String targetFinancialStatement);
}
```


```java
@GetMapping("/v1/detail/price")
    public ResponseEntity<GetListedStockPriceDetailResponse> getListedStockPriceDetail(GetListedStockPriceDetailRequest request){
        Mono<GetListedStockResponse> listedStock = listedStockService.getListedStock(request.itemCodeNumber());
        Mono<GetListedStockLatestPriceResponse> latestPrice = listedStockService.getListedStockLatestPrice(request.itemCodeNumber());
        Mono<GetListedStockPricesResponse> prices = listedStockService.getListedStockPrices(request.itemCodeNumber(),GetListedStockPricesRequest.builder()
                .baseDateTime(request.baseDateTime())
                .deltaDay(360L)
                .build());

        return ResponseEntity.ok().body(
                Mono.zip(listedStock,latestPrice,prices)
                        .map(it -> GetListedStockPriceDetailResponse.builder()
                                .stockKoreanName(it.getT1().stockKoreanName())
                                .itemCodeNumber(it.getT1().itemCodeNumber())
                                .latestPrice(it.getT2().closePrice())
                                .latestRatio(it.getT2().changeRate())
                                .pricesCount(it.getT3().list().stream().count())
                                .prices(it.getT3().list().stream().map(mapper::toSubResponse).collect(Collectors.toList()))
                                .previousDayMinPrice(it.getT2().lowPrice())
                                .previousDayMaxPrice(it.getT2().highPrice())
                                .yearlyMinPrice(it.getT3().minPrice())
                                .yearlyMaxPrice(it.getT3().maxPrice())
                                .build()).block()
        );
    }
```

CompletableFuture + Blocking 사용하는것보다 확실히 논블로킹은 좀 선언적인 느낌이 있어서 보기에는 좋다. 
참 아쉬운건..service → mediation → gateway는 stream 처리(Mono,Flux) 할려면 할 수 있음. 어차피 MSA 환경이라 리스트 90개짜리 이런건 Flux 처리하면 괜찮을 것 같은데, 어차피 MCI에 넘겨줄 때 전문을 줘야하기 때문에 gateway → MCI 에서 블로킹 무조건 발생함.
그럼에도 불구하고 선언적 조합은 가독성이 좋다.

