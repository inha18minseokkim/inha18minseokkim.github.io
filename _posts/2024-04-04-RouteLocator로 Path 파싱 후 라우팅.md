---
title: RouteLocator로 Path 파싱 후 라우팅
date: 2024-04-04
tags:
  - Spring
  - SCG
  - Webflux
  - 케이뱅크
category:
  - 실무경험
---

```javascript
@Bean
public RouteLocator SimpleRouteLocator(RouteLocatorBuilder builder) {
    return builder.routes()
          .route("unlistsed-stock-service", p-> p.path("/api-gateway/**").and()
          .predicate((exchange) -> {
	          RequestPath path = exchange.getRequest().getPath();
	          PathContainer.element element = path.elements().get(path.elements().size()-1);
	          log.info("Path Predicate:{}",element.value());
	          return element.value().contains("CSVSTK2");
          })
                .filters((f->f
                    .cacheRequestBody(String.class)//일단 샘플이니 문자열로 캐싱(이때 flux consume)
                    .filter(customFilter) //정상적인 uri 조립
                )
              )
          .uri("http://unlisted-stock-service.convenience.svc.cluster.local")
          )
          .route("ipo-service", p-> p.path("/api-gateway/**").and()
          .predicate((exchange) -> {
	          RequestPath path = exchange.getRequest().getPath();
	          PathContainer.element element = path.elements().get(path.elements().size()-1);
	          log.info("Path Predicate:{}",element.value());
	          return element.value().contains("CSVSTK1");
          })
                .filters((f->f
                    .cacheRequestBody(String.class)//일단 샘플이니 문자열로 캐싱(이때 flux consume)
                    .filter(customFilter) //정상적인 uri 조립
                )
              )
          .uri("http://ipo-service.convenience.svc.cluster.local")
          )
        .build();
}
```

filter 로 uri 조립하는 부분 진입 전 path+ predicate로 분기를 침
api-gateway/CSVSTK2000001 인 경우 → unlisted-stock-service로 라우팅
api-gateway/CSVSTK1000001 인 경우 → ipo-sersvice로 라우팅

만약에 3번 서비스가 나오는 경우 해당 로직은 인터페이스와 enum으로 묶어서 관리할 예정.
