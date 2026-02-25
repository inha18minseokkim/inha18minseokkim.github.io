---
title: Jpa Upsert 존재하지 않는 이유
date: 2025-02-06
tags:
  - Spring
  - Spring-Data
  - JPA
category: 기술
---

[Is there any inbuilt method for UPSERT in spring JPA?](https://stackoverflow.com/questions/76160633/is-there-any-inbuilt-method-for-upsert-in-spring-jpa)

## JPA에 Upsert가 없는 이유

**JPA 표준 스펙 자체에 Upsert가 없다.** Spring Data JPA는 JPA 표준 위에 구축되어 있기 때문에 native Upsert를 제공하지 않는다.

`SimpleJpaRepository.save()`는 내부적으로 아래 로직으로 동작한다.

```java
if (entity.getId() == null) {
    em.persist(entity); // INSERT
} else {
    em.merge(entity);   // UPDATE
}
```

이 로직은 **ID가 자동 생성(generated)되는 경우에만 유효**하다. 수동으로 ID를 할당하거나 복합 키를 사용하면 항상 `merge()`를 타기 때문에 실제로 Upsert처럼 동작하지 않는다.

## 대안

### 1. `@Query`로 네이티브 쿼리 직접 사용

DB별 Upsert 문법을 `@Query`에 직접 명시한다.

```java
// PostgreSQL
@Query(value = "INSERT INTO my_table (id, name) VALUES (:id, :name) ON CONFLICT (id) DO UPDATE SET name = :name", nativeQuery = true)
void upsert(@Param("id") Long id, @Param("name") String name);

// MySQL
@Query(value = "INSERT INTO my_table (id, name) VALUES (:id, :name) ON DUPLICATE KEY UPDATE name = :name", nativeQuery = true)
void upsert(@Param("id") Long id, @Param("name") String name);
```

### 2. Hibernate 6.5+ `ON CONFLICT DO` (JPQL 지원)

[Hibernate ON CONFLICT DO clause - Vlad Mihalcea](https://vladmihalcea.com/hibernate-on-conflict-do-clause/)

Hibernate 6.5부터 JPQL에서 `ON CONFLICT DO` 절을 사용할 수 있다. **`save()` 메서드로 자동으로 되는 게 아니라**, `EntityManager`로 HQL 쿼리를 직접 작성해야 한다.

```java
entityManager.createQuery("""
    insert into Book (id, title, isbn)
    values (:id, :title, :isbn)
    on conflict(id) do update
    set title = excluded.title, isbn = excluded.isbn
    """)
.setParameter("id", 1L)
.setParameter("title", "High-Performance Java Persistence")
.setParameter("isbn", "978-9730228236")
.executeUpdate();
```

Hibernate가 실행 시 DB에 맞는 문법으로 자동 변환해준다.

| DB | 변환 문법 |
|---|---|
| PostgreSQL | `ON CONFLICT DO UPDATE` |
| MySQL | `ON DUPLICATE KEY UPDATE` |
| Oracle / SQL Server | `MERGE` |

### 3. 조회 후 분기 처리

```java
Optional<Entity> existing = repository.findById(id);
if (existing.isPresent()) {
    // UPDATE
} else {
    // INSERT
}
```

단순하지만 **race condition** 가능성이 있어 트랜잭션 격리 수준 또는 DB 락 처리가 필요하다.
