---
title: RateLimiting을 응용하여 이력 적재 속도를 조절해보자
date: 2025-04-01
tags:
  - 주식
  - 케이뱅크
  - 개발
  - Redis
category:
  - 기술
---

## 조건

고객들이 조회한 종목 top N을 집계해서 게시하는 기능이 필요.
적재는 rdb에 해야함(rdb 밖에 없음)
redis 있음
집계는 N초에 한번만 하고싶음  ex) 30초 동안 삼성전자 상세조회를 왔다갔다 10번해도 이력 10개가 아니라 1개 이력으로
너무 많은 insert는 현 mono edb에 부담


### 방법

RateLimiting 아이디어를 응용해서 Redis를 게이트키퍼로 활용한다.

- 조회 요청이 들어오면 Redis에 `(userId, symbolId)` 조합 키로 먼저 조회
- Redis에 키가 존재하면 → DB insert 스킵 (이미 최근에 적재된 이력)
- Redis에 키가 없으면 → Redis에 TTL과 함께 저장 후 DB insert

TTL 시간 안에 동일 사용자가 동일 종목을 재조회해도 이력은 1건만 쌓인다.

---

## 구현

### 흐름

```
PUT /v1/{stockServiceType}/{securities}/{nation}  (이력 적재 요청)
  └─ HitServiceImpl.addHitHistory()
       └─ HitReader.save(user, symbol, stockServiceType)
            ├─ HitRedisReader.findHitByUserIdAndSymbolId()  →  Redis 조회
            │    ├─ 존재 → return hit  (DB insert 스킵)
            │    └─ 없음 → HitRedisReader.saveHit(ttl=3min)  →  Redis 저장 후 DB insert
```

### HitReader - 핵심 게이트 로직

```kotlin
fun save(user: User, symbol: Symbol, stockServiceType: StockServiceType): Hit {
    val hit = hitRedisReader.findHitByUserIdAndSymbolId(
        userId = user.customerId,
        symbolId = symbol.symbolId
    )
    return when (hit != null) {
        true -> hit  // Redis에 있으면 DB insert 스킵
        false -> Hit(user = user, symbol = symbol, inquiredAt = LocalDateTime.now())
            .run { hitRedisReader.saveHit(hit = this, ttl = Duration.ofMinutes(HIT_TTL_MINUTE)) }
            .run { save(hit = this, stockServiceType = stockServiceType) }
    }
}

companion object {
    private const val HIT_TTL_MINUTE = 3L
}
```

`HIT_TTL_MINUTE = 3`으로 설정했다. 동일 사용자가 동일 종목을 3분 이내에 재조회하면 DB insert가 발생하지 않는다.

### HitRedisReader - Redis 키 설계

```kotlin
fun findHitByUserIdAndSymbolId(userId: String, symbolId: String): Hit? {
    return HitKey(userId, symbolId)
        .let { RedisCacheKey.generateKey(hitKey, objectMapper, it) }
        ?.run { redisManager.get(this, Hit::class) }
}

fun saveHit(hit: Hit, ttl: Duration): Hit {
    return Pair(
        RedisCacheKey.generateKey(hitKey, objectMapper, HitKey(hit.user.customerId, hit.symbol.symbolId)),
        hit
    )
        .let { (key, value) -> key?.run { redisManager.set(this, value, ttl) } }
        .let { hit }
}
```

키를 `HitKey(userId, symbolId)` 조합으로 구성했다. symbolId 단독이 아니라 userId를 같이 쓴 이유는 **사용자별로 이력을 중복 제거**하기 위해서다. A가 삼성전자를 조회한 것과 B가 삼성전자를 조회한 것은 각각 이력으로 남아야 한다.

---

## 정리

| 상황 | 동작 |
|------|------|
| Redis에 `(userId, symbolId)` 키 존재 | DB insert 스킵 |
| Redis에 키 없음 | Redis에 TTL 3분으로 저장 → DB insert |
| TTL 만료 후 재조회 | 새로운 이력으로 DB insert |

RateLimiting처럼 Redis TTL을 게이트로 사용하면, 별도의 배치나 디바운스 없이도 DB insert 빈도를 자연스럽게 제한할 수 있다.
