
## 필요성

MSA 프로젝트 회사에서 계속 개발 함에 따라 프로젝트 숫자가 늘어남. 중간에 공통 단위 모듈(패키지 및 클래스 파일 모두)들이 늘어나는데 이걸 지금 복붙으로 처리하고 있는 상황.

## 구조

현재 듣고 있는 강의 내용 기준으로(강의는 Maven 기준이라 들으면서 변환중)

```javascript
microservices-demo(no bootJar,소스없음)
		- docker-compose(카프카 및 아래 프로젝트 배포 도커 파일들)
    - app-config-data (no bootJar)
    - twitter-to-kafka-service
	  - kafka (no bootJar, avro gradle 사용)
			  - kafka-admin
			  - kafka-producer
			  - kafka-model
```


![](https://prod-files-secure.s3.us-west-2.amazonaws.com/c38aebd7-2834-4fac-b2fc-a2f0c17ce81d/d1788120-6f67-4360-a593-1cfc004f8c6c/Untitled.png)

이런식으로 하나의 프로젝트에 여러 하위 모듈 프로젝트를 넣음. 각각의 프로젝트에 build.gradle, settings.gradle 다 있음.

Settings.gradle 예제(microservices-demo)

```java
rootProject.name = 'microservices-demo'
include ':twitter-to-kafka-service',':app-config-data'
```

build.gradle 예제(twitter-to-kafka-service)

```java
dependencies {
    implementation 'org.twitter4j:twitter4j-stream:4.0.7'
    implementation project(path: ':app-config-data') //config에서 공통 모듈 import
}

```

도메인 단위로 넣는 경우 공통 모듈들을 참조해서 테이블 엔티티 같은것들 가져올 수 있을듯


```java
@SpringBootApplication
@ComponentScan("com.microservices.demo")
public class KafkaAdminApplication {

    public static void main(String[] args) {
        SpringApplication.run(KafkaAdminApplication.class, args);
    }

}

```

Spring 사용 시, 프로젝트가 다르기 때문에 

## 장점

공통모듈 잘 정의하면 소스코드 중복 막을 수 있음.
각 프로젝트마다 인텔리제이를 켜야할 필요 없음(물론 프로젝트 세팅을 하면 되지만 귀찮고 설정한 내용을 가지고 다니기도 그렇고)

## 단점

초기 셋팅이 힘듦
단일 프로젝트로만 개발했기 때문에 처음에 러닝커브가 약간 있을듯.
현재 케이뱅크 CHA-PKG 브랜치 전략에 적합한지는 의문.
영향도 문제
원래 프로젝트 하나에 파드 하나로 정한 이유는 공통 모듈을 최소화 함으로써, 복붙을 하더라도 다른 파드에 영향을 주지 않게 하기 위해서
다만 저 당시 논의는 비즈니스 공통로직에 관한 것이기 보다는 행내 시스템 관련 공통로직(EAI 호출 Http메소드, DB커넥션 관련, GUID 채번같은) 에 관한 논의였음
업무별로 묶는것
공모주서비스,공모주데이터수신배치,공모주데이터푸시배치
→ 공모주 프로젝트 내에 서비스,수신배치,푸시배치
식품물가서비스,식품물가api배치,식품물가적재배치,식품물가푸시배치,식품물가알림톡배치
→ 식푸물가 프로젝트 내에 ….
이정도는 괜찮지 않을 까 하는 개인적인 생각(왜냐하면 내부의 공통 entity,configuration은 복붙으로 작업중이기 때문)

## 할일

SRE 협의 
현재는 프로젝트 하나에 파드 하나 개념이므로 1 : N 구조에 대한 파이프라인 협의 필요
또한 지금 생각으로는 공통모듈 변경 시 현재 배포 대상인 하위 모듈들은 문제가 없겠지만 배포 대상이 아닌 모듈들은 그대로 떠있다가 다음 배포 시 공통모듈이 적용될 것.
또는 올릴 때 해당 프로젝트 하위 모듈들 다 같이 배포될 것.
무엇이 맞을지..
20240516 협의 시작

중간결과:
투자홈 서비스의 프로젝트에 멀티모듈 구조를 적용시킴.
최선은 아닌것 같지만 현 상황에서는 최선을 다했다고 생각.