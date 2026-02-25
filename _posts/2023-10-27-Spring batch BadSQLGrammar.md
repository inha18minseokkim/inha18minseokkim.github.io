---
title: "Spring batch BadSQLGrammar"
date: 2023-10-27
tags: [미지정]
category: 기술
---

### 경과

배치 실행 시 BadSQLGrammar 뜸. 빈은 만들어지지만 JobExecution이 안됨
SQLDialect문제인줄 알았음
DBSafer 경고문 
  - BEGIN;SELECT * FROM BATCH_JOB_INSTANCE ~ ; COMMIT; 뜸


### 해결방법

BEGIN 권한 넣으면 됨
DBA가 깜빡하고 권한을 안준거임;;;