---
title: "JDK Dynamic Proxy Casting이슈"
date: 2023-12-05
tags: [미지정]
---
Bxm 프레임워크 쓰다가 에러를 발견하고 비슷한 이슈를 김영한 아저씨 강의에서 봐서 간단하게 끄적임


```java
@Slf4j
@SpringBootTest(properties = "spring.aop.proxy-target-class=true")
@Import(ProxyDIAspect.class)
public class ProxyDITest {
    @Autowired
    MemberService memberService;
    @Autowired
    MemberServiceImpl memberServiceImpl;

    @Test
    void go() {
        log.info("memberService class={}",memberService.getClass());
        log.info("memberServiceImpl class={}",memberServiceImpl.getClass());
        memberServiceImpl.hello("hello");
    }
}
```

이런식으로 되어있을 때, spring.aop.proxy-target-class=false로 주면
Jdk Dynamic Proxy를 사용하여 프록시 생성

```java
org.springframework.beans.factory.UnsatisfiedDependencyException: Error creating bean with name 'com.example.aop.proxyvs.code.ProxyDITest': 
Unsatisfied dependency expressed through field 'memberServiceImpl': Bean named 'memberServiceImpl' is expected to be of type 'com.example.aop.order.member.MemberServiceImpl' but was actually of type 'jdk.proxy3.$Proxy55'
```

원인은 Jdk Dynamic의 경우
인터페이스를 기반으로 새로운 프록시를 만듬. 그러므로 실제 Impl타입과는 형제(?)인 타입의 프록시가 만들어지므로 타입 호환이 되지 않음(서로 방계이므로)
CGLIB의 경우
구현체 Impl기반으로 새로운 프록시를 만듬. 그러므로 따지고보면 타입이 ImplImpl이겠지?? 직계 타입을 만들기 때문에 타입호환 됨.

비슷하게 카드계 Bxm에서 KbankApplicationContext.getBean을 이상한(?) 방식으로 호출하게 되면 com.sun.proxy.$Proxy  타입이라 클래스 타입이랑 맞지않는다는 이상한 소리를 함.
아마 JDK Dynamic Proxy를 내부적으로 사용해서 그런것같은데
문제는 Enhancer By CGLIB 로그가 찍히기도 한다
둘 다 사용하는건가..?
