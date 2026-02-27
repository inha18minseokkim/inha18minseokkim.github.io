---
title: mediation 패턴 도입기 - RECYCLE_FACADES
date: 2024-11-26
tags:
  - 개발
  - 아키텍처
  - Java
  - BFF
category:
  - 실무경험
---
Mediation 패턴의 RECYCLE_FACADES 설정 관련 정리.
### 이슈내용


헤더 전파를 위해 RequestInterceptor를 사용 시 

```
java.lang.IllegalStateException: The request object has been recycled and is no longer associated with this facade
	at org.apache.catalina.connector.RequestFacade.checkFacade(RequestFacade.java:857) ~[tomcat-embed-core-9.0.78.jar:9.0.78]
	at org.apache.catalina.connector.RequestFacade.getLocale(RequestFacade.java:426) ~[tomcat-embed-core-9.0.78.jar:9.0.78]
	at org.springframework.web.servlet.i18n.AcceptHeaderLocaleResolver.resolveLocale(AcceptHeaderLocaleResolver.java:102) ~[spring-webmvc-5.3.29.jar:5.3.29]
	at org.springframework.web.servlet.DispatcherServlet.lambda$buildLocaleContext$3(DispatcherServlet.java:1186) ~[spring-webmvc-5.3.29.jar:5.3.29]
	at org.springframework.context.i18n.LocaleContextHolder.getLocale(LocaleContextHolder.java:224) ~[spring-context-5.3.29.jar:5.3.29]
	at org.springframework.context.i18n.LocaleContextHolder.getLocale(LocaleContextHolder.java:205) ~[spring-context-5.3.29.jar:5.3.29]
	at io.github.luizimcpi.asynccontext.service.CarsService.processCarsByLanguage(CarsService.java:27) ~[classes/:na]
	at io.github.luizimcpi.asynccontext.service.CarsService$$FastClassBySpringCGLIB$$53476055.invoke(<generated>) ~[classes/:na]
	at org.springframework.cglib.proxy.MethodProxy.invoke(MethodProxy.java:218) ~[spring-core-5.3.29.jar:5.3.29]
	at org.springframework.aop.framework.CglibAopProxy$CglibMethodInvocation.invokeJoinpoint(CglibAopProxy.java:793) ~[spring-aop-5.3.29.jar:5.3.29]
	at org.springframework.aop.framework.ReflectiveMethodInvocation.proceed(ReflectiveMethodInvocation.java:163) ~[spring-aop-5.3.29.jar:5.3.29]
	at org.springframework.aop.framework.CglibAopProxy$CglibMethodInvocation.proceed(CglibAopProxy.java:763) ~[spring-aop-5.3.29.jar:5.3.29]
	at org.springframework.aop.interceptor.AsyncExecutionInterceptor.lambda$invoke$0(AsyncExecutionInterceptor.java:115) ~[spring-aop-5.3.29.jar:5.3.29]
	at java.base/java.util.concurrent.FutureTask.run(FutureTask.java:264) ~[na:na]
	at java.base/java.util.concurrent.ThreadPoolExecutor.runWorker(ThreadPoolExecutor.java:1136) ~[na:na]
	at java.base/java.util.concurrent.ThreadPoolExecutor$Worker.run(ThreadPoolExecutor.java:635) ~[na:na]
	at java.base/java.lang.Thread.run(Thread.java:833) ~[na:na]
```

위 에러 발생

사유는 이것도 어느정도 동시성 문제라고 생각되는데, 
  - mediation으로 request가 옴 
  - > 각 단위업무에 N개의 api 호출
    - 하면서 mediation에서 온 request header를 까서 N개의 비동기 호출에 header propagation
이러다보니  공통 인터셉터 부분에서 request를 가져올 때 이미 facade가 discard 되었는데 왜 가져오나 이런 느낌임. 비동기로 후속 호출들 하고 있는데 이미 앞에서 호출 끝나서 객체 참조가 불가능한 경우.

```java
@Component
@Slf4j
public class CurrentRequestHeadersInterceptor implements RequestInterceptor {
//케이뱅크 공통 헤더를 각 업무단에 propagate 하기 위한 인터셉터
	@Override
	public void apply(RequestTemplate requestTemplate) {
		ServletRequestAttributes requestAttributes = (ServletRequesAttributes)RequestContextHolder.getRequestAttributes;
		HttpServletRequest request = requestAttributes.getRequest;

```

그러므로 해결방법은 

```java
@Bean
TomcatConnectorCustomizer disableFacadeDiscard {
	return (connector) -> connector.setDiscardFacades(false);
}
```

discard 하지 않도록 하게 하면 된다.
> You are relying upon the request still be usable after its handling has completed which may not work reliably. You got away with it with Spring Boot 2.7 and Tomcat 9.x as Tomcat 9.x is less aggressive in its clean up when a request completes. This default [changed in Tomcat 10](https://github.com/apache/tomcat/commit/c7457dcbd2e7b347addfa204a33604435da9c4c6).

다만 톰캣이 이걸 true로 바꿨는데 내가 false로 다시 바꿔도 되나? 의문을 가짐
[Disadvantages of setting Tomcat's RECYCLE_FACADES = true?](https://stackoverflow.com/questions/57777941/disadvantages-of-setting-tomcats-recycle-facades-true)
일단 false로 되어있으면 재사용해서 gc 부담을 줄여주긴 해도 이상한 짓을 하면 공유가 되어버릴 수 있는 여지가 있으니 퍼포먼스 감소를(거의 없겠지만) 감수하고서라도 그냥 각 요청마다 새로 인스턴스를 만들어서 쓰는것이 좋아서 true로 하지 않았을까..
브로드컴 글에서는 이거 enable 해야 secure 해진다고 추천함.
> For secure sites, tomcat servers are required to have RECYCLE_FACADES enabled
[How to Configure Tomcat and Enable RECYCLE_FACADES](https://knowledge.broadcom.com/external/article/219611/how-to-configure-tomcat-and-enable-recyc.html)


톰캣 공식문서 보고 
[Apache Tomcat 9 (9.0.97) - Changelog](https://tomcat.apache.org/tomcat-9.0-doc/changelog.html#Tomcat_9.0.97_(remm))

![](https://prod-files-secure.s3.us-west-2.amazonaws.com/c38aebd7-2834-4fac-b2fc-a2f0c17ce81d/c0436449-be41-4a21-9424-6cbdba482f6e/image.png)

톰캣 9버전부터 RECYCLE_FACADES는 true가 기본값으로 설정되었다고 한다.
  - 그러니깐 RECYCLE_FACADES의 기본값이 true로 바뀜 > Connector의 discardFacades 프로퍼티에 영향 줌 왜냐하면 이 설정을 기본으로 따르도록 하고있음. > 그래서 별설정 안하면 해당 Facade 객체는 자동으로 버려짐 

![](https://prod-files-secure.s3.us-west-2.amazonaws.com/c38aebd7-2834-4fac-b2fc-a2f0c17ce81d/4b81570e-d6ae-47d8-a068-2bb55d7794dd/image.png)



일단 RequestFacade와 톰캣 관련해서 좀 더 알아보고
[Tomcat의 RequestFacade, ResponseFacade 클래스 - 안전하게 Request, Response 전달하기](https://acafela.github.io/tomcat/2021/01/18/tomcat-facade.html)
[[Middleware] Tomcat이요청/응답을 처리하는 법](https://developer-nyong.tistory.com/69)
[[Spring] HttpServletRequest 요청마다 같은 주소값을 반환하는 이유](https://dongs-record.tistory.com/44)
[http 요청을 보낼때마다 request, response 객체의... - 인프런 | 커뮤니티 질문&답변](https://www.inflearn.com/community/questions/307198/http-%EC%9A%94%EC%B2%AD%EC%9D%84-%EB%B3%B4%EB%82%BC%EB%95%8C%EB%A7%88%EB%8B%A4-request-response-%EA%B0%9D%EC%B2%B4%EC%9D%98-%EC%A3%BC%EC%86%8C%EA%B0%92%EC%9D%B4-%EB%B3%80%ED%95%98%EC%A7%80-%EC%95%8A%EB%8A%94-%EC%9D%B4%EC%9C%A0)
