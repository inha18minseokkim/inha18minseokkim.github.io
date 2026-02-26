---
title: MCI2api-gateway 개선(spring-cloud) 삽질기
date: 2024-03-21
tags:
  - 주식서비스
  - SCG
  - Spring-Cloud
  - 아키텍처
  - 개발
  - 케이뱅크
category:
  - 실무경험
---

![이미지](/assets/images/Pasted%20image%2020260226115739.png)

여기서 구조를 봤을 때 
MCI(채널) 단위업무 편의서비스(convenience)/주식(STK) 에 대응하는 어댑터는 단 한개
MCI 어댑터에서 NLB에 찌르는 Path는 하나(aws-eks-주소/convenience/stock/api-gateway)

기존에 api-gateway에서는 공모주 서비스(ipo-servie) 한 가지만 라우팅 해주고 있었음
즉, convenience/stock/api-gateway/ipo-service 를 찌름
다만 여기서 convenience/stock/api-gateway/unlisted-stock-service가 추가된다면 문제가 생김

예를들어, 예시코드를 보면(현재 이런느낌으로 되어있음)

```java
@Bean
public RouteLocator routeLocator(RouteLocatorBuilder builder) {
  return builder.routes()
      .route(p -> p.path("/stock/api-gateway")
      .filters(
	      f -> f.setPath("/messageChannel/events")
	      /*
	      여기서 mci에서 Post로 온(MCI는 POST Only) HttpRequest 받아서 1. body에 있는
		    케이뱅크 표준 헤더를 까서 MCI인터페이스/서비스코드 열어서 이 요청이 GET/POST인지 다시 식별 후
		    코드에 맞는 요청 생성하는 필터 있음
		    2. body의 실제 Data 부분에 있는 json을 꺼내서 pathVariable/queryParam으로 uri 조립하는
		    필터 있음 
		    3. 요청정보 postgre repository 및 redis repository에 저장하는 필터 있음
	      */
      )
      .uri("http://ipo-service.convenience.default.svc.cluster.local"))//여기로 라우팅
      .build();
}

```

여기서 이렇게 됨

```java
@Bean
public RouteLocator routeLocator(RouteLocatorBuilder builder) {
  return builder.routes()
    .route(p -> p.path("/stock/api-gateway")
      .filters(
	      f -> f.setPath("/messageChannel/events")
				//대충 그 로직
      )
      .uri("http://ipo-service.convenience.default.svc.cluster.local"))//여기로 라우팅
    .route(p -> p.path("/stock/api-gateway")
      .filters(
	      f -> f.setPath("/messageChannel/events")
				//대충 그 로직
      )
      .uri("http://unlisted-stock-service.convenience.default.svc.cluster.local"))//신규 업무 추가
     .build();
}
```

라우터 로직이 두 개가 됨. 실제로 routes() 쓰는 빌더 뜯어서 .route() 호출하는 부분 보면 리스트로 되어서 add 함.
문제는 path 저기가 booleanSpec으로 되어있는데 그럼 라우팅 리스트에서 필터링 할 때 predicate filter 같은 느낌으로 필터를 할것.
다만 현재 구조라면 uri path로 필터링을 할 때 항상 true 이므로(”/stock/api-gateway” 둘 다 똑같음) 무조건 첫 번째 .route 된 곳으로 uri가 빠질것임(위 구조라면 ipo-servie로 항상 빠짐)  실제로 위아래 순서 바꾸면 Unlisted-stock-service로 계속 빠짐
원래 RouteLocator의 사상은 라우팅을 할 때 path가 다르다면 다른 서비스 uri 로 라우팅 하려고 만든 라이브러리인것같은데
문제는 행 MCI 어댑터가 하나(더 늘리면 개발속도가 안남)이므로 해당 어댑터는 무조건 고정된 path로 찌름. 
  - 그리고 우리는 body 부분의 케이뱅크 표준 헤더에 있는 서비스코드를 기준으로 어디로 라우팅할지를 식별함
    - 그러므로 다른것 없이 path() 하나로 위 모듈을 사용하는것은 애초에 논리적으로 말이 안되는거였다
      - 알았으면 진작에 이렇게 안만들었겠지만..스프링에서 라우팅하는건 처음이니깐….

다만 .path() 옆에 .찍으니깐 booleanSpec 타입으로 리턴하는 함수들이 많아서 몇 개 찍어봤는데 바디값을 가져올 수 있을 것 같아서 

```java
@Bean
public RouteLocator routeLocator(RouteLocatorBuilder builder) {
  return builder.routes()
      .route(p -> p.path("/events").and().method(HttpMethod.POST).and().
          readBody(Event.class, eventPredicate("message.channels")).
          filters(f -> f.setPath("/messageChannel/events")).uri("lb://messageChannel"))
      .route(p -> p.path("/events").and().method(HttpMethod.POST).and().
          readBody(Event.class, eventPredicate("message"))
          .filters(f -> f.setPath("/message/events")).uri("lb://message"))
      .build();
}

```

요런식으로 시도해봐야할것같음. body에서 서비스코드 까보고 ipo-service로 라우팅 할 지 unlisted-stock-service로 라우팅 할 지 결정하는걸로.
다만 이부분은 코드가 지저분해질 수 있으므로(심지어 8월에 주식 Namespace에 신규 단위업무 추가 예정) Enum을 사용해서 잘 정리해놔야할듯 함. 끝.


### +추가(20240322) 저렇게 못함

저런식으로 하니깐 .readBody가 request flux(stream)를 열어서 바디부분을 가져와버림. 
  - body가 flux로 되어있어 한번밖에 못씀
그래서 readBody 뒤에 filter에서 cacheRequestBody()를 호출하는데 **requestBody가 null이라 null이 저장되고 후속에서 mci 정보 기반으로 라우팅 uri 조립하는 filter에서 이상한(?) 값을 꺼내와서 에러남.**

이런식으로 재현하면 exchange에서 캐시된 바디를 가져올 때 오류가 남(readBody할 때 flux 사용해서)
대충 예상했던 그림

```java
@Bean
    public RouteLocator SimpleRouteLocator(RouteLocatorBuilder builder) {
        return builder.routes()
        //바디에 1 들어가있으면 Ipo service로 라우트
          .route("ipo-service", p-> p.path("/api-gateway/**").and()
                    .readBody(String.class, body -> {//여기서 Flux 읽음
                        log.info(body);
                        return body.contains("1");
                    })
                    .filters((f->f.cacheRequestBody(String.class) //소모된 값을 저장
                                .filter((exchange, chain) -> {
                                    String finalUrl = "http://localhost:8881/api-gateway/A";
                                    //여기서 캐시를 읽어올 때 문제생김
                                    ServerHttpRequest build = exchange.getRequest().mutate().uri(URI.create(finalUrl)).build();
                                    return chain.filter(exchange.mutate().request(build).build());
                                })
                    )
                    )
            .uri("http://127.0.0.1:8881/")
          )
        //2 들어가있으면 비상장으로 라우트
          .route("unlisted-stock-service", p->p.path("/api-gateway/**").and()
                    .readBody(String.class, body -> {
                        log.info(body);
                        return body.contains("2"); 
                    })
                    .filters(f->f.cacheRequestBody(String.class)
                            .filter((exchange, chain) -> {
                                String finalUrl = "http://localhost:8881/api-gateway/B";
                                ServerHttpRequest build = exchange.getRequest().mutate().uri(URI.create(finalUrl)).build();
                                return chain.filter(exchange.mutate().request(build).build());
                            })
                    )
	          .uri("http://127.0.0.1:8882/")
          )
          .build();
    }
```

이렇게 하면 boolean으로 분기 치는 곳은 잘 타지만, 실제 cacheRequestBody가 정상적이지 않고 exchange에서 꺼내보면 에러남(주석처리).
  - readBody 부분에서 꺼낸 다음 레디스로 저장, 후속 필터에서 JVM 메모리 말고 레디스 값을 꺼내오게 하면 되겠지만 이러면 네트워크쪽에 부하가 갈듯 + 현재 자원상황에서 레디스 뻗을 수도 있음. ⇒ 레디스가 단일실패지점
    - 그리고 자바 Native Memory 영역에서 끝나는걸 굳이 네트워크 타고 레디스까지 꾸역꾸역 가는것도 이상함
20241027추가) 뭔가 jvm 메모리에 저장되어있던것을 가져오는 로직이 있는 것 같다.

그럼에도 불구하고 readBody는 지양할것이다..왜냐하면..

# no://op placeholder를 사용한 라우팅


정리는 해놓았지만, 가급적이면 사용하고 싶지 않음
이유는 다음과 같음
1. predicate에서 booleanSpec을 활용하여 각각에 해당되는 라우터 필터로 가지 않고 하나의 필터에서 분기로 처리함
  1. 이렇게 되면 문제가 각각의 타겟 서비스(공모주서비스,비상장서비스 등..)에서 개별로 대응해야 하는 로직이 발생하는 경우 하나의 필터에서 분기를 쳐야하는 상황이 발생할 수 있음
  2. 이렇게되면 코드가 복잡해짐
  3. 아 물론 그정도로 복잡해질만큼 대단한 서비스가 나올 것 같진 않음. 실시간성을 위해서 HTTP말고 소켓이나 RPC 정도도 분기쳐서 라우팅하는것 아니면..
2. spring cloud gateway의 의도와 맞지 않다
  1. /uri/path1 → /target1 , /uri/path2 → /target2 이런식으로 해놓으라고 만들어놓은 것 같은데
    - 억지로 끼워맞추려고 하는듯한 느낌 받음.

# no://op vs MCI 엔드포인트 추가 - 결론

결국 MCI 에서 uri 뒤에 서비스코드 붙이는 식으로 대응개발 해주신다고 함 
ASIS
  - /convenience/stock/api-gateway/ 
TOBE
  - /convenience/stock/api-gateway/CSVSTK200001 이런식으로
그러면 뒤에 있는 내용 파싱해서 enum화 하여 분기칠 수 있음.
  - 이렇게 결정한 이유는 readBody 하고 캐싱 수동으로 하고 할 수 있지만, 
  1. 특정 uri가 들어오면 해당 uri에 해당하는 후속 파드로 DownStream 하려고 route를 하는것이 RouteLocator의 본 사상과 의도라고 생각
  2. body를 읽어서(수동으로 Flux를 소모하면서) 맨 처음 uri를 바꾸면서까지 다른 uri로 라우팅하는것은 필터 조립로직이 상당히 복잡해짐
  3. 그리고 predicate에서 세부 업무 파드 분기를 하지 않으면 후에 uri를 활용해서 라우팅하는  규칙이 업무마다 달라질 때 코드가 더 복잡해질 수 있다.
    1. 뒤에 공통으로 적용되는 필터에 if문으로 업무마다 로직을 분기치는 로직이 들어갈 수도 있음.
  - 그러므로 MCI 솔루션에서 URI에 서비스코드 매핑을 해달라고 함. 


# uri Path를 이용한 라우팅





# 이행(2024.04.18)


### 이행계획

기존 공모주 서비스(ipo-service)는 convenience/stock/api-gateway 하나로 들어오고 있는 상황이므로 총 3가지 분기 로직이 필요하고 적용하였음. 만약 MCI에서 api-gateway로 uri가 오면
  1. convenience/stock/api-gateway/CSVSTK1~~~ ⇒ 공모주 서비스로
  2. convenience/stock/api-gateway/CSVSTK2~~~ ⇒ 비상장 서비스로
  3. convenience/stock/api-gateway/ ⇒ 공모주 서비스로(기존 로직)

왜냐하면 현재 공모주 서비스가 운영상황이고 api-gateway 는 변경건, 비상장 알림서비스는 신규 건이므로 api-gateway에서 3번 기존 로직을 걷어내면 장애남. 배포 완료 후 운영에 문제 없음이 판단되면 

그러므로 
  1. SRE 요청하여 Argo CD 상의 비상장주식 서비스 및 배치 > api-gateway 배포 > 공모주 서비스 정상접속 확인
  2. MCI 솔루션에서 서비스코드 매핑 기능 추가 > 공모주 서비스 정상접속 확인(iGate 엔드포인트 확인 필수)
  3. 프론트 배포 후 공모주메이트 + 비상장 서비스 둘 다 잘 되는지 확인
다른 절차는 다 바꿔도 이건 지켜야 장애가 나지 않음

## 이행 시 이슈사항

- MCI 솔루션 배포 시 약간 쫄린다(스테이징에서는 순단 없었음)
  - 구성이랑 솔루션 설명 기준 상 런타임 적용 가능하기는 한데 트래픽이 있긴해서(1+1=2인것을 믿어의심치 않지만 까기전까지는 모름. 깠을때 2 아니면 진짜 큰일남 카드고 뭐고 다안됨)
  - 왜냐하면 행 밖에서 오는 호출들은 다 여기로 들어오기 때문
- 재기동은 필요 없는데 혹시 이슈가 있을 수도 있음(영향도범위 : 계정계 CUI COR CRD) 레거시 공통모듈이라.. 이거 이슈생기면 입금 카드 다안됨
  - MSA 용으로 오퍼레이션 분리 가능한지 봐야됨(저번에는 이게 안되서 이런식으로 영향도 있는 구조가 됨)
    - ⇒ 2024.04.16 기준으로 오퍼레이션 분리 가능하다고 해서 별 문제 없고 야간작업 안해도됨
- 업체 문의 해놓고 만약 불안해서 안되면 18~19일 일자전환 시 한다(강제야간작업) 


### 투자홈 오픈 후 리팩토링 및 개선사항


mediation api pod를 도입하고 나서부터는 더 이상 사용할 필요가 없어짐.
  - 왜냐하면  MCI 서비스코드 → 타겟 api로의 라우팅 의 개념이 아니라
  - MCI 서비스코드 → 여러 api의 조합 의 개념으로 바뀌었기 때문
  - 서비스코드가 1은 공모주, 2는 비상장 이런식이 아니라 조합의 개념으로 바뀜
