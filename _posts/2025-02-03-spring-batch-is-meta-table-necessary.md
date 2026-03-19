---
title: "스프링부트 배치) 배치 메타테이블이 필요할까"
date: 2025-02-03
tags:
  - Spring Batch
  - 개발
  - Java
category:
  - 기술
---

멀티 데이터소스를 만들어서 공통 테이블을 만들면되긴함.
[Spring Cloud Data Flow](https://spring.io/projects/spring-cloud-dataflow)
spring batch admin이 deprecated 되고 spring cloud data flow 로 통합되었다.

spring cloud dataflow 깃 프로젝트를 클론한 다음

```yaml
services:
  dataflow-server:
    environment:
      - SPRING_DATASOURCE_URL=jdbc:postgresql://host.docker.internal:5432/dataflow
      - SPRING_DATASOURCE_USERNAME=minseokkim
      - SPRING_DATASOURCE_PASSWORD=rlaalstjr99!
      - SPRING_DATASOURCE_DRIVER_CLASS_NAME=org.postgresql.Driver
  skipper-server:
    environment:
      - SPRING_DATASOURCE_URL=jdbc:postgresql://host.docker.internal:5432/dataflow
      - SPRING_DATASOURCE_USERNAME=minseokkim
      - SPRING_DATASOURCE_PASSWORD=rlaalstjr99!
      - SPRING_DATASOURCE_DRIVER_CLASS_NAME=org.postgresql.Driver
```


```yaml
services:
  dataflow-server:
    user: root
    image: springcloud/spring-cloud-dataflow-server:${DATAFLOW_VERSION:-2.11.3-SNAPSHOT}${BP_JVM_VERSION:-}
    container_name: dataflow-server
    ports:
      - "8081:9393"
    environment:
      - LANG=en_US.utf8
      - LC_ALL=en_US.utf8
      - JDK_JAVA_OPTIONS=-Dfile.encoding=UTF-8 -Dsun.jnu.encoding=UTF-8
      # Set CLOSECONTEXTENABLED=true to ensure that the CRT launcher is closed.
      - SPRING_CLOUD_DATAFLOW_APPLICATIONPROPERTIES_TASK_SPRING_CLOUD_TASK_CLOSECONTEXTENABLED=true
      - SPRING_CLOUD_SKIPPER_CLIENT_SERVER_URI=${SKIPPER_URI:-http://skipper-server:7577}/api
      # (Optionally) authenticate the default Docker Hub access for the App Metadata access.
      - SPRING_CLOUD_DATAFLOW_CONTAINER_REGISTRY_CONFIGURATIONS_DEFAULT_USER=${METADATA_DEFAULT_DOCKERHUB_USER}
      - SPRING_CLOUD_DATAFLOW_CONTAINER_REGISTRY_CONFIGURATIONS_DEFAULT_SECRET=${METADATA_DEFAULT_DOCKERHUB_PASSWORD}
      - SPRING_CLOUD_DATAFLOW_CONTAINER_REGISTRYCONFIGURATIONS_DEFAULT_USER=${METADATA_DEFAULT_DOCKERHUB_USER}
      - SPRING_CLOUD_DATAFLOW_CONTAINER_REGISTRYCONFIGURATIONS_DEFAULT_SECRET=${METADATA_DEFAULT_DOCKERHUB_PASSWORD}
    depends_on:
      - skipper-server
    restart: always
    volumes:
      - ${HOST_MOUNT_PATH:-.}:${DOCKER_MOUNT_PATH:-/home/cnb/scdf}

  app-import-stream:
    image: springcloud/baseimage:1.0.4
    container_name: dataflow-app-import-stream
    depends_on:
      - dataflow-server

  app-import-task:
    image: springcloud/baseimage:1.0.4
    container_name: dataflow-app-import-task
    depends_on:
      - dataflow-server
    command: >
      /bin/sh -c "
        ./wait-for-it.sh -t 360 dataflow-server:9393;
        wget -qO- '${DATAFLOW_URI:-http://dataflow-server:9393}/apps' --no-check-certificate --post-data='uri=${TASK_APPS_URI:-https://dataflow.spring.io/task-maven-3-0-x&force=true}';
        echo 'Maven Task apps imported'"

  skipper-server:
    user: root
    image: springcloud/spring-cloud-skipper-server:${SKIPPER_VERSION:-2.11.3-SNAPSHOT}${BP_JVM_VERSION:-}
    container_name: skipper-server
    ports:
      - "7577:7577"
      - ${APPS_PORT_RANGE:-20000-20195:20000-20195}
    environment:
      - LANG=en_US.utf8
      - LC_ALL=en_US.utf8
      - JDK_JAVA_OPTIONS=-Dfile.encoding=UTF-8 -Dsun.jnu.encoding=UTF-8
      - SERVER_PORT=7577
      - SPRING_CLOUD_SKIPPER_SERVER_PLATFORM_LOCAL_ACCOUNTS_DEFAULT_PORTRANGE_LOW=20000
      - SPRING_CLOUD_SKIPPER_SERVER_PLATFORM_LOCAL_ACCOUNTS_DEFAULT_PORTRANGE_HIGH=20190
      - LOGGING_LEVEL_ORG_SPRINGFRAMEWORK_CLOUD_SKIPPER_SERVER_DEPLOYER=ERROR
    restart: always
    volumes:
      - ${HOST_MOUNT_PATH:-.}:${DOCKER_MOUNT_PATH:-/home/cnb/scdf}
```


```yaml
docker compose -f ./IDC-MSA-Replica/spring-cloud-dataflow/docker-compose.yml -f ./spring-cloud-dataflow/src/docker-compose/docker-compose.yml up
```

postgre로 사용할것이고 host.docker.internal을 호스트로 해서 db 지정 진행합니다
이렇게 도커 이미지 올리면 됨.
Dataflow를 위한 dataflow database를 postgresql에 만들고 docker compose up 하면

![이미지](/assets/images/Pasted%20image%2020260301004047.png)

spring metatable 만들듯이 다른 테이블도 만들어짐. spring boot 2와 boot3의 테이블 스키마가 다르기 때문에 별도로 boot3 테이블에 대한 config 해줘야 함.

```java
@Configuration
public class BatchConfig extends DefaultBatchConfiguration {

    private final DataSource dataSource;
    private final PlatformTransactionManager transactionManager;

    public BatchConfig(@Qualifier("dataSource") DataSource dataSource,@Qualifier("transactionManager") PlatformTransactionManager transactionManager) {
        this.dataSource = dataSource;
        this.transactionManager = transactionManager;
    }

    @Override
    protected DataSource getDataSource {
        return dataSource;
    }

    @Override
    protected ExecutionContextSerializer getExecutionContextSerializer {
        return new Jackson2ExecutionContextStringSerializer;
    }

    @Override
    protected PlatformTransactionManager getTransactionManager {
        return transactionManager;
    }

    @Override
    protected String getTablePrefix {
        return "boot3_batch_";
    }
}

```


Spring Cloud Task 로 통합되어서 그런지 배치 단독으로는 spring cloud data flow 어드민 웹에서 뭔가 안맞음. task 디펜던시 추가하고

```java
	implementation 'org.springframework.cloud:spring-cloud-task-core:3.2.0'
	implementation 'org.springframework.cloud:spring-cloud-task-batch:3.2.0'
```


```java
@EnableTask
public class ListedStockSubJobApplication {

	public static void main(String[] args) {
		SpringApplication.run(ListedStockSubJobApplication.class, args);
	}

}

```

EnableTask 해줘야함


# 사용 후기

행내에서 이미 사용중인 Jflow, Argo Workflow의 역할과 기능이 유사하다.(잡 정의, Quartz를 쓰긴 해야겠지만 task 스케줄링 모니터링… Batch 작업 status 관리 등)
data flow 어드민을 보면서 어떤 의도로 이런걸 만들었는지 어느정도 생각이 정리됨.
Batch 메타테이블의 데이터ex)커밋카운트, 오프셋 등 로 작업의 일관성을 관리하는것이 아닌 jflow에서 파라미터, 케이뱅크 공통 영업일 캘린더, 스케줄러로 관리하기 때문에 현재 배치 메타테이블은 단순히 관리포인트만 증가시킨다고 생각
그러므로 spring batch를 행 내에서 사용할 때는 스케줄러의 경우 케이뱅크 행 내 스케줄러를 사용하는것이 적절할 것 같고, spring batch를 사용한다는것은 트랜잭션 관리 기능(chunk 단위 커밋)을 사용한다 정도로만 생각하면 될것 같다. 
그러므로 Job execution이 외부 쉘스크립트나 http request에 의존한다면 메타테이블의 효용은 거의 없다고 본다. 즉, 인메모리로 그냥 띄워도 무방하다(현재 내가 담당하고 있는 업무에서는 대부분의 작업이 멱등처리가 다 되기 때문에)

만약 spring batch에 잡 별로 commit count나 실행시간 기준으로 뭔가를 관리한다고 하면 
  1. 다시 한번 생각해 볼 것(기존 정기작업 솔루션에서 지원하는 기능을 가능한 사용하는것이 관리포인트를 줄이는 길)
  2. 그래도 필요하다면 개별적으로 사용
