---
title: FindAll~사용시 JPA FetchJoin + 안됨
date: 2024-11-04
tags:
  - Spring
  - Spring-Data
  - JPA
category:
  - 기술
---

["N+1 selects problem" with JpaRepository method despite using @Fetch(FetchMode.JOIN)](https://stackoverflow.com/questions/77806343/n1-selects-problem-with-jparepository-method-despite-using-fetchfetchmode-j/77817535#77817535)

## 문제 원인

`spring-data-jpa`의 `findAll*` 계열 메서드는 **Fetch Mode를 무시**한다.

`@Fetch(FetchMode.JOIN)` 어노테이션을 설정해도, `findAll` 같은 메서드는 내부적으로 JPQL 쿼리를 생성하는데, JPQL은 엔티티에 설정된 Fetch Mode를 따르지 않는다. 쿼리 자체에 명시적으로 JOIN을 작성해야만 실제로 JOIN이 적용된다.

## Fetch Mode가 적용되는 경우

Fetch Mode는 아래 경우에만 동작한다.

- `findById`처럼 **단건 조회** 시 (Hibernate Session을 통해 엔티티를 직접 로드할 때)
- 이미 로드된 엔티티의 **연관관계를 탐색(Lazy Loading)** 할 때

## 해결 방법

`findAll` 사용 시 N+1 문제를 피하려면, `@Query`로 JPQL에 **`JOIN FETCH`를 직접 명시**해야 한다.

```java
@Query("SELECT e FROM Entity e JOIN FETCH e.association")
List<Entity> findAllWithAssociation();
```
