---
title: "**Advanced data modeling for Amazon ElastiCache **"
date: 2025-12-03
tags: [미지정]
category: 기타
---

### low latency, high throughput

RDS workload가 점점 많아지면 레플리카를 만들어 계속 읽는데
  - db 자체도 캐시가 있긴한데 비싸기도 하고 개발자가 통제할 수 있는 영역이 아님
인메모리 디비 써서 응답시간 줄이자
>> RDS 스케일 다운해서 돈을 아끼도록 하자

캐싱전략은 흔히 사용하는 그 전략 소개함
  - lazy loading - 캐시 찌르고 없으면 디비에서 가져와서 주고 캐시에 적재
rds에서 람다 호출해서 레디스 적재하는방법도 소개됨

![](attachment:ef8438ae-f498-43d4-8527-30f194a735bf:image.png)


베리 핫 아이템을 캐시하고싶으면 멀티커맨드(multi exec) 해서 set과 ttl 한트랜에 넣어야 ttl이 제대로 먹음(한트랜에 안하면 ttl이 매우 짧은 경우 부정확하게 동작할 수 있음)


### thundering herd problem - multiple process simultaneously bottleneck

레디스 순간적으로 expire 되면 db에 갑자기 부하 몰림 응답시간 영향받음
오직 하나의 클라이언트가 DB에 넣고 캐시에 넣음 
그럼 대기하고 있던 나머지 클라이언트 파드가 레디스에서 가져가는 기법

![](attachment:ad6986fd-cc0f-430d-bc1b-42bea96ac7ad:46935b8d-cee4-43d2-8241-c76a0a7f283d.png)

처음 들어간 클라이언트가 nx ex 써서 락을 걸어
걸고 디비에서 쿼리하고 넣어 
  - 두번째 클라는 Nx때문에 쿼리하면 실패해서 최대 5초동안 기다리고 

![](attachment:a407fefa-c7de-43ee-8e00-4840dbbb88f1:image.png)

첫번째 클라가 SET 하면 대기하고 있던 두 번째 클라이언트가 가져가면됨


### 클라이언트사이드 캐싱


![](attachment:98ee9c4a-f3c1-4420-92ed-0c649c1155ce:image.png)

로컬캐시를 쓰자 로컬캐시도 ttl 관리해야함 

또는 remote cache subscribe 해서 쓰는거

![](attachment:258110ee-4333-4438-8b0a-4ef73e1f6f08:image.png)


### 클라이언트 사이드 캐싱할때 invalidate를 하는 방법


![](attachment:3bdcb753-8e57-42d9-acf7-a60946261a1d:936f0170-bdbe-4845-9fa3-9caa95a982ca.png)

로컬에서 커넥션풀로 tcp 커넥션 만들어놓음

invalidation connection 하나 두고 이걸로 로컬 cache invalidate를 제어함

![](attachment:ccb37f92-4896-4e46-a985-db7265a7bcbf:image.png)


![](attachment:e2fe1f6e-b386-4625-b270-cecf035c0d41:image.png)





### hash vs json


![](attachment:bb8fca6a-d06e-45fb-9a9f-2445302a4af3:image.png)

흔히 아는 HSET

![](attachment:208c6a6f-6009-444b-9831-9228a6eb9982:image.png)

다들 아는 Value SET하는 방법.
단지, SET할때 String이 아니라 Json으로 진짜 저장할 수 있음

![](attachment:0c8c0985-e189-496c-a115-c206b28a7695:image.png)

필드 추가도 가능

![](attachment:d3ef506b-c9fa-4a02-8ec9-d7482dd388b8:image.png)





### 시맨틱 캐시

몇주전에 엘라스팈캐시에 시맨틱 캐시 가능하게됨
이건 그저께 들었던 내용과 크게 다르지않음

![](attachment:19c6ae50-c114-4f8a-8fac-0d3261f57125:image.png)


![](attachment:d79803a8-0ab1-40dd-a01a-ce6596acfd1d:image.png)



### pub sub

샤딩 pubsub이 더 추천함 확장성있어서
게임 채팅 모델

![](attachment:e96614d9-06f6-420b-948c-8a41cf0ec84f:image.png)


![](attachment:818ca5c7-195e-4bce-b322-43da67523c2e:image.png)

alice가 spub 하면 자기 메세지도 ssub되므로 참고


### probablistic data structure - 완벽하진않은데 대충 빠르게 맞게


![](attachment:05c0046a-6a74-48e1-928c-d66b3160c04c:image.png)

dau 구할 때 사용 가능 원래는 set을 사용하는데 그러면 O(N)

hyperloglog 이걸로 정확성을 좀 버리고 시간을 많이 얻을 수 있다
이거 쓰면 O(1)임 보통 uniqueness 보려면 O(N)인데
HLL 알고리즘 - murmurhash함수로 64비트 분산 바이너리 스트링 만듬

![](attachment:0d7430f6-704f-4a93-9078-35ae8f4ab0d1:image.png)


![](attachment:f2a402c7-4cfb-41b5-9f68-b56e5ef79d62:image.png)

아래와같이 100% 정확한건 아닌데 얼추 1% 내외 오차니깐 갠또 때릴때 쓰면되겠다

![](attachment:78d56289-d3dd-4f45-8b6b-d58c2d7c4cf4:image.png)

키 파티션으로도 적용 가능한듯 ㄷㄷㄷ

bloom filter

![](attachment:c20abf91-c748-4f62-ad67-bf86aae9e536:image.png)

O(K) 복잡도 N(사람 수)가 아닌게 어딘가 싶음
FP 낮출수록 메모리 사용량 늘어남

![](attachment:cfe35314-83bb-4503-8346-7d1d103d244e:image.png)

[임베드]()
얘도 100% 맞는건 아닌데 얼추 관계에 대해 맞출 수 있음(위 예시에서는 1% 확률로 False Positive)


### geospatial


![](attachment:ee2ed612-df81-4c57-be63-2955344d5406:image.png)

진짜 가까운거 찾는것같음
geohash 알고리즘이 또 따로있음

![](attachment:723522aa-527c-49b7-a135-44361fbed718:image.png)

해시값 비슷하면 가까운거네 이거 sorted set에 넣으면 됨 정렬하면 가까운거 순서대로 있으니깐

![](attachment:62bf9e1b-d188-44d3-9de7-928f213c28aa:image.png)

좌표 간 거리 구하기도 할 수 있음

![](attachment:fe5089c1-8c65-493f-b8c8-e6bed9bbb416:image.png)



### rate limiting

INCR 사용해서 하는게 제일 쉬움
  - ttl 동안 INCR 계속 증가시킬 수 있게 하고(1,2,3…) ttl 지나면 다시 0 되도록 하는 전략

token bucket을 사용하는것도 됨

![](attachment:9bf64fa7-465a-4306-96b0-c850c6707b02:image.png)

  - 그냥 통 만들어서 안에서 마지막 업뎃시간 토큰 개수 이런거 업데이트 하는거



