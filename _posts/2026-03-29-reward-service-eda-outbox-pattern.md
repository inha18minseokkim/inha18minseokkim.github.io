---
title: 리워드 서비스를 Event Driven으로 만든 이유 - Transactional Outbox 패턴
date: 2026-03-29
tags:
  - Kafka
  - Debezium
  - CDC
  - EDA
  - Spring
category:
  - 실무경험
  - MSA표준
---

리워드 지급 서비스를 만들면서 Transactional Outbox 패턴 + Debezium CDC를 적용했음.
왜 이렇게 만들었는지, 기존 방식의 문제점이 뭐였는지 정리함.

---

## 프로젝트 개요

게임/이벤트 서비스에서 유저가 특정 행동(로그인, 구매, 레벨업 등)을 하면 리워드를 지급하는 서비스임.

**요구사항:**
- 이벤트 발생 시 리워드 지급
- 기간별 횟수 제한 (예: 하루 1회, 주 3회)
- 이벤트 발생과 리워드 지급 간 **데이터 일관성** 보장
- 실패 시 재처리 가능

---

## 기존 방식의 문제점

보통 이벤트 기반 리워드 지급은 이렇게 구현함:

```kotlin
@Transactional
fun grantReward(request: RewardRequest) {
    // 1. DB에 리워드 내역 저장
    rewardRepository.save(reward)

    // 2. Kafka로 이벤트 발행
    kafkaTemplate.send("reward-topic", event)
}
```

이 방식의 문제점:

### 1. 트랜잭션 불일치

```
┌─────────────────────────────────────────────────────┐
│ DB 트랜잭션                                          │
│   save(reward)  ─────┐                              │
│                      │ ← 여기서 커밋                 │
└──────────────────────┼──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│ Kafka 발행 (DB 트랜잭션 밖)                          │
│   kafkaTemplate.send()  ← 실패하면?                 │
└─────────────────────────────────────────────────────┘
```

- **DB 저장 성공 + Kafka 발행 실패**: 리워드는 저장됐는데 이벤트는 없음
- **DB 저장 실패 + Kafka 발행 성공**: 이벤트는 갔는데 리워드 없음 (드묾)

### 2. 재처리 어려움

Kafka 발행 실패 시 어떻게 재처리할 건지?
- 별도 스케줄러로 미발행 건 조회? → 복잡함
- 애플리케이션 재시작 시 누락 위험

### 3. 배포 중 이벤트 손실

롤링 배포 중 애플리케이션 종료되면 발행 대기 중인 이벤트 손실 가능.

---

## Transactional Outbox 패턴

이 문제를 해결하기 위해 **Transactional Outbox 패턴**을 적용함.

### 핵심 아이디어

Kafka로 직접 발행하지 않고, **Outbox 테이블에 INSERT**함.
Outbox 테이블을 Debezium이 CDC로 감시하다가 Kafka로 발행함.

```
┌─────────────────────────────────────────────────────┐
│ DB 트랜잭션 (원자적)                                 │
│                                                     │
│   비즈니스 로직 처리                                 │
│       ↓                                             │
│   Outbox 테이블에 INSERT                            │
│       ↓                                             │
│   COMMIT                                            │
│                                                     │
└──────────────────────────────┬──────────────────────┘
                               │
                               ▼ WAL 기록
┌─────────────────────────────────────────────────────┐
│ Debezium (별도 프로세스)                             │
│   WAL 읽기 → Kafka 발행                             │
└─────────────────────────────────────────────────────┘
```

### 장점

| 항목 | 기존 방식 | Outbox 패턴 |
|------|-----------|-------------|
| 트랜잭션 일관성 | DB와 Kafka 분리 | DB 트랜잭션 내 처리 |
| 누락 위험 | 높음 | 없음 (WAL 기반) |
| 재처리 | 별도 구현 필요 | Kafka 오프셋으로 자동 |
| 애플리케이션 부담 | Kafka 연결/발행 로직 | 단순 INSERT |

---

## 아키텍처

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Reward Service                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   ┌─────────────────┐      ┌─────────────────┐                      │
│   │  API Controller │      │  Kafka Consumer │◀─────────────────┐   │
│   │  (이벤트 발생)   │      │  (리워드 지급)   │                  │   │
│   └────────┬────────┘      └────────┬────────┘                  │   │
│            │                        │                           │   │
│            ▼                        ▼                           │   │
│   ┌─────────────────┐      ┌─────────────────┐                  │   │
│   │ Occurrence      │      │ Reward          │                  │   │
│   │ Service         │      │ Service         │                  │   │
│   └────────┬────────┘      └─────────────────┘                  │   │
│            │                                                    │   │
└────────────┼────────────────────────────────────────────────────┘   │
             │                                                        │
             ▼                                                        │
┌─────────────────────────────────────────────────────────────────┐   │
│                      PostgreSQL                                 │   │
├─────────────────────────────────────────────────────────────────┤   │
│  TB_RWD_EVENT_OCCURRENCE (Outbox)                               │   │
│  ┌──────────────┬──────────┬──────────┬────────────┐            │   │
│  │ occurrence_seq│ user_seq │ event_seq│ status     │            │   │
│  ├──────────────┼──────────┼──────────┼────────────┤            │   │
│  │ 1            │ 100      │ 1        │ PENDING    │            │   │
│  │ 2            │ 101      │ 2        │ PROCESSED  │            │   │
│  └──────────────┴──────────┴──────────┴────────────┘            │   │
│                           │                                     │   │
│                           │ WAL (pgoutput)                      │   │
│                           ▼                                     │   │
└─────────────────────────────────────────────────────────────────┘   │
                            │                                         │
                            ▼                                         │
┌─────────────────────────────────────────────────────────────────┐   │
│                      Debezium                                   │   │
│  reward_debezium_slot → reward_outbox_pub                       │   │
│                           │                                     │   │
│                           ▼                                     │   │
│  Kafka Topic: reward-server.public.tb_rwd_event_occurrence      │───┘
└─────────────────────────────────────────────────────────────────┘
```

---

## 테이블 구조

### Outbox 테이블 (TB_RWD_EVENT_OCCURRENCE)

```sql
CREATE TABLE TB_RWD_EVENT_OCCURRENCE (
    occurrence_seq BIGSERIAL   NOT NULL,
    user_seq       BIGINT      NOT NULL,
    event_seq      BIGINT      NOT NULL,
    occurred_at    TIMESTAMP   NOT NULL,
    status         VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    created_at     TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_rwd_event_occurrence PRIMARY KEY (occurrence_seq)
);
```

- **INSERT만 발생**: Debezium은 INSERT만 감지하면 됨
- **status**: `PENDING` → `PROCESSED` / `FAILED`로 Consumer가 업데이트
- **인덱스 최소화**: Outbox 특성상 쓰기 집중, row 수명 짧음

### 리워드 테이블 (TB_RWD_REWARD_M)

```sql
CREATE TABLE TB_RWD_REWARD_M (
    reward_seq      BIGSERIAL NOT NULL,
    base_date_time  TIMESTAMP NOT NULL,
    user_seq        BIGINT    NOT NULL,
    event_seq       BIGINT    NOT NULL,
    CONSTRAINT pk_rwd_reward_m PRIMARY KEY (reward_seq)
);

-- 기간별 횟수 제한 쿼리용 인덱스
CREATE INDEX idx_rwd_reward_user_event_date
    ON TB_RWD_REWARD_M (user_seq, event_seq, base_date_time);
```

---

## 처리 흐름

### 1. 이벤트 발생 (API)

```kotlin
@PostMapping
fun createOccurrence(@RequestBody request: EventOccurrenceCreateRequest) =
    occurrenceService.createOccurrence(request)
```

외부 서비스나 게임 서버에서 "유저가 로그인했다" 같은 이벤트 발생 시 호출함.
**Outbox 테이블에 INSERT만 하고 끝**. Kafka 발행은 안 함.

### 2. Debezium CDC

Outbox 테이블 INSERT 감지 → Kafka 토픽으로 발행.

```json
{
  "op": "c",
  "after": {
    "occurrence_seq": 11,
    "user_seq": 1,
    "event_seq": 1,
    "status": "PENDING"
  }
}
```

### 3. Consumer 처리

```kotlin
@KafkaListener(topics = ["\${app.kafka.topics.event-occurrence}"])
fun consume(message: String) {
    val payload = objectMapper.readValue(message, DebeziumEventPayload::class.java)

    // INSERT 이벤트만 처리
    if (payload.payload.op != "c") return

    rewardService.grantReward(occurrence)
}
```

### 4. 리워드 지급 로직

```kotlin
@Transactional
fun grantReward(occurrence: EventOccurrence) {
    val event = eventReader.getEvent(occurrence.eventSeq)

    // 비활성 이벤트 스킵
    if (!event.isAvailable) {
        occurrenceWriter.updateStatus(occurrence.occurrenceSeq, PROCESSED)
        return
    }

    // 기간별 횟수 제한 체크
    val periodCount = rewardReader.countRewardsInPeriod(
        userSeq = occurrence.userSeq,
        eventSeq = occurrence.eventSeq,
        from = periodStart,
        to = occurredAt
    )

    if (periodCount >= event.maxEventPerDuration) {
        log.info("[RewardGrant] 기간 한도 초과 스킵")
        occurrenceWriter.updateStatus(occurrence.occurrenceSeq, PROCESSED)
        return
    }

    // 리워드 지급
    rewardWriter.createReward(reward)
    occurrenceWriter.updateStatus(occurrence.occurrenceSeq, PROCESSED)
}
```

---

## CDC vs Domain Event 논쟁

이전에 {% post_url 2026-01-02-postgresql-cdc-debezium-kafka-eda-transactional-outbox %} 에서 정리했던 내용인데,
CDC를 이벤트 소싱에 쓰면 "비즈니스 의미가 사라진다"는 비판이 있음.

> "도메인 이벤트는 비즈니스 의미를 담아야 한다. CDC는 DB 레벨 변경 사실만 준다."
> — Chris Richardson

### 내 입장

**Outbox 패턴에서는 이 문제가 완화됨**.

| 구분 | 순수 CDC | Outbox 패턴 |
|------|----------|-------------|
| 감시 대상 | 비즈니스 테이블 전체 | Outbox 테이블만 |
| 이벤트 의미 | DB 변경 사실 | 명시적 이벤트 발생 기록 |
| 스키마 결합 | 강함 | Outbox 스키마에만 의존 |

순수 CDC는 `products` 테이블 변경을 그대로 전파하니까 "왜 변경됐는지" 모름.
근데 Outbox 패턴은 **애플리케이션이 명시적으로 "이벤트가 발생했다"고 기록**하는 거임.
Outbox 테이블 자체가 도메인 이벤트를 담는 그릇인 셈.

물론 Consumer에서 Debezium 메시지 포맷을 알아야 하긴 함.
근데 트랜잭션 일관성이랑 운영 안정성 얻는 대가로 감수할 만함.

---

## 프로젝트 구조

```
src/main/kotlin/com/kbank/.../reward/
├── api/
│   ├── occurrence/          # 이벤트 발생 API
│   │   ├── EventOccurrenceController.kt
│   │   └── EventOccurrenceService.kt
│   └── reward/              # 리워드 API + Consumer
│       ├── RewardController.kt
│       ├── RewardConsumer.kt     ← Kafka Consumer
│       └── RewardServiceImpl.kt  ← 기간 제한 로직
├── domain/
│   ├── occurrence/          # Outbox 도메인
│   ├── reward/              # 리워드 도메인
│   ├── event/               # 이벤트 마스터
│   ├── user/                # 유저 마스터
│   └── dlq/                 # DLQ 저장
└── infrastructure/
    └── kafka/
        └── dto/
            └── DebeziumEventPayload.kt  ← CDC 메시지 DTO
```

---

## 결과

```
2026-03-29T23:18:02.498  INFO [RewardGrant] 리워드 지급 완료 userSeq=1 eventSeq=1 occurrenceSeq=11
2026-03-29T23:21:18.202  INFO [RewardGrant] 기간 한도 초과 스킵 userSeq=1 eventSeq=1 periodCount=1 limit=1 duration=DAY
```

- CDC 정상 동작
- 기간별 횟수 제한 정상 동작
- 트랜잭션 일관성 확보

---

## 정리

| 항목 | 내용 |
|------|------|
| **문제** | DB 저장과 Kafka 발행 간 트랜잭션 불일치 |
| **해결** | Transactional Outbox 패턴 + Debezium CDC |
| **장점** | 트랜잭션 원자성, 누락 없음, 재처리 용이 |
| **단점** | 인프라 복잡도 증가 (Debezium, Kafka Connect) |

트래픽이 적은 서비스에서는 오버엔지니어링일 수 있음.
근데 이벤트 누락이 치명적인 리워드/결제 도메인에서는 고려할 만한 패턴임.