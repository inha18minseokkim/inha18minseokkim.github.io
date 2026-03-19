---
title: Spring Cloud Config-Server + Spring Security (Basic Auth) 정리(Bootstrap 사용 안함)
date: 2024-05-18
tags:
  - Spring
  - Spring-Cloud
category:
  - 기술
---

### 정리 사유

20240518 기준 spring boot 2.4 이상에서  bootstrap 옵션이 더이상 기본이 되지 않고 spring cloud config옵션을 사용한 방법론이 많이쓰임
그래서 둘 다 사용해봄

하지만 해당 글에 대한 정리가 한글버전으로 없어서 정리해놓음.

![이미지](/assets/images/Pasted%20image%2020260225091253.png)

이렇게 설정해놓으면
config-server의 Uri는 다음과 같다
[http://대충너의호스트:8888/elastic_query_service/default](http://rlaalstjr99.ddns.net:8888/elastic_query_service/default)
elastic_query_service : 서비스 이름
default: 프로필
뒤에 label 까지 더 붙일 수 있음(여기선 안함)

![이미지](/assets/images/Pasted%20image%2020260225091304.png)
다만 위의 Config-server의 경우, Spring security Basic Auth가 걸려있는데, 
해당 옵션을 사용하기 위해 application.yml 파일에 작성하면 된다.

```sql
server:
  port:
    8124
logging:
  level:
    root: TRACE
spring:
  application:
    name: elastic-query-service
  config:
    import: configserver:http://너의 호스트:8888
  cloud:
    config:
      enabled: true
      #uri: http://너의 호스트:8888
      username: asdf
      password: asdf
      name: elastic_query_service
      profile: default

```

spring.config.import & spring.cloud.config.enabled
enabled가 True인 경우, remote source로 부터 가져오는걸 기본으로 하겠다는 것,
그러므로 True로 설정해놓는 경우 Import Uri 설정이 필수

spring.cloud.username, spring.cloud.password
 기재해놓으면(여기서는 jasypt 사용안함) 알아서 Basic Auth로 접근함. 물론 spring cloud config server에 보안설정이 없는경우 스킵

[spring.cloud.name](http://spring.cloud.name) & spring.cloud.profile
[http://대충너의호스트:8888/elastic_query_service/default](http://rlaalstjr99.ddns.net:8888/elastic_query_service/default) 위에서 썼던 name/profile 을 여기다 기재해주면 된다

위와 같이 설정해놓는 경우,
맨 위의 application.yml의 기본 옵션

```sql
server:
  port:
    8124
logging:
  level:
    root: TRACE
```

은 무시당하게 된다.
왜냐하면 원격 저장소에 다 있기 때문에 덮어쓰여짐(config-server에서 읽어들이는것이 우선순위 높음)


### Legcy Bootstrap 사용방법

위에서 말한것처럼, 더이상 Bootstrap은 기본 사양이 아니게 되었으므로 bootstrap을 사용하려면 다음과 같은 Dependency를 추가로 받아야함

```yaml
implementation 'org.springframework.cloud:spring-cloud-starter-bootstrap:4.1.2
```


![이미지](/assets/images/Pasted%20image%2020260225091311.png)
application.yml은 그냥 비워두고 bootstrap.yml에 다음과 같이 사용 

```yaml
spring:
  application:
    name: kafka-to-elastic-service
  profiles:
    active: kafka_to_elastic
  cloud:
    config:
      name: kafka-to-elastic-service,config-client
      uri: http://rlaalstjr99.ddns.net:8888
      username: asdf
      password: ENC(xcMyooKqAgYyOlbucvUcWIFTUieHSk/8fRYjBErt7TNFLJtf0a2quV4oejGIRqN1)
jasypt:
  encryptor:
    password: asdf
```

jasypt를 사용하지 않는 경우 password에 그냥 비밀번호 치면 됨.(Config-server에서 security 사용하지 않는 경우 username,password 스킵 ㄱㄱ)
jasypt를 사용하는 경우

```yaml
	implementation 'com.github.ulisesbocchio:jasypt-spring-boot-starter:3.0.5'
```

를 선언해줘야함


출처
[https://docs.spring.io/spring-cloud-config/docs/3.0.0/reference/html/#config-data-import](https://docs.spring.io/spring-cloud-config/docs/3.0.0/reference/html/#config-data-import)
