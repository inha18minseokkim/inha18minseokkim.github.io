---
title: Servlet ThreadLocal vs Netty Context
date: 2025-03-23
tags:
  - Webflux
  - JPA
  - Spring
---

## Servlet ThreadLocal

Java에서 지원하는 Thread Safe기술, 멀티 스레드 환경에서 개별 스레드에게 별도의 저장공간 할당하여 별도 상태를 갖게 함.

```java
HttpServletRequest httpServletRequest = ((ServletRequestAttributes)RequestContextHolder.getRequestAttributes()).getRequest();
```

보통 이런식으로 RequestContextHolder를 사용해서 Tomcat의 ThreadLocal 변수를 추출한다


```java
/**
 * Process this request, publishing an event regardless of the outcome.
 * <p>The actual event handling is performed by the abstract
 * {@link #doService} template method.
 */
protected final void processRequest(HttpServletRequest request, HttpServletResponse response)
		throws ServletException, IOException {

```

HttpServlet에서 processRequest부. 여기서 Servlet으로 부터 리퀘스트를 받아서 처리하는부

Spring AOP를 활용해서 다음과 같은 로직을 작성할 수 있음.

```java
@Aspect
@Component
@RequiredArgsConstructor
@Slf4j(topic="PreProcess")
public class PreProcess {
    @Pointcut("@within(org.springframework.web.bind.annotation.RestController)")
    private void preProcess() {

    }
    @Before("preProcess()")
    public void doProcess(JoinPoint joinPoint){
        ServletRequestAttributes requestAttributes = (ServletRequestAttributes) RequestContextHolder.getRequestAttributes();
        //HTTP 리퀘스트가 아닌 경우 그냥 보내, TOBE : GUID 채번 및 생성(서비스단에서 업무가 시작하는 로직이 생기는 경우)
        if(requestAttributes == null) return;

        //헤더에서 가져온 GUID를 Context 객체에 셋팅해줌
        HttpServletRequest request = requestAttributes.getRequest();
        String userId = request.getHeader("userId");
        String createDate = request.getHeader("createDate");
        CommonContextHolder.setHeader(new CommonContext(userId,createDate));
        log.info("@@@@@@@@@@@@@@@@@@@@@@@@@@");
        log.info(CommonContextHolder.getHeader().toString());
    }
}
```

ServletRequest에 바인딩된 리퀘스트 변수를 받는다(1Request = 1Thread(Logical) = 1ThreadLocal)
request에서 헤더부를 추출한다(케이뱅크로 따지면 staffId, custId, mciIntfId 이런거)
CommonContext 라는 ThreadLocal 변수에 저장함
DB 저장 시 GUID 채번시 사용함

![[Pasted image 20260225083518.png]]

즉 MVC의 기본 요청은 1 요청 1 스레드
WAS는 Thread를 효율적으로 관리하기 위해 Thread와 ThreadPool을 생성한다 - (Tomcat의 기본 쓰레드 갯수 200이다)
HTTP 요청이 들어오면 요청은 Queue에 적재되고, ThreadPool 내의 특정 Thread가 Queue에서 요청을 가져와 처리하게된다
이 때, 일반적인 HTTP 요청은 처음부터 끝까지 동일한 Thread에서 처리된다
레이어드 아키텍처라면 1 request = 1 thread = Controller-service-repostiory 같은 쓰레드이다
HTTP 요청 처리가 끝나면 Thread는 다시 ThreadPool에 반납된다.
즉, WAS의 최대 동시 처리 HTTP 요청의 갯수는 ThreadPool의 갯수와 같다.


### 사용시 주의점

Tomcat은 Thread Pool 기반으로 동작함. 스레드 호출이 끝난 다음 clear 하지 않으면 다음 리퀘스트에서 재사용 가능함.

![[Pasted image 20260225083523.png]]

Thread 갯수를 늘리면 동시 처리 갯수가 늘어나겠지만, 쓰레드 끼리의Context switching에 의한 오버헤드도 커지기 때문에 성능이쓰레드 갯수에 비례해서 선형적으로 증가하지는 않는다.
오히려 많은 쓰레드 자체를 관리하는 오버헤드도 커지기 때문이다.

그래서 도입된 것

## Netty Context


![[Pasted image 20260225083614.png]]


<<싱글 스레드 상황>> 에서 N개의 요청을 처리해야 함.

```java
public interface ServerHttpRequest extends HttpRequest, ReactiveHttpInputMessage {
    String getId();

    RequestPath getPath();

    MultiValueMap<String, String> getQueryParams();

    MultiValueMap<String, HttpCookie> getCookies();
    .....
    public interface Builder {
        Builder method(HttpMethod httpMethod);

        Builder uri(URI uri);

        Builder path(String path);

        Builder contextPath(String contextPath);

        Builder header(String headerName, String... headerValues);
```

HttpServletRequest와 대응되는 인터페이스

```java
public interface ServerWebExchange {
    String LOG_ID_ATTRIBUTE = ServerWebExchange.class.getName() + ".LOG_ID";

    ServerHttpRequest getRequest();

    ServerHttpResponse getResponse();
```

를 스프링 webflux에서 바인딩하는 ServerWebExchange

실제로 이런식으로 context propagation 사용함.

```java
@Component
@Slf4j
class KbankHeaderToContextFilter : WebFilter {
    private var log = logger()
    override fun filter(exchange: ServerWebExchange, chain: WebFilterChain): Mono<Void> {
        return chain.filter(exchange)
                .contextWrite { e: Context ->
                    //Webflux 기반 컨트롤러로 들어온 요청의 헤더를 context write 함
                    val singleValueMap = exchange.request.headers.toSingleValueMap()

                    log.debug("chain Header from stock-gateway {}", singleValueMap["kbank_standard_header"])
                    e.put("kbank_standard_header", singleValueMap["kbank_standard_header"]!!)
                }
    }
}

```



### 덕분에 JPA를 사용하지 못한다.


![[Pasted image 20260225083632.png]]

출처) 위의 [DataSourceTransactionManager](https://docs.spring.io/spring-framework/docs/current/javadoc-api/org/springframework/jdbc/datasource/DataSourceTransactionManager.html) 클래스의 문서
 DataSource로 부터 현재 스레드에 JDBC Connection을 바인딩해서 잠재적으로 DataSource당 하나의 스레드를 연결하게 된다. 
여기서 `현재 스레드` 라는 것은 실행 중인 스레드를 의미한다. 일반적인 경우 아마도 `main-thread` 일 것이고, 그게 아니라면 비동기 처리 메서드를 호출한 `thread` 가 될 것이다.
즉 JPA는 Thread Safe 하다.
Thread Safe 하다는건, 동시성 처리에 있어서 스레드를 사용하지 않는경우 동시성 처리가 보장이 되지 않을 수도 있음.
따라서 JPA 를 사용하는것이 아니라 R2dbc 같은 기술을 사용해야 함.

Jdbc TransactionManager만 보더라도 이런식으로 ThreadLocal로 구현되어 있음.
결국 이렇게 `ThreadLocal` 에서 Connection이 관리된다는 것은 `Transaction 은 하나의 쓰레드에서 시작해서 종료되어야 한다` 라는 것을 의미하게 된다.

```java
public abstract class TransactionSynchronizationManager {
    private static final Log logger = LogFactory.getLog(TransactionSynchronizationManager.class);
    private static final ThreadLocal<Map<Object, Object>> resources = new NamedThreadLocal("Transactional resources");
    private static final ThreadLocal<Set<TransactionSynchronization>> synchronizations = new NamedThreadLocal("Transaction synchronizations");
    private static final ThreadLocal<String> currentTransactionName = new NamedThreadLocal("Current transaction name");
    private static final ThreadLocal<Boolean> currentTransactionReadOnly = new NamedThreadLocal("Current transaction read-only status");
    private static final ThreadLocal<Integer> currentTransactionIsolationLevel = new NamedThreadLocal("Current transaction isolation level");
    private static final ThreadLocal<Boolean> actualTransactionActive = new NamedThreadLocal("Actual transaction active");
}
```

