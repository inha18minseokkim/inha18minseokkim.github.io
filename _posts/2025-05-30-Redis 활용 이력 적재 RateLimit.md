---
title: "Redis 활용 이력 적재 RateLimit"
date: 2025-05-30
tags: [미지정]
category: 기술
---

# 상황

주식 상세 정보 조회 이력을 적재 해야 함
사용할 수 있는 DB는 RDB 단 하나
해당 이력은 적재해서 다음과 같은 곳에 쓰일 예정
  1. 그냥 데이터 분석용
  2. 검색 순위 상위 Top N개 산출 로직
  3. 개인별 최근 조회 종목 리스트 구성
3번의 경우 꼭 서버에 데이터를 활용해야 하는가에 대한 논란의 여지가 있지만 아무튼 2번 때문에 필요함
왜냐하면 검색 창에서 순위를 집계하기 위해서 이런 데이터를 컬럼에 넣을 것임
  - 2025-04-10 16:46:03.997967,005930,KR,STOCK,20160860
2025-04-10 16:46:22.893004,000660,KR,STOCK,20160860
rdb에 이런식으로 데이터를 밀어넣고 있는데 중복호출 방지 로직이 없다면 한사람이 어뷰징을 한다면 무한 인서트로 순위 조작이 가능해진다. 예를 들어 어떤 김모씨가 도이치모터스를 10만번 클릭하는 로직이 어디서 발생한다면 10만건 row insert가 가능해지는 구조
중복산출 방지야 분단위 partition group by 쿼리로 처리하면 되긴 하는데 row가 무한정 쌓일 수 있어서 조회성능 자체가 문제가 생길 수 있다. 별도 파기 프로세스를 준비하는건 덤이고 쓰레기 row가 쌓이는 것을 방지해야 한다.

# 조건 정의

같은 고객이 같은 종목에 대한 검색이력은 10분에 한 번씩만 조회 이력을 쌓을 수 있도록 한다 

# 구현방법

redis를 활용하여 구현할 예정

## 고민

1안
종목코드:고객아이디 로 키를 세팅함

```shell
stock_customer:hit:20160860:005930  ttl 10분
stock_customer:20160860:005935      ttl 10분
```

2안
고객아이디 키 안에 sorted set으로 키를 세팅함

```shell
ZADD stock_customer:hit:20160860 1717042800 005930
ZADD stock_customer:hit:20160860 1717042900 005935
```

2안 할려면 별도 스레드가 돌면서 10분 지난 element들은 지우는식으로 동작 해야 함
처음에 생각할 때 1안이 제일 좋아보이긴 했는데 DAU 60만 기준으로 거의 1만 종목 찌를 수 있으니 극단적으로 
60만 * 1만 가능
물론 10분만에 60억개 다 차진않겠고 히트율도 고려해야 하니 일단 1안으로 가겠다.
한사람이 10분동안 10 종목 조회 한다고 생각하고 DAU가 60만이면 600만개 정도니깐.. 괜찮을듯
  - 50% 이상의 고객은 메인에서 나갈거고.. 그 중 5프로의 고객만 상세를 클릭하겠지
물론 이렇게까지 히트를 많이 할 정도로 서비스가 잘 되면 레디스를 클러스터로 만들어 샤딩해달라고 하자
  - +) ElastiCache Redis OSS에서 Valkey로 곧 바꾼다고 한다

 

### 견본용 코드


```kotlin
override fun addHitHistory(criteria: HitHistoryAddCriteria): HitHistoryAddResult {
        val key = "stock_customer:hit:${criteria.custId}:${criteria.symbId}"
        val cached: String? = redisTemplate.opsForValue().get(key)

        return if (cached == null) {
            val hit = Hit(
                inqryBaseDttm = criteria.inqryBaseDttm,
                symbId = criteria.symbId,
                isoNatCd = criteria.isoNatCd,
                scrtsDsVal = criteria.scrtsDsVal,
                custId = criteria.custId
            )
            hitRepository.save(hit)
            HitHistoryAddResult(
                inqryBaseDttm = criteria.inqryBaseDttm,
                symbId = criteria.symbId,
                isoNatCd = criteria.isoNatCd,
                scrtsDsVal = criteria.scrtsDsVal,
                custId = criteria.custId
            )
        } else {
            // 캐시가 없으면 "1"을 10분 동안 저장
            redisTemplate.opsForValue().set(key, "1", Duration.ofMinutes(10))
            HitHistoryAddResult(
                inqryBaseDttm = criteria.inqryBaseDttm,
                symbId = criteria.symbId,
                isoNatCd = criteria.isoNatCd,
                scrtsDsVal = criteria.scrtsDsVal,
                custId = criteria.custId
            )
        }
    }
```


```shell
127.0.0.1:6379> keys *
1) "stock_customer:hit:20160860:252670"
```

요런식인데 redisTemplate 관련 기술은 인프라레이어로 숨겨주자

```kotlin
@Component
class RedisHitCache(
    private val redisTemplate: RedisTemplate<String, String>
): HitCache {

    override fun getHitMark(custId: String, symbId: String): Boolean {
        val key = "stock_customer:hit:$custId:$symbId"
        return redisTemplate.opsForValue().get(key) != null
    }

    override fun markHit(custId: String, symbId: String) {
        val key = "stock_customer:hit:$custId:$symbId"
        redisTemplate.opsForValue().set(key, "1", Duration.ofMinutes(10))
    }
}
```


```kotlin
override fun addHitHistory(criteria: HitHistoryAddCriteria): HitHistoryAddResult {
        return if (hitCache.getHitMark(criteria.custId, criteria.symbId)) {
            val hit = Hit(
                inqryBaseDttm = criteria.inqryBaseDttm,
                symbId = criteria.symbId,
                isoNatCd = criteria.isoNatCd,
                scrtsDsVal = criteria.scrtsDsVal,
                custId = criteria.custId
            )
            hitRepository.save(hit)
            HitHistoryAddResult(
                inqryBaseDttm = criteria.inqryBaseDttm,
                symbId = criteria.symbId,
                isoNatCd = criteria.isoNatCd,
                scrtsDsVal = criteria.scrtsDsVal,
                custId = criteria.custId
            )
        } else {
            hitCache.markHit(criteria.custId, criteria.symbId)
            HitHistoryAddResult(
                inqryBaseDttm = criteria.inqryBaseDttm,
                symbId = criteria.symbId,
                isoNatCd = criteria.isoNatCd,
                scrtsDsVal = criteria.scrtsDsVal,
                custId = criteria.custId
            )
        }
    }
```

