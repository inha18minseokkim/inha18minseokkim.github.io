---
title: "Spring Batch 5.2에서 ResourcelessJobRepository로 DB 없이 배치 실행하기"
date: 2025-02-11
tags: [Spring, Batch, Java, Kotlin, 백엔드]
---

## 배경

Spring Batch를 사용할 때 가장 번거로운 부분 중 하나는 **JobRepository를 위한 데이터베이스 설정**이다. 배치 메타데이터(Job 실행 이력, Step 상태 등)를 저장하기 위해 반드시 DataSource가 필요했기 때문이다.

간단한 배치 작업이나 테스트 환경에서는 이 설정이 과하게 느껴질 수 있다. Spring Batch 4까지는 인메모리 HashMap 기반의 `MapJobRepositoryFactoryBean`을 지원했지만, **Spring Batch 5에서 deprecated 되면서** 사라졌다.

그런데 [Spring Batch 5.2.0-M2](https://spring.io/blog/2024/10/11/spring-batch-5-2-0-m2-is-available-now) 릴리즈에서 **`ResourcelessJobRepository`가 다시 도입**되었다는 소식을 듣고 바로 적용해보았다.

---

## ResourcelessJobRepository란?

`ResourcelessJobRepository`는 말 그대로 **리소스(DB)가 없는 JobRepository** 구현체다.

- 배치 메타데이터를 어디에도 저장하지 않음
- 데이터베이스 설정 불필요
- 간단한 배치 작업이나 테스트에 적합
- 재시작(restart) 기능은 지원하지 않음 (상태를 저장하지 않으므로)

---

## 적용 방법

### 1. 기존 DataSource 설정 제거

인메모리 구현을 위해 만들어뒀던 DataSource 관련 설정을 모두 삭제한다.

![DataSource 설정 제거](/assets/images/Pasted%20image%2020260228164855.png)

### 2. ResourcelessJobRepository 빈 등록

```kotlin
@Bean
fun jobRepository(): JobRepository {
    return ResourcelessJobRepository()
}
```

### 3. JobLauncher에 주입하여 실행

```kotlin
@Component
class BatchRunner(
    private val jobRepository: JobRepository,
    private val priceBatchJob: Job
) : ApplicationRunner {

    private val log = LoggerFactory.getLogger(this::class.java)

    override fun run(args: ApplicationArguments) {
        val jobLauncher = TaskExecutorJobLauncher().apply {
            setJobRepository(jobRepository)
            setTaskExecutor { task ->
                log.info("ListedStockPrice 적재 시작 @@@@@@")
                task.run()
            }
        }

        jobLauncher.run(priceBatchJob, createJobParameters())
    }

    private fun createJobParameters(): JobParameters {
        return JobParametersBuilder()
            .addString(
                "instance_id",
                LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyyMMddHHmmss")),
                true
            )
            .toJobParameters()
    }
}
```

---

## 정리

| 항목 | 기존 방식 | ResourcelessJobRepository |
| --- | --- | --- |
| DB 필요 여부 | 필수 | 불필요 |
| 메타데이터 저장 | O | X |
| 재시작 지원 | O | X |
| 설정 복잡도 | 높음 | 낮음 |
| 적합한 용도 | 운영 환경 | 테스트, 단순 배치 |

**주의사항**: 운영 환경에서 재시작이 필요하거나 실행 이력 관리가 필요한 경우에는 기존 방식(DB 기반 JobRepository)을 사용해야 한다.

---

## 참고

- [Spring Batch 5.2.0-M2 릴리즈 노트](https://spring.io/blog/2024/10/11/spring-batch-5-2-0-m2-is-available-now)
