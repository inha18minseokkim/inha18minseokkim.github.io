---
title: "뻘짓) Spring Batch 5 + Multiple DataSource"
date: 2023-10-10
tags: [미지정]
category:
  - 기술
---

목적
  - 그냥 개인이 스프링 배치 프로그램을 만드는데 Job을 돌리는데 귀찮음
  - 그래서 갑자기 생각이 듦. 배치 관련 메타데이터를 인메모리 처리해버리면 그냥 런자체는 편하게 할 수 있지 않을까
뻘짓시작

1. application.properties

```yaml
 server:
  port: 8888
dataPortal:
  secret: "Rujw+Isa8li+a/gKuQ2M5xnXH9wNS8evvDQnU1h+pRTcm+QpzUcAMi7woS1urDmsbRycaM0/cBhToF1ut2BQyw=="

spring:
  h2:
    console:
      enabled: true
  batch:
    job:
      enabled: true
    initialize-schema: embedded
    jdbc:
      initialize-schema: embedded
  datasource:
    batch-properties:
      driver-class-name: org.h2.Driver
      url: jdbc:h2:mem:testdb;MODE=MySQL;DB_CLOSE_DELAY=-1
      jdbc-url: jdbc:h2:mem:testdb;MODE=MySQL;DB_CLOSE_DELAY=-1
      username: sa
    work-properties:
      driver-class-name: com.mysql.cj.jdbc.Driver
      url: jdbc:mysql://3.39.94.242:55386/FINService
      jdbc-url: jdbc:mysql://3.39.94.242:55386/FINService
      username: root
      password: admin
  jpa:
    show-sql: true
    hibernate:
      ddl-auto: create
      naming:
        physical-strategy: org.hibernate.boot.model.naming.PhysicalNamingStrategyStandardImpl
    properties:
      hibernate:
        show_sql: true
        dialect: org.hibernate.dialect.MySQL57Dialect
    #database-platform: org.hibernate.dialect.H2Dialect
    database-platform: org.hibernate.dialect.MySQL57Dialect
  main:
    web-application-type: none
    allow-bean-definition-overriding: true


logging:
  level:
    org.springframework: DEBUG
```

  -       url: jdbc:h2:mem:testdb;MODE=MySQL;DB_CLOSE_DELAY=-1 여기서 DB_CLOSE_DELAY=-1 지정하지 않으면 에러 발생. 사유 : 인메모리 DB에서 배치 관련 메타테이블 만들고 난 다음(Spring에서 BatchAutoConfigure) DB 연결을 한번 끊는데 거기서 만들어놨던 DB 소실됨.. 인메모리 특수성인듯하다
  - 참고
  - [https://stackoverflow.com/questions/5763747/h2-in-memory-database-table-not-found](https://stackoverflow.com/questions/5763747/h2-in-memory-database-table-not-found)

  - datasource를 batch-properties와 work-properties로 나눔
2. DatasourceConfiguration

```java
@Configuration
public class DataSourceConfiguration {
    @Primary
    @Bean(value = "dataSource")
    @ConfigurationProperties(prefix = "spring.datasource.batch-properties")
    public DataSource datasource() {
        DriverManagerDataSource dataSource = new DriverManagerDataSource();
        return dataSource;
    }

    @Bean("platformTransactionManager")
    public PlatformTransactionManager platformTransactionManager(@Qualifier("dataSource")DataSource dataSource){
        return new DataSourceTransactionManager(dataSource);
    }
    //@Primary
    @Bean(value = "secondDataSource")
    @ConfigurationProperties(prefix = "spring.datasource.work-properties")
    public DataSource workDataSource() {
        DriverManagerDataSource dataSource = new DriverManagerDataSource();
        return dataSource;
    }
    @Bean("secondPlatformTransactionManager")
    public PlatformTransactionManager secondPlatformTransactionManager(@Qualifier("secondDataSource")DataSource dataSource){
        return new DataSourceTransactionManager(dataSource);
    }
}
```

  - 사용한 프로퍼티를 기준으로 Datasource를 두 개 만듬. 여기서 기본으로 사용할 inmemory datasource는 Primary 필요
3. JobRepositoryConfiguration

```java
@Configuration
public class JobRepositoryConfiguration {
    @Bean
    public JobRepository jobRepository(@Qualifier("dataSource") DataSource dataSource,
                                       PlatformTransactionManager transactionManager) throws Exception {
        JobRepositoryFactoryBean jobRepositoryFactoryBean = new JobRepositoryFactoryBean();
        jobRepositoryFactoryBean.setDataSource(dataSource);
        jobRepositoryFactoryBean.setTransactionManager(transactionManager);
        jobRepositoryFactoryBean.setIsolationLevelForCreate("ISOLATION_DEFAULT");
        return jobRepositoryFactoryBean.getObject();
    }
}
```

  - 배치 에서 사용할 datasource를 명시적으로 주입받아서 JobRepository 가져옴
4. 어디서 가져온것 참조.

```java
public class DatabaseConfigUtils {
    public static final String BASE_PACKAGE = "com.example.housingfinanceloanrate";
    public static final String ENTITY_PACKAGE = BASE_PACKAGE + ".Entity";
    public static final String REPOSITORY_PACKAGE = BASE_PACKAGE + ".Repository";


    private DatabaseConfigUtils() {
        throw new IllegalStateException("Utility class");
    }


    public static LocalContainerEntityManagerFactoryBean entityManagerFactoryBean(
            String persistenceUnitName, DataSource dataSource) {
        LocalContainerEntityManagerFactoryBean emf = new LocalContainerEntityManagerFactoryBean();
        emf.setPersistenceUnitName(persistenceUnitName);
        emf.setDataSource(dataSource);
        emf.setJpaVendorAdapter(jpaVendorAdapters());
        emf.setPackagesToScan(ENTITY_PACKAGE);
        emf.setJpaProperties(jpaProperties());

        return emf;
    }

    public static JpaTransactionManager jpaTransactionManager(EntityManagerFactory entityManagerFactory) {
        JpaTransactionManager jpaTransactionManager = new JpaTransactionManager();
        jpaTransactionManager.setEntityManagerFactory(entityManagerFactory);
        jpaTransactionManager.setJpaDialect(new HibernateJpaDialect());

        return jpaTransactionManager;

    }

    static Properties jpaProperties() {
        Properties properties = new Properties();
        System.out.println("@@@@@@@@@@@@@@@");
        properties.setProperty("hibernate.show_sql", "true");
        properties.setProperty("hibernate.format_sql", "false");
        properties.setProperty("hibernate.use_sql_comments", "false");
        properties.setProperty("hibernate.globally_quoted_identifiers", "true");

        properties.setProperty("hibernate.temp.use_jdbc_metadata_defaults", "false");

        properties.setProperty("hibernate.jdbc.batch_size", "5000");
        properties.setProperty("hibernate.order_inserts", "true");
        properties.setProperty("hibernate.order_updates", "true");
        properties.setProperty("hibernate.jdbc.batch_versioned_data", "true");

        properties.setProperty("spring.jpa.hibernate.jdbc.batch_size", "5000");
        properties.setProperty("spring.jpa.hibernate.order_inserts", "true");
        properties.setProperty("spring.jpa.hibernate.order_updates", "true");


        //properties.setProperty("spring.batch.jdbc.initialize-schema", "always");
        //properties.setProperty("spring.batch.initialize-schema", "always");
        //properties.setProperty("spring.jpa.hibernate.ddl-auto", "create");

        properties.setProperty("spring.jpa.hibernate.jdbc.batch_versioned_data", "true");
        properties.setProperty("spring.jpa.properties.hibernate.jdbc.batch_size", "5000");
        properties.setProperty("spring.jpa.properties.hibernate.order_inserts", "true");
        properties.setProperty("spring.jpa.properties.hibernate.order_updates", "true");
        properties.setProperty("spring.jpa.properties.hibernate.jdbc.batch_versioned_data", "true");
        return properties;
    }

    static JpaVendorAdapter jpaVendorAdapters() {
        HibernateJpaVendorAdapter hibernateJpaVendorAdapter = new HibernateJpaVendorAdapter();
        hibernateJpaVendorAdapter.setDatabasePlatform("org.hibernate.dialect.MySQL57Dialect");
        //hibernateJpaVendorAdapter.setDatabasePlatform("org.hibernate.dialect.H2Dialect");



        return hibernateJpaVendorAdapter;
    }

}
```

  - EntityManagerFactory를 사용하여 hibernate를 수동으로 설정(application.properties)에서 사용하는 hibernate 관련 변수들은 배치 repository인 Inmemory Datasource와 연관이 있기 때문에 여기서 수동으로 설정.
  - 그리고 패키지 이름을 명시하면 entityManager가 자동으로 주입받은 Datasource를 활용하여 그 패키지에 있는 Repository, Entity들은 다 해당 데이터소스 영향 아래 있는것같음

  - +) @EnableBatchProcessing 을 선언하거나 DefaultBatchConfiguration을 상속하는 Configuration을 작성하는 경우 기존에 스프링 부트에서 해주던 자동 배치 환경 설정을 하지 않음. 스프링 배치 5 부터 적용된 사항임. 꼭 기억해놓자
  - [https://stackoverflow.com/questions/75619930/spring-batch-5-and-spring-boot-3-meta-data-tables-not-created-when-using-program](https://stackoverflow.com/questions/75619930/spring-batch-5-and-spring-boot-3-meta-data-tables-not-created-when-using-program)


### 문제점

로컬환경과 테스트, 실제 운영환경이 많이 다름(로컬환경에서는 2개의 DataSource(h2 Inmemory, DB서버), 실제 프로덕션 환경에서는 하나)
그래서 이건 진짜 로컬테스트 아니면 못쓸듯
차라리 배치 인스턴스 테이블에 JobParameter를 시간단위로 넣어서 로컬테스트 시 똑같은 잡을 여러 번 실행할 수 있게 하자..


### 202408 추가

만약에 각 서브도메인별로 배치 테이블을 관리하는 것이 아니라 MSA 공통 서브도메인이 나와서 온라인 서비스 말고 spring batch를 사용하는 컨테이너의 실행이력같은것을 중앙에서 관리한다고 하면 이 뻘짓이 의미가 있을수도 있을 듯 하다..

### 20250120 추가


묵혀놓은 프로젝트를 쓸 일이 생겼다.