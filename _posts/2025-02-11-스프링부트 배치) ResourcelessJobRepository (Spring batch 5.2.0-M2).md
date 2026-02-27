---
title: "스프링부트 배치) ResourcelessJobRepository (Spring batch 5.2.0-M2)"
date: 2025-02-11
tags:
  - Spring Batch
  - 개발
  - Java
category:
  - 기술
---
Spring Batch 관련 개발 내용 정리.
[Spring Batch 5.2.0-M2 is available now!](https://spring.io/blog/2024/10/11/spring-batch-5-2-0-m2-is-available-now)
Spring batch 4 까지는 인메모리 HashMap 형태로 JobRepository 를 만드는것을 지원하였지만, 5 부터는 ResourcelessJobRepository를 다시 지원한다는 제보를 들었다.
그래서 그대로 기존 배치 프로젝트에 적용해보았다.

![](attachment:abfb8f94-1bae-4ab2-982f-c6b31a929000:image.png)

인메모리 구현을 위해 구현해놨던 DataSource 관련 설정을 모두 삭제해주고

```kotlin
    @Override
    public void run(ApplicationArguments args) throws Exception {
        TaskExecutorJobLauncher jobLauncher = new TaskExecutorJobLauncher;

        jobLauncher.setJobRepository(jobRepository);
        jobLauncher.setTaskExecutor(task -> {
            log.info("ListedStockPrice 적재 시작 @@@@@@");
            task.run;
        });
        jobLauncher.run(priceBatchJob,jobParameters);
    }
    public JobParameters jobParameters {
        return new JobParametersBuilder
                .addString("instance_id",
                        LocalDateTime.now.format(DateTimeFormatter.ofPattern("yyyyMMddHHmmss")),
                        true)
                .toJobParameters;
    }
    @Bean
    public JobRepository jobRepository {
        return new ResourcelessJobRepository;
    }
```

jobRepository를 Resourceless 구현체로 빈등록 해주고 주입하면 끝.

