---
title: "mediaion 패턴 도입기 - webclient + openfeign 사용"
date: 2024-12-17
tags:
  - BFF
  - 아키텍처
  - CI/CD
  - MSA
category:
  - 실무경험
  - MSA표준
  - BFF
---



![](/assets/images/Pasted%20image%2020260228171312_04c59265.png)

아직 reactive support가 공식은 아니지만 비공식 라이브러리를 샤라웃 한 라이브러리가 있어서 일단 이걸로 알아보자.

![](/assets/images/Pasted%20image%2020260228171313_2f2b6729.png)


![](/assets/images/Pasted%20image%2020260228171314_f372da21.png)

생각보다 잘 관리되고 있고, 공식문서에서도 사용을 추천하기 때문에 사용하기로 했다.

pure reactor 대신 WebClient를 사용하면 좋은점은, spring aop에서 컨텍스트를 관리할 수 있어 확장성에 용이하다.
openfeign 클라이언트 호출 시 webclient를 사용하여 호출하고, 그 webclient를 빈등록할때 필터를 먹이면 context를 스프링 빈 관리하에 넣을 수 있다고 생각하고 시작했다.


webflux RestController는 전술한 포스트에서 사용한 webfilter를 그대로 사용한다.  요청 헤더에서 필요한 필드를 가져와서 webflux 컨텍스트에 넣는다.

```java
@Component
@Slf4j
public class KbankHeaderToContextFilter implements WebFilter {
    @Override
    public Mono<Void> filter(ServerWebExchange exchange, WebFilterChain chain) {
        return chain.filter(exchange)
                .contextWrite(e -> {
                    //Webflux 기반 컨트롤러로 들어온 요청의 헤더를 context write 함
                    Map<String, String> singleValueMap = exchange.getRequest().getHeaders().toSingleValueMap();
                    log.debug("chain Header from stock-gateway {}",singleValueMap.get("kbank_standard_header"));
                    return e.put("kbank_standard_header", singleValueMap.get("kbank_standard_header"));
                });
    }
}

```

 코드는 이대로 올린다기 보다는 컨텍스트로 헤더 전파가 된다는걸 보여주기 위해 임의 샘플로 만든거.
ExchangeFilterFunction.ofRequestProcessor를 사용해서 request를 가로챌 수 있는 필터를 하나 만든다. ClientRequest를 복사생성해서 헤더만 넣고 새로 생성한다. 아마 여기서는 mutate가 불가능한 모양이다. 

```java
@Bean
public WebClient.Builder webClientBuilder() {
    return WebClient.builder()
            .filter(kbankHeaderPropagationFilter()
            );
}

private static ExchangeFilterFunction kbankHeaderPropagationFilter() {
    return ExchangeFilterFunction
            .ofRequestProcessor(
                    request -> Mono.deferContextual(context -> {
                                //KbankHeaderToContextFilter 에서 ContextWrite 한 헤더 값을 여기서 Context get 함
                                log.debug("WebClient header from Context {}", context.get("kbank_standard_header").toString());
                                log.debug("{}", request.url());
                                //ClientRequest를 새로 만들어서 헤더값을 propagate 함. 이러면 종단 파드에 헤더 전달 가능.
                                ClientRequest build = ClientRequest.from(request)
                                        .header("kbank_standard_header", context.get("kbank_standard_header").toString())
                                        .build();
                                return Mono.just(build);
                            }
                    )
            );
}

@Bean
public ListedStockService listedStockService() {
    return WebReactiveFeign
            .<ListedStockService>builder(webClientBuilder())
            .target(ListedStockService.class,"http://127.0.0.1:8088/listed-stock-service");
}
```

WebReactiveFeign 을 사용하면 webClientBuilder를 inject 할 수 있다. 여기다가 위에서 만든 필터를 뿌려주면 자동으로 listedStockService 파드로 헤더 전파가 가능해진다.

playtika 라이브러리를 사용하니 생각보다 너무 쉽게 해결되었다..
