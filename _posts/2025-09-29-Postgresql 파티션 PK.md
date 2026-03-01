---
title: Postgresql 파티션 PK
date: 2025-09-29
tags:
  - DB
category:
  - 기술
  - DB
---

Postgresql 파티션을 사용할 때 현재 케이뱅크 DBA 작업자분들은 표준으로 아래와 같이 잡는다

```sql
CREATE TABLE sample_table (
  id BIGINT NOT NULL,
  yyyymmdd VARCHAR(8) NOT NULL,
  ...,
  PRIMARY KEY (id, yyyymmdd)
) PARTITION BY RANGE (yyyymmdd);

```

R2dbc를 사용하고 있기 때문에 multiple key 인 경우 혹시 문제가 있을까 생각은 해봤는데 아마 결국에는 id 가지고 유일성이 보장되기 때문에 driver 입장에서는 크게 문제가 없을 듯 하다.


### pk 입장에서는 선행 컬럼이 무조건 유일한 값이라 두 번째 컬럼의 효용성이 전혀 없어보이는데 파티션을 잡는게 의미가 있는가?

pk 기준으로 봤을 때 1번 키가 무조건 유일하기 때문에 2번 pk는 사실상 의미가 없다. 그러면 해당 pk로 파티션을 선언하는 것이 의미가 있나? 라는 의문이 들었다.


## 원리 설명

- 파티셔닝된 테이블은 실제 데이터를 여러 하위 테이블(파티션)로 나눠 저장. 이 때, 데이터의 분산 기준이 되는 컬럼이 “파티션 키”.
- 파티션 키는 테이블 분할 기준 
  - 쿼리에서 파티션 키 조건이 명확하면 관련 파티션만 탐색하도록 최적화.
- **파티션 키는 PK에 포함되어야 합니다.** 그래야 데이터 전체에 대해 유일성 제약이 유지되며, 파티션별 PK도 각각 관리됩니다.
- PK의 첫 번째 컬럼이 이미 행을 고유하게 식별하더라도, 파티션 키는 물리적으로 데이터를 나누고 최적화 목적으로 반드시 필요합니다. 이는 PK 컬럼과 역할이 다릅니다.

파티션 키를 잡는것과는 관련없이 파티션을 선언해놓으면 물리적으로 테이블이 분산되어 저장되는 것


```sql
CREATE TABLE Posts (
       user_id         INT NOT NULL,
       post_time       TIMESTAMP(0) NOT NULL,
       contents        TEXT
) PARTITION BY RANGE(post_time); -- sets the partition

insert into Posts (user_id, post_time, contents)
values (1,'1/1/2024','test');
```

요렇게 ddl을 만들고

```sql
CREATE TABLE Posts_Jun2024 PARTITION OF Posts 
 FOR VALUES FROM ('2024-06-01') to ('2024-07-01');
 
CREATE TABLE Posts_Jul2024 PARTITION OF Posts
 FOR VALUES FROM ('2024-07-01') to ('2024-08-01');
 
CREATE TABLE Posts_Aug2024 PARTITION OF Posts
 FOR VALUES FROM ('2024-08-01') to ('2024-09-01');
```

이렇게 파티션을 선언하면 물리적으로 다르게 저장된다는 말이다.


![](/assets/images/Pasted%20image%2020260301231403_cf055f10.png)



[PostgreSQL 파티션 테이블 1부](https://postgresql.kr/blog/postgresql_partition_table.html)
[PostgreSQL 파티션 테이블 2부](https://postgresql.kr/blog/postgresql_partition_table_2.html)

[PostgreSQL Partitioning: The Most Useful Feature You May Never Have Used](https://www.red-gate.com/simple-talk/databases/postgresql/postgresql-partitioning-the-most-useful-feature-you-may-never-have-used/)
