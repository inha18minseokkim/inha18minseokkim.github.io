---
title: "CompletableFuture"
date: 2023-08-20
tags: [미지정]
---
Future예제

```java
public List<String> findPrices(String product) {
	return shops.stream().map(shop -> shop,getPrice(product))//각상점에서 가격얻기
					.map(Quote::parse) //문자열을 quote객체로 변환
					.map(Discount::applyDiscount) //할인 적용
					.collect(Collectors.toList());
}
```

문제점 : 파이프라이닝을 하는데 병렬처리를 하지않아 순차적으로 실행함. 순차적으로 기다리고 순차적으로 처리함 ex) getPrice에서 1초 걸리고 리스트가 5개면 5초걸림. 파이프라인을 타면서 블록을 한 스레드에서 다섯번 맞음
⇒ parallelStream()을 사용하면 되겠네??
⇒ ㅇㅇ 되긴하는데 리스트 수가 스레드풀의 가용스레드 넘으면 이것도 문제임


```java
public List<String> findPrices(String product) {
	List<CompletableFuture<String>> priceFutures = 
			shops.stream()
			.map(shop -> CompletableFuture.supplyAsync(
																			() -> shop.getPrice(product), executor))
			.map(future -> future.thenApply(Quote::parse))
			.map(future -> future.thenCompose(quote ->
									CompletableFuture.supplyAsync(
													() -> Discount.applyDiscount(quote,executor))
						.collect(toList());
	return priceFutures.stream()
							.map(CompletableFuture::join)
							.collect(toList());
}
```


![](https://s3-us-west-2.amazonaws.com/secure.notion-static.com/5f772a47-92a2-4dad-8b25-f0fb51018d8d/Untitled.png)


### 독립적인 두 개의 CompletableFuture 합치기


```java
Future<Double> futurePriceInUSD = 
			CompletableFuture.supplyAsync(() -> shop.getPrice(product))
					.thenCombine(
							CompletableFuture.supplyAsync(
									() -> exchangeService.getRate(Money.EUR, Money.USD)),
							(price, rate) -> price * rate
				));
```


![](https://s3-us-west-2.amazonaws.com/secure.notion-static.com/d122a80d-5c06-4124-826c-a6b7ac5de28d/Untitled.png)

