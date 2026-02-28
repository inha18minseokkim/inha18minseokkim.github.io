---
title: "mediation 패턴 도입기 - Reactor에 대한 오해와 실수"
date: 2024-12-09
tags: [미지정]
category:
  - 기타
---


현재 구조를 보면 

![](/assets/images/Pasted%20image%2020260228171308_8649ebed.png)

구조가 이렇게 되어있다.
stock-gateway는 최대한 많은 요청을 처리하기 위해 Spring Cloud Gateway, netty를 사용함.
하지만 mediation과 나머지는 tomcat 사용 중. 블로킹 방식임. 채널에서 오는 MCI도 블로킹 방식.
나의 생각은 이랬다
1. 언젠가는(과연) 프론트도 사용성을 위해 논블로킹 호출을 지원할것
2. 일단 백서비스는 당장 reactor로 구현할 이유가 없기 때문에 나중에 구현한다고 침
3. stock-gateway > stock-mediation > 에서 각 서비스단으로 N개의 호출을 날리는데 spring cloud gateway에서 처리량을 높이기 위해 만들어놓은 로직들이 mediation에서 스레드 하나로 제한되는것이 아쉬웠음
4. 그래서 stock-mediation에서 도입하려고 한 것이 reactor feign. 
5. mediation에서 각 서비스에 N개의 호출을 concurrent하게 일으켜서 스레드 자원을 효율적으로 사용하자 !! 일단 이게 첫 번째 목표.
6. 두 번째 목표는 stock-mediation 또한 netty로 전환하자. 는것. 다만 아직은 그럴 유인이 없으므로 간단하게 톰캣으로 구현해놓자. 나중에 바꾸면 됨 이라고 생각함.


### 문제점

케이뱅크 표준헤더를 다음과 같이 Propagate 해야 함.

![](/assets/images/Pasted%20image%2020260228171310_a23c2ee5.png)

왜냐하면 회사 내부 규칙을 준수하기 위해 호출한 인스턴스 번호, 일자등을 활용해서 guid를 생성하고 테이블 row에 있어야 함.
그래서 Interceptor를 사용하기로 함. HttpServletRequest를 게이트웨이로 받았음 > 여기 헤더 정보를 stock-mediation에서 각 업무단으로 호출 할 때 헤더를 그대로 전달해주면 됨. 

```java
@Component
@Slf4j
public class CurrentRequestHeadersInterceptor implements RequestInterceptor {
//케이뱅크 공통 헤더를 각 업무단에 propagate 하기 위한 인터셉터
	@Override
	public void apply(RequestTemplate requestTemplate) {
		ServletRequestAttributes requestAttributes = (ServletRequesAttributes)RequestContextHolder.getRequestAttributes();
		HttpServletRequest request = requestAttributes.getRequest();
			requestTemplate.header("Log-level",request.getHeader("Log-level"));
			requestTemplate.header("rcvSrvcCd",request.getHeader("rcvSrvcCd"));
			requestTemplate.header("mciIntfId",request.getHeader("mciIntfId"));
			requestTemplate.header("tlgrWrtnDt",request.getHeader("tlgrWrtnDt"));
			requestTemplate.header("staffId",request.getHeader("staffId"));
			requestTemplate.header("tlgrCrtnSysNm",request.getHeader("tlgrCrtnSysNm"));
			requestTemplate.header("tlgrSrlNo",request.getHeader("tlgrSrlNo"));
			requestTemplate.header("tlgrPrgrsNo",request.getHeader("tlgrPrgrsNo"));
	}
}
```

그래서 이렇게 RequestInterceptor를 작성하고 잘 된다고 생각했는데, 처리량이 높아지면서 문제가 생김. 자꾸 업무단에서 헤더를 못가지고 온다. 
왜 그런지에 대해서 곰곰히 생각해봤는데 (당연히 동시성 문제인건 어느정도 가늠하고 있었는데) 
RequestContextHolder를 보면 ThreadLocal로 컨텍스트가 관리되고 있는것을 볼 수 있다.

```java
public abstract class RequestContextHolder {

	private static final boolean jsfPresent =
			ClassUtils.isPresent("jakarta.faces.context.FacesContext", RequestContextHolder.class.getClassLoader());

	private static final ThreadLocal<RequestAttributes> requestAttributesHolder =
			new NamedThreadLocal<>("Request attributes");

	private static final ThreadLocal<RequestAttributes> inheritableRequestAttributesHolder =
			new NamedInheritableThreadLocal<>("Request context");
```

갑자기 그런 생각이 들었다. 이거 리액터에서 스레드 관리 이렇게 안하지 않나??
  - 정확하게는 내가 호출 한 스레드와 작업을 할당 받은 스레드가 같은가? 같진 않더라도 ThreadLocal이 전파되는 모 - 자  관계인가 라는 생각이 문득 들었다. 그리고 아니다.

![](/assets/images/Pasted%20image%2020260228171311_2f3f2722.png)

일단 스케줄러 방식이므로 작업을 할당받는 스레드가 다를 수 있으므로 Reactor에서 제시하는 Context를 이으려고 노력해야 한다. 일단 Interceptor는 맞지 않으므로 폐기
방법은 두 가지가 있다.
1. 헤더를 직접 전달
  1. 아래와 같이 전달하면 문제는 없다. 임시방편
  2. 그리고 맵을 사용하는 경우 나중에 공통로직 처리 할때 key가 http 버전에 따라 대소문자 구별 안할수도 있다는 사실이 갑자기 떠오름 ex) http1.1은 대소문자 구별 안함. 

```java
 @GetMapping("/v1/detail/price")
    public ResponseEntity<GetListedStockPriceDetailResponse> getListedStockPriceDetail(@RequestHeader Map<String,Object> header, GetListedStockPriceDetailRequest request){
```

  - 컨트롤러에서 @RequestHeader를 사용하면 헤더값을 받아올 수 있는데, 이걸 조합할 때 넘겨주면 컨텍스트 전파 없이도 헤더를 넘겨줄 수 있다.
  - feign의 파라미터에 header를 다음과 같이 넣어주면 된다.

```java
public interface ListedStockService {
    @RequestLine("GET /v1/listedStock/{itemCodeNumber}")
    Mono<GetListedStockResponse> getListedStock(@HeaderMap Map<String,Object> header, @Param("itemCodeNumber") String itemCodeNumber);
```

  - 이렇게 되면 헤더를 받아서 별 처리 없이 넘겨주는 공통 로직을 계속 불필요하게 써야 한다. 스프링 개발자라면 이정도는 AOP로 처리하고 싶어진다.
2. WebFilter 사용
  - Controller는 WebFlux 기반으로 구성하였기 때문에 WebFlux로 들어온 요청을 filter로 intercept 할 수 있다. request header를 깐 다음 Reactor Context에 넣고 deferContextual를 사용해서 컨텍스트에서 헤더값을 꺼내면 된다.
  - 그렇다 하더라도 RestController에서 헤더값을 제거하는건 성공했지만 컨텍스트를 열고 헤더값을 가져와서 api client 인터페이스에넣어주는것은 변함이 없다.

```java
@GetMapping("/v1/detail/price")
    public Mono<GetListedStockPriceDetailResponse> getListedStockPriceDetail(GetListedStockPriceDetailRequest request){
        Mono<GetListedStockResponse> listedStock = listedStockService.getListedStock(request.itemCodeNumber());
        Mono<GetListedStockLatestPriceResponse> latestPrice = listedStockService.getListedStockLatestPrice(request.itemCodeNumber());
        Mono<GetListedStockPricesResponse> prices = listedStockService.getListedStockPrices(request.itemCodeNumber(),GetListedStockPricesRequest.builder()
                .baseDateTime(request.baseDateTime())
                .deltaDay(360L)
                .build());

        return
                Mono.deferContextual(context -> {
                    String kbankStandardHeader = context.get("kbank_standard_header").toString();
                    return Mono.zip(listedStock,latestPrice,prices)
                            .map(it -> GetListedStockPriceDetailResponse.builder()
                                    .stockKoreanName(it.getT1().stockKoreanName())
                                    .itemCodeNumber(it.getT1().itemCodeNumber())
                                    .latestPrice(it.getT2().closePrice())
                                    .latestRatio(it.getT2().changeRate())
```



### 그후..

헤더 전파영역도 사실 공통이기 때문에 spring aop 를 사용하면 좋을 것 같다고 생각했지만, openfeign 에서 wrapper로 제공하는 reactive는 스프링 컨테이너의 관리를 받지 않기 때문에 별도의 aop 개발이 필요했다.
그러니깐 webflux도 reactor 기반이고, openfeign-reactive도 reactor 기반이긴 한데 스프링 컨테이너에서 openfeign-reactive를 지원하지 않는다.

다행히도 webclient를 클라이언트로 사용하는 openfeign 라이브러리가 있어서  사용하기로 했다.(Playtika)


[ThreadLocal 사용시 주의할점](https://velog.io/@slolee/ThreadLocal-%EC%82%AC%EC%9A%A9%EC%8B%9C-%EC%A3%BC%EC%9D%98%ED%95%A0%EC%A0%90)
