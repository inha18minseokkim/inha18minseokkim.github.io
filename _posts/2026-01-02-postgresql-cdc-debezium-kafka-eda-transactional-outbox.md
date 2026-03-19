---
title: "Postgresql CDC + Debezium + kafka 사용 EDA > transactional outbox 패턴"
date: 2026-01-02
tags:
  - Kafka
  - 개발
  - 인프라
category:
  - 기술
---
PostgreSQL CDC + Debezium + Kafka를 활용한 EDA 구현 정리.
# 동기

Event Driven을 공부하면서 위와 같은 공부를 좀 해봄
AWS EventBridge + DynamoDB EventStream을 사용해서 DB의 변경사항을 캡쳐해서 뭔가를 처리하는 로직을 보고 기존 주간 투자왕에서 사용하던 이벤트 발행 로직을 대체할 수 있지 않을까라는 생각으로 시작해봄
  - 왜냐하면 현재는 테이블에 내역 저장 > 메세지 발행 순서로 진행되기 때문에 둘 사이의 트랜잭션을 보장하는것이  힘들기 때문.
그런데 현재 행내에서는 DynamoDB를 절대로 사용할 수 없기 때문에 Aurora Postgresql에서 사용할 수 있는 postgresql Publisher 를 사용해보려 함

# POC

특정 테이블 publication 생성

```kotlin
CREATE PUBLICATION products_publication FOR TABLE products;
```

Replication Slot 생성

```kotlin
SELECT * FROM pg_create_logical_replication_slot('products_publication', 'pgoutput');
```



debezium, kafka(KRAFT) docker-compose 구성 및 네트워크 연결

debezium connector 연결

```sql
curl -X PUT -H "Content-Type:application/json" \
  http://localhost:8881/connector-plugins/io.debezium.connector.postgresql.PostgresConnector/config/validate \
  -d '{
    "name": "postgres-test-connector",
    "config": {
      "connector.class": "io.debezium.connector.postgresql.PostgresConnector",
      "tasks.max": "1",
      "topic.prefix": "testdb",
      "database.hostname": "host.docker.internal",
      "database.port": "5432",
      "database.user": "아이디",    
      "database.password": "비번",
      "database.dbname": "test",
      "database.server.name": "testdb",
      "slot.name": "test_product",    
      "publication.name": "my_publication",
      "plugin.name": "pgoutput",
      "table.include.list": "public.products"
    }
  }'
  
```


```sql
curl -X POST -H "Accept:application/json" \
  -H "Content-Type:application/json" \
  http://localhost:8881/connectors/ \
  -d '{
    "name": "postgres-test-connector",
    "config": {
      "connector.class": "io.debezium.connector.postgresql.PostgresConnector",
      "tasks.max": "1",
      "topic.prefix": "testdb",
      "database.hostname": "host.docker.internal",
      "database.port": "5432",
      "database.user": "아이디",    
      "database.password": "비번",
      "database.dbname": "test",
      "database.server.name": "testdb",
      "slot.name": "test_product",    
      "publication.name": "my_publication",
      "plugin.name": "pgoutput",
      "table.include.list": "public.products"
    }
  }'
```


INSERT 문 입력

```sql
test> INSERT INTO public.products (name, description) VALUES ('sadfa', 'asdfasdfas')
```

kafka consumer cli 메세지 output

```sql
minseokkim@gimminseog-ui-Macmini ~ % docker exec -it kafka kafka-console-consumer \
  --bootstrap-server kafka:9092 \
  --topic testdb.public.products \
  --from-beginning
{"schema":{"type":"struct","fields":[{"type":"struct","fields":[{"type":"int64","optional":false,"field":"id"},{"type":"string","optional":false,"field":"name"},{"type":"string","optional":true,"field":"description"}],"optional":true,"name":"testdb.public.products.Value","field":"before"},{"type":"struct","fields":[{"type":"int64","optional":false,"field":"id"},{"type":"string","optional":false,"field":"name"},{"type":"string","optional":true,"field":"description"}],"optional":true,"name":"testdb.public.products.Value","field":"after"},{"type":"struct","fields":[{"type":"string","optional":false,"field":"version"},{"type":"string","optional":false,"field":"connector"},{"type":"string","optional":false,"field":"name"},{"type":"int64","optional":false,"field":"ts_ms"},{"type":"string","optional":true,"name":"io.debezium.data.Enum","version":1,"parameters":{"allowed":"true,last,false,incremental"},"default":"false","field":"snapshot"},{"type":"string","optional":false,"field":"db"},{"type":"string","optional":true,"field":"sequence"},{"type":"int64","optional":true,"field":"ts_us"},{"type":"int64","optional":true,"field":"ts_ns"},{"type":"string","optional":false,"field":"schema"},{"type":"string","optional":false,"field":"table"},{"type":"int64","optional":true,"field":"txId"},{"type":"int64","optional":true,"field":"lsn"},{"type":"int64","optional":true,"field":"xmin"}],"optional":false,"name":"io.debezium.connector.postgresql.Source","field":"source"},{"type":"string","optional":false,"field":"op"},{"type":"int64","optional":true,"field":"ts_ms"},{"type":"int64","optional":true,"field":"ts_us"},{"type":"int64","optional":true,"field":"ts_ns"},{"type":"struct","fields":[{"type":"string","optional":false,"field":"id"},{"type":"int64","optional":false,"field":"total_order"},{"type":"int64","optional":false,"field":"data_collection_order"}],"optional":true,"name":"event.block","version":1,"field":"transaction"}],"optional":false,"name":"testdb.public.products.Envelope","version":2},"payload":{"before":null,"after":{"id":1,"name":"sadfa","description":"asdfasdfas"},"source":{"version":"2.6.2.Final","connector":"postgresql","name":"testdb","ts_ms":1767346293996,"snapshot":"false","db":"test","sequence":"[null,\"26777872\"]","ts_us":1767346293996570,"ts_ns":1767346293996570000,"schema":"public","table":"products","txId":749,"lsn":26777872,"xmin":null},"op":"c","ts_ms":1767346294362,"ts_us":1767346294362832,"ts_ns":1767346294362832099,"transaction":null}}
```

상세

```sql
{
  "schema": {
    "type": "struct",
    "fields": [
      {
        "type": "struct",
        "fields": [
          {
            "type": "int64",
            "optional": false,
            "field": "id"
          },
          {
            "type": "string",
            "optional": false,
            "field": "name"
          },
          {
            "type": "string",
            "optional": true,
            "field": "description"
          }
        ],
        "optional": true,
        "name": "testdb.public.products.Value",
        "field": "before"
      },
      {
        "type": "struct",
        "fields": [
          {
            "type": "int64",
            "optional": false,
            "field": "id"
          },
          {
            "type": "string",
            "optional": false,
            "field": "name"
          },
          {
            "type": "string",
            "optional": true,
            "field": "description"
          }
        ],
        "optional": true,
        "name": "testdb.public.products.Value",
        "field": "after"
      },
      {
        "type": "struct",
        "fields": [
          {
            "type": "string",
            "optional": false,
            "field": "version"
          },
          {
            "type": "string",
            "optional": false,
            "field": "connector"
          },
          {
            "type": "string",
            "optional": false,
            "field": "name"
          },
          {
            "type": "int64",
            "optional": false,
            "field": "ts_ms"
          },
          {
            "type": "string",
            "optional": true,
            "name": "io.debezium.data.Enum",
            "version": 1,
            "parameters": {
              "allowed": "true,last,false,incremental"
            },
            "default": "false",
            "field": "snapshot"
          },
          {
            "type": "string",
            "optional": false,
            "field": "db"
          },
          {
            "type": "string",
            "optional": true,
            "field": "sequence"
          },
          {
            "type": "int64",
            "optional": true,
            "field": "ts_us"
          },
          {
            "type": "int64",
            "optional": true,
            "field": "ts_ns"
          },
          {
            "type": "string",
            "optional": false,
            "field": "schema"
          },
          {
            "type": "string",
            "optional": false,
            "field": "table"
          },
          {
            "type": "int64",
            "optional": true,
            "field": "txId"
          },
          {
            "type": "int64",
            "optional": true,
            "field": "lsn"
          },
          {
            "type": "int64",
            "optional": true,
            "field": "xmin"
          }
        ],
        "optional": false,
        "name": "io.debezium.connector.postgresql.Source",
        "field": "source"
      },
      {
        "type": "string",
        "optional": false,
        "field": "op"
      },
      {
        "type": "int64",
        "optional": true,
        "field": "ts_ms"
      },
      {
        "type": "int64",
        "optional": true,
        "field": "ts_us"
      },
      {
        "type": "int64",
        "optional": true,
        "field": "ts_ns"
      },
      {
        "type": "struct",
        "fields": [
          {
            "type": "string",
            "optional": false,
            "field": "id"
          },
          {
            "type": "int64",
            "optional": false,
            "field": "total_order"
          },
          {
            "type": "int64",
            "optional": false,
            "field": "data_collection_order"
          }
        ],
        "optional": true,
        "name": "event.block",
        "version": 1,
        "field": "transaction"
      }
    ],
    "optional": false,
    "name": "testdb.public.products.Envelope",
    "version": 2
  },
  "payload": {
    "before": null,
    "after": {
      "id": 1,
      "name": "sadfa",
      "description": "asdfasdfas"
    },
    "source": {
      "version": "2.6.2.Final",
      "connector": "postgresql",
      "name": "testdb",
      "ts_ms": 1767346293996,
      "snapshot": "false",
      "db": "test",
      "sequence": "[null,\"26777872\"]",
      "ts_us": 1767346293996570,
      "ts_ns": 1767346293996570000,
      "schema": "public",
      "table": "products",
      "txId": 749,
      "lsn": 26777872,
      "xmin": null
    },
    "op": "c",
    "ts_ms": 1767346294362,
    "ts_us": 1767346294362832,
    "ts_ns": 1767346294362832100,
    "transaction": null
  }
}
```


이제 변동분을 가지고 비즈니스 로직을 짜면 된다
다만 궁금한점이 생김

### 인프라 레이어에 대한 비즈니스의 의존 > 도메인 영향도 파악의 어려움? 

즉 현재 CDC 토픽을 카프카 메세지 소비로 비즈니스 로직을 처리하겠다는것이므로
기존에 도메인 기반 서비스에서 메세지를 발행하든 테이블에 레코드를 넣는 행위로 고객에게 리워드를 지급하겠다는 명시적인 의지를 보인 반면 db에 테이블 레코드 변경된 것을 보고 “비즈니스 로직” 을 수행하면 비즈니스 로직에서 동작이 명시되지 않으므로 좀 그렇지 않나 라는 생각이 들었음.

## 🔴 CDC/인프라 레이어 비판 (부정적 의견)


## "비즈니스 가시성 상실" - Chris Richardson (Eventuate 창시자)

> "도메인 이벤트는 비즈니스 의미를 담아야 한다. 
> CDC는 DB 레벨 '변경 사실'만 주는데, 비즈니스 컨텍스트가 사라져 
> 개발자가 '이 변경이 무슨 의미인가'를 알기 어렵다."
- **예**: **`description=""`** → CDC는 **`{"op":"u", "after":{"description":""}}`**만 줌. 이게 "고객 불만"인지 "임시 비활성"인지 모름
- **문제점**:
  - **디버깅 어려움**: 로그만 봐도 "왜 이런 이벤트가" 발생했는지 추적 불가
  - **도메인 지식 분산**: 이벤트 의미가 DB 스키마에만 남음
  - **과도한 결합**: 소비자가 DB 스키마를 알아야 함

## Martin Fowler도 지적

> "Infrastructure-generated events는 도메인 전문가와 대화하기 어렵다. 비즈니스 용어가 빠진다."

## ✅ Domain Event 반박 (긍정적 의견)


## "운영 효율성 + 정확성" - Debezium 팀 / Netflix 사례

> "애플리케이션 코드에서 이벤트 발행하면:
> 1. 버그로 이벤트 누락
> 2. 트랜잭션 실패 시 이벤트 롤백 불가
> 3. 배포 중 이벤트 드리프트 발생
> CDC는 DB 트랜잭션과 완벽 동기화 + 누락 0"

## 실무 우위


| **항목** | **Domain Event (app 코드)** | **CDC (Debezium)** |
| --- | --- | --- |
| **누락 위험** | 높음 (버그/예외) | 없음 (DB 레벨) |
| **트랜잭션 일관성** | 애플리케이션 트랜잭션 한정 | DB 트랜잭션 전체 |
| **도메인 풍부함** | 높음 | 낮음 (DB 스키마 한정) |
| **운영 복잡도** | 배포/재시작 시 이벤트 손실 위험 | 인프라 관리 부담 |
| **개발 생산성** | 빠름 (코드 한 곳) | 느림 (소비자에서 컨텍스트 복원) |


# Outbox 패턴 활용

그래서 Outbox 패턴을 활용해서 위에서 문제가 생겼던(db적재는 성공, 메세지 발행은 실패 또는 반대상황) 것을 방어할 수 있다.
메세지 발행 대신 CDC용 테이블을 만들고 해당 테이블을 debezium이랑 연결시켜놓으면 비즈니스 로직에서 db적재 

> 비즈니스 트랜잭션: save(product)
> WAL CDC:      → WAL 로그에 즉시 기록 (누락 불가)
> Outbox:       → outbox 테이블에 INSERT (동일 트랜잭션)


### Outbox 패턴이 Debezium 단독보다 일관성에 유리한 이유

1. 비즈니스상 의미적으로 일관적임
2. 선택적으로 이벤트 발행 가능
단점은 CDC용 테이블을 하나 더 만들어서 운용해야함, 거래량이 많지 않는 경우 행내에서는 오버엔지니어링 아니냐고 물어볼 수 있을듯


조금 감성이 다르긴 하지만 AWS Summit Seoul 2025에서 Recon Lab이라는 곳에서 DB 이벤트 가지고 모니터링이나 증설 같은 로직을 걸어놓음
위 기업 같은 경우는 인프라 관리 인력이 부족하기 때문에 인프라 관리 인력과 설비 DB 이벤트 로직으로 대응을 한 거라 규모가 큰 기업이 봤을때는 적합하지 않은 세팅이라 했음
이벤트 드리븐 로직이 좀 다르긴 하지만 

비슷한 stackoverflow 논의
[Is Event sourcing using Database CDC considered good architecture?](https://stackoverflow.com/questions/54379623/is-event-sourcing-using-database-cdc-considered-good-architecture)
[Domain Events versus Change Data Capture | Kislay Verma](https://kislayverma.com/software-architecture/domain-events-versus-change-data-capture/)

결론적으로, CDC 자체는 도메인 모델링이 아닌 데이터 통합을 위한 기술
DDD의 원칙을 따르기 위해서는 CDC를 통해 캡처된 로우 레벨 변경 사항을 비즈니스 문맥이 담긴 **도메인 이벤트로 변환하는 과정**이 필요

> 이벤트란 시스템 도메인에서 발생한 어떤 일에 대한 알림이며, 해당 발생과 관련된 데이터가 함께 전달된다고 설명했습니다. 언뜻 보면 CDC(데이터 변경 알림)와 비슷해 보일 수 있습니다. 시스템에 변화가 생기면 다른 시스템에 알려야 한다는 점에서 CDC는 정확히 같은 역할을 합니다. 하지만 여기에는 중요한 차이점이 있습니다. 이벤트는 도메인에 의미 있는 변화를 가져오기 때문에 데이터 변경보다 훨씬 높은 추상화 수준에서 정의됩니다. 엔티티를 나타내는 데이터는 해당 엔티티 전체에 "비즈니스"적인 영향을 미치지 않고 변경될 수 있습니다. 예를 들어, 주문 관리 시스템은 주문에 대해 내부적으로 여러 하위 상태를 유지할 수 있지만, 이러한 상태는 외부에는 중요하지 않습니다. 주문이 이러한 상태로 변경되더라도 이벤트는 발생하지 않지만, 변경 사항은 CDC 시스템에 기록됩니다. 반대로, 외부에서 중요하게 여기는 상태(생성됨, 발송됨 등)가 있고, 주문 관리 시스템은 이러한 상태를 외부에 명시적으로 노출합니다. 이러한 상태로의 변경은 이벤트를 생성합니다.
> 하지만 일부 사람들은 CDC 스트림을 시스템의 이벤트 스트림으로 사용하자고 제안하는데, 앞서 언급한 모든 이유 때문에 저는 이 의견에 전적으로 반대합니다. 이렇게 하면 다른 시스템이 우리 시스템의 물리적 데이터 모델에 종속되고, 공개 엔티티를 데이터베이스 모델과 영원히 동일하게 유지해야 합니다. 이는 도메인 모델의 표현력을 심각하게 저해합니다. 