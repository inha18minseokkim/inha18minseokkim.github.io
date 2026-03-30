---
title: Debezium CDC 연동 삽질기 - PostgreSQL + Kafka
date: 2026-03-29
tags:
  - Kafka
  - Debezium
  - CDC
  - PostgreSQL
  - Spring
  - EDA
  - 이슈정리
category:
  - 실무경험
  - MSA표준
---
신규 게임 서비스에 EDA를 적용하기 위해 
샘플로 만든 리워드 서비스에 Transactional Outbox 패턴 적용하면서 Debezium CDC 연동했음.
PostgreSQL WAL → Debezium → Kafka → Spring Consumer 흐름인데, 예상대로 삽질 좀 했음.

---

## 아키텍처

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Application   │     │   PostgreSQL    │     │    Debezium     │
│                 │     │                 │     │  (Kafka Connect)│
│  INSERT INTO    │────▶│  WAL (logical)  │────▶│  pgoutput 읽기   │
│  outbox table   │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └────────┬────────┘
                                                         │
                                                         ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Spring Kafka   │◀────│     Kafka       │◀────│  Kafka Topic    │
│    Consumer     │     │     Broker      │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

Outbox 테이블에 INSERT 하면 Debezium이 WAL 읽어서 Kafka 토픽으로 발행하고, Consumer가 받아서 리워드 지급 처리하는 구조임.

---

## 삽질 1: Replication Slot이 active=false

### 상황

PostgreSQL에서 복제 슬롯 상태 확인했더니 `active=false`임.

```sql
SELECT slot_name, plugin, active
FROM pg_replication_slots
WHERE slot_name = 'reward_debezium_slot';
```

```
 slot_name            | plugin   | active
----------------------+----------+--------
 reward_debezium_slot | pgoutput | f
```

### 원인

Debezium Connector 상태 확인해보니 **tasks가 비어있음**.

```bash
curl http://localhost:8881/connectors/reward-outbox-connector/status
```

```json
{
  "name": "reward-outbox-connector",
  "connector": {"state": "RUNNING"},
  "tasks": [],  // ← 비어있음!
  "type": "source"
}
```

Connector는 RUNNING인데 실제로 일하는 Task가 없으면 CDC 안 됨.

### 해결

삭제 후 재등록함.

```bash
# 삭제
curl -X DELETE http://localhost:8881/connectors/reward-outbox-connector

# 재등록
curl -X POST http://localhost:8881/connectors \
  -H "Content-Type: application/json" \
  -d '{
    "name": "reward-outbox-connector",
    "config": {
      "connector.class": "io.debezium.connector.postgresql.PostgresConnector",
      "tasks.max": "1",
      "database.hostname": "125.186.138.131",
      "database.port": "5432",
      "database.user": "minseokkim",
      "database.password": "xxx",
      "database.dbname": "rewarddb",
      "plugin.name": "pgoutput",
      "publication.name": "reward_outbox_pub",
      "slot.name": "reward_debezium_slot",
      "table.include.list": "public.tb_rwd_event_occurrence",
      "topic.prefix": "reward-server"
    }
  }'
```

Task가 생성 안 되는 이유는 보통 이것들임:
- DB 연결 실패
- Publication 없음
- Slot 없음
- 권한 부족

Kafka Connect 로그 확인하면 원인 나옴.

---

## 삽질 2: 토픽 이름 대소문자 불일치

### 상황

Debezium은 메시지 잘 발행하는데 Spring Consumer가 안 받음.

Kafka peek 해보니 토픽에 메시지 쌓여있음:

```json
{
  "op": "c",
  "after": {
    "occurrence_seq": 10,
    "user_seq": 1,
    "event_seq": 1,
    "status": "PENDING"
  }
}
```

### 원인

**토픽 이름 대소문자가 다름**.

| 구분 | 토픽 이름 |
|------|-----------|
| application.yml | `reward-server.public.TB_RWD_EVENT_OCCURRENCE` |
| 실제 Kafka 토픽 | `reward-server.public.tb_rwd_event_occurrence` |

Kafka 토픽 이름은 **대소문자 구분**함. Consumer가 없는 토픽 구독하고 있었음.

### 해결

```yaml
# application-postgre.yml
app:
  kafka:
    topics:
      event-occurrence: reward-server.public.tb_rwd_event_occurrence  # 소문자
```

Debezium connector의 `table.include.list`를 소문자로 설정했으면 토픽도 소문자로 생성됨.

---

## 삽질 3: Jackson 역직렬화 에러

### 상황

Consumer가 메시지 받자마자 예외 터짐.

```
UnrecognizedPropertyException: Unrecognized field "status"
(4 known properties: "occurrence_seq", "event_seq", "user_seq", "occurred_at")
```

### 원인

Debezium 메시지에는 7개 필드가 있는데 DTO에는 4개만 정의됨.

```json
// Debezium 메시지
"after": {
  "occurrence_seq": 10,
  "user_seq": 1,
  "event_seq": 1,
  "occurred_at": 1774785600000000,
  "status": "PENDING",        // ← DTO에 없음
  "created_at": 1774825951,   // ← DTO에 없음
  "updated_at": 1774825951    // ← DTO에 없음
}
```

### 해결

`@JsonIgnoreProperties(ignoreUnknown = true)` 추가함.

```kotlin
@JsonIgnoreProperties(ignoreUnknown = true)
data class DebeziumEventPayload(
    val payload: Payload
) {
    @JsonIgnoreProperties(ignoreUnknown = true)
    data class Payload(
        val op: String?,
        val after: OccurrenceRow?
    )

    @JsonIgnoreProperties(ignoreUnknown = true)
    data class OccurrenceRow(
        @JsonProperty("occurrence_seq") val occurrenceSeq: Long,
        @JsonProperty("user_seq") val userSeq: Long,
        @JsonProperty("event_seq") val eventSeq: Long,
        @JsonProperty("occurred_at") val occurredAt: Long
    )
}
```

필요한 필드만 매핑하고 나머지는 무시. Debezium 스키마 변경돼도 안전함.

---

## 삽질 4: Timestamp 단위 불일치

### 상황

리워드 지급은 되는데 `occurredAt` 날짜가 이상함. 58000년 뭐 이런 식으로 나옴.

### 원인

Debezium의 `MicroTimestamp`는 **microseconds** 단위인데, `Instant.ofEpochMilli()`로 처리하고 있었음.

```kotlin
// 잘못된 코드
occurredAt = LocalDateTime.ofInstant(
    Instant.ofEpochMilli(row.occurredAt),  // milliseconds로 처리
    ZoneId.systemDefault()
)
```

### 해결

1000으로 나눠서 milliseconds로 변환함.

```kotlin
// 수정된 코드
occurredAt = LocalDateTime.ofInstant(
    Instant.ofEpochMilli(row.occurredAt / 1000),  // microseconds → milliseconds
    ZoneId.systemDefault()
)
```

---

## 최종 결과

```
2026-03-29T23:18:02.498  INFO [RewardGrant] 리워드 지급 완료 userSeq=1 eventSeq=1 occurrenceSeq=11
2026-03-29T23:21:18.202  INFO [RewardGrant] 기간 한도 초과 스킵 userSeq=1 eventSeq=1 periodCount=1 limit=1 duration=DAY
```

CDC 정상 동작 확인됨. 하루 1회 제한도 잘 먹음.

---

## CDC 체크리스트

Debezium CDC 연동할 때 확인할 것들:

| 항목 | 확인 방법 |
|------|-----------|
| PostgreSQL `wal_level=logical` | `SHOW wal_level;` |
| Replication Slot 존재 | `SELECT * FROM pg_replication_slots;` |
| Slot `active=true` | 위 쿼리에서 active 컬럼 확인 |
| Publication 존재 | `SELECT * FROM pg_publication;` |
| Publication에 테이블 등록 | `SELECT * FROM pg_publication_tables;` |
| Connector 상태 RUNNING | `curl .../connectors/{name}/status` |
| **Task 존재** | tasks 배열이 비어있으면 안 됨 |
| 토픽 이름 대소문자 | Kafka 토픽명과 Consumer 설정 일치 확인 |
| DTO 필드 매핑 | `@JsonIgnoreProperties(ignoreUnknown = true)` |
| Timestamp 단위 | Debezium은 microseconds 사용 |

---

## 느낀점

CDC 자체는 어렵지 않은데 환경 설정에서 삽질이 많이 발생함.
특히 **tasks가 비어있는 문제**는 Connector가 RUNNING이라서 정상인 줄 알았는데 실제로는 아무것도 안 하고 있었음.
토픽 대소문자 문제도 은근 빠지기 쉬운 함정임.

Transactional Outbox 패턴 + Debezium 조합은 확실히 좋음.
애플리케이션 코드에서 Kafka 발행 신경 안 써도 되고, DB 트랜잭션과 메시지 발행이 원자적으로 처리됨.