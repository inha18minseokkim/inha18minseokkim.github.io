---
title: WebClient.Builder + 싱글톤 시 헤더 설정 주의(중복 정의 가능)
date: 2024-10-19
tags:
  - Spring
  - Webflux
  - 이슈정리
  - 케이뱅크
---

```java
@Configuration
public class WebClientConfig {
    @Bean
    WebClient.Builder commonWebClientBuilder() {
        SslContext build;
        try {
            build = SslContextBuilder.forClient().trustManager(InsecureTrustManagerFactory.INSTANCE)
                    .build();
        } catch (SSLException e) {
            throw new RuntimeException(e);
        }

        HttpClient httpClient = HttpClient.create().secure(t -> t.sslContext(build));

        return WebClient.builder()
                .clientConnector(new ReactorClientHttpConnector(httpClient))
                .exchangeStrategies(ExchangeStrategies.builder()
                        .codecs(configurer -> configurer.defaultCodecs().maxInMemorySize(-1))
                        .build());
    }
}

```

이런식으로 기관 호출하기 위한 공통 스펙을 빌더로 말아놓고(싱글톤)

```java
List<JsonNode> list = listedStocks.stream()
                .map(itemCodeNumber-> {
	                //각각의 종목코드에 대해 api 루프 호출
                    log.info("{}",itemCodeNumber);
                    String url = String.format("https://api.deepsearch.com/company/v1/summary?symbol_krx=%s", itemCodeNumber);
                    log.info(url);

                    WebClient webClient = webClientBuilder.baseUrl(url)
                            .defaultHeaders((httpHeaders) -> {
                                httpHeaders.add("Authorization", createBasicAuthHeader("id", "pw"));
                                httpHeaders.add("Accept-Encoding", "gzip, deflate, br");
                            })
                            .build();
```

이런식으로 공통된 webclientBuilder를 사용해서 헤더를 넣고 리퀘스트를 날리면 두 번째 루프부터 400 에러가 떨어진다.
별 짓을 다해봤는데 결론 헤더를 찍어보니 답이 나옴.

```java
private static ExchangeFilterFunction logRequest() {
        return ExchangeFilterFunction.ofRequestProcessor(clientRequest -> {
            System.out.println("Request Headers: " + clientRequest.headers());
            return Mono.just(clientRequest);
        });
    }
```

필터를 사용해서 중간에 인터셉트하고

```java
List<JsonNode> list = listedStocks.stream()
                .map(itemCodeNumber-> {
	                //각각의 종목코드에 대해 api 루프 호출
                    log.info("{}",itemCodeNumber);
                    String url = String.format("https://api.deepsearch.com/company/v1/summary?symbol_krx=%s", itemCodeNumber);
                    log.info(url);

                    WebClient webClient = webClientBuilder.baseUrl(url)
                            .defaultHeaders((httpHeaders) -> {
                                httpHeaders.add("Authorization", createBasicAuthHeader("id", "pw"));
                                httpHeaders.add("Accept-Encoding", "gzip, deflate, br");
                            })
                            .filter(logRequest())
                            .build();
```

찍어보면

```java
Request Headers: [Authorization:"Basic a2Jhbms6a2Jhbmsx", "Basic a2Jhbms6a2Jhbmsx", Accept-Encoding:"gzip, deflate, br", "gzip, deflate, br"]
Request Headers: [Authorization:"Basic a2Jhbms6a2Jhbmsx", "Basic a2Jhbms6a2Jhbmsx", Accept-Encoding:"gzip, deflate, br", "gzip, deflate, br"]
```

헤더에 중복해서 들어가있다.