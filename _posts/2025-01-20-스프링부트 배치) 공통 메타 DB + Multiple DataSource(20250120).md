---
title: "스프링부트 배치) 공통 메타 DB + Multiple DataSource(20250120)"
date: 2025-01-20
tags: [미지정]
category: 기타
---

재작년에 혹시몰라 가볍게 작성했는데 실제로 필요할 것 같음.

# 요인

1. 현재 주식업무쪽은 배치가 필수는 아니지만 앞으로 트랜잭션이 중요해지는 금융 서비스들이 들어온다면 배치 어플리케이션이 필요하긴 하다
  1. ex) 뭔가의 정산, 계정 회원 관련 일괄 집계 등등… 또는 최소 만건 단위 벌크 데이터 처리 등등..
2. 각 단위업무에 batch metatable이 산재되어 있다 ex) 주식,환율,지수,방송,퀴즈,혜택 db 모두 각각의 batch_job_execution 같은 테이블이 있다. 이런 업무들 하나 만들 때 마다 배치 테이블도 각각 생성해야 함.
3. 그렇기 때문에 배치 인스턴스들이 파편화되어 관리되고 있다(사실상 안함).
4. 현재 argo workflow에서 파드가 뜰 때마다 was가 기동되는 형태인데, node 자원이 부족한 경우 38080 already in use가 뜬다. 
  1. 외) 이건 컨테이너 was의 포트 번호를 쓰지 않는 이상 그냥 서비스에서 노출 안시키면 될 것 같은데 좀 더 알아보자
  2. 외) 배치 어플리케이션이 꼭 pod 기동의 형태로 실행되어야 하는건지도 의문이긴 하다. 배치 테이블 찌르고 메타 데이터 생성하는데 노드 자원이 튀고, 기동 속도도 느리다. 배치를 가져갈거면 java 파일 실행도 고려해봄직하다.
    - 하지만 자바단위 실행이라면 문제가 생길 수 있음

5. 가끔 작업이 실패하는 경우 테이블에서 락이 걸리는데, 재택이 안되다보니 조치가 안된다.
  1. 외) 그러다보니 jobParameter에 해시 값을 넣어 기동할 때 마다 다른 execution으로 인식하게 하여 현재는 문제점을 회피하고 있지만, 완벽한 멱등처리가 되지 않는 이상 스프링 배치의 chunk 기반 대량 데이터 처리가 필요한 시점이 오면 metatable이 필요하긴 할 것임.
  2. 외) 재택이 안되다보니 현재 4.b 로 만들어 실행 환경을 격리시키긴 했다.

# 목표

1. spring batch metatable을 한 곳으로 몰아넣는다
2. 하지만 각 업무의 db는 분리되어있도록 한다
3. metatable이 필요하지 않는 경우(단순 트랜잭션 보장 처리의 용이성만 이용할 경우, 현재 MSA 업무에서 작성된 대부분의 배치)에 batch datasource를 인메모리로 구현할수 있게 만든다
4. spring batch metatable을 한곳에서 관리하여 배치 관리자를 구성해서 조치할 수 있도록 한다.
  - 조직,업무 특성상 정기작업은 was처럼 실시간 처리를 요하지는 않다보니 이런 요건은 MSA보다는 잘 관리된 모노환경이 오히려 적합할 수 있다는 생각이 요즘 강하게 듦. (높은 격리수준으로 인한 안정성에 대한 효용 <<<< 낮은 격리수준이지만 현재 행 내 변경계획 정책 compatibility에 따른 효용)


![](https://prod-files-secure.s3.us-west-2.amazonaws.com/c38aebd7-2834-4fac-b2fc-a2f0c17ce81d/31cf7c9d-c850-4f48-b06f-3160a0d09b7c/image.png)

제목 없는 다이어그램.drawio

## DataSource

jdbc를 사용하여 커넥션 맺는 빈객체. 여기서는 대상 db가 두 종류 이므로 DataSource 객체 두 개 필요. 
주된 설정에 필요한 것은 배치 메타 테이블을 바라보는 datasource 빈을 통해서 이루어지므로 batch datasource를 @Primary 선언해준다. 
만약 그렇지 않으면 DefaultBatchConfiguration을 상속하는 configuration 빈 객체를 직접 하나 하나 (datasource,jobRepository,jobLauncher,jobExplorer,jobParameterIncrementer 등등을 오버라이딩 해줘야 함…) 다 설정해야 하므로 “스프링 부트” 배치의 장점을 살리기 위해 최대한 configuration을 활용한다

```java
spring:
  application:
    name: listed-stock-data-receive-service
  datasource:
    batch-properties:
      url: jdbc:postgresql://${outer-host}:5432/center_batch
      username: batchUser
      password: pw
      driverClassName: org.postgresql.Driver
    business-properties:
      url: jdbc:postgresql://${outer-host}:5432/deepsearch
      username: businessUser
      password: pw
      driverClassName: org.postgresql.Driver
```

spring 기본 yml(spring.datasource.url…) 이 아닌 커스텀이 필요하므로 ConfigurationProperties를 사용하여 명시적으로 선언해줌

```java
@Configuration
@ConfigurationProperties(prefix = "spring.datasource.batch-properties")
@Getter
@Setter
public class BatchDbProperties {
    private String url;
    private String username;
    private String password;
    private String driverClassName;
}
```


```java
@Configuration
@ConfigurationProperties(prefix = "spring.datasource.business-properties")
@Getter
@Setter
public class JpaDbProperties {
    private String url;
    private String username;
    private String password;
    private String driverClassName;
}
```

각각을 주입해서 DataSource 객체를 두 개 생성해준다.

```java
@Bean(value="dataSource")
@Primary
public DataSource dataSource() {
    DataSource dataSource = DataSourceBuilder.create()
            .driverClassName(batchDbProperties.getDriverClassName())
            .url(batchDbProperties.getUrl())
            .username(batchDbProperties.getUsername())
            .password(batchDbProperties.getPassword())
            .build();
    return dataSource;
}
@Bean(value = "businessDataSource")
public DataSource businessDataSource() {
    return DataSourceBuilder.create()
            .url(jpaDbProperties.getUrl())
            .driverClassName(jpaDbProperties.getDriverClassName())
            .username(jpaDbProperties.getUsername())
            .password(jpaDbProperties.getPassword())
            .build();
}
```

여기서 배치 메타 테이블 트랜잭션을 관리하는 PlatformTransactionManager는 Primary DataSource를 주입하고, JPA를 사용한 비즈니스 테이블의 트랜잭션을 관리하는 JpaTransactionManager는 businessDataSource를 주입한다.
배치 메타테이블 기능이 필요하지 않다면 Primary DataSource가 H2와 같은 인메모리 db를 바라보도록 해도 된다.

## JobRepository

우리가 CrudRepository를 사용하듯, batch MetaTable에 CRUD 기능을 수행하는 Repository bean이다. Job, Step을 실행함에 따라 배치 메타테이블에 연산(job 시작, 진행중, 끝 실패 성공 ,UNKNOWN 등 상태 기록)을 이 빈을 통해 수행한다. 이 역시 배치 빈을 커스터마이징 하기 때문에 스프링 부트가 기본으로 말아주는 빈을 사용할 수 없어 수동으로 선언해준다.

  - 이런식으로 내부적으로는 jdbc로 구현되어 있는 듯 하다. 옆에보면 Mongo도 구현되어있는걸보면 jobRepository로 몽고도 사용할 수 있는듯.

```java
@Bean
@Primary
public JobRepository jobRepository() throws Exception {
    JobRepositoryFactoryBean jobRepositoryFactoryBean = new JobRepositoryFactoryBean();
    jobRepositoryFactoryBean.setDataSource(dataSource());
    jobRepositoryFactoryBean.setIncrementerFactory(new DefaultDataFieldMaxValueIncrementerFactory(dataSource()));
    jobRepositoryFactoryBean.setTransactionManager(transactionManager());
    jobRepositoryFactoryBean.setDatabaseType("POSTGRES");
    jobRepositoryFactoryBean.setJobKeyGenerator(new DefaultJobKeyGenerator());
    jobRepositoryFactoryBean.setJdbcOperations(new JdbcTemplate(dataSource()));
    jobRepositoryFactoryBean.setConversionService(new DefaultConversionService());
    jobRepositoryFactoryBean.setSerializer(new DefaultExecutionContextSerializer());
    jobRepositoryFactoryBean.setIsolationLevelForCreate("ISOLATION_DEFAULT");
    return jobRepositoryFactoryBean.getObject();
}
```

@Primary 선언을 하지 않으면 시스템이 기본으로 만드는 jobRepository의 우선순위에 밀리기 때문에 선언해주어야 한다. 
  - 시스템이 직접 만들(려고 시도하는)dataSource는 우리가 아무런 config도 작성하지 않았기 때문에 스프링부트가 자동으로 만든 jobRepository가 주입됨 > 이것에 의해 스프링부트가 자동으로 dataSource를 만듬 > 근데 우리는 spring.application.datasource 에 컨피그를 작성안함 > url 입력해달라고 오류뱉음 대충 이런 흐름이다.
사용예)

```java
@Configuration
@Slf4j(topic = "ListedStockPrice")
@RequiredArgsConstructor
@ConditionalOnProperty(name = "JOB_NAME", havingValue = "ListedStockPrice")
public class ListedStockPriceListener implements ApplicationRunner {
...........중략
@Override
public void run(ApplicationArguments args) throws Exception {
    TaskExecutorJobLauncher jobLauncher = new TaskExecutorJobLauncher();

    jobLauncher.setJobRepository(jobRepository);
    jobLauncher.setTaskExecutor(task -> {
        log.info("ListedStockPrice 적재 시작 @@@@@@");
        task.run();
    });
    jobLauncher.run(priceBatchJob(),jobParameters());
}
@Bean
public Job priceBatchJob() {
    return new JobBuilder(jobName, jobRepository)
            .start(listedStockPriceStep())
            .build();
}
```

실제 batch를 실행하는 ApplicationRunner(구 CommandLineRunner)부분에서 jobLauncher에 jobRepository를 주입하는데, 이럴때 필요하다.
jobLauncher가 priceBatchJob 을 기동할 때 배치 메타테이블에 STARTED, COMPLETED, FAILED, UNKNOWN을 쳐야하는데 해당 jobRepository를 통해 CRUD 연산을 수행한다고 생각하면 편함.


## TransactionManager

기존에 메타 db의 위치와 비즈니스 db의 위치가 같은 경우 datasource가 하나이므로 transactionmanager가 하나이면 됐지만, 현재는 db가 다른 관계로 두 개의 transactionManager를 사용한다
Spring batch에서 jobRepository의 트랜잭션 관리는 PlatformTransactionManager를 기본으로 사용하고, 비즈니스 db의 트랜잭션 관리도 원래는 그냥 저 PlatformTransactionManager를 사용하면 되겠지만 지금은 각각 타겟 db가 다르므로 별도의 JpaTransactionManager를 선언한다. 
이 JpaTransactionManager는  비즈니스 db의 트랜잭션을 관리해야 하기 때문에 businessDataSource를 주입받는다. 

```java
@Bean(value="transactionManager")
@Primary
public PlatformTransactionManager transactionManager(){
    return new DataSourceTransactionManager(dataSource());
}
```


```java
@Bean
public JpaTransactionManager jpaTransactionManager() {
    JpaTransactionManager jpaTransactionManager = new JpaTransactionManager();
    jpaTransactionManager.setDataSource(businessDataSource());
    return jpaTransactionManager;
}
```

앞으로 배치 관련 transactionManager를 달라고 한다 > transactionManager를 주입, 비즈니스 테이블에 접근할려고 할 때 transactionManager를 달라고 한다 > jpaTransactionManager를 주입 하면 된다.
현재 샘플 프로젝트의 비즈니스 부분은 순수 Jpa를 사용하여 구현하였기 때문에 jpaTransactionManager를 사용하지만 그렇지 않다면 다른 transactionManager(예컨데 dataSourceTransactionManager, platformTransactionManager)를 선언하고 주입하면 된다.
사용예)

```java
@Bean("listedStockPriceStep")
public Step listedStockPriceStep() {
    log.info("##listedStockPriceStep 기동##");
    return new StepBuilder("listedStockPriceStep",jobRepository)
            .<String, List<ListedStockPrice>>chunk(5,jpaTransactionManager)
            .reader(priceItemReader())
            .processor(priceItemProcessor())
            .transactionManager(jpaTransactionManager) //데이터소스 여러개인 경우 여기마저도 수동으로 해야함
            .writer(priceItemWriter())
            .build();
}
```

Step을 기동할 때 batch_step_execution과 같은 메타테이블에 crud 해야하므로 StepBuilder시에 어떤 Batch DB에 CRUD 할지 정해야 하므로 jobRepository를 주입해야함. 
하지만 실제 비즈니스 부분의 트랜잭션은 비즈니스 db와 연결되어있는 트랜잭션 매니저(여기서는 Jpa를 사용하였기때문에 jpaTransactionManager)를 주입해야 reader,processor,writer 에서 트랜잭션 관리할 때 비즈니스 db를 찌른다.

## EntityManagerFactory

이건 Jpa를 사용하기 때문에 필요해진 빈이라 optional 이다. 아마 이건 자동으로 빌드되는 영역에 들어갈 것 같기는 하지만 @Primary datasource 가 배치 db를 바라보고 있기 때문에 기본 entityManagerFactory를 사용하면 비즈니스 Db가 아닌 배치 db를 바라볼 것이다.
실제 JpaItemWriter,JpaItemReader를 사용할 때 jpa 를 통한 crud 연산을 수행하기 때문에 필요하다.
jpa를 사용하지 않는다면 필요하지 않다. 우리가 인터넷에 찾아보면 하이버네이트의 영속성 컨텍스트 - 실제 db 사이를 관리하기 위해 필요한 객체라고 생각하면 됨.
 

```java
@Bean
public LocalContainerEntityManagerFactoryBean entityManagerFactory() {
    LocalContainerEntityManagerFactoryBean factoryBean = new LocalContainerEntityManagerFactoryBean();
    factoryBean.setDataSource(businessDataSource());
    factoryBean.setPackagesToScan("com.kbank.convenience.stock.*"); // JPA 엔티티 패키지 경로

    JpaVendorAdapter vendorAdapter = new HibernateJpaVendorAdapter();
    factoryBean.setJpaVendorAdapter(vendorAdapter);

    Properties jpaProperties = new Properties();
    jpaProperties.put("hibernate.dialect", "org.hibernate.dialect.PostgreSQLDialect");
    jpaProperties.put("hibernate.hbm2ddl.auto", "none");
    jpaProperties.put("hibernate.show_sql", "true");
    jpaProperties.put("hibernate.format_sql", "true");
    factoryBean.setJpaProperties(jpaProperties);

    return factoryBean;
}
```

사용예)

```java
@Bean
public ItemWriter<List<ListedStockPrice>> priceItemWriter() {
    JpaItemWriter<ListedStockPrice> itemWriter = new JpaItemWriterBuilder<ListedStockPrice>()
            .entityManagerFactory(entityManagerFactory)
            .build();
    JpaItemsWriter<ListedStockPrice> listedStockPriceJpaItemsWriter = new JpaItemsWriter<>(itemWriter);
    listedStockPriceJpaItemsWriter.setEntityManagerFactory(entityManagerFactory);
    return listedStockPriceJpaItemsWriter;
}
```

 JpaItemsWriter는 List<엔티티>를 직접 지원하진 않아서 이렇게 만든것

```java
@RequiredArgsConstructor
public class JpaItemsWriter<T> extends JpaItemWriter<List<T>> {
    private final JpaItemWriter<T> jpaItemWriter;
    @Override
    public void write(Chunk<? extends List<T>> items) {
        Chunk<T> toBeWritten = new Chunk<>();
        for(var item: items){
            toBeWritten.addAll(item);
        }
        jpaItemWriter.write(toBeWritten);
    }
}

```


![](https://prod-files-secure.s3.us-west-2.amazonaws.com/c38aebd7-2834-4fac-b2fc-a2f0c17ce81d/f874171b-40d8-480e-93b0-05615364b89a/image.png)

이런 식으로 배치 인스턴스는 배치 db에, 비즈니스 내용은 비즈니스 db에 저장됨. 끝. 

참고)
[Spring에서 transactionManager와 entityManager 차이에 대해 아시나요?](https://goodgid.github.io/Spring-Difference-TransactionManager-EntityManager/)
[Spring Batch TransactionManager 개념, 구현체 종류와 특징](https://chung-develop.tistory.com/146#PlatformTransactionManager%20%EA%B5%AC%ED%98%84%EC%B2%B4%20%EC%A2%85%EB%A5%98%EC%99%80%20%ED%8A%B9%EC%A7%95-1)
[[Spring Batch] 4장 : 잡 설정 및 실행(Configuring and Running a Job) 2](https://tech-monster.tistory.com/237)




### 20250211 추가)

해당 포스트는 ResourceLessJobRepository의 등장으로 인메모리로 적재를 한다면 안써도 됨.
Spring Batch 5.2.0-M2(2024년 11월쯤?) 에 다시 지원한듯 ㅋㅋ
