---
title: 구조 (202401 ver,Kbank MSA 최초 오픈 시점)
date: 2024-03-11
tags:
  - 주식서비스
  - 케이뱅크
  - 개발
  - 아키텍처
category:
  - 실무경험
---

![이미지](/assets/images/Pasted%20image%2020260226115448.png)

현재 MCI의 어댑터는 한 개(STK 주제업무폴더에 있는 서비스 인터페이스 코드들은 모조리 /convenience/stock/api-gateway로 찌름) MCI는 무조건 Post only
api-gateway에서 post를 그대로 받아서 body에 있는 케이뱅크 표준 전문 헤더를 뜯어 mci인터페이스 아이디 찾아서 api-gateway 내부에 있는 enum 정보를 갖고 uri 조립
  - 호출 경로(RestController의 uri), 호출방식(GET/POST), 변수넘겨주는방법(pathVariable/queryParam) 을 enum에서 꺼내와서 후속 filter로 조립
  - Post body에 json으로 이런식으로 들어가있음

```java
{"haeder_part" : {
		"mciIntfId" : "CSVSTK1000005",
		.....
	},
	"body_part" : {
		//대충 진짜 body 내용
	}
}
```

행내 표준이 MCI로 표준화되어있으므로 이런 제약조건이 있음
  - 채널에서 백엔드로 오려면 MCI 경로밖에 없음(현재)
    - MCI는 URI + json 기반이 아닌 서비스코드 + fixedLength 전문 교환 방식이므로 restful 설계에 제약
  - post only이므로 restful api 설계에 제약



## 개선 필요 사항

MCI 어댑터가 하나라 두 가지 경로를 찌를 수 없음(2024년 1월, MSA 오픈 당시 시점)
  - MCI의 CSV-STK 어댑터에 매핑되는 Uri는 convenience/stock/api-gateway 하나임
    - convenience/stock/ipo-service,convenience/stock/unlisted-stock 이런식으로 두 개 구성 불가(애초에 이게 됐으면 api-gateway가 이렇게 복잡하진 않을것)
    - 기존에는 ipo-service 하나라서 그냥 뒀는데 비상장 주식 서비스가 추가됨에 따라 body를 까서 uri 분기치는 로직 개발 필요
Redis에 의존적임
  - 이게 뭔소리인가 싶지만 처음 구축한 시점에는 각 서비스 파드가 redis에 의존적이었음
  - 현재 api-gateway에서 body 저장 →body 뜯어서 uri 조립 → ipo-service로 라우팅 → ipo-service에서 redis 찔러서 body 가져옴(redisTemplate) → guid 및 사용자 정보 가져오고 요청 수행 이런식
    - body에는 케이뱅크 표준헤더(http헤더 말고 케이뱅크 자체 메타정보,코드,guid기준정보 등등)와 실제 바디부분 있음.
  - 레디스가 단일 실패지점 될 수 있음. 현재 자원이 빵빵하지 못해서.. 레디스가 파드로 올라가있음. 가끔 메모리 오버플로우 문제 생김.
  - 레디스 가용성이 완벽하다고 해도 로컬테스트에서 문제가 생김(Aspect로 호출하는  레디스에서 body를 못가져옴, 로컬테스트할 때 하드코딩으로 박아넣거나 Aspect를 끄는 등 코드조작 필요함)
  - redis에서 가져오는게 아니라 api-gateway에서 헤더로 가져오게 짜볼 예정(Redis 저장도 하긴 할것, 비동기로)
    - body에 있는 "haeder_part" 를 실제 라우팅 할 때는 HttpHeader로 변환하여 넘길 예정
    - 전문 k:v 54개 쌍 중 MSA 환경에서 필요한 것만 addHeader 할 예정
    - 전문이 54개긴 하지만 실제로 사용하는 부분만 넘기면 그렇게 무겁지 않을 것
    - 물론 Locust로 부하테스트 해봐야함 ⇒ 이상없음 땅땅


