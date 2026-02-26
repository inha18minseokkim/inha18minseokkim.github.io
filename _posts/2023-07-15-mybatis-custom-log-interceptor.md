---
title: "MyBatis 쿼리 파라미터 로깅 - Custom Interceptor 구현"
date: 2023-07-15
tags: [Java, MyBatis, Spring, 디버깅, 삽질]
category:
  - 기술
---

MSA 마이그레이션 통합 테스트 중 MyBatis 쿼리 로그에 파라미터 바인딩이 표시되지 않아서 Custom Interceptor를 구현했다.

## 문제 상황

```sql
insert into ProductPriceInfo (hprice,lprice,productId,receiveDate) values (?,?,?,?)
insert into ProductPriceInfo (hprice,lprice,productId,receiveDate) values (?,?,?,?)
```

`?`가 실제 값으로 치환되어 출력되길 원했는데, DEBUG 레벨 로그에도 파라미터 바인딩이 보이지 않았다. 레거시 BXM 프레임워크의 이클립스 환경에서는 됐었는데 Spring 환경으로 오면서 안 됨.

## 해결 방법 검토

1. Lombok 없이 Custom log4j 구현
2. **MyBatis Interceptor 사용** ← 선택
3. Log4jdbc 프록시 JDBC 드라이버 사용 (폐쇄망 Nexus에 라이브러리 없어서 불가)

MyBatis가 자체 Interceptor 기능을 제공한다는 걸 알고 방법 2를 선택했다.

---

## Custom MyBatis Interceptor 구현

```java
@Intercepts({
    @Signature(type = Executor.class, method = "update",
               args = {MappedStatement.class, Object.class}),
    @Signature(type = Executor.class, method = "query",
               args = {MappedStatement.class, Object.class, RowBounds.class,
                       ResultHandler.class, CacheKey.class, BoundSql.class})
})
@Slf4j
public class CustomLogInterceptor implements Interceptor {

    @Override
    public Object intercept(Invocation invocation) throws Throwable {
        MappedStatement mappedStatement = (MappedStatement) invocation.getArgs()[0];
        Object parameter = invocation.getArgs()[1];
        BoundSql boundSql = mappedStatement.getBoundSql(parameter);

        log.info("=============================");
        log.info(construct(boundSql, parameter));
        log.info("=============================");

        return invocation.proceed();
    }

    private String construct(BoundSql boundSql, Object originalParameter)
            throws IllegalAccessException, NoSuchFieldException {
        String sql = boundSql.getSql();
        Object parameterObject = boundSql.getParameterObject();
        List<ParameterMapping> parameterMappings = boundSql.getParameterMappings();

        if (parameterObject != null && parameterMappings != null) {
            List<String> parameters = new ArrayList<>();
            for (ParameterMapping parameterMapping : parameterMappings) {
                String property = parameterMapping.getProperty();
                Class<?> originalClass = originalParameter.getClass();
                Field field = originalClass.getDeclaredField(property);
                field.setAccessible(true);
                Object originalValue = field.get(originalParameter);
                parameters.add(originalValue.toString());
            }
            for (String parameterValue : parameters) {
                sql = sql.replaceFirst("\\?", Matcher.quoteReplacement(parameterValue));
            }
        }
        return sql;
    }

    @Override
    public Object plugin(Object target) {
        return Plugin.wrap(target, this);
    }

    @Override
    public void setProperties(Properties properties) {
        Interceptor.super.setProperties(properties);
    }
}
```

### Spring 설정

```java
@Configuration
public class MyBatisConfig {

    @Bean
    public CustomLogInterceptor customLogInterceptor() {
        return new CustomLogInterceptor();
    }

    @Bean
    public org.apache.ibatis.session.Configuration myBatisConfiguration(
            CustomLogInterceptor customLogInterceptor) {
        org.apache.ibatis.session.Configuration configuration =
            new org.apache.ibatis.session.Configuration();
        configuration.addInterceptor(customLogInterceptor);
        return configuration;
    }
}
```

---

## 설계 포인트

- 매핑 로직은 선언 순서가 아닌 **DTO 필드명과 MyBatis 매퍼 컬럼명을 매칭**
- 필드 수가 다를 때도 강건하게 동작
- `field.setAccessible(true)`: 프라이빗 필드도 리플렉션으로 접근 가능

## 추가 고민

- 이 방식은 로깅 실패 시 다운스트림 문제를 야기할 수 있으므로, 프로덕션에서는 try-catch로 감싸는 게 안전하다
- 장기적으로는 MyBatis → JPA 마이그레이션이 바람직하지만, 기존 DB 스키마가 JPA 관례와 달라서 즉각 마이그레이션은 불가
- Log4jdbc 방식(bgee 라이브러리)이 더 간단하지만 내부 폐쇄망 Nexus에서 사용 불가였음

### 결론
정보보호팀에 문의해서 방화벽 레벨을 협의하여 bgee log4jdbc를 사용 ㅋㅋ