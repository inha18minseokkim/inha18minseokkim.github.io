---
title: "JPA with Spring batch"
date: 2024-07-04
tags: [미지정]
---

```lua
spring:
  jpa:
    properties:
      hibernate:
        jdbc:
          batch_size: 100
          batch_versioned_data: true
        order_updates: true
        order_inserts: true
```

다음과 같이 설정
batch insert의 경우 sequence generate 할 때 allocation size를 100으로 주고 postgresql interval도 100으로 줌(prod나 상황따라 100 말고 더 큰 숫자로)
@GeneratedValue를 AUTO로 하면 max+1 무한호출함 무조건 시퀀스 사용

+) findById할 때 N+1 문제 안생기게 조심
