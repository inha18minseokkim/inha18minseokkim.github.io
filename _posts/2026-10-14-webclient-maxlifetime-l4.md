---
title: keep-alive 커넥션이 안 죽어서 L4가 뺀 서버로 요청이 계속 간 이야기 — maxLifeTime
date: 2026-10-14
tags:
  - Spring
  - WebFlux
  - Reactor
  - Netty
  - Kotlin
  - 실무경험
category:
  - 실무경험
---

[499 삽질]({% post_url 2026-08-17-stock-mediation-499-part1 %}) 때는 커넥션이 너무 빨리 죽어서 문제였는데, 이번엔 반대로 커넥션이 **안 죽어서** 문제가 됐다. 같은 keep-alive 커넥션 수명 얘기인데 방향이 정반대라 따로 정리해둠.

---

## L4에서 뺐는데 왜 계속 감?

EAI 호출을 대신 해주는 어댑터 서비스가 있는데, L4에서 EAI 서버 하나를 로테이션에서 빼놨는데도 그 서버로 요청이 계속 들어간다는 얘기가 나왔다.

처음엔 L4 설정 문제겠지? 했는데 코드 보니까 우리쪽 문제였음.

```kotlin
@Bean("eaiWebclient")
fun eaiWebClient(): WebClient = WebClient.builder()
    .filter(loggingFilter("EAI"))
    .exchangeStrategies(exchangeStrategies)
    .build()
```

`clientConnector`를 안 넣었다. 이러면 Reactor Netty **전역 풀**을 쓰는데, 여기엔 `maxIdleTime`도 `maxLifeTime`도 없다. 한 번 맺은 keep-alive 커넥션을 무기한 재사용함.

문제는 L4가 하는 일이 **새 연결을 어느 서버로 보낼지 정하는 것**까지라는 거. 이미 맺어진 TCP 연결을 다른 서버로 옮겨주진 못한다.

```
[어댑터 풀]                [L4]              [EAI 서버]
 conn#1 ─────────────────────────────────────▶ 서버 A  (L4에서 제외됨)
 conn#2 ─────────────────────────────────────▶ 서버 A
 conn#3 ─────────────────────────────────────▶ 서버 B

 새 연결만 B로 감. conn#1, #2는 안 죽으니까 계속 A로 감
```

그럼 idle timeout 걸면 되지 않나? 싶었는데 그것도 안 됨. EAI 호출은 계속 들어오니까 커넥션이 **idle 상태가 될 틈이 없다.** idle timeout은 쉬고 있는 커넥션만 정리하니까 트래픽이 꾸준한 이상 영원히 안 걸림 ~~499 때 idle만 열심히 맞췄던 게 여기선 소용없었다~~

## 499랑 뭐가 다름

| | stock-mediation 499 | 이번 건 |
|---|---|---|
| 커넥션 상태 | 너무 빨리 죽음 | 너무 오래 삶 |
| 무슨 일이 | 상대(SCG idle 1초)가 먼저 끊은 커넥션을 재사용 → premature close | 커넥션이 안 죽어서 L4가 뺀 서버로 계속 감 |
| 겉으로 보이는 것 | 499, Connection reset 같은 에러 | 에러 없음. 그냥 엉뚱한 서버로 감 |
| 해결한 설정 | `maxIdleTime` < 상대 idle timeout | `maxLifeTime` |
| idle 설정으로 되나 | 됨 | 안 됨 |

정리하면 클라이언트 풀의 커넥션 수명은 위아래로 둘 다 막혀 있어야 했던 거.

- **아래쪽(idle)**: 상대 서버, L4, 방화벽 중 누가 먼저 끊기 전에 내가 먼저 정리해야 함 → 499가 여기서 터짐
- **위쪽(lifetime)**: L4에서 서버를 빼면 정해진 시간 안에 따라가야 함 → 이번 건이 여기서 터짐

## 왜 idle 말고 lifetime이어야 함

둘 다 타이머인데 시간을 재기 시작하는 기준이 다르다.

| | 기준 | 언제 0으로 돌아감 | 보장하는 것 |
|---|---|---|---|
| `maxIdleTime` | 마지막으로 **쓴** 시점 | 쓸 때마다 | 안 쓰는 커넥션은 오래 안 둠 |
| `maxLifeTime` | **만들어진** 시점 | 절대 안 돌아감 | 어떤 커넥션도 T보다 오래 못 삼 |

idle은 쓰기만 하면 계속 연장된다. Reactor Netty 풀은 기본이 FIFO라 커넥션을 골고루 돌려 쓰는데, 예를 들어 초당 10건에 커넥션 20개면 각 커넥션이 2초에 한 번씩은 쓰인다.

```
conn#1  사용 ─2s─ 사용 ─2s─ 사용 ─2s─ ...   idle 최대 2초
conn#2  사용 ─2s─ 사용 ─2s─ 사용 ─2s─ ...   idle 최대 2초
→ 40초 idle에 걸리는 커넥션이 하나도 없음
```

L4가 기존 연결을 못 옮기는 것도 원래 그렇게 동작하는 거다. SYN 들어올 때 어느 서버로 보낼지 정해서 세션 테이블에 박아두고, 그 뒤 패킷은 테이블대로 보낸다. 중간에 다른 서버로 옮기면 그 서버는 이 연결이 뭔지 모르니까.. 그래서 L4가 서버를 뺄 때는 기존 연결은 두고 새 연결만 막거나(이번 경우로 보임), RST로 다 끊거나 둘 중 하나다. RST로 끊으면 처리 중이던 POST가 날아간다.

결국 기존 연결은 **클라이언트가 직접 다시 맺어줘야** L4 변경을 따라간다. 트래픽이 있든 없든 다시 맺게 만드는 건 `maxLifeTime`뿐이다.

```
t=0    L4에서 서버 A 제외. A에 붙은 커넥션 나이: 10s, 45s, 80s
t=10   80초짜리 90초 도달 → 요청 끝나면 닫힘 → 새 연결은 B로
t=45   45초짜리 교체 → B
t=80   10초짜리 교체 → B
→ 늦어도 90초(+ 처리 중이던 요청 하나)면 A로 가는 커넥션 0개
```

그렇다고 idle이 필요 없는 건 아님. 막는 문제가 다르다.

| | `maxIdleTime` | `maxLifeTime` |
|---|---|---|
| 막는 것 | 상대가 먼저 끊은 커넥션 재사용 | 너무 오래 살아서 L4·서버 변경을 못 따라감 |
| 언제 터짐 | 트래픽이 **뜸할 때** | 트래픽이 **꾸준할 때** |
| 증상 | Connection reset, premature close | 에러 없이 엉뚱한 서버로 감 |
| 맞출 값 | 상대 idle timeout보다 짧게 | L4 제외 후 기다려주는 시간보다 짧게 |

트래픽 상황이 정반대일 때 터지는 거라 하나로 다른 하나를 못 막는다. 둘 다 걸어야 함.

찾아보니 다른 데도 같은 이유로 다 있는 설정이었다. HikariCP `maxLifetime`(DB 페일오버나 방화벽 바뀌어도 커넥션이 안 죽는 거 막으려고), gRPC `MAX_CONNECTION_AGE`, Envoy `max_connection_duration` 같은 거. 서버 쪽에서 막는 방법도 있는데 Tomcat `maxKeepAliveRequests`(기본 100)나 nginx `keepalive_requests`처럼 연결 하나당 요청 수를 제한해서 강제로 다시 맺게 하는 거다. EAI 서버에 이런 게 있었으면 이번 건이 덜 드러났을지도..

## EKS에선 왜 신경 안 썼지

EKS에서 개발할 땐 `maxLifeTime` 신경 쓴 적이 거의 없다. 생각해보니 EKS에선 **서버가 라우팅에서 빠지는 순간이랑 프로세스가 죽는 순간이 거의 같아서** 그랬던 거.

| | IDC L4 → EAI 서버 | EKS Service → Pod |
|---|---|---|
| 빠지는 계기 | 운영자가 L4에서 수동으로 제외 | 배포, 스케일 인, 장애로 Pod 종료 |
| 빠진 뒤 서버 | 멀쩡히 살아서 기존 연결 요청 계속 처리 | 프로세스 종료. 기존 연결도 같이 닫힘 |
| 클라이언트가 알아채나 | 못 알아챔. 응답이 잘 오니까 | 연결이 닫히니까 다음 요청부터 다시 맺음 |

Pod는 엔드포인트에서 빠지면 SIGTERM 받고 내려가니까 graceful shutdown이 keep-alive 연결을 닫아주고, 클라이언트 풀은 그 커넥션 버리고 새로 맺는다. **Pod가 죽는 게 maxLifeTime 역할을 대신 해주고 있었던 거.**

거기다 EKS는 연결을 갈아엎을 일이 원래 많다.

- 배포할 때마다 롤링 업데이트로 양쪽 Pod가 다 바뀜
- HPA, KEDA로 Pod가 생겼다 없어졌다 함
- 새벽처럼 한가할 땐 idle timeout으로 상당수 정리됨

반면 EAI 서버는 몇 달씩 떠 있는 VM이고, 트래픽은 계속 오고, 운영자는 서버를 끄지 않고 로테이션에서만 뺀다. 커넥션이 진짜로 무기한 살아남을 수 있는 환경이었음.

그리고 EKS 안에서는 중간에 L7이 끼는 경우가 많다. Istio 사이드카가 붙어 있으면 앱은 localhost의 Envoy랑 연결을 맺고 요청 단위 분배는 Envoy가 하니까, 앱 쪽 연결을 아무리 오래 써도 Pod 쏠림이 안 생긴다. SCG, Ingress, ALB도 요청마다 대상을 다시 고르고. 이번 건은 클라이언트 → **L4** → 서버처럼 연결 단위로 대상을 정하는 경로라서 터진 거다.

물론 EKS라고 아예 필요 없는 건 아니다.

- **스케일 아웃 쏠림**: Pod를 늘려도 기존 keep-alive 연결은 원래 Pod에 붙어 있어서 새 Pod엔 트래픽이 늦게 감. ClusterIP 직접 호출(kube-proxy는 L4)이면 생기는데 트래픽이 크지 않으면 잘 안 보임
- **HTTP/2, gRPC**: 연결 하나로 계속 보내서 쏠림이 훨씬 심함
- **DNS 뒤 대상이 바뀔 때**: Aurora 페일오버처럼 IP가 바뀌어도 풀에 있는 커넥션은 옛 IP에 붙어 있음
- **EKS 밖을 L4로 부를 때**: 이번 EAI처럼

## maxLifeTime 걸기

풀을 직접 만들어서 수명 제한을 걸었다.

```kotlin
internal fun pooledConnector(name: String, pool: WebclientPoolProperties): ReactorClientHttpConnector {
    val provider = ConnectionProvider.builder(name)
        .maxConnections(pool.maxConnections)
        .pendingAcquireMaxCount(pool.pendingAcquireMaxCount)
        .pendingAcquireTimeout(pool.pendingAcquireTimeout)
        .maxIdleTime(pool.maxIdleTime)
        .maxLifeTime(pool.maxLifeTime)
        .evictInBackground(pool.evictInterval)
        .build()
    var client = HttpClient.create(provider)
        .option(ChannelOption.CONNECT_TIMEOUT_MILLIS, pool.connectTimeout.toMillis().toInt())
        .compress(true) // 기본 커넥터가 하던 거 그대로 유지
    if (!pool.responseTimeout.isZero) client = client.responseTimeout(pool.responseTimeout)
    return ReactorClientHttpConnector(client)
}
```

`maxLifeTime`이 지난 커넥션은 요청 처리 중이면 끊지 않고, 끝나서 풀에 돌아올 때 닫는다고 한다. 풀에 놀고 있는 커넥션은 꺼낼 때나 백그라운드 evict 때 정리되고. 그래서 **L4에서 뺀 서버로 요청이 계속 가는 시간의 상한 ≒ maxLifeTime** 이 된다.

### 풀 직접 만들 때 함정

**풀을 직접 만들면 최대 커넥션 수 기본값이 확 줄어든다.** 전역 풀은 500인데 builder로 만들면 16이 됨. 이거 모르고 그냥 만들었다가 499 2부에서 `pending acquire queue has reached its maximum size`로 터졌던 거라 이번엔 500을 명시함.

그리고 `maxLifeTime > maxIdleTime`은 기동할 때 검증하게 했다. 499 때 idle/life 값을 잘못 잡아서 수명이 먼저 걸리는 바람에 idle 설정이 아무 의미 없어졌던 적이 있어서;

```kotlin
require(maxLifeTime > maxIdleTime) {
    "webclient.pool.max-life-time($maxLifeTime) must be longer than max-idle-time($maxIdleTime)"
}
```

### 기본값

stock-mediation에서 쓰던 값을 그대로 가져왔다.

| 설정 | 값 | 이유 |
|---|---|---|
| `maxConnections` | 500 | 기존 전역 풀이랑 같게. 상대 서버 용량 보고 정한 값은 아님 |
| `pendingAcquireMaxCount` | 1000 | 499 때 값 |
| `pendingAcquireTimeout` | 5s | 기본 45초 동안 붙잡고 있지 말고 빨리 실패 |
| `maxIdleTime` | 40s | 상대 idle timeout(60s)보다 짧게 |
| `maxLifeTime` | 90s | L4에서 뺀 서버로 요청이 가는 시간의 상한 |
| `evictInterval` | 30s | 499 때 값 |
| `responseTimeout` | 60s | 레거시 HTTP 타임아웃(60~70s)에 맞춤. 원래는 없었음 |

### POST라 재시도는 안 넣음

stock-mediation은 GET에만 premature close 1회 재시도를 달았는데, EAI 호출은 전부 POST라 재시도를 안 넣었다. 결제성 호출을 두 번 보낼 순 없으니까. 그래서 풀에서 꺼내 쓰는 순간 상대가 막 끊는 race는 `maxIdleTime`을 상대보다 충분히 짧게 두는 것 말고는 막을 방법이 없다.

## 테스트는 소스 포트로

커넥션이 재사용되는지 바뀌는지 어떻게 보지? 하다가 로컬 HTTP 서버가 요청마다 **클라이언트 소스 포트**를 기록하게 했다. 같은 커넥션이면 포트가 같고, 갈아끼워지면 바뀜.

```kotlin
server.createContext("/") { ex ->
    ports.add(ex.remoteAddress.port)
    // ...
}
```

- 기존 방식(전역 풀): 2초 동안 계속 호출해도 포트 1개로 고정 → 같은 커넥션 계속 재사용하는 거 재현됨
- `maxLifeTime` 400ms: 계속 호출해도(idle 안 되는 상태) 커넥션이 3개 이상 바뀜
- `maxIdleTime` 300ms: 쉬었다 호출하면 새 커넥션

이거 생각보다 깔끔하게 보여서 좋았음

## 아직 모르는 것

**maxIdleTime 40초는 이 경로에서 확인한 값이 아니다.** stock-mediation 하위 서비스(idle 60초) 기준으로 맞춘 값이라, L4나 방화벽 세션 timeout이 40초보다 짧으면 499 같은 race가 다시 생긴다. 이번엔 POST라 재시도도 없어서 바로 실패하고; L4 담당자한테 실제 timeout 값 받아서 다시 맞춰야 함.

**L4 서버 제외 절차랑 90초가 맞는지도 봐야 한다.** 서버 빼고 90초 안에 그 서버를 내리면 아직 붙어 있던 커넥션의 요청은 실패한다. 내부망 평문 HTTP면 재연결 비용이 크지 않아서 더 줄여도 될 것 같긴 한데..

그리고 `maxLifeTime`은 만료 시각을 흩뜨려주는 기능이 없어서, 한꺼번에 맺은 커넥션들이 비슷한 시점에 같이 만료될 수 있다. 내부망이라 괜찮을 것 같지만 외부 HTTPS 호출도 같은 클라이언트를 타서 TLS 핸드셰이크가 몰리는지는 지표로 한번 봐야 할듯

idle은 짧게, lifetime은 L4 운영 절차에 맞게. 499 때 이거까지 같이 봤으면 좋았을텐데..
