---
title: Spring Boot(r2dbc) 업그레이드했더니 OTel 계측 비호환으로 ClassCastException 터진 이야기
date: 2026-06-15
tags:
  - OTel
  - Spring
  - R2DBC
category:
  - 실무경험
---

OTel Java Agent는 1.32.0으로 그대로 둔 채 Spring Boot 버전만 올렸는데, r2dbc-postgresql이랑 reactor 버전이 같이 끌려 올라가면서 OTel 계측 코드랑 충돌이 남.

---

## 이슈 1 — ClassCastException

### 증상

Pod `/actuator/health` 헬스체크가 실패하고, 로그에 이런 에러가 계속 찍힘.

```
java.lang.ClassCastException: class io.r2dbc.postgresql.PostgresqlConnection
  cannot be cast to class reactor.core.scheduler.Scheduler
  (io.r2dbc.postgresql.PostgresqlConnection and reactor.core.scheduler.Scheduler
   are in unnamed module of loader 'LaunchedClassLoader')
```

### 원인 분석

OTel Java Agent는 r2dbc랑 reactor를 계측할 때 **클래스 로딩 시점에 바이트코드를 변환**함. 근데 OTel 1.32.0의 계측 코드는 구버전 r2dbc/reactor 기준으로 짜여있었고, Spring Boot 업그레이드로 r2dbc-postgresql이랑 reactor 내부 API가 바뀌면서 OTel이 가로채던 지점 자체가 어긋나버림.

구체적으로는 `ConnectionPool` 내부 스케줄러 콜백 연결 지점을 잘못 가로채면서, Connection 객체가 Scheduler 슬롯에 바인딩되는 상황이 만들어짐.

```
ConnectionPool.create()
  └─ reactor-pool 내부에서 Scheduler로 eviction 스케줄링
       ↑
       OTel 1.32.0 계측 코드가 이 지점을 잘못 가로채
       Connection 객체를 Scheduler 슬롯에 바인딩
       → ClassCastException 발생
```

에러 메시지에 r2dbc 클래스 이름이 나와서 처음엔 r2dbc 자체 문제인 줄 알았는데, 실제로 터진 위치는 reactor-pool 내부 scheduler 연결부였음. r2dbc 버그가 아니었던 거.

여기에 OTel export 실패(connection reset)까지 같이 발생하고 있으면 상황이 더 꼬임. export 실패 시 OTel 내부 span 종료 콜백이 예외를 던지고, 이 예외가 OTel이 심어놓은 reactor 훅을 타고 전파되면서 connection pool의 scheduler 처리 흐름에 섞여 들어감. 결국 두 문제가 겹쳐서 `PostgresqlConnection → Scheduler` cast 오류로 표면에 드러난 거였음.

### 삽질한 것들

에러 메시지만 보고 r2dbc 문제인 줄 알고 아래 순서로 시도했는데 전부 효과 없었음.

| 시도 | 이유 | 결과 |
|---|---|---|
| `bootJar { requiresUnpack("org.postgresql:r2dbc-postgresql") }` | LaunchedClassLoader 클래스 격리 해소 목적 | 효과 없음 |
| `spring.r2dbc.pool.enabled: false` | r2dbc-pool ↔ reactor-pool 버전 충돌 의심 | 효과 없음 |
| Spring Boot 4.0.5 → 3.3.12 다운그레이드 | BOM 의존성 충돌 의심 | 효과 없음 |
| Spring Boot 3.3.12 → 3.4.5 업그레이드 | Spring Core 6.1.x CVE 대응 겸 시도 | 효과 없음 |

다 안 먹혔던 이유는 원인이 r2dbc/reactor 버전이 아니라 **OTel agent가 클래스 로딩 시점에 하는 바이트코드 변환**이었기 때문. Spring Boot 버전을 아무리 바꿔도 OTel 1.32.0 agent는 그대로였으니까 문제가 계속 유지될 수밖에 없었음.

### 해결

OTel agent를 2.26.1로 업그레이드함. 2.x에서 Reactor / R2DBC 계측 코드가 전면 재작성되면서 비호환 문제가 해소됨.

---

## 이슈 2 — OTel 2.26.1 올렸더니 이번엔 connection reset

### 증상

OTel 2.26.1로 업그레이드하고 나니까 스테이징 환경에서 telemetry export가 실패하면서 connection reset이 남.

### 원인

OTel 2.x에서 기본 export 프로토콜이 바뀜.

| 항목 | OTel 1.x | OTel 2.x |
|---|---|---|
| 기본 export 프로토콜 | `grpc` | `http/protobuf` |
| 기본 포트 | 4317 (gRPC) | 4318 (HTTP) |

스테이징 환경의 Alloy가 구버전이라 4317 포트에서 gRPC 신호를 기다리고 있었는데, 2.26.1 에이전트는 기본값이 HTTP라 그쪽으로 전송해버려서 프로토콜 불일치로 connection reset이 난 거였음.

### 해결 방법

**방법 1 — 에이전트 측에서 프로토콜 명시 (단기)**

```bash
# 환경변수
OTEL_EXPORTER_OTLP_PROTOCOL=grpc

# 또는 JVM 옵션 (main class 앞에 위치)
-Dotel.exporter.otlp.protocol=grpc
```

**방법 2 — Alloy 업그레이드하거나 HTTP 수신 포트 추가 (장기)**

```yaml
otelcol.receiver.otlp "default" {
  grpc {
    endpoint = "0.0.0.0:4317"
  }
  http {                        # 추가
    endpoint = "0.0.0.0:4318"
  }
}
```

에이전트 버전 올릴 때 계측 대상 라이브러리 버전만 신경쓰지, export 프로토콜 기본값이 바뀌는 건 놓치기 쉬운 부분이라 따로 체크리스트에 넣어둬야겠음.

SRE의 결론 중 하나는, 그래서 OTel Java Agent 갖다버리고 eBPF 기반 Beyla로 바꾼다고 한다. 애초에 애플리케이션 코드/클래스로더에 바이트코드 주입하는 방식 자체가 라이브러리 버전 올릴 때마다 이런 식으로 터질 여지를 계속 깔고 가는 거라, 커널 레벨에서 트래픽 잡는 쪽으로 가는 게 낫다고 판단한 듯. 관련 공부 해봐야할듯
+ 이런식으로는 프로덕션에서 잘 안쓴다고 한다. 지금 otel이 @Observed로 쓰는것도 아니고 완전 인젝션되어서 내부에서 진행되는 자바 메서드 다 캐치해서 보내다보니 그라파나쪽 부하가 상당하다고 한다. 
