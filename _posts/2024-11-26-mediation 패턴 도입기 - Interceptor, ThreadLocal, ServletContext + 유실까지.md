---
title: "mediation 패턴 도입기 - Interceptor, ThreadLocal, ServletContext + 유실까지"
date: 2024-11-26
tags: [미지정]
category:
  - 기타
---

### Interceptor 도입 사유

MCI에서 오는 케이뱅크 공통 헤더를 후의 말단 엔드포인트 헤더까지 전달하기 위해(CRUD시 이력 필요)

그러므로 api-gateway에서 post body의  header_part 에서 넘어온 HttpHeader를 그대로 전달한다
 

```java
@Component
@Slf4j
public class CurrentRequestHeadersInterceptor implements RequestInterceptor {
//케이뱅크 공통 헤더를 각 업무단에 propagate 하기 위한 인터셉터
	@Override
	public void apply(RequestTemplate requestTemplate) {
		ServletRequestAttributes requestAttributes = (ServletRequesAttributes)RequestContextHolder.getRequestAttributes();
		HttpServletRequest request = requestAttributes.getRequest();
		request.getHeaderNames().asIterator()
			.forEachRemaining(h -> requestTemplate.header(h, request.getHeader(h)));
	}
}
```


```java
@Bean
public OverseasStockService overseasStockService() {
	return ReactorFeign.builder()
	.decoder(new ReactorDecoder(jacksonDecoder())
	.encoder(new JacksonEncoder())
	.requesInterceptor(currentRequestHeadersInterceptor)
	.target(OverseasStockService.class, overseasStockServiceEndpointt);
}
```


다만 우리는 OpenFeign - Reactive를 사용하므로 다른 스레드에서도 ServletContext를 참조해야 함.
다음과 같은 설정 필요

```java
@Bean
public TomcatConnectorCustomizer disableFacadeDiscard() {
	return connector -> connector.setDiscardFacades(false);
}
```

[Multi-thread에서 RequestContextHolder 전달해서 사용하는 방법::LEAPHOP TECH BLOG](https://blog.leaphop.co.kr/blogs/38/Multi_thread%EC%97%90%EC%84%9C_RequestContextHolder_%EC%A0%84%EB%8B%AC%ED%95%B4%EC%84%9C_%EC%82%AC%EC%9A%A9%ED%95%98%EB%8A%94_%EB%B0%A9%EB%B2%95)
[threadContextInheritable](https://findmypiece.tistory.com/126)


### 이슈 : POST를 할 때 여러 번 나간다

단순한 이슈임. 사유는 Interceptor에서 기존 Header에서 넘어온 Body의 Content-Length 까지 같이 넘겨줘서 커넥션 맺고 요청 후 body 길이가 맞지 않아 바디만큼 더 받기 위해 연결을 유지하면서 요청이 더 간듯 함.
Interceptor에서 Content-Length만 삭제한 다음 요청 시 알아서 계산하도록 넘겨주면 해결. 

```java
@Component
@Slf4j
public class CurrentRequestHeadersInterceptor implements RequestInterceptor {
//케이뱅크 공통 헤더를 각 업무단에 propagate 하기 위한 인터셉터
	@Override
	public void apply(RequestTemplate requestTemplate) {
		ServletRequestAttributes requestAttributes = (ServletRequesAttributes)RequestContextHolder.getRequestAttributes();
		HttpServletRequest request = requestAttributes.getRequest();
		requestTemplate.removeHeader("content-length");
		request.getHeaderNames().asIterator()
			.forEachRemaining(h -> requestTemplate.header(h, request.getHeader(h)));
	}
}
```




### 이슈 : 가끔 업무단으로 요청 보낼 때 NullPointerException과 함께 유실이 난다


```java
org.apache.coyote.http11.Http11Processor process
        SEVERE: Error processing request
        java.lang.NullPointerException
        at org.apache.tomcat.util.http.MimeHeaders.clear(MimeHeaders.java:152)
        at org.apache.coyote.Response.reset(Response.java:292)
        at org.apache.catalina.connector.Response.reset(Response.java:659)
        at org.apache.catalina.valves.ErrorReportValve.invoke(ErrorReportValve.java:119)
        at org.apache.catalina.core.StandardEngineValve.invoke(StandardEngineValve.java:109)
        at org.apache.catalina.connector.CoyoteAdapter.service(CoyoteAdapter.java:293)
        at org.apache.coyote.http11.Http11Processor.process(Http11Processor.java:861)
        at org.apache.coyote.http11.Http11Protocol$Http11ConnectionHandler.process(Http11Protocol.java:606)
        at org.apache.tomcat.util.net.JIoEndpoint$Worker.run(JIoEndpoint.java:489)
        at java.lang.Thread.run(Thread.java:748)
```

대충 이런느낌. 헤더 네임을 가져오는데 NULL이라고 뜸
뭔가 

비슷한 증상
느낌상 동시성 문제인데.. 1개의 호출 > N개의 호출을 reactorFeign 사용하여 비동기호출을 함.
~~딱 여기서 헤더 세팅을 복사할 때 request.getHeaderNames().asIterator() 이 부분 전후로 동시성문제가 생기는것같음. 복사하고 있을 때 이미 컨텍스트가 끝나버린다던가 하는..~~
  - 20241210 추가) 이거 iterator라서 생기는 문제 아님. 내가 단단히 Interceptor를 잘못 사용하고 있었음.
그래서 수동으로 세팅해주니깐 문제가 사라짐.

```java
@Component
@Slf4j
public class CurrentRequestHeadersInterceptor implements RequestInterceptor {
//케이뱅크 공통 헤더를 각 업무단에 propagate 하기 위한 인터셉터
	@Override
	public void apply(RequestTemplate requestTemplate) {
		ServletRequestAttributes requestAttributes = (ServletRequesAttributes)RequestContextHolder.getRequestAttributes();
		HttpServletRequest request = requestAttributes.getRequest();
//		requestTemplate.removeHeader("content-length");
//		request.getHeaderNames().asIterator()
//			.forEachRemaining(h -> requestTemplate.header(h, request.getHeader(h)));
			requestTemplate.header("Log-level",request.getHeader("Log-level"));
			requestTemplate.header("rcvSrvcCd",request.getHeader("rcvSrvcCd"));
			requestTemplate.header("mciIntfId",request.getHeader("mciIntfId"));
			requestTemplate.header("tlgrWrtnDt",request.getHeader("tlgrWrtnDt"));
			requestTemplate.header("staffId",request.getHeader("staffId"));
			requestTemplate.header("tlgrCrtnSysNm",request.getHeader("tlgrCrtnSysNm"));
			requestTemplate.header("tlgrSrlNo",request.getHeader("tlgrSrlNo"));
			requestTemplate.header("tlgrPrgrsNo",request.getHeader("tlgrPrgrsNo"));
	}
}
```

케이뱅크 공통헤더 오십몇개 중 사용하는 부분이 몇개 없고 변할일이 없어서 그냥 하드코딩 해도 무방할듯.
후에 enum으로 묶어서 loop 돌릴 예정.

일단 문제는 해결했는데 비슷한 사례 문서를 찾아보려는데 잘 안찾아짐.

