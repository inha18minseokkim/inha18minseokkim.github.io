---
title: "mediation 도입기 - 높은 부하 상황에서 자원 사용량"
date: 2024-12-02
tags:
  - 개발
  - 아키텍처
  - Java
category:
  - 실무경험
---
Mediation 패턴 구현 과정 정리.
### 상황

현재 TPS 200정도 쏘니깐 cpu 사용률이 70~90 사이로 왔다갔다 함. api 호출 유형을 늘리면 100% 넘어가서 죽지도 살지도 않아버릴 때가 있음.


### 원인, 또는 개선사항이라고 생각되는 부분

1. openfeign 조합하는 부분을 너무 복잡하게 하였나
2. 스테이징 환경의 빈약한 자원? (운영은 파드 4개, 스테이징은 2개)
3. httpclient 설정을 바꾸기
  1. 이부분은 토스페이먼츠 블로그를 참조함
    1. [https://toss.tech/article/engineering-note-3](https://toss.tech/article/engineering-note-3)
  2. 다만 이미 JDK17을 사용하여 Java Standard Http를 사용해서 동시성 문제가 생기는것 같지는 않다.
    1. ReactorFeign.Builder의 Client.class를 뜯어보면 Clilent.Default는
    2. HttpUrlConnection을 사용중

```java
 HttpURLConnection convertAndSend(Request request, Request.Options options) throws IOException {
            URL url = new URL(request.url);
            HttpURLConnection connection = this.getConnection(url);
            if (connection instanceof HttpsURLConnection) {
```

    3. 그런데 어차피 jdk 17 이상의 java standard http 라이브러리는 synchronized문제 해결한것 같아 차이는 없지만 실제 prod 환경에서 기본 httpurlconnection 사용하지 말라는 글을 봄
    4. ‣
> The current default Client is the JDK provided, notoriously slow `HttpURLConnection`. We don't recommend using the `Default` Client implementation except for development and prototyping. It lack most of the benefits provided by the more robust solutions like Apache and OkHttp. This is almost certainly the reason for the disparity.

1. 일단 mediation 파드의 cpu 점유율이 7~90%로 유지되는데, 만약 POD가 4배가 되면 cpu 점유율이 유의미하게 내려갈까.
  - ⇒다행히 40% 이하로 내려감.


