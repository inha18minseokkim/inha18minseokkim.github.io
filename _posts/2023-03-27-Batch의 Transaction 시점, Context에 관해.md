---
title: Batch의 Transaction 시점, Context에 관해
date: 2023-03-27
tags:
  - Spring
  - Batch
---
![이미지](/assets/images/Pasted%20image%2020260224162733.png)

Spring Batch 계층 구조

![이미지](/assets/images/Pasted%20image%2020260224162740.png)
흔히 알고 있는 Spring Batch의 Chunk 생명주기(?)

들었던 의문
1. Chunk-Oriented Batch 에서 Spring Batch는 어느 시점 까지 트랜잭션을 보장하나? 바꿔 말해서 befoechunk,open,read,process,write,update 와 같은 내부 생명주기 메서드 중 어느 시점부터 lock이 걸리고 lock이 해제되는가?
2. 1000개의 파일이 있고 commit-interval이 100이라면 총 10번의 chunk cycle이 만들어진다. chunk를 한 5번째 쯤 끝나고 6번째 쯤에서 exception이 발생한다면 db에 커밋된 데이터는 500개인가 0개인가
3. Tasklet-Oriented Batch에서 Tasklet interface를 implement 하면 execute()메서드를 구현해야 함. execute()메서드 내부에서 한 가지가 아닌 수 번의 DB write가 일어나게 된다. 그럼 중간에 비정상종료가 된다면 그때까지 write 된 데이터는 db에 들어가있는가, 아니면 싹 다 롤백되는가?
4. RepeatStatus.FINISHED는 왜 쓰는것인가? 아마 위에서 내렸던 의문들과 관련이 있을것 같은 직관이 들었다.

## Spring Batch에서 Transaction 범위는 Chunk 단위

따라서 5번째 chunk까지는 성공하고 다음 chunk에서 실패한다면 일단 500개(commit-interval = 100 * 5)는 db에 반영됨

## Transaction 설정 시점은 특정 시점에 따라 다를 수 있다(예컨데 DB 접근 시, 설정으로 바꿀 수 있는듯),Spring Batch가 Runtime에 DB접근 코드를 보고 판단함.

beforechunk가 끝나고 lock을 무조건 거는것도 아니고 db에 접근하는 시점에 따라서 알아서 판단함.
![이미지](/assets/images/Pasted%20image%2020260224162747.png)
대체로 이런 환경을 따르긴 한다. 기본적으로 스프링 배치는 read, process, write의 프로세스를 하나의 트랜잭션으로 싸고 있다고 생각.


## Tasklet-Oriented Batch에서는 끝났을 때 정상인지에 따라 commit 여부 달라짐

정상종료가 되었다면 execute() 메서드 내부에 오버라이딩된 내용들(특히 외부 db에 R/W했던 내용들)을 commit 시키고 그렇지 않다면 Rollback

## 정상종료의 기준? → RepeatStatus.FINISHED를 리턴하는지?

1. All database operations perfomed within the execute method are executed within a single transaction
2. The transaction is committed once the execute method returns a RepeatStatus of Finished
3. If there are no changes(트랜잭션을 걸어도 write 하지 않고 read만 하는경우), the transaction will still be committed, but there will be no changes to the database.
execute() 에서 RepeatStatus.FINISHED를 리턴하면 커밋과 함께 배치 종료, CONTINUABLE인 경우 다시 실행.

*응용 - Chunk Interface를 implement한 클래스에서 StepExecution을 통해 setExitStatus를 수동으로 설정할 수 있다. + Chunk batch에서 특정 메서드를 넘기고 싶은 경우 null리턴하면 해당 step의 데이터는 다음 메서드에 넘어가지 않는다. ex) read에서 null 리턴하면 process에서 해당 row 데이터는 처리하지 않는다. + read에서 새로운 OMM객체를 만들어 리턴하면 무한루프 걸림. 내부적으로 계속 read가 호출됨.


## 배치 사용시 유의점

1. 최대한 심플하게 작성. 스프링에서 트랜잭션 전파는 이전 트랜잭션을 계속 물려받도록 설계되어있음. 따라서 너무 길게 작성하여 배치가 물고 물리면 전반적 시스템 퍼포먼스 하락 가능.
2. 네트워크상으로 멀리 있으면 전반적 시스템 퍼포먼스 하락 가능(수행하는 동안 특정 자원에 Lock을 걸기도 하기 때문)
3. 똑같은 동작이나 데이터 처리를 반복하지 않게 하기
4. 데드락 조심
