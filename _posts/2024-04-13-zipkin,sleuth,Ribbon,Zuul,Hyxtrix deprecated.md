---
title: "zipkin,sleuth,Ribbon,Zuul,Hyxtrix deprecated"
date: 2024-04-13
tags: [미지정]
---
Udemy  [Spring Cloud Fundamentals](https://kmooc.udemy.com/course/spring-cloud-fundamentals/) >> 이 강의를 들으면서 zipkin,sleuth를 사용. spring boot 3.1 부터는 두 패키지가 Micrometer로 옮겨지면서 몇 가지 변경사항이 있음

cloud와 zipkin 대신 아래 dependency 추가

```sql
implementation 'org.springframework.boot:spring-boot-starter-actuator'
implementation 'io.micrometer:micrometer-tracing-bridge-brave'
implementation 'io.zipkin.reporter2:zipkin-reporter-brave'
```


```sql
management.zipkin.tracing.endpoint=http://localhost:9411/api/v2/spans
management.tracing.propagation.consume=w3c
management.tracing.propagation.produce=w3c
management.tracing.sampling.probability=1.0
logging.pattern.level=INFO

```

이런식으로 properties 추가하고 zipkin 서버 띄우면 잘 됨
[https://easywritten.com/post/using-spring-boot-3-with-zipkin/](https://easywritten.com/post/using-spring-boot-3-with-zipkin/)

위와 같이 설정한 다음 이슈(Span Id propagation이 되지 않음)

![](https://prod-files-secure.s3.us-west-2.amazonaws.com/c38aebd7-2834-4fac-b2fc-a2f0c17ce81d/d34e1858-5bd7-4ae7-887c-89674873f733/Untitled.png)

이런식으로 하나의 거래인데 propagation이 되지 않는 상황
대처방법은

```sql
implementation 'org.springframework.cloud:spring-cloud-starter-openfeign'
implementation 'io.github.openfeign:feign-micrometer'
```

feignClient 관련한 dependency 두 가지 다 가지고있어야 함



![](https://prod-files-secure.s3.us-west-2.amazonaws.com/c38aebd7-2834-4fac-b2fc-a2f0c17ce81d/6ecd2f2b-2567-42b3-9141-0154589b70ba/Untitled.png)

이렇게 하면 거래별로 헤더 Propagation 가능

![](https://prod-files-secure.s3.us-west-2.amazonaws.com/c38aebd7-2834-4fac-b2fc-a2f0c17ce81d/8e32009f-ebb6-4f96-87f5-356ec3a926a0/Untitled.png)

