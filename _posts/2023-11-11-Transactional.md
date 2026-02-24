---
title: Transactional
date: 2023-11-11
tags:
  - Spring
  - JPA
  - Spring-Data
---
트랜잭션을 처리하는 객체와 비즈니스 로직을 완벽하게 분리 가능

```java
public void logic() {
	TransactinoalStatus status = transactionManager.getTransaction(..);
	try{
		//비즈니스
		target.logic();
		transactionManager.commit(status); //성공 시 커밋
	} catch(Exception e) {
		transactionManager.rollback(status); //실패시 롤백
		throw new IllegalArgumentException(e);
	}
}
```

문제상황 Tracing
기존 DBConnection(DriverManager)를 통해 DB 접근 시 로직이 DBMS 종류마다 다 다름 → DataSource 표준 등장해서 각 벤더들은 여기다 다 맞춰라
  - →DataSource를 통해 커넥션풀을 생성하여 더이상 DB 커넥션에 비즈니스가 의존하지 않는것까지는 좋은데 트랜잭션을 관리할 때 DataSource를 통해서 커넥션을 얻고 setAutoCommit 설정하고 트랜잭션을 얻고 하는 행위들이 덕지덕지 더러워 
    - → PlatformTransactionManager를 바라보게 하고 getTransaction commit rollback 을 표준화 함. 이 표준만 지켜서 비즈니스 로직 구현하면 됨 
      - → 비즈니스 로직은 이제 PlatformTransactionManager를 바라봐서 이제 비즈니스 로직이 DataSource를 바라보지 않아도 된다. 그런데 비즈니스 로직에 여전히 PlatformTransactionManager가 덕지덕지 붙어있다
        - →TransactionTemplate를 사용하여 덕지덕지 붙어있는걸 정리해준다 (execute,executeWithoutResult 안에 람다식으로 넣으면 나머지 트랜잭션 처리는 알아서 해줌)
          - →근데 덕지덕지는 아닌데 여전히 TransactionTemplate이 비즈니스 로직에 묻어있다

트랜잭션 프록시에 Target Business 로직을 호출하면 로직 호출 이전에 트랜잭션 획득 → 실제 비즈니스 호출 → 별문제 없으면 커밋, 예외있으면 잡아서 롤백 → 트랜잭션 회수 이런식으로 비즈니스 안건들고 호출 가능
덕분에 서비스 계층에 순수한 비즈니스 로직만 남을 수 있음
이걸

```java
public void accountTransfer(String fromId, String toId, int money) throws SQLException {
        txTemplate.executeWithoutResult((status) -> {
            //비즈니스 로직
            try {
                bizLogic(fromId, toId, money);
            } catch (SQLException e) {
                throw new IllegalStateException(e);
            }
        });
    }
```

이렇게

```java
@Transactional
public void accountTransfer(String fromId, String toId, int money) throws SQLException {
    bizLogic(fromId, toId, money);
}
```

트랜잭션 걸고 시작 할 수 있음
아 물론 스프링 컨테이너 안쓰면 안됨 ㅋㅋ 빈등록해야함

AOP 체크

```java
@Test
void AopCheck() {
    log.info("memberService class={}", memberService.getClass());
    log.info("memberRepository class={}", memberRepository.getClass());
    Assertions.assertThat(AopUtils.isAopProxy(memberService)).isTrue();
    Assertions.assertThat(AopUtils.isAopProxy(memberRepository)).isFalse();
}
```

@Transactional 붙어있으면 빌드하고 실행할 때 스프링 컨텍스트가 AOP 대상이면 프록시 상속받는 클래스로 코드 만들어서 그걸로 실행시켜버림
