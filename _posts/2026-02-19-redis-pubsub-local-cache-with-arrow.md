---
title: Redis pub/sub 활용해서 Local Cache 동기화 - kotlin arrow 응용
date: 2026-02-19
tags:
  - Redis
  - Cache
  - Kotlin
  - Spring
  - arrow
---
([])
코틀린 코루틴 스코프 상에서는 어노테이션 보다는 함수형으로 처리하는것이 좋기 때문에 arrow를 사용해서 캐시 공통화를 해보도록 하겠다.

### cacheEither(cacheManager,cacheKey,key,type)

cacheManager의 cacheKey로 cache가 존재하는지 확인하고 해당 cache에서 값을 가져옴,

Class? 를 arrow.Option<Class>로 바꾸고 비어있으면 구현부를 invoke, 캐시가 존재하면 캐시를 get해서 줌

cacheKey로 cache 조회 실패하면 그냥 invoke 해서 주는것

```kotlin
@OptIn(ExperimentalTypeInference::class)
suspend inline fun <Error: ApplicationError, reified A : Any> cacheEither(
    cacheManager: CacheManager,
    cacheKey: String,
    key: String,
    type: Class<A>,
    @BuilderInference crossinline block: suspend Raise<Error>.() -> A,
): Either<Error, A> {
    val localCache = cacheManager.getCache(cacheKey)
    require(localCache != null)

    return when (cacheKey != null) {
        true -> localCache.get(cacheKey, type)
            .toOption()
            .fold(
                ifEmpty = {
                    fold<Error, A, Either<Error, A>>(
                        block = { block.invoke(this) },
                        catch = { throw it },
                        recover = { it.left() },
                        transform = { it.right() },
                    ).onRight { localCache.set(key, it) }
                },
                ifSome = { it.right() },
            )
        false -> fold<Error, A, Either<Error, A>>(
            block = { block.invoke(this) },
            catch = { throw it },
            recover = { it.left() },
            transform = { it.right() },
        )
    }
}
```

### localCachePubEvictEither(redisManager,keys)

redisManager는 직접 구현한 클라이언트(opsForValue)

keys 에 있는 값들 **redis**:invalidate 채널에다가 pub 해서 invalidate service가 local cache를 invalidate 할 수 있도록 함

```kotlin
@OptIn(ExperimentalTypeInference::class)
suspend inline fun <Error: ApplicationError, reified A : Any> localCachePubEvictEither(
    redisManager: RedisManager,
    keys: List<String?>,
    @BuilderInference crossinline block: suspend Raise<Error>.() -> A,
): Either<Error, A> = fold<Error, A, Either<Error, A>>(
    block = { block.invoke(this) },
    catch = { throw it },
    recover = { it.left() },
    transform = { it.right() }
).onRight{
    keys.mapNotNull { it }
        .forEach {
            redisManager.convertAndSend(CacheInvalidationService.REDIS_INVALIDATION_CHANNEL,it)
        }
}
```

### 실제 사용

service

```kotlin
suspend fun getUser(id: Long): Either<ApplicationError, UserDto> = coroutineScope {
    transactionEither(transactionManager, coroutineContext) {
        tryCatchAsync { userReader.findById(id).bind() }.await()
    }
}
```

infra

```kotlin
suspend fun findById(id: Long): Either<ApplicationError, UserDto> =
    cacheEither(cacheManager,CacheKey.USER.key, id.toString() , UserDto::class.java){
        userRepository.findById(id)
            ?.let { userMapper.toDomain(it) }
            .toOption()
            .toEither { ApplicationError() }
            .mapLeft {
                log.error("[UserReader][getUser] 뭔가 잘못됨 : $it")
                throw it
            }.bind()
}

suspend fun save(user: UserDto): Either<ApplicationError, UserDto> {
    val keys = listOf("${CacheKey.USER.key}:${user.id}")
    return localCachePubEvictEither(redisManager,keys){
        user.toEntity().let {
            userRepository.save(it)
        }.let { userMapper.toDomain(it) }
    }
}

```

redis json과 다르게 caffeine cache는 json serde를 지원하지 않기 때문에 타입 명시를 해줘야 deserialize 시 타입에 맞게 복호화 가능

[구현 샘플](https://github.com/inha18minseokkim/local-redis-invalidate-sample)