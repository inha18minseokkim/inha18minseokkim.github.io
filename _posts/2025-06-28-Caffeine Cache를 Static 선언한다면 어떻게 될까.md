---
title: Caffeine Cache를 Static 선언한다면 어떻게 될까
date: 2025-06-28
tags:
  - Java
  - 동시성
  - 개발
---

### 왜?

개발을 하다가 다른 팀원 코드를 볼 일이 있어서 보고 있는데 쿼리 조회 결과를 static HashMap에 저장해놓고 올리는 패턴을 봐서 

### 예시


```java
public class PriceReader {
	private final Map<String, PriceResult> latestPrices;
	...
	public Map<String, PriceResult> getLatestPrices() {
		return latestPrices;
	}
	public Optional<PriceResult> getLatestPrice(String itemCodeNumber) {
		return Optional.ofNullble(this.getLatestPrices().get(itemCodeNumber));
	}
```

이러면 latestPrices HashMap은 @Async 작업이 크론형식으로 실행되어 jpa 조회 후 주기적으로 데이터를 밀어넣는 형식. 즉 정적 데이터이다 보니 굳이 db를 온라인 콜로 찌르지 않으려고 하는 감성이라고 보면 됨.
그래서 해외주식을 만들때도 비슷한 형식으로 만들어봄

```java
public class PriceReader {
	private final Cache<String, Map<String,PriceResult>> latestPrices =
      Caffeine.newBuilder()
      //대충초기용량설정하고 ttl 설정하는 코드
      .build();
	private final PriceRepository priceRepository;
	...
	public Map<String, PriceResult> getLatestPrices() {
		return Optional.ofNullable(latestPrices.get("latestPrice")) //캐시를 먼저 가져와
		.orElse(//캐시에서 반환된 값이 Null이면 
			Optional.ofNullable(
				query.selectFrom(price)//쿼리를 찔러
						.where(price.priceBaseDt.eq(
										JpaExpressions.select(latestPrice.priceBaseDt.max())
										.from(latestPrice))
										.stream()
										.collect(//List<PriceResult> -> Map<String,PriceResult> 변환
											Collectors.groupingBy(
												Price::getItmsCdNbr,
												PriceResult::toResult)
			).map(it -> { //반환하기 전에 메모리에 저장해
				latestPrices.set("latestPrice",it);
				return it;
		);												
	}
	public Optional<PriceResult> getLatestPrice(String itemCodeNumber) {
		return Optional.ofNullble(this.getLatestPrices().get(itemCodeNumber));
	}
```

여기서는 Caffeine을 사용해서 @Async 작업이 변수를 채워주는것이 아니라 ttl이 지나면 자동으로 지워지고 다cache miss 발생 시 db 접근하는 구조임. 
국내주식이 5분에 한번씩 크론으로 돌리지만 해외는 그렇게 하지 않는 이유는 해외는 가격 갱신 주기가 하루에 한 번이기 때문.
5분에 한번씩 가격을 갱신시켜줘야하는 국내는 5분에 한 번씩 캐시미스가 발생하는게 부담이지만 해외는 굳이? Scheduled 작업을 내가 만들고 관리해줘야 하는가 라는 생각

아무튼 그랬는데


## 📊 **Bean vs Static 선언 핵심 비교**


## **Bean 선언의 우위점**

**의존성 주입 지원**
Repository, 외부 설정값 등과 쉬운 연동
**`@Value`**, **`@ConfigurationProperties`**로 TTL 동적 설정 가능
**라이프사이클 관리**
**`@PostConstruct`**로 초기화 로직 구현
**`@PreDestroy`**로 리소스 정리 보장
Spring 컨테이너가 자동 관리
**테스트 편의성**

```java
@MockBean
private CacheManager cacheManager; *// Mock으로 대체 가능*
```



## **Static 선언의 한계**

**메모리 누수 위험**
JVM 종료까지 해제되지 않음
명시적 정리 로직 필요
대용량 데이터 처리 시 OutOfMemoryError 위험
**확장성 제약**
의존성 주입 불가능
AOP, 이벤트 처리 등과 통합 어려움
외부 환경 변화 대응 제한

### 내가 생각하는 static 장점

JVM 종료까지 해제되지 않음 > 어차피 컨테이너로 올라가서 종료하면 해제됨
단, Cache를 인메모리가 아닌 스토리지와 미러링 시킨 형태로 사용한다면 다시 생각해봐야함
명시적 정리 로직 필요 > 컨테이너로 올라가서 필요없음
의존성 주입 불가능 > 어차피 stateful한 로직이므로 의존성 없어도됨
AOP, 이벤트 처리 등과 통합 어려움 > 이건 인정
외부 환경 변화 대응 제한 > 기술에 대한 의존 추상화는 Reader 영역에서 끝이고 Service 영역에서는 래핑된 Reader를 사용할 것이기 때문에 Reader에서 더 이상 추상화된 레이어가 존재하지 않는다는 전제 하에 필요없음
 


## 그러므로


## ** Bean 사용하자**


```java
@Bean
public CacheManager overseasCacheManager() {
    CaffeineCacheManager manager = new CaffeineCacheManager("overseasPrices");
    manager.setCaffeine(Caffeine.newBuilder()
        .expireAfterWrite(10, TimeUnit.MINUTES)
        .maximumSize(1000));
    return manager;
}
```

**이유**: TTL 자동 관리, 설정 유연성

## **Bean 선언을 권장하는 이유**

**확장성**: 향후 분산 캐시(Redis) 전환 시 설정만 변경
**안정성**: **Spring의 라이프사이클 관리로 메모리 누수 방지**
**유지보수성**: 외부 설정으로 TTL, 크기 등 동적 조정
**테스트 용이성**: Mock 지원으로 단위 테스트 간편

> 핵심: static이 성능상 유리할 수 있지만, Spring 환경에서는 Bean의 장기적 이익이 단기 성능 차이를 압도합니다. 특히 Kubernetes 환경에서는 Pod 종료 시 메모리가 자동 회수되므로, Bean의 라이프사이클 관리와 확장성이 더욱 중요해집니다.

라고 함.