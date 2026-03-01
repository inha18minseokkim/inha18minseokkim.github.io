---
title: R2dbc Connection POOL 설정
date: 2025-10-16
tags:
  - DB
  - 개발
  - Java
  - Kotlin
  - R2dbc
category:
  - 기술
  - DB
---
DB 관련 개발 내용 정리.
# 문제상황

Postgresql 시퀀스 nextval을 호출하는데 자꾸 20씩 증가한다. INCREMENT BY 1 CACHE 20 이고 r2dbc Connection pool을 1로 조정해도 계속 20씩 증가함.

### 초기 진단

옆에 계시는분이 no cache로 가도 되니깐 no cache로 가야한다고 말씀하심. jpa 에서는 sequenceGenerator가 자동으로 관리해주는데(한번에 nextval 한 번 호출하는게 아니라  20번에 한 번 nextval 호출) r2dbc는 그게 안되기때문에 no cache가 맞다는 주장

### 반론
[[2024-03-04-PostgreSQL 시퀀스 + 캐시 주의점]]
2023년에 공부했던 내용으로 비추어보았을 때, cache는 db 와 연결되어 있는 세션별로 가지고 있어서 세션이 여러 개인 경우 , 연결이 끊겼다가 다시 연결되는 경우 시퀀스에 단층이 발생할 수 있지만 jdbc든 r2dbc든 물리적으로 db와 연결되어 있는 세션은 하나이기 때문에 시퀀스가 항상 20씩 증가하면 안됨(커넥션풀이 한 개고 연결이 지속되고 있다는 가정하에)
 이건 db 드라이버의 문제이지 r2dbc 자체의 문제는 아니었다고 생각함

### 까보기

커넥션풀 max_size 1 개, initial_size 1 개로 하고 커넥션타임아웃은 충분히 주고 끊기지 않도록 한 다음 계속 sequence generate를 해 보았다.

![[Pasted image 20260301231531.png]]


![[Pasted image 20260301231536.png]]

각 호출마다 항상 다른 pid를 가지고 온다

### 원래 postgresql pid는 쿼리 한 번 실행될 때 마다 계속 올라가나?

내가 알고있던것과 현상이 달라서 Perplexity에 물어봄. 한동안 커넥션을 유지하면 pid가 그동안은 일정해야 하는데 그렇지 않기 때문. 
A)
PostgreSQL에서 PID(프로세스 ID)는 커넥션을 나타내는 고유한 값으로, 해당 세션이 지속되는 동안 일정합니다. 즉, 쿼리를 여러 번 실행해도 PID는 변하지 않고 같은 값이 유지됩니다.
쿼리가 실행될 때마다 PID가 계속 올라가거나 변경되는 것은 아닙니다. 커넥션이 새로 생기거나 닫히면 새로운 PID가 할당되지만, 기존 커넥션 내에서는 일정한 값을 가집니다.
따라서, 같은 커넥션에서 여러 쿼리를 실행하면 늘 같은 PID가 반환되며, PID가 증가하는 현상은 커넥션 풀 등에서 커넥션이 새로 생성될 때 나타납니다.

---

요약:
- PostgreSQL PID는 커넥션 단위로 할당되는 프로세스 ID라 쿼리 한 번 실행할 때마다 증가하지 않습니다.
- PID는 커넥션이 바뀔 때만 변경됩니다.

근거1)
커넥션풀이기 때문에 세션을 계속 유지해야 하는데 그러면 pid 값이 달라지면 안됨. 근데 달라짐. 
그러니깐 세션이 끊겼다가 다시 연결되니 시퀀스 캐시를 버리고 20개씩 채번하는거
근거2)
pg_stat_activity 테이블을 보면 커넥션풀을 30개를 잡아놔도 해당 계정으로 연결되어있는 pid 수가 30개가 안된다. 

### 그러므로 커넥션풀이 제대로 동작하지 않았다

는것을 알 수 있었다


### 해결방법

asis)

```sql
@Bean
override fun connectionFactory: ConnectionFactory{
	return PostgresqlConnectionConfiguration.builder
	.host(host)
	.port(port.toInt)
	.database(name)
	.username(user)
	.password(password)
	.codecRegister(EnumCodec.builder.build)
	.connectTimeout(Duration.ofSeconds(CONNECT_TIMEOUT_SECONDS))
	.build
	.let {PostgresqlConnectionFactory }
}
@Bean
fun connectionPool(connectionFactory: ConnectionFactory): ConnectionPool {
	return ConnectionPoolConfiguration.builder
	.initialSize(INITIAL_SIZE)
	.maxSize(MAX_SIZE)
	.connectionFactory(connectionFactory)
	.build
	.let {ConnectionPool(it)}
}
```

tobe)

```sql
    override fun connectionFactory: ConnectionFactory {

        val connectionFactory = ConnectionFactories.get(
            builder
                .option(DRIVER, "pool")
                .option(HOST, host)
                .option(USER, userName)
                .option(PORT, port)
                .option(PASSWORD, passWord)
                .option(DATABASE, db)
                .build)

        val configuration = ConnectionPoolConfiguration.builder(connectionFactory)
            .maxIdleTime(Duration.ofSeconds(maxIdleTime))
            .maxCreateConnectionTime(Duration.ofSeconds(maxCreateConnectionTime))
            .maxLifeTime(Duration.ofMinutes(maxLife))
            .initialSize(initialSize)
            .maxSize(maxSize)
            .build

        return ConnectionPool(configuration)
    }

```

다른 ConnectionFactory Config에는 “pool”을 명시적으로 사용하는 옵션이 있었다;;

```
r2dbc-pool 소스를 디버그해보니 option(DRIVER, "pool")이 있고 없고에 따라서ConnectionFactoryProvider가 달라지는 것을 확인 함option(DRIVER, "mysql")로 설정시dev.miku.r2dbc.MySqlConnectionFactoryProvider가 동작하고option(DRIVER, "pool")로 설정시io.r2dbc.pool.PoolingConnectionFactoryProvider가 동작하는데dev.miku.r2dbc.MySqlConnectionFactoryProvider에는 initSize, maxSize에 대한 설정이 없고(github.com/mirromutth/r2dbc-mysqlgithub.com/mirromutth/r2dbc-mysql) 풀링되는 커넥션 팩토리가 아니기 때문에 그때그때마다 필요한 커넥션을 생성하는 방식이었음.
```


그래서 이 문제를 해결하니 테스트코드 실행 속도가 빨라짐;; 커넥션풀을 알고보니 계속 지혼자 생성하고 있던것;;


[r2dbc-pool 설정시 커넥션 풀이 제대로 생성되지 않은 케이스 확인](https://devsh.tistory.com/entry/r2dbc-pool-%EC%84%A4%EC%A0%95%EC%8B%9C-%EC%BB%A4%EB%84%A5%EC%85%98-%ED%92%80%EC%9D%B4-%EC%A0%9C%EB%8C%80%EB%A1%9C-%EC%83%9D%EC%84%B1%EB%90%98%EC%A7%80-%EC%95%8A%EC%9D%80-%EC%BC%80%EC%9D%B4%EC%8A%A4-%ED%99%95%EC%9D%B8#google_vignette)