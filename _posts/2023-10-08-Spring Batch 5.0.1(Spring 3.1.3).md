---
title: "Spring Batch 5.0.1(Spring 3.1.3)"
date: 2023-10-08
tags: [미지정]
category:
  - 기술
---
1. Job과 Container 1:1 로 만들고 인프라 환경에서 크론잡을 돌리는 방식, 또는 컨트롤엠 쿠버네티스 버전 사용
2. Job : Container로 만들었을 때 생기는 문제점
  - 개발 환경 표준화가 안됨 + 초기 Configuration 작성 하는데 비용 많이 듦
  - 템플릿이 필요할 수도 있음..

```javascript
package com.example.opendartannouncereceivebatch.Job;

import com.example.opendartannouncereceivebatch.Tasklet.DailyAnnounceApiReceiveTasklet;
import com.example.opendartannouncereceivebatch.Tasklet.FreeIssueReceiveTasklet;
import com.example.opendartannouncereceivebatch.Tasklet.PaidIncreaseReceiveTasklet;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.batch.core.Job;
import org.springframework.batch.core.Step;
import org.springframework.batch.core.configuration.annotation.JobScope;
import org.springframework.batch.core.job.builder.JobBuilder;
import org.springframework.batch.core.repository.JobRepository;
import org.springframework.batch.core.step.builder.StepBuilder;
import org.springframework.boot.ApplicationArguments;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.transaction.PlatformTransactionManager;


@Configuration
@RequiredArgsConstructor
@Slf4j
public class DefaultAnnouncementApiReceiveJobConfig {
    private final DailyAnnounceApiReceiveTasklet dailyAnnounceApiReceiveTasklet;
    private final PaidIncreaseReceiveTasklet paidIncreaseReceiveTasklet;
    private final FreeIssueReceiveTasklet freeIssueReceiveTasklet;
    private final ApplicationArguments applicationArguments;

    @Bean
    public Job dailyReceiveJob(JobRepository jobRepository,
                               PlatformTransactionManager transactionManager){
        String beginDate = applicationArguments.getOptionValues("beginDate").get(0);
        String endDate = applicationArguments.getOptionValues("endDate").get(0);
        log.info(String.format("dailyReceiveJob 실행 시작 %s ~ %s",beginDate,endDate));

        Job exampleJob = new JobBuilder(String.format("dailyReceiveJob%s%s",beginDate,endDate),jobRepository)
                .start(dailyReceiveStep(jobRepository,dailyAnnounceApiReceiveTasklet,transactionManager))
                .next(dailyPaidIncreaseReceiveStep(jobRepository, paidIncreaseReceiveTasklet, transactionManager))
                .next(dailyFreeIssueReceiveStep(jobRepository,freeIssueReceiveTasklet,transactionManager))
                .build();
        return exampleJob;
    }

    @Bean
    @JobScope
    public Step dailyReceiveStep(JobRepository jobRepository
                                , DailyAnnounceApiReceiveTasklet defaultTasklet
                                , PlatformTransactionManager transactionManager) {
        String beginDate = applicationArguments.getOptionValues("beginDate").get(0);
        String endDate = applicationArguments.getOptionValues("endDate").get(0);
        log.info(String.format("%s ~ %s dailyReceiveStep 실행",beginDate,endDate));
        return new StepBuilder("dailyReceiveStep",jobRepository)
                .tasklet(defaultTasklet,transactionManager).build();
    }

    @Bean
    @JobScope
    public Step dailyPaidIncreaseReceiveStep(JobRepository jobRepository
            , PaidIncreaseReceiveTasklet defaultTasklet
            , PlatformTransactionManager transactionManager) {
        String beginDate = applicationArguments.getOptionValues("beginDate").get(0);
        String endDate = applicationArguments.getOptionValues("endDate").get(0);
        log.info(String.format("%s ~ %s dailyPaidIncreaseReceiveStep 실행",beginDate,endDate));
        return new StepBuilder("dailyPaidIncreaseReceiveStep",jobRepository)
                .tasklet(defaultTasklet,transactionManager).build();
    }

    @Bean
    @JobScope
    public Step dailyFreeIssueReceiveStep(JobRepository jobRepository
    , FreeIssueReceiveTasklet defaultTasklet
    , PlatformTransactionManager transactionManager) {
        String beginDate = applicationArguments.getOptionValues("beginDate").get(0);
        String endDate = applicationArguments.getOptionValues("endDate").get(0);
        log.info(String.format("%s ~ %s dailyFreeIssueReceiveStep 실행",beginDate,endDate));
        return new StepBuilder("dailyFreeIssueReceiveStep",jobRepository)
                .tasklet(defaultTasklet,transactionManager).build();
    }

}
```

  - 로컬환경에서 테스트 - JobRepository 관리 필요
  - 질문 : 스프링 배치를 실행/관리하는 DataBase가 주제영역별인가? 아니면 주제영역 상관없이 특정 DB에 다 몰아넣고 관제할 것인가?

![](https://prod-files-secure.s3.us-west-2.amazonaws.com/c38aebd7-2834-4fac-b2fc-a2f0c17ce81d/fb597120-f1bb-4194-9277-52ea27bb3b3d/Untitled.png)

    - 이 테이블을 각 주제영역 DB별로 넣는 경우 문제 없음
    - 후자의 경우 각 컨테이너 내지 프로젝트를 만들 때 DataSource, TransactionManager를 두 개를 둬야하는데,, 해당 Configuration 템플릿이 필요함


### OpenAPI 데이터 적재 배치

클러스터 환경이 정해지는 경우 괜찮은 데이터가 있는 경우 형상 띄워서 빠르게 수집하려 함.
오픈api 개발하는 프로세스도 정해놓는게 좋다(현재는 안정해져있다 생각함)
각 기관별(공공데이터포털,오피넷,국토교통부 등등) 키값을 저장하고 관리하는 곳 필요함
주제영역이 만들어지기 전 적재만을 위한 업무영역과 DB 필요함

1. WebFlux.WebClient 사용하여 Response 받아옴
2. 행 표준 매핑(이거 문제)
3. Entity 만듦
4. DB 적재
 
Spring Batch 테스트 환경
[뻘짓) Spring Batch 5 + Multiple DataSource]({% post_url 2023-10-10-뻘짓) Spring Batch 5 + Multiple DataSource %})
로컬테스트도 원래 있던 개발 서버에서 수행하는것으로
크론잡 실행은 CronJob(ControlM) 즉 인프라단에서 수행하는것으로 결정
데이터소스는 각 네임스페이스별로 하나씩 만들어오는것으로 함

회의 결과
[JobLauncher Configuration + JobParameter]({% post_url 2023-10-12-JobLauncher Configuration + JobParameter %})