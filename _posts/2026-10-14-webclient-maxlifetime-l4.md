---
title: 또 다른 네티 네트워크 이슈
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

[499 삽질]({% post_url 2026-08-17-stock-mediation-499-part1 %})의 시작은 IDC ↔ stock-gateway 구간 idle timeout이 너무 짧아서 커넥션이 빨리 죽는 문제였는데, 이번엔 반대로 커넥션이 **안 죽어서** 문제가 됐다. 같은 keep-alive 커넥션 수명 얘기인데 방향이 정반대라 따로 정리해둠.

---

## L4에서 뺐는데 왜 계속 감?

EAI 호출을 대신 해주는 어댑터 서비스가 있는데, L4에서 EAI 서버 하나를 로테이션에서 빼놨는데도 그 서버로 요청이 계속 들어간다는 얘기가 나왔다.

L4 설정이 문제라고 생각한 건 아니고, 생각해보니 IDC > 내부 통신에 대한 타임아웃 설정은 했는데 내부 > IDC 통신할 때 설정에 대해서는 생각해본 적이 없었다.

직감적으로 이건 TCP 커넥션이 유지되고 있는 거니까 일단 재기동하면 L4 차단된 곳으로 더 이상 커넥션을 맺진 않을 거라 판단했고, 재기동 요청해서 급하게 상황은 마무리했다. 그리고 코드를 보니

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

그럼 idle timeout 걸면 되지 않나? 싶었는데 그것도 안 됨. 대략 100tps 정도가 계속 유지되고 있는 상황이라 커넥션이 **idle 상태가 될 틈이 없다.** idle timeout은 쉬고 있는 커넥션만 정리하니까 트래픽이 꾸준한 이상 영원히 안 걸림 ~~499 때 idle만 열심히 맞췄던 게 여기선 소용없었다~~

## 499랑 뭐가 다름

|              | IDC ↔ stock-gateway (499 때)                       | 이번 건                      |
| ------------ | ------------------------------------------------- | ------------------------- |
| 커넥션 상태       | 너무 빨리 죽음                                          | 너무 오래 삶                   |
| 무슨 일이        | 상대(SCG idle 1초)가 먼저 끊은 커넥션을 재사용 → premature close | 커넥션이 안 죽어서 L4가 뺀 서버로 계속 감 |
| 겉으로 보이는 것    | 499, Connection reset 같은 에러                       | 에러 없음. 그냥 엉뚱한 서버로 감       |
| 해결한 설정       | `maxIdleTime` < 상대 idle timeout                   | `maxLifeTime`             |

정리하면 클라이언트 풀의 커넥션 수명은 위아래로 둘 다 막혀 있어야 했던 것이다.

- **아래쪽(idle)**: 상대 서버, L4, 방화벽 중 누가 먼저 끊기 전에 내가 먼저 정리해야 함 → stock-gateway idle 이슈가 여기서 터짐
- **위쪽(lifetime)**: L4에서 서버를 빼면 정해진 시간 안에 따라가야 함 → 이번 건이 여기서 터짐

## 왜 idle 말고 lifetime이어야 함

이번에 제대로 찾아본 사실.

| | 기준 | 언제 0으로 돌아감 | 보장하는 것 |
|---|---|---|---|
| `maxIdleTime` | 마지막으로 **쓴** 시점 | 쓸 때마다 | 안 쓰는 커넥션은 오래 안 둠 |
| `maxLifeTime` | **만들어진** 시점 | 절대 안 돌아감 | 어떤 커넥션도 T보다 오래 못 삼 |

idle은 쓰기만 하면 계속 연장된다. Reactor Netty 풀은 기본이 FIFO라 커넥션을 골고루 돌려 쓰는데, 예를 들어 초당 10건에 커넥션 20개면 각 커넥션이 2초에 한 번씩은 쓰인다고 한다.

```
conn#1  사용 ─2s─ 사용 ─2s─ 사용 ─2s─ ...   idle 최대 2초
conn#2  사용 ─2s─ 사용 ─2s─ 사용 ─2s─ ...   idle 최대 2초
→ 40초 idle에 걸리는 커넥션이 하나도 없음
```

IDC의 서버는 EKS의 ReplicaSet처럼 완전히 롤아웃하고 새 이미지를 띄우는 게 아니다. 두 그룹이 있다면 작업이나 배포가 있을 때

1. L4로 1그룹을 막고 1그룹에 신규 클래스 파일을 복사 배포하거나 작업
2. 1그룹을 오픈하고 2그룹을 막고 똑같은 작업을 함
3. L4 제어 없앰

그래서 재기동을 하지 않다 보니 기존 커넥션이 계속 살아있고, 서버에서 RST로 끊어버리면 처리 중이던 POST가 날아갈 수 있다.

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

EKS에서 개발할 땐 `maxLifeTime` 신경 쓴 적이 거의 없다(물론 설정을 하긴 했는데 이번엔 ㄹㅇ 누락되어 있었고, IDC로 요청을 보내는 걸 netty로 처음 하다 보니 생긴 일). 생각해보니 EKS에선 **서버가 라우팅에서 빠지는 순간이랑 프로세스가 죽는 순간이 거의 같아서** 그랬던 거.
>> 보통 파드를 죽이는 거랑 로드밸런서 라우팅 빼는 걸 같이 하니까 신경 쓸 일이 없었다.

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

반면 EAI 서버는 몇 달씩 떠 있는 VM이고, 트래픽은 계속 오고, 운영자는 서버를 끄지 않고 로테이션에서만 뺀다. 커넥션이 진짜로 무기한 살아남을 수 있는 환경이었음. 그러다 보니 제어가 되지 않으면 해당 서버 배포를 못 한다.

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

idle은 짧게, lifetime은 L4 운영 절차에 맞게. 499 때 이거까지 같이 봤으면 좋았을텐데..
