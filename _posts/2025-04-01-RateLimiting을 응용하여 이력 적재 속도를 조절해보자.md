---
title: "RateLimiting을 응용하여 이력 적재 속도를 조절해보자"
date: 2025-04-01
tags: [미지정]
---

## 조건

고객들이 조회한 종목 top N을 집계해서 게시하는 기능이 필요.
적재는 rdb에 해야함(rdb 밖에 없음)
redis 있음
집계는 N초에 한번만 하고싶음  ex) 30초 동안 삼성전자 상세조회를 왔다갔다 10번해도 이력 10개가 아니라 1개 이력으로
너무 많은 insert는 현 mono edb에 부담


### 방법

(005930, Unix TimeStampNow) 을 insert 한다고 가정
redis에 005930 ttl 30초로 set
다음 사용자가 (005930, Unix TimeStampNow)를 insert
redis에 남아있으면 insert 호출안하고 없으면 호출 후 다시 ttl 30초 set


