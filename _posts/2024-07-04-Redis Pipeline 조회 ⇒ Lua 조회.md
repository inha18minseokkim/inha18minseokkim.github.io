---
title: Redis Pipeline 조회 ⇒ Lua 조회
date: 2024-07-04
tags:
  - Redis
  - Lua
  - 케이뱅크
---

```java
public GetListedStockRankOutDto getListedStockRank(GetListedStockRankInDto in){
        ZSetOperations<String, String> zSetOperations = redisTemplate.opsForZSet();
        HashOperations<String, Object, Object> hashOperations = redisTemplate.opsForHash();
        List<GetListedStockRankOutDto.GetListedStockRankSubOutDto> list = zSetOperations.range(in.orderCode().getCacheHashId().toString(), 0, 100)
                .stream().map(itemCodeNumber -> hashOperations.get(CacheHashId.ListedStockPrices.toString(), itemCodeNumber))
                .filter(result -> result != null)
                .map(listedStockPrices -> {
                    try {
                        return objectMapper.readValue(listedStockPrices.toString(), GetListedStockRankOutDto.GetListedStockRankSubOutDto.class);
                    } catch (JsonProcessingException e) {
                        throw new RuntimeException(e);
                    }
                })
                .limit(in.limitLength())
                .toList();
        return GetListedStockRankOutDto.builder()
                .list(list)
                .build();
    }
```

이렇게 하면 redis 100번 찌름
이러면 IO 조회성능 문제 있기 때문에 배치 조회 해야함

```java
List<Object> results = redisTemplate.executePipelined((RedisConnection connection) -> {
            byte[] hashKeyBytes = hashKey.getBytes(StandardCharsets.UTF_8);
            for (String field : fields) {
                byte[] fieldBytes = field.getBytes(StandardCharsets.UTF_8);
                connection.hashCommands().hGet(hashKeyBytes, fieldBytes);
            }
            return null;
```

pipeline으로 bulk insert 할때처럼 bulk 조회하면 될 줄 알았는데 이렇게 해도 안됨.(스펙상 pipeline 내부에서 hGet은 null 리턴)

```lua
local rankItemCodeNumber = redis.call('zrange',ARGV[1],0,-1)
local a = {}
for i = 1, #rankItemCodeNumber do
    local res = redis.call('hget','ListedStockPrices',rankItemCodeNumber[i])
    a[i] = res
    if #a >= tonumber(ARGV[2]) then return a end
end
return a
```

Lua스크립트 작성
실행 검증

```lua
eval "local rankItemCodeNumber = redis.call('zrange',ARGV[1],0,-1) local a = {} for i = 1, #rankItemCodeNumber do    local res = redis.call('hget','ListedStockPrices',rankItemCodeNumber[i])    a[i] = res    if #a >= tonumber(ARGV[2]) then return a end end return a" 0 ListedStocksOrderBy:PriceChangeDescending 10
```

Luascript 실행부

```lua
public GetListedStockRankOutDto getListedStockRank(GetListedStockRankInDto in){
    List<Object> execute = redisTemplate.execute(getListedStockRankScript, List.of(in.orderCode().getCacheHashId().toString()), 10);
    return GetListedStockRankOutDto.builder()
            .list(execute.stream().map(
                    element -> objectMapper.convertValue(element, GetListedStockRankOutDto.GetListedStockRankSubOutDto.class)
            ).toList())
            .build();
}
```

빠릿하게 잘됨
