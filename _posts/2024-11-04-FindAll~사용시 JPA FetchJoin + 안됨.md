---
title: "FindAll~사용시 JPA FetchJoin + 안됨"
date: 2024-11-04
tags: [미지정]
---

["N+1 selects problem" with JpaRepository method despite using @Fetch(FetchMode.JOIN)](https://stackoverflow.com/questions/77806343/n1-selects-problem-with-jparepository-method-despite-using-fetchfetchmode-j/77817535#77817535)

`FindAll*` methods of `spring-data-jpa` implemented Queries that ignore fetch modes. When you write a query, you are telling what is joined and what is not joined.

Fetch mode is only taken into account when entity is loaded with methods like `findById` or when navigating through some other entity graph and loading its associations.
