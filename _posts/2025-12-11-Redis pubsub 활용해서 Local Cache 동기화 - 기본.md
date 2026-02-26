---
title: "Redis pub/sub 활용해서 Local Cache 동기화 - 기본"
date: 2025-12-11
tags: [미지정]
category:
  - 기술
---

해당 세션을 보고 하나씩 따라해보는 중이다.

### 목표

redis sub을 사용해서 레디스에서 특정 키를 invalidate 하라는 sub을 받으면 로컬 Caffeine Cache에 해당하는 키를 invalidate

![](attachment:8f18e6b9-f256-44bf-9037-9f8c59e5c53e:image.png)

실제 invalidate publish 를 하는 서버 중 하나

```kotlin
publish __redis__:invalidate User:getUser:1
```

pub 한 메세지를 sub 한 클라이언트의 로그

```kotlin
kimminseok@MacBook-Pro-16 ~ % redis-cli
127.0.0.1:6379> subscribe __redis__:invalidate
1) "subscribe"
2) "__redis__:invalidate"
3) (integer) 1
1) "message"
2) "__redis__:invalidate"
3) "User:getUser:1"
Reading messages... (press Ctrl-C to quit or any key to type command)
```

이걸 사용해서 invalidate 시키면 됨


```kotlin
    private val logger = LoggerFactory.getLogger(CacheInvalidationService::class.java)
    private val REDIS_INVALIDATION_CHANNEL = "__redis__:invalidate"
    private var subscription: Disposable? = null

    /**
     * Initializes the Redis subscription when the service starts.
     */
    @PostConstruct
    fun init() {
        logger.info("Starting Redis cache invalidation listener on channel: $REDIS_INVALIDATION_CHANNEL")
        
        val topic = ChannelTopic(REDIS_INVALIDATION_CHANNEL)
        
        subscription = reactiveRedisTemplate.listenTo(topic)
            .map { message -> message.message.toString() }
            .doOnNext { message -> 
                logger.info("Received cache invalidation message: $message")
                invalidateCache(message)
            }
            .doOnError { error ->
                logger.error("Error in Redis subscription: ${error.message}", error)
            }
            .subscribe()
    }

```

__redis__:invalidate 를 subscribe 하고 메세지 파싱해서 cache invalidate 시킴

```kotlin
private fun invalidateCache(message: String) {
        logger.info("Invalidate Message detected : $message")
        try {
            // Find the matching cache key from the CacheKey enum
            val matchingCacheKey = CacheKey.values().find { cacheKey ->
                message.startsWith(cacheKey.key)
            }

            if (matchingCacheKey != null) {
                val cache = cacheManager.getCache(matchingCacheKey.key)
                
                if (cache != null) {
                    // Extract the ID from the message (e.g., "1" from "User:getUser:1")
                    val id = message.substring(matchingCacheKey.key.length + 1) // +1 for the colon
                    
                    logger.info("Invalidating cache entry: ${matchingCacheKey.key} with ID: $id")
//                    cache.invalidate()
                    logger.info("${cache.get("$id")}")
                    logger.info("캐시 삭제 결과 : ${cache.evictIfPresent(id)}")
                    logger.info("Cache entry invalidated successfully")
                } else {
                    logger.warn("Cache not found for key: ${matchingCacheKey.key}")
                }
            } else {
                logger.warn("No matching cache key found for message: $message")
            }
        } catch (e: Exception) {
            logger.error("Error invalidating cache for message: $message", e)
        }
```


해당 메세지를 받아서 invalidate 하는 서비스 3개

8081 포트로 인스턴스 1번

```kotlin
2025-12-11T21:51:08.014+09:00  INFO 16919 --- [local-redis-invalidate] [           main] o.s.boot.reactor.netty.NettyWebServer    : Netty started on port 8081 (http)
2025-12-11T21:51:08.018+09:00  INFO 16919 --- [local-redis-invalidate] [           main] o.e.l.LocalRedisInvalidateApplicationKt  : Started LocalRedisInvalidateApplicationKt in 2.301 seconds (process running for 2.654)
2025-12-11T21:51:33.990+09:00  INFO 16919 --- [local-redis-invalidate] [ctor-http-nio-3] o.e.l.controller.UserController          : Received request to get user with ID: 1
2025-12-11T21:51:34.019+09:00  INFO 16919 --- [local-redis-invalidate] [ctor-http-nio-3] o.e.l.service.UserService                : Cache miss for user with ID: 1, retrieving from database
2025-12-11T21:51:34.100+09:00  INFO 16919 --- [local-redis-invalidate] [ctor-http-nio-3] o.e.l.controller.UserController          : Retrieved user: UserDto(id=1, name=aa)
2025-12-11T21:51:44.215+09:00  INFO 16919 --- [local-redis-invalidate] [ioEventLoop-5-2] o.e.l.service.CacheInvalidationService   : Received cache invalidation message: User:getUser:1
2025-12-11T21:51:44.215+09:00  INFO 16919 --- [local-redis-invalidate] [ioEventLoop-5-2] o.e.l.service.CacheInvalidationService   : Invalidate Message detected : User:getUser:1
2025-12-11T21:51:44.215+09:00  INFO 16919 --- [local-redis-invalidate] [ioEventLoop-5-2] o.e.l.service.CacheInvalidationService   : Invalidating cache entry: User:getUser with ID: 1
2025-12-11T21:51:44.217+09:00  INFO 16919 --- [local-redis-invalidate] [ioEventLoop-5-2] o.e.l.service.CacheInvalidationService   : ValueWrapper for [UserDto(id=1, name=aa)]
2025-12-11T21:51:44.218+09:00  INFO 16919 --- [local-redis-invalidate] [ioEventLoop-5-2] o.e.l.service.CacheInvalidationService   : 캐시 삭제 결과 : true
2025-12-11T21:51:44.218+09:00  INFO 16919 --- [local-redis-invalidate] [ioEventLoop-5-2] o.e.l.service.CacheInvalidationService   : Cache entry invalidated successfully
```

8082 포트로 인스턴스 2번

```kotlin
2025-12-11T21:51:22.852+09:00  INFO 17283 --- [local-redis-invalidate] [           main] o.s.boot.reactor.netty.NettyWebServer    : Netty started on port 8082 (http)
2025-12-11T21:51:22.857+09:00  INFO 17283 --- [local-redis-invalidate] [           main] o.e.l.LocalRedisInvalidateApplicationKt  : Started LocalRedisInvalidateApplicationKt in 2.299 seconds (process running for 2.649)
2025-12-11T21:51:36.619+09:00  INFO 17283 --- [local-redis-invalidate] [ctor-http-nio-3] o.e.l.controller.UserController          : Received request to get user with ID: 1
2025-12-11T21:51:36.655+09:00  INFO 17283 --- [local-redis-invalidate] [ctor-http-nio-3] o.e.l.service.UserService                : Cache miss for user with ID: 1, retrieving from database
2025-12-11T21:51:36.712+09:00  INFO 17283 --- [local-redis-invalidate] [ctor-http-nio-3] o.e.l.controller.UserController          : Retrieved user: UserDto(id=1, name=aa)
2025-12-11T21:51:44.211+09:00  INFO 17283 --- [local-redis-invalidate] [ioEventLoop-5-2] o.e.l.service.CacheInvalidationService   : Received cache invalidation message: User:getUser:1
2025-12-11T21:51:44.211+09:00  INFO 17283 --- [local-redis-invalidate] [ioEventLoop-5-2] o.e.l.service.CacheInvalidationService   : Invalidate Message detected : User:getUser:1
2025-12-11T21:51:44.211+09:00  INFO 17283 --- [local-redis-invalidate] [ioEventLoop-5-2] o.e.l.service.CacheInvalidationService   : Invalidating cache entry: User:getUser with ID: 1
2025-12-11T21:51:44.214+09:00  INFO 17283 --- [local-redis-invalidate] [ioEventLoop-5-2] o.e.l.service.CacheInvalidationService   : ValueWrapper for [UserDto(id=1, name=aa)]
2025-12-11T21:51:44.216+09:00  INFO 17283 --- [local-redis-invalidate] [ioEventLoop-5-2] o.e.l.service.CacheInvalidationService   : 캐시 삭제 결과 : true
2025-12-11T21:51:44.216+09:00  INFO 17283 --- [local-redis-invalidate] [ioEventLoop-5-2] o.e.l.service.CacheInvalidationService   : Cache entry invalidated successfully
```

8083 포트로 인스턴스 3번

```kotlin
2025-12-11T21:51:27.425+09:00  INFO 17293 --- [local-redis-invalidate] [           main] o.s.boot.reactor.netty.NettyWebServer    : Netty started on port 8083 (http)
2025-12-11T21:51:27.429+09:00  INFO 17293 --- [local-redis-invalidate] [           main] o.e.l.LocalRedisInvalidateApplicationKt  : Started LocalRedisInvalidateApplicationKt in 2.252 seconds (process running for 2.59)
2025-12-11T21:51:38.108+09:00  INFO 17293 --- [local-redis-invalidate] [ctor-http-nio-3] o.e.l.controller.UserController          : Received request to get user with ID: 1
2025-12-11T21:51:38.136+09:00  INFO 17293 --- [local-redis-invalidate] [ctor-http-nio-3] o.e.l.service.UserService                : Cache miss for user with ID: 1, retrieving from database
2025-12-11T21:51:38.189+09:00  INFO 17293 --- [local-redis-invalidate] [ctor-http-nio-3] o.e.l.controller.UserController          : Retrieved user: UserDto(id=1, name=aa)
2025-12-11T21:51:44.211+09:00  INFO 17293 --- [local-redis-invalidate] [ioEventLoop-5-2] o.e.l.service.CacheInvalidationService   : Received cache invalidation message: User:getUser:1
2025-12-11T21:51:44.211+09:00  INFO 17293 --- [local-redis-invalidate] [ioEventLoop-5-2] o.e.l.service.CacheInvalidationService   : Invalidate Message detected : User:getUser:1
2025-12-11T21:51:44.211+09:00  INFO 17293 --- [local-redis-invalidate] [ioEventLoop-5-2] o.e.l.service.CacheInvalidationService   : Invalidating cache entry: User:getUser with ID: 1
2025-12-11T21:51:44.215+09:00  INFO 17293 --- [local-redis-invalidate] [ioEventLoop-5-2] o.e.l.service.CacheInvalidationService   : ValueWrapper for [UserDto(id=1, name=aa)]
2025-12-11T21:51:44.216+09:00  INFO 17293 --- [local-redis-invalidate] [ioEventLoop-5-2] o.e.l.service.CacheInvalidationService   : 캐시 삭제 결과 : true
2025-12-11T21:51:44.216+09:00  INFO 17293 --- [local-redis-invalidate] [ioEventLoop-5-2] o.e.l.service.CacheInvalidationService   : Cache entry invalidated successfully

```



### 요약

broadcasting 으로 레디스가 뿌려주면 알아서 invalidate 하는 로직
invalidate를 해 주지만 redis connection fail 시 캐시 최신화 문제를 방지하기 위해 최후의 보루로 caffeine cache에 ttl을 넣으면 좋긴 할듯 함.
  - 만약 redis 연결 문제가 생기면 자체적인 로컬 캐시 사이클로 라도 서비스가 되도록.
  - 로컬 캐시에 ttl이 없는 상태에서 redis fail시 캐시 갱신은 재기동 하지 않는이상 영원히 되지 않음



### 의문점 및 알아봐야 할 문제점

1. 그냥 invalidate 해버리면 thundering herd problem이 있을 수 있음
  - 모두 같은 시점에 cache invalidate 되고 invalidate 되어버리는 순간 동시에 db를 같이 쳐버릴것이므로..
2. 예시를 User로 만들긴 했는데 User와 같이 개인화된 캐시는 동기화 문제가 해결된다고 하더라도 굳이 로컬로 가져갈 필요가 없을 듯 함. 오히려 안될 듯 함.
  - 캐시 공간이 고객 수에 비례해서 늘어나면 ttl을 짧게 가져가더라도 로컬로 부담이고 의미가 없음. 
    - 왜냐하면 특히 MSA 환경인 경우 인스턴스가 12개 이렇게 될텐데 12개 파드에 다 복사해놓더라도 cache hit 는 12개 중 하나에서만 일어나고 나머지는 쓸모가 없음
  - 공통으로 사용되니깐 로컬 캐시에 넣고 싶은데 ttl 때문에 파드간의 데이터 싱크 문제가 생겨서 울며 겨자먹기로 로컬 캐시를 사용하고 있는 경우에 유용하게 사용할듯



### pub할때 dto 정보를 넣을까 → 1번 문제에 대한 해답

pub 할때 키 정보만 주지말고  value 정보도 받아서 인스턴스가 해당 정보로 업데이트 치도록 하면?
결론) 일반적인 상황에서는 추천하지 않음
- 간단하게 가려면: 각 인스턴스 내부에서 Caffeine 로더 패턴으로 **per-instance herd만 줄이고** DB 최대 QPS를 감당할 수 있도록 사이징.
- 더 강하게 막으려면: Redis에 **per-key 분산 락 + 중앙 캐시 채우기** 레이어를 추가해서 전 시스템에서 해당 키는 한 번만 로드 하도록 설계.
위에서 했던것은 전자라고 생각하면 되고 pub할때 메세지까지 전달해서 아예 락으로 잡는건 추천하지 않는다.

## 왜 invalidate & reload on cache miss 보편적인가

- Redis pub/sub 메시지에는 “어떤 키가 바뀌었는지”만 넣고, 실제 값은 각 인스턴스가 다음 요청 시 DB/원천에서 가져와 캐싱하는 패턴이 단순하고 서비스 간 결합도가 낮다.
- value 자체를 메시지로 실어 나르면 타입/버전 관리, 메시지 유실 시 일관성 등이 복잡해져서, 대부분 시스템에서는 invalidate만 브로드캐스트하고 로드는 각자 하도록 설계한다.


### 결론

“local Caffeine cache sync용 Redis pub”이라면, 대부분은 “무효화(invalidate)만 pub/sub로 하고, 값은 각 인스턴스가 DB나 원천에서 다시 로드”하는 방식이 가장 단순하다.

그리고 로컬캐시가 동시에 invalidate 되어서 N개의 인스턴스가 한 번에 DB 조회하는것이 부담이 되지 않나요 의 문제는 요지가 아니다.
애초에 해당 쿼리의 QPS를 고려했을때 M명의 고객이 찌르는것보다는 N개의 인스턴스가 찌르는것으로 문제를 해결하려고 하는것.
그러므로 N개의 인스턴스에 대해 thundering herd problem을 걱정하는 것은 현 상황에서 적절하지는 않다.
