---
title: "@Transactional(readOnly=True)를 막 쓰지 말자"
date: 2025-07-06
tags:
  - Spring
  - Spring-Data
---

# @Transactional(readOnly = true) 완벽 가이드: 언제 사용하고 언제 사용하지 말아야 할까?


## 1. 카카오페이 글에서 시작된 Transactional readOnly = True 논란

카카오페이 기술 블로그에서 흥미로운 발견을 공유했음1. 서비스에서 **`@Transactional(readOnly = true)`**를 무분별하게 사용했을 때 오히려 성능이 **2~3배 악화**되는 현상을 확인했음1.
문제의 핵심은 단순 단건 조회에서도 트랜잭션을 명시적으로 열면서 발생하는 **불필요한 네트워크 라운드트립**이었음. 실제로 하나의 SELECT 쿼리를 위해 최대 6개의 추가 쿼리(autocommit 설정, transaction 시작, commit 등)가 발생했고, 이로 인해 DB QPS 24K 중 set_option 쿼리가 14K를 차지하는 상황이 벌어졌음1.

## 2. MySQL에서 readOnly 옵션을 걸었을 때 생기는 문제점


## 불필요한 네트워크 라운드트립 증가

MySQL에서 **`@Transactional(readOnly = true)`**를 사용하면 다음과 같은 추가 쿼리들이 발생함1:
**`SET autocommit=0`** - 자동 커밋 비활성화
**`START TRANSACTION READ ONLY`** - 읽기 전용 트랜잭션 시작
실제 SELECT 쿼리
**`SET SESSION CHARACTERISTICS AS TRANSACTION READ ONLY`** - 세션 특성 변경
**`COMMIT`** - 트랜잭션 종료
**`SET autocommit=1`** - 자동 커밋 재활성화
단순 조회 하나를 위해 **6배의 네트워크 왕복**이 발생하게 됨1.

## Transaction ID 관리 오버헤드

MySQL InnoDB에서는 readOnly = true를 설정하면 Transaction ID를 부여하지 않아 오버헤드를 줄일 수 있다고 하지만[2](https://velog.io/@hyunrrr/Transactionalread-only-true%EB%A5%BC-%EC%82%AC%EC%9A%A9%ED%95%B4%EC%95%BC-%ED%95%98%EB%8A%94-%EC%9D%B4%EC%9C%A0), 실제로는 트랜잭션을 명시적으로 시작하는 과정에서 발생하는 비용이 더 클 수 있음.

## 커넥션 점유 시간 증가

트랜잭션을 명시적으로 시작하면 DB 커넥션을 더 오래 점유하게 되어, 커넥션 풀 고갈 등의 문제가 발생할 수 있음[3](https://latewalk.tistory.com/241).

## 3. PostgreSQL에서도 유사한 문제가 발생하는지와 MySQL과의 차이점


## PostgreSQL의 트랜잭션 처리 방식

PostgreSQL에서도 **`@Transactional(readOnly = true)`** 사용 시 MySQL과 **유사한 문제**가 발생할 수 있음[4](https://lob-dev.tistory.com/entry/DBMS-%EB%B3%84-Transaction-Read-Only%EC%97%90-%EB%8C%80%ED%95%9C-%EB%8F%99%EC%9E%91-%EB%B0%A9%EC%8B%9D-1). PostgreSQL JDBC 드라이버는 **`BEGIN READ ONLY`**와 같은 명령을 통해 트랜잭션을 시작하며, 필요에 따라 세션 특성 변경 쿼리도 추가로 실행됨.

## MySQL과 PostgreSQL의 주요 차이점


| **구분** | **MySQL** | **PostgreSQL** |
| --- | --- | --- |
| **readOnly 트랜잭션 최적화** | Transaction ID 미부여로 오버헤드 감소[2](https://velog.io/@hyunrrr/Transactionalread-only-true%EB%A5%BC-%EC%82%AC%EC%9A%A9%ED%95%B4%EC%95%BC-%ED%95%98%EB%8A%94-%EC%9D%B4%EC%9C%A0) | 가상 Transaction ID 사용으로 성능 개선 가능[4](https://lob-dev.tistory.com/entry/DBMS-%EB%B3%84-Transaction-Read-Only%EC%97%90-%EB%8C%80%ED%95%9C-%EB%8F%99%EC%9E%91-%EB%B0%A9%EC%8B%9D-1) |
| **MVCC 구현** | InnoDB 엔진에서 읽기 뷰 최적화[5](https://www.inflearn.com/community/questions/1200906/%ED%8A%B8%EB%9E%9C%EC%9E%AD%EC%85%98-readonly-%EA%B1%B0%EB%8A%94-%EC%9D%B4%EC%9C%A0) | 튜플 기반 MVCC로 더 엄격한 일관성 보장[4](https://lob-dev.tistory.com/entry/DBMS-%EB%B3%84-Transaction-Read-Only%EC%97%90-%EB%8C%80%ED%95%9C-%EB%8F%99%EC%9E%91-%EB%B0%A9%EC%8B%9D-1) |
| **트랜잭션 관리** | 상대적으로 단순한 트랜잭션 처리[6](https://ctrs.tistory.com/532) | 더 엄격한 ACID 준수와 트랜잭션 관리[7](https://carpe08.tistory.com/348)[8](https://aiday.tistory.com/149) |
| **readOnly 효과** | 주로 성능 최적화 목적[2](https://velog.io/@hyunrrr/Transactionalread-only-true%EB%A5%BC-%EC%82%AC%EC%9A%A9%ED%95%B4%EC%95%BC-%ED%95%98%EB%8A%94-%EC%9D%B4%EC%9C%A0) | **동시성 제어**가 주 목적, 성능 이점은 제한적[4](https://lob-dev.tistory.com/entry/DBMS-%EB%B3%84-Transaction-Read-Only%EC%97%90-%EB%8C%80%ED%95%9C-%EB%8F%99%EC%9E%91-%EB%B0%A9%EC%8B%9D-1) |


## PostgreSQL의 특별한 점

PostgreSQL에서는 readOnly 설정의 주목적이 **성능 향상이 아닌 동시성 제어**임[4](https://lob-dev.tistory.com/entry/DBMS-%EB%B3%84-Transaction-Read-Only%EC%97%90-%EB%8C%80%ED%95%9C-%EB%8F%99%EC%9E%91-%EB%B0%A9%EC%8B%9D-1). 읽기 동작에서 Read/Write 속성과 성능 차이를 크게 갖지 않으며, 주로 데이터 무결성과 안전한 동작을 보장하는 용도로 사용됨[4](https://lob-dev.tistory.com/entry/DBMS-%EB%B3%84-Transaction-Read-Only%EC%97%90-%EB%8C%80%ED%95%9C-%EB%8F%99%EC%9E%91-%EB%B0%A9%EC%8B%9D-1).

## 4. @Transactional readOnly 옵션을 언제 사용해야 할까?


## 사용해야 하는 경우


## **여러 쿼리의 일관된 스냅샷이 필요한 경우**


```java
@Transactional(readOnly = true)
public DashboardDto getDashboardData(Long userId) {
    User user = userRepository.findById(userId);
    List<Order> orders = orderRepository.findByUserId(userId);
    Statistics stats = statisticsRepository.findByUserId(userId);
    *// 모든 데이터가 동일한 시점의 스냅샷으로 조회됨*
    return new DashboardDto(user, orders, stats);
}
```


## **JPA 환경에서 성능 최적화가 필요한 경우**

**Dirty Checking 비활성화**: 영속성 컨텍스트가 스냅샷을 저장하지 않아 메모리 사용량 감소[3](https://latewalk.tistory.com/241)
**FlushMode.MANUAL 설정**: 트랜잭션 종료 시 자동 flush가 일어나지 않아 불필요한 연산 제거[3](https://latewalk.tistory.com/241)

## **Master/Replica 구조에서 읽기 부하 분산**

readOnly = true가 설정된 메서드는 Slave DB로 자동 라우팅되어 Master DB의 부하를 줄일 수 있음[3](https://latewalk.tistory.com/241).

## **OSIV=false 환경에서 Lazy Loading이 필요한 경우**


```java
*// application.properties*
spring.jpa.open-in-view=false

@Transactional(readOnly = true)
public Member getMemberWithTeam(Long memberId) {
    Member member = memberRepository.findById(memberId);
    *// OSIV가 false여도 트랜잭션 범위 내에서 Lazy Loading 가능*
    System.out.println(member.getTeam().getName());
    return member;
}
```


## **코드 가독성과 의도 명확화**

**`@Transactional(readOnly = true)`**를 통해 해당 메서드가 **조회 전용**임을 명확히 드러낼 수 있음[3](https://latewalk.tistory.com/241).

## 사용하지 말아야 하는 경우


## **단순 단건 조회**


```java
*// 이런 경우는 readOnly = true 불필요*
public User findById(Long id) {
    return userRepository.findById(id).orElseThrow();
}
```

단건 조회는 트랜잭션 자체가 불필요하며, 오히려 성능 저하를 유발할 수 있음1.

## **데이터 변경이 예상되는 경우**

readOnly = true에서는 변경 감지가 비활성화되어 의도하지 않은 데이터 불일치가 발생할 수 있음[9](https://hstory0208.tistory.com/entry/TransactionalreadOnly-true%EB%8A%94-%EC%96%B4%EB%96%A4-%EC%B5%9C%EC%A0%81%ED%99%94%EA%B0%80-%EC%9D%B4%EB%A4%84%EC%A7%88%EA%B9%8C).

## **커넥션 사용 시간이 긴 작업**

트랜잭션을 명시적으로 열면 DB 커넥션을 더 오래 점유하게 되어 커넥션 부족 문제를 야기할 수 있음[3](https://latewalk.tistory.com/241).

## 권장 사항

카카오페이에서 도출한 컨벤션1:
**단건 수정 요청에서 @Transactional 미사용**
**`@Transactional(readOnly=true)`**** 대신 커스텀 어노테이션 사용** (Propagation.SUPPORTS 적용)
**조회가 많은 엔티티의 경우 findById override 고려**
**클래스 레벨에서의 @Transactional 미사용**
결론적으로 **`@Transactional(readOnly = true)`**는 **명확한 목적이 있을 때만** 사용하고, 단순 조회에는 트랜잭션을 생략하는 것이 성능상 유리함.