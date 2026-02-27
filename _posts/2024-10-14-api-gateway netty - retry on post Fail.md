---
title: "api-gateway netty - retry on post Fail"
date: 2024-10-14
tags:
  - 개발
  - 인프라
  - 아키텍처
category:
  - 기술
---
API Gateway 관련 설정 및 이슈 해결 정리.
[Retry GatewayFilter Factory :: Spring Cloud Gateway](https://docs.spring.io/spring-cloud-gateway/reference/spring-cloud-gateway/gatewayfilter-factories/retry-factory.html)
> When using the retry filter with any HTTP method with a body, the body will be cached and the gateway will become memory constrained. The body is cached in a request attribute defined by `ServerWebExchangeUtils.CACHED_REQUEST_BODY_ATTR`. The type of the object is `org.springframework.core.io.buffer.DataBuffer`.

Post Retry의 경우 테이블을 기본설정으로 두면 3번 칠 수 있기 때문에 몇가지 사항을 고려할 필요가 있어보인다.
1. retry의 Predicate 구문에서 POST 호출인 경우 java.net.ConnectException 가 난 경우에만 POST Retry
2. 
