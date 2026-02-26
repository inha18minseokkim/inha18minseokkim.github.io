---
title: "Spring batch + Control M"
date: 2023-11-01
tags: [미지정]
category:
  - 기술
---

### ASIS(카드계 배치 BXM, Spring Legacy 3)

1. Control M 상에서 작업경로 설정(/kbksw/swdpt/crdbxm/bat/shl) 후 스크립트 실행 (executeJob.sh)
  - +추가적인 args 넣음(LIBMEMSYM, PARM1=CRDBat,Parm2=Job이름, Parm3=%%JOBNAME, Parm4=procDt=%%ODATE 이런식)
  - 로컬에서 실행시킬 때 
    - sh [executeJob.sh](http://executeJob.sh) CRDBat KamisDataSttcLdngJob KamisDataSttcLdngJob procDt=20230921…. 
2. 결국 컨트롤엠은 executeJob.sh를 실행시키는 용도
3. Job은 n개 Step으로 구성됨
4. ItemReader로 파일을 읽어오거나(xml 빈 정의) open에서 DBIO호출
  - DBIO로 한 번에 읽어와서(Cursor,Paging X) 내부 반복하기 때문에 Cursor에 관련된 권한 필요없었음
5. Job을 XML로 정의, runJob.sh가 어플리케이션에서 Job을 실행하는 형태
6. 로컬,스테이징 테스트는 로컬 컴퓨터가 아닌 서버에 접속해서 executeJob.sh를 실행하는 형태

### TOBE

1. (로컬에서만 가능)
  - ./gradlew bootrun —args=’—processDate=20230920 —jobName=ipo-data-load-job’
  - Control M에서는 아마 pod로 말아진 도커 이미지를 호출할 것이므로 
    - java -jar jar이름.jar —processDate=20230920 —jobName=ipo-data-load-job
2. 쿠버네티스 버전 컨트롤엠에서는 아마 kubectl create cronjob ~~ 이런식의 스크립트를 sh에 넣어서 컨트롤엠이 구동하지 않을까
3. Job에 FlowJob 유형 추가(최소 Spring 5.3.X 이상 지원)
  - Job 내에서 Flow를 만들어 Step을 조건별 호출 가능(첫 번째 Step에서 ExitStatus 코드가 COMPLETED면 AStep 호출, B 코드를 리턴했다면 BStep 호출, 중간에 조건이 바뀌면 동적으로 Step을 등록해서 해당 Step 호출 가능)
    - BATCH 테이블의 STEP_EXECUTION테이블에 여러 유형의 ExitStatus가 등록될 수 있음을 인지
    - [https://stackoverflow.com/questions/7879550/spring-batch-how-do-i-return-a-custom-job-exit-code-from-a-steplistener](https://stackoverflow.com/questions/7879550/spring-batch-how-do-i-return-a-custom-job-exit-code-from-a-steplistener)
4. FlatFileItemReader,RepositoryItemReader,MyBatisCursorItemReader… 여러 유형의 리더 명시적으로 생성 가능
  - Cursor Based ItemReader의 경우(DB to ?) Commit 권한 명시적으로 호출 필요
  - 내부적으로 커서 정보를 Batch Table에 넣고 트랜잭션을 잡고있는데, 해당 상황에서 Commit 권한 명시적으로 없으면(Select,Insert,Update,Delete 있어도 필요) 오류
5. Job 하나 당 컨테이너 하나 - @Configuration 을 사용하여 사용자가 직접 Job에 대한 Configuration을 자바 소스코드로 정의
6. 로컬 테스트, 스테이징 테스트를 로컬에서 실행(DB접근 시 BEGIN 권한 명시적으로 필요, DB 배치 테이블에 클러스터가 아닌 개발자 로컬PC가 DB에 접근하기 때문)

