---
title: LocalDateTime 직/역직렬화 관련 이슈
date: 2024-03-28
tags:
  - Redis
  - Java
category:
  - 기술
---
참고
[https://velog.io/@bagt/Redis-역직렬화-삽질기-feat.-RedisSerializer](https://velog.io/@bagt/Redis-%EC%97%AD%EC%A7%81%EB%A0%AC%ED%99%94-%EC%82%BD%EC%A7%88%EA%B8%B0-feat.-RedisSerializer)
[https://ksh-coding.tistory.com/107](https://ksh-coding.tistory.com/107)

Redis에 캐싱 또는 Controller Response dto에서 직/역직렬화를 할 때 LocalDateTime이 직렬화되지 않는 이슈가 있음


```javascript
implementation 'com.fasterxml.jackson.datatype:jackson-datatype-jsr310'
```

해당 의존성 추가
RedisCacheConfig에서 사용할 ObjectMapper를 수동 정의해줘야 함

```javascript
@Bean
public CacheManager cacheManager(RedisConnectionFactory cf) {
	BasicPolymorphicTypeValidator basicPolymorphicTypeValidator = BasicPolymorphicTypeValidator.builder().allowIfSubType(Object.class).build();
	ObjectMapper objectMapper = new ObjectMapper();
	objectMapper.registerModule(new JavaTimeModule()); //com.fasterxml.jackson.datatype.jsr310.JavaTimeModule 추가해서 LocalDateTime Serialize 가능
	objectMapper.activateDefaultTyping(basicPolymorphicTypeValidator,ObjectMapper.DefaultTyping.EVERYTHING); //LocalDateTime도 가져가기 위함
	RedisCacheConfiguration redisCacheConfiguration = RedisCacheConfiguration.defaultCacheConfig()
																							.serializeKeysWith(RedisSerializationContext.SerializationPair.fromSerializer(new StringRedisSerializer()))
																							.serializeValuesWith(RedisSerializationContext.SerializationPair.fromSerializer(new GenericJackson2JsonRedisSerializer((objectMapper)))
																							.entryTtl(Duration.ofMinutes(2880L));
	return RedisCacheManager
				.RedisCacheManagerBuilder.fromConnectionFactory(cf)
				.cacheDefaults(redisCacheConfiguration).build();
}
```

objectMapper 클래스에 대해 LocalDateTime을 다룰 수 있는 모듈을 추가해주고 난 다음 해당 objectMapper를 사용한 redisCacheConfiguration을 등록해줘야 문제없음.


비슷한 패턴으로 RedisTemplate에도 설정가능

```java
@Bean
    public RedisTemplate<String, Object> redisTemplate(RedisConnectionFactory redisConnectionFactory) {

        RedisTemplate<String, Object> template = new RedisTemplate<>();
        template.setConnectionFactory(redisConnectionFactory);
        template.setEnableTransactionSupport(true);
        ObjectMapper objectMapperForLocalDateTime = new ObjectMapper();
        objectMapperForLocalDateTime.registerModule(new JavaTimeModule());
        GenericJackson2JsonRedisSerializer genericJackson2JsonRedisSerializer = new GenericJackson2JsonRedisSerializer(objectMapperForLocalDateTime);

        template.setDefaultSerializer(genericJackson2JsonRedisSerializer);
        template.setKeySerializer(new StringRedisSerializer());
        template.setValueSerializer(genericJackson2JsonRedisSerializer);

        template.setHashKeySerializer(new StringRedisSerializer());
        template.setHashValueSerializer(genericJackson2JsonRedisSerializer);
        return template;
    }
```

