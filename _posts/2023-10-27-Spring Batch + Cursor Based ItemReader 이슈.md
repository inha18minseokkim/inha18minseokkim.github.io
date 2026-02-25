---
title: "Spring Batch + Cursor Based ItemReader 이슈"
date: 2023-10-27
tags: [미지정]
category: 기술
---


### 문제상황

Spring batch 를 팀원들 각각 구현 후 특정 배치만 돌 때 Bad SQL Grammar 에러(Permission Denied)

### 환경

Spring batch 5, PostgreSQL, 허용명령어 Select,Update,Delete,Begin


### 경과

MyBatisCursorItemReader를 사용한 ItemReader 빈 오류 발생(Bad SQL Grammar 및 BEGIN;SELECT * FROM BATCH_JOB_INSTANCE…. COMMIT; 명령어에 대한 실행 권한 없음 예외 발생)
FlatFileItemReader는 정상 작동 확인(Batch Instance 테이블에 Complete 완료 및 정상 데이터 적재 확인)
ItemReader에서 Iterator를 저장하여 hasNext로 read 인터페이스를 구현한 ItemReader는 정상 작동 확인
Cursor 에 문제가 있는 것 같다고 판단(사실 찍음) JdbcCursorItemReader 를 사용하여 MyBatisCursorItemReader와 같은 현상 관측


### 해결

commit 권한을 받아 해결 완료


### 왜 이런 문제가 생긴것인가

DB 계정 권한을 명령어 단위로 관리를 하는데 안넣어줌.. 휴먼에러
