---
title: "EKS - IDC kafka - openApi 그대로 구현해보기(절망 프로젝트)"
date: 2024-09-04
tags:
  - Kafka
  - 개발
category:
  - 실무경험
---
Kafka 관련 개발 내용 정리.
괴물 만들기 프로젝트
비슷하게 맞추기
1. 집 맥미니에 confluent kafka 7.5.0 설치 (with Kraft)
  1. 단순 데이터 전송 목적이므로 파티션은 1개
  2. 로컬 용이므로 브로커도 1개
  3. ‣
2. 오픈api 솔루션(DBridge) 에 붙어있는 was servlet 구현
  1. openApi 라는 토픽에 레코드가 들어오면 해당 레코드 읽어서 대외로 http request를 쏘고 응답을 레코드 안에 지정된 토픽으로 pub 해줌
  2. requestDto

```java
@Builder
public record OpenApiRequestDto(
        UUID uuid, //tracing용 uuid
        String originalUrl, //타겟Url
        HttpMethod httpMethod, //GET POST ...
        Map<String,String> originalHeaders, //HttpHeader
        byte[] bodyArr, //Json,XML등으로 구분안짓고 바이트로 보냄(압축 위함)
        LocalDateTime registerDateTime, //tracing용 생성일시
        String topicsToBeSent //이 토픽으로 responseDto를 보냄
) {
}
```

  3. ‣
3. pub-sub 서비스 구현
  1. 부트스트랩 서버 L4는 귀찮으므로 생략
  2. ‣
  3. 회사에서는 topic : pod 를 1:1로 설계했는데 public demo용으로는 N:1로 해봄

데이터 메세지 크기 제한을 늘리고 싶을 때 이런식으로 신청받는것같음

```javascript
kafka-configs --alter --add-config max.message.bytes=20971520 --bootstrap-server localhost:29092 --topic ListedStockRealtimePrice
```


Consumer group peek

```java
 kafka-consumer-groups --bootstrap-server localhost:29092 --describe --group python_data_load
```



[Kafka 외부 접속 허용](https://syk531.tistory.com/61)
