---
title: Aurora에서 Debezium CDC 포기하고 Polling으로 간 이야기
date: 2026-05-15
tags:
  - PostgreSQL
  - Aurora
  - Kafka
  - Spring
category:
  - 기술
---

정보계로 데이터를 실시간으로 흘려보내야 해서 Debezium CDC를 도입하려다가 DBA한테 제지당하고 방향을 바꾼 이야기.

---

## 처음 계획: Aurora PostgreSQL + Debezium CDC

운영 DB에서 변경 이벤트를 Kafka로 실시간으로 밀어넣는 CDC 파이프라인을 구성하려고 했다. 가장 표준적인 방법이 PostgreSQL 논리적 복제(Logical Replication)를 활용하는 Debezium이라서, Aurora에 `wal_level = logical` 설정을 하려고 DBA에게 요청했다.

Aurora에서는 `postgresql.conf`를 직접 못 건드리고, RDS 파라미터 그룹에서 `rds.logical_replication = 1`로 설정하면 `wal_level`이 자동으로 `logical`로 올라간다. 이걸 바꾸면 정적 파라미터라 인스턴스 재부팅도 필요하다.

```sql
SHOW rds.logical_replication; -- on
SHOW wal_level;               -- logical
```

여기까지는 잘 됐는데 DBA가 난색을 표했다.

---

## DBA의 반론: "Aurora 쓰는 의미가 없어진다"

DBA가 한 말의 핵심은 이거였다.

> "Aurora는 마스터-리플리카 간 WAL 로그를 네트워크로 전송하지 않아요. 공유 스토리지를 같이 바라보는 구조라서 로그 전송 자체가 필요 없는데, `logical`로 올리면 그 장점이 사라져요."

처음엔 "Debezium은 Aurora 내부 복제랑 무관하지 않나?"라는 생각이 들었다. 실제로 Debezium은 Aurora 리플리카가 아니라 외부 시스템이고, 공유 스토리지를 직접 읽을 수 없으니 PostgreSQL 표준 논리적 복제 인터페이스를 쓸 수밖에 없다. 그러니 `wal_level = logical`은 여전히 필요하다.

근데 DBA 말의 포인트는 이게 아니었다.

**Aurora를 쓰는 이유가 뭔지**를 짚은 거였다. Aurora의 핵심 이점은:
- 마스터-리플리카 간 별도 로그 전송 없이 스토리지 레이어에서 자동으로 동기화
- 이 덕분에 `wal_level = replica` 기본 설정으로도 읽기 분산이 자연스럽게 된다
- 즉, WAL을 최소한으로 써도 복제가 된다는 게 Aurora의 설계 철학

근데 `logical`로 올리면?

- Row 단위 변경 전/후 데이터를 WAL에 전부 기록 → WAL 생성량 급증
- 쓰기 I/O, CPU 올라감
- Debezium 장애 시 복제 슬롯이 WAL을 계속 붙잡아서 디스크 풀 → DB 다운 위험

비싼 돈 주고 Aurora를 쓰는 이유가 "WAL 관리 부담 없이 안정적인 복제"인데, `logical`로 올리는 순간 그 이점을 스스로 포기하는 격이다.

---

## 정보계도 그냥 쿼리로 긁어간다고 했다

DBA 얘기를 들어보니 정보계 쪽에서도 Kafka 커넥터는 안 쓰고 그냥 주기적으로 쿼리를 날려서 데이터를 가져간다고 했다. 같은 이유였다.

수긍이 됐다. 실시간성이 초 단위로 타이트하게 필요한 게 아니라면, 굳이 DB 아키텍처에 리스크를 얹을 이유가 없다.

---

## 결론: Polling 기반 CDC로 방향 전환

결국 크론잡 또는 Spring WebFlux의 `Flux.interval`을 활용하는 방식으로 구현하기로 했다. 구조는 이렇다.

```
[스케줄러] --주기적 실행--> [Aurora Reader Endpoint]
                              SELECT * FROM orders
                              WHERE id > :lastId
                              ORDER BY id ASC LIMIT 1000
                           --> [결과 처리] --> [다음 주기 대기]
```

코드 레벨로는 이런 식이다.

```java
Flux.interval(Duration.ofSeconds(3))
    .flatMap(tick -> orderRepository.findNewOrders(lastProcessedId.get()))
    .doOnNext(order -> lastProcessedId.set(
        Math.max(lastProcessedId.get(), order.getId())
    ));
```

이렇게 하면 `Kafka Consumer`처럼 스트림을 구독하는 것과 비슷한 경험을 만들 수 있다.

몇 가지 조건은 지켜야 한다:

- **오프셋 컬럼 인덱스 필수** — `id`나 `updated_at` 기준으로 조회할 때 인덱스 없으면 매 사이클마다 풀 스캔
- **Aurora Reader Endpoint 격리** — 폴링 쿼리는 반드시 리더 인스턴스로만
- **LIMIT 걸기** — 한 사이클에 대량이 몰려 OOM 나는 거 방지
- **Soft Delete 설계** — 하드 딜리트된 데이터는 폴링으로 감지 불가, `is_deleted` 플래그로 처리해야 함

---

## 정리

| | Debezium CDC (`logical`) | Polling CDC |
|---|---|---|
| 실시간성 | 밀리초 단위 | 초 단위 (간격 조절 가능) |
| Aurora 적합성 | 낮음 (WAL 비용 증가) | 높음 (리더 분산 활용) |
| 장애 리스크 | 복제 슬롯 미소비 → 디스크 풀 | 없음 |
| Delete 감지 | 가능 | Soft Delete 필요 |
| 구현 복잡도 | 높음 (Kafka, Connector 관리) | 낮음 |

Aurora를 쓰면서 `wal_level = logical`을 올리는 건 설계 철학이랑 안 맞는 선택이었다. DBA의 제지가 맞았다.
