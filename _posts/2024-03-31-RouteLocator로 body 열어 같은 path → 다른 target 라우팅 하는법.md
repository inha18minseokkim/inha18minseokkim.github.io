---
title: "RouteLocator로 body 열어 같은 path → 다른 target 라우팅 하는법"
date: 2024-03-31
tags: [미지정]
---

### 상황

같은 uri를 통해 리퀘스트가 들어옴
body안의 특정한 값을 기반으로 분기를 쳐야함
나갈 때 각각 다른 target으로 라우팅 되어야 함
이런 상황이 자주 있는 일은 아닐 것 같음(대체로 uri가 같으면 같은곳에서 던지지.. 이렇지는 않아)


### RouteLocator 기본(body의 문자를 보고 one ingress uri→many routing uri) 라우팅

/api-gateway라는 uri로 들어오는 신호를 cache 해야함(여기서 캐싱은 자바 메모리 영역임)

```java
@Bean
public RouteLocator SimpleRouteLocator(RouteLocatorBuilder builder) {
    return builder.routes()
          .route("stock-service", p-> p.path("/api-gateway/**").and()
          .method(HttpMethod.POST)
                .filters((f->f
                    .cacheRequestBody(String.class)//일단 샘플이니 문자열로 캐싱(이때 flux consume)
                    .filter(customFilter)
                )
              )
          .uri("no://op")
          )
        .build();
}
```

우선 filter를 
customFilter를 @Component로 선언해줌

```java
@Slf4j
@Component
public class CustomFilter implements GatewayFilter, Ordered {
    @Override
    public Mono<Void> filter(ServerWebExchange exchange, GatewayFilterChain chain) {
        String attribute = exchange.getAttribute(ServerWebExchangeUtils.CACHED_REQUEST_BODY_ATTR);//문자열로 받아옴
        String finalUrl = "";
        if(attribute.contains("1")) //대충 body에 따라 target 분기치는 로직
            finalUrl = "http://localhost:8881";
        else if(attribute.contains("2"))
            finalUrl = "http://www.naver.com";
        log.info("{}로 라우팅",finalUrl);

        try {
            exchange.getAttributes().put(GATEWAY_REQUEST_URL_ATTR, new URI("https://www.google.com"));
        } catch (URISyntaxException e) {
            throw new RuntimeException(e);
        }
        return chain.filter(exchange);
    }

    @Override
    public int getOrder() {
        return RouteToRequestUrlFilter.ROUTE_TO_URL_FILTER_ORDER + 1;
    }
}

```

String.class로 캐스팅하긴 했는데 원하는 dto나 JsonNode로 가져와서 판단하셔도 됩니다.
그리고 2번은 네이버로 가니깐 method not allowed 뜨는게 정상. 샘플이므로 필요하신 pod 추가하시면 됨

### 중요!!!

Ordered를 상속하여 빈 오더를 설정하지 않으면 안된다. 안그러면 스프링 기본으로 설정되어있는 ROUTE_TO_URL_FILTER에 우선순위를 역전당해서 계속 지정하지 않은 uri로 라우팅되어 200 response가 떨어지지만 리턴값은 아무것도 없는 상황이 발생할 수 있음.
URI는 이런식으로 바꿨지만, request에 관한 전반을 바꾸려고 한다면

```java
@Override
    public Mono<Void> filter(ServerWebExchange exchange, GatewayFilterChain chain) {
        String attribute = exchange.getAttribute(ServerWebExchangeUtils.CACHED_REQUEST_BODY_ATTR);//문자열로 받아옴
        String finalUrl = "";
        if(attribute.contains("1")) //대충 body에 따라 target 분기치는 로직
            finalUrl = "http://localhost:8881";
        else if(attribute.contains("2"))
            finalUrl = "http://www.google.com";
        log.info("{}로 라우팅",finalUrl);

        ServerHttpRequest build = exchange.getRequest().mutate()
                .method(HttpMethod.GET)
                .build();

        UriComponents uri = UriComponentsBuilder.fromUri(URI.create(finalUrl))
                .path("/api-gateway/A").build();

        ServerWebExchange mutatedExchange = exchange.mutate().request(build).build();
        Map<String, Object> attributes = mutatedExchange.getAttributes();
        attributes.put(GATEWAY_REQUEST_URL_ATTR,uri.toUri());
        return chain.filter(mutatedExchange);
    }
```

이런식으로 POST → GET 처리 가능

### URIBuilder 사용하여 path 및 queryParam 추가 가능


```java
@Override
public Mono<Void> filter(ServerWebExchange exchange, GatewayFilterChain chain) {
    String attribute = exchange.getAttribute(ServerWebExchangeUtils.CACHED_REQUEST_BODY_ATTR);//문자열로 받아옴
    String finalUrl = "";
    if(attribute.contains("1")) //대충 body에 따라 target 분기치는 로직
        finalUrl = "http://localhost:8881";
    else if(attribute.contains("2"))
        finalUrl = "http://www.google.com";
    log.info("{}로 라우팅",finalUrl);
		//원 url에 있던 queryParam kv 가져옴
    MultiValueMap<String, String> queryParams = exchange.getRequest().getQueryParams();
    //원래 리퀘스트 정보 가져옴
    ServerHttpRequest build = exchange.getRequest().mutate()
            .method(HttpMethod.GET)
            .build();

    UriComponentsBuilder uriBuilder = UriComponentsBuilder.fromUri(URI.create(finalUrl))
            .path("/api-gateway/queryParamExample"); //타겟 uri 지정
            
    for(Map.Entry<String,String> entry : queryParams.toSingleValueMap().entrySet()){
        uriBuilder = uriBuilder.queryParam(entry.getKey(),entry.getValue());
    }
    UriComponents uriComponents = uriBuilder.build();

    ServerWebExchange mutatedExchange = exchange.mutate().request(build).build();
    Map<String, Object> attributes = mutatedExchange.getAttributes();
    attributes.put(GATEWAY_REQUEST_URL_ATTR,uriComponents.toUri());
		//uri 조립끝났으면 바꿀 exchange에 조립해서 넣어
    return chain.filter(mutatedExchange);//바꿔진 exchange를 넣어야함
}
```

예시(post→ get 변경)

![](https://prod-files-secure.s3.us-west-2.amazonaws.com/c38aebd7-2834-4fac-b2fc-a2f0c17ce81d/59c9c85d-cda4-46b4-aabe-1fbeeb999b24/Untitled.png)



### Post→Post body 전달


```java
@Override
public Mono<Void> filter(ServerWebExchange exchange, GatewayFilterChain chain) {
    String attribute = exchange.getAttribute(ServerWebExchangeUtils.CACHED_REQUEST_BODY_ATTR);//문자열로 받아옴
    String finalUrl = "";
    if(attribute.contains("1")) //대충 body에 따라 target 분기치는 로직
        finalUrl = "http://localhost:8881";
    else if(attribute.contains("2"))
        finalUrl = "http://www.google.com";
    log.info("{}로 라우팅",finalUrl);

    ServerHttpRequest build = exchange.getRequest().mutate()
            //post -> post 이므로 불필요
            .build();

    UriComponentsBuilder uriBuilder = UriComponentsBuilder.fromUri(URI.create(finalUrl))
            .path("/postBypass");

    UriComponents uriComponents = uriBuilder.build();

    ServerWebExchange mutatedExchange = exchange.mutate().request(build).build();
    Map<String, Object> attributes = mutatedExchange.getAttributes();
    attributes.put(GATEWAY_REQUEST_URL_ATTR,uriComponents.toUri());
    return chain.filter(mutatedExchange);
}
```

아무것도 안건들고 uri만 바뀐 exchange를 넘기면됨

![](https://prod-files-secure.s3.us-west-2.amazonaws.com/c38aebd7-2834-4fac-b2fc-a2f0c17ce81d/f8f084cd-14e6-4b26-b850-4b1b77b9470e/Untitled.png)

대상 컨트롤러는 requestbody 받아서 바로 문자열 리턴하는 단순한 로직
