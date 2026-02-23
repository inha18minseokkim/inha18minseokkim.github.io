---
title: "SpringDataElasticsearch 4 vs 5"
date: 2024-05-17
tags: [미지정]
---
[https://docs.spring.io/spring-data/elasticsearch/reference/elasticsearch/versions.html](https://docs.spring.io/spring-data/elasticsearch/reference/elasticsearch/versions.html)
4.~~ 버전 configuration

```java
@Configuration
@EnableElasticsearchRepositories("com.microservices.demo.elastic.index.client.repository")
@RequiredArgsConstructor
@Slf4j
public class ElasticsearchConfig extends AbstractElasticsearchConfiguration {
    private final ElasticConfigData elasticConfigData;

    @Override
    public RestHighLevelClient elasticsearchClient() {
        UriComponents serverUri = UriComponentsBuilder.fromHttpUrl(elasticConfigData.getConnectionUrl()).build();
        return new RestHighLevelClient(
                RestClient.builder(new HttpHost(
                        Objects.requireNonNull(serverUri.getHost()),
                        serverUri.getPort(),
                        serverUri.getScheme()
                )).setRequestConfigCallback(
                        requestConfigBuilder -> requestConfigBuilder.setConnectionRequestTimeout(elasticConfigData.getConnectionTimeout())
                                .setSocketTimeout(elasticConfigData.getSocketTimeout())
                )
        );
    }
    @Bean
    public ElasticsearchOperations elasticsearchTemplate() {
        return new ElasticsearchRestTemplate(elasticsearchClient());
    }
}
```

5.~~ 버전  configuration


```java
@Configuration
@EnableElasticsearchRepositories("com.microservices.demo.elastic.index.client.repository")
@RequiredArgsConstructor
@Slf4j
public class ElasticsearchConfig extends ElasticsearchConfiguration {
    private final ElasticConfigData elasticConfigData;
    @Override
    public ClientConfiguration clientConfiguration() {
        log.info("@@@@{} {} {} {}",elasticConfigData.getConnectionUrl(),elasticConfigData.getConnectionTimeout(),elasticConfigData.getSocketTimeout());
        return ClientConfiguration.builder()
                .connectedTo(elasticConfigData.getConnectionUrl())
                .withConnectTimeout(elasticConfigData.getConnectionTimeout())
                .withSocketTimeout(elasticConfigData.getSocketTimeout())
                .withHeaders(() -> {
                    HttpHeaders headers = new HttpHeaders();
                    headers.add("X-Elastic-Product", "Elasticsearch");
                    return headers;
                })
                .build();
    }
}

```


Spring boot 3 이상에서는 AbstractElasticsearchConfiguration 사용할 수 없는듯


### Java client 8 → Elasticsearch 7.X 접근 시


```java
 status: 200, [es/indices.exists] Missing [X-Elastic-Product] header. Please check that you are connecting to an Elasticsearch instance, and that any networking filters are preserving that header.

```

특정 헤더가 없다는 현상
[https://stackoverflow.com/questions/73384762/can-i-use-elasticsearch-java-with-elasticsearch-7-5-2](https://stackoverflow.com/questions/73384762/can-i-use-elasticsearch-java-with-elasticsearch-7-5-2)
사유 : 클라이언트는 8.X 인데 외부 elastic host 는 7.X여서
조치 : ContentType : application/json 추가

```java
@Configuration
@EnableElasticsearchRepositories("com.microservices.demo.elastic.index.client.repository")
@RequiredArgsConstructor
@Slf4j
public class ElasticsearchConfig extends ElasticsearchConfiguration {
    private final ElasticConfigData elasticConfigData;
    @Override
    public ClientConfiguration clientConfiguration() {
        log.info("@@@@{} {} {} {}",elasticConfigData.getConnectionUrl(),elasticConfigData.getConnectionTimeout(),elasticConfigData.getSocketTimeout());
        return ClientConfiguration.builder()
                .connectedTo(elasticConfigData.getConnectionUrl())
                .withConnectTimeout(elasticConfigData.getConnectionTimeout())
                .withSocketTimeout(elasticConfigData.getSocketTimeout())
                .withHeaders(() -> {
                    HttpHeaders headers = new HttpHeaders();
                    headers.add("X-Elastic-Product", "Elasticsearch");
                    return headers;
                })
                .withClientConfigurer(
                        ElasticsearchClients.ElasticsearchHttpClientConfigurationCallback.from(
                                httpClientBuilder -> httpClientBuilder.
                                        disableAuthCaching()
                                        .addInterceptorFirst(
                                                (HttpRequestInterceptor) (request,context) -> {
                                                    log.info("@@@@ {}",request.getAllHeaders());
                                                    request.setHeader("Content-type","application/json");
                                                })
                                        .addInterceptorLast(
                                                (HttpResponseInterceptor) (response, context) -> response.addHeader("X-Elastic-Product", "Elasticsearch")
                                        )
                                        )
                )
                .build();
    }

}

```



### IndexModel 의 @Field 에서 LocalDateTime 넣는법

[https://www.elastic.co/guide/en/elasticsearch/reference/current/mapping-date-format.html](https://www.elastic.co/guide/en/elasticsearch/reference/current/mapping-date-format.html)
DateFormat.custom 삭제됨 → 위 링크에서 하나 골라가
그래서 인덱스 생성시 다음과 같이 바꿈

```javascript
{
    "mappings": {
        "properties": {
            "userId": {
                "type": "long"
            },
            "id": {
                "type": "text",
                "fields": {
                    "keyword": {
                        "type": "keyword",
                        "ignore_above": 256
                    }
                }
            },
            "createdAt": {
                "type": "date",
		"format": "yyyy-MM-dd'T'HH:mm:ss.SSS"
            },
            "text": {
                "type": "text",
                "fields": {
                    "keyword": {
                        "type": "keyword",
                        "ignore_above": 256
                    }
                }
            }
        }
    }
}
```



### 그외 다양한 메서드들 다 Deprecated 됨

NativeSearchQueryBuilder ⇒`NativeQuery.builder()` 
[https://docs.spring.io/spring-data/elasticsearch/reference/elasticsearch/template.html](https://docs.spring.io/spring-data/elasticsearch/reference/elasticsearch/template.html)
elasticQuery 참조


### Point in Time

elasticSearch 7.10 버전부터 사용가능
Spring boot 버전이 업그레이드 되면서 구버전 es와 신버전 spring data es를 사용하는 경우 구버전 es에 _pit Post를 날리는 경우가 있음. 조심
그리고 [es/search] failed: [search_phase_execution_exception] all shards failed.. 
[https://discuss.elastic.co/t/elastic-no-mapping-found-for-shard-doc-in-order-to-sort-on/268188/2](https://discuss.elastic.co/t/elastic-no-mapping-found-for-shard-doc-in-order-to-sort-on/268188/2)
7.12 버전 부터 *shard doc 사용 가능(3시간 날림)*