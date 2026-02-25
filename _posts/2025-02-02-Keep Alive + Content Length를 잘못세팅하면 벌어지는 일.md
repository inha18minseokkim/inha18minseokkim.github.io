---
title: Keep Alive + Content Length를 잘못세팅하면 벌어지는 일
date: 2025-02-02
tags:
  - HTTP
  - 이슈정리
---
갑자기 생각나서 글 써봄(20250202)
3달전쯤에 mediation 파드를 만들 때 Header Propagation을 하려고 하던 중, 가끔(아니 자주) 요청들이 5번 이상 와바박 호출되는 현상이 발생했었다. 이 때 왜 이랬었는지 곰곰히 생각해보니 기존 로직은 
1. 클라이언트로부터 온 헤더를 K,v 쌍으로 모두 forEach 돌린다
2. 현재 ThreadLocal객체 변수에다가 “모두” 다 집어넣는다
3. 다른 파드로 호출 시(그당시에는 openfeign) requestInterceptor에서 ThreadLocal 변수에 있던 값들을 헤더에 적재해서 호출한다
이렇게 하니 갑자기 어떤 호출의 경우 한 번 호출했는데 말단 파드로 여러 번 연속해서 호출하는 경우가 나왔다.
 생각해보니 클라이언트에서 가져왔던 헤더를 모두 다 넘겨주는데, 넘겨주면 안되는 정보들이 있었다. 

그 중 하나가 Content-Length.
Content Length의 경우 body 길이를 호출 할 때 계산해서 헤더에 적재하고 보내주는데, 클라이언트에서 온 바디의 content Length를 그대로 foreach에 섞어서 새로 만들어야 하는 헤더에 써버리니 실제 body size와 내가 임의로 적어서 제출한 content length가 달라짐.
그런데 아마 당시 httpclient를 apache hc5로 썼을거임. 비동기 호출 지원하고 처리량 면에서 유리하다는것을 미루어 보아 최소 http 1.1 이상을 사용할 것 내지는 그게 아니더라도 커넥션을 유지하는 keep alive를 사용할 것인데 Keep Alive 를 사용하는 경우 정확한 Content Length를 사용해라고 한다.
  - [nGrinder에 적용한 HttpCore 5와 HttpClient 5 살펴보기](https://d2.naver.com/helloworld/0881672)
  - 윗글을 보면 HTTP/1.1 , 서버가 지원하는경우 2를 쓴다고 함

[[HTTP] keep alive란? (persistent connection에 대하여)](https://etloveguitar.tistory.com/137)

아마 이것때문에 Content Length 만큼 body가 들어오지 않아 커넥션이 닫히지 않은 상태에서 뭔가 잘못 작동해서 호출이 여러 번 나간듯 하다.
