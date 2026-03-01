---
title: PostgreSQL 시퀀스 + 캐시 주의점
date: 2024-03-04
tags:
  - DB
category:
  - 기술
  - DB
---

```json
CREATE SEQUENCE STK_OWN.SQ_STK_INTE_NOLI_STCK_M_01 INCREMENT BY 1
MAXVALUE 999999999
MINVALUE 1
CYCLE 
CACHE 20;
```

[https://www.postgresql.org/docs/9.5/sql-createsequence.html](https://www.postgresql.org/docs/9.5/sql-createsequence.html)

Spring batch에서 데이터를 EDB Postgres에 적재를 하려고 할 때.. @id 가 박혀있는 컬럼의@GeneratedValue 전략으로 시퀀스 채번을 선택함

샘플 배치와 데이터로 데이터 적재를 하는데 계속 값이 20 씩 올라감
Queryone으로 insert 하는 경우 1씩 잘 올라감


### 사유

Postgresql은 DB Conn 세션 별로 할당함

![](/assets/images/Pasted%20image%2020260301231402_958465de.png)

이건 그냥 예시로 그린거라..관련 그림이 없어서

그러므로 이런 식으로 가능. 배치 뿐만 아니라 pod 여러 개 * 커넥션 여러 개 인 경우도 가능
그래서 데이터 많이 넣으면 20씩 올라가는 현상 안보임
쿼리원에서도 세션 끊고 다시 연결하면 쿼리원 세션에서 잡고 있던 시퀀스 보다 큰 값으로 다시 count 시작함
> Sequences are based on bigint arithmetic, so the range cannot exceed the range of an eight-byte integer (-9223372036854775808 to 9223372036854775807).
모든 세션에서 값이 겹칠 일이 없게 보장하려 해서 끊기면 그냥 버리고 더 큰 숫자 잡아버림.
데이터가 적은 경우 각 세션별로 앞 값만 가져와서 20씩 증가하는것 처럼 보일 수 있음. 이게 구멍처럼 보임
> Furthermore, although multiple sessions are guaranteed to allocate 
> distinct sequence values, the values might be generated out of sequence 
> when all the sessions are considered. For example, with a cache setting of 10, session A might reserve values 1..10 and return `nextval`=1, then session B might reserve values 11..20 and return `nextval`=11 before session A has generated nextval=2. Thus, with a cache setting of one it is safe to assume that `nextval` values are generated sequentially; with a cache setting greater than one you should only assume that the `nextval` values are all distinct, not that they are generated purely sequentially. Also, last_value will reflect the latest value reserved by any session, whether or not it has yet been returned by `nextval`.


결론 : 이렇고 운영에서는 별 일 없을 것이다. 다만 세션이 여러가지인 경우 데이터 순서가 일정하다는 보장을 받을 수 없음. 참고.
