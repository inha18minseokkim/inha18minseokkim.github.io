---
title: "RestController + 멀티모듈 경로"
date: 2024-05-19
tags: [미지정]
---
이런식으로 구성되어 있는 Spring Web app

```java
package com.microservices.demo.elastic.query.service;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.ComponentScan;

@SpringBootApplication
@ComponentScan(basePackages = {"com.microservices.demo"})
public class ElasticQueryServiceApplication {

    public static void main(String[] args) {
        SpringApplication.run(ElasticQueryServiceApplication.class, args);
    }

}
```


```java
package com.microservices.demo.elastic.query.service.api;
....

@RestController
@RequestMapping("/documents")
@Slf4j
@RequiredArgsConstructor
public class ElasticDocumentController {
    private final ElasticQueryService elasticQueryService;

    @Value("${elastic-config.index-name}")
    private String testValue;

    @GetMapping("/")
    public @ResponseBody
    ResponseEntity<List<ElasticQueryServiceResponseModel>> getAllDocuments() {
        List<ElasticQueryServiceResponseModel> response = elasticQueryService.getAllDocuments();
        log.info("Elasticsearch returned {} of documents", response.size());
        return ResponseEntity.ok(response);
    }
```

하위모듈을 구성하면 엔드포인트는
[http://localhost:8183/elastic-query-service/documents/](http://localhost:8183/elastic-query-service/documents/)

위와 같이 됨