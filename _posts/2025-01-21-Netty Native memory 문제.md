---
title: "Netty Native memory 문제"
date: 2025-01-21
tags: [미지정]
---

여기서 openapi-servlet 프로젝트를 구현하다가 맞닥뜨린 이슈.
블로킹 라이브러리를 사용할 때는 나지 않았만 논블로킹으로 프로젝트를 야매로 전환하면서 Memory OOM이 나기 시작함(특정 메가바이트 단위의 응답값에 대해), 날 때도 있고, 안날 때도 있고, 처음에는 안나다가 나중에는 나고 이런식



```yaml
 Cannot reserve 4854065 bytes of direct buffer memory (allocated: 8787367, limit: 10475760)
```

이런 느낌의 로그가 나온다. 도커 메모리가 낮은것도 아닌데, 왜 자꾸 버퍼메모리가 없냐라고 생각했는데, Java DirectMemory를 찾아보면서 실마리를 찾을 수 있었다.


### 알기 전

1. 톰캣이든 네티든 자바로 구현되었으면 안의 메모리관리는 무조건 JVM이 해주겠지
2. 힙메모리도 가변적으로 조절하라고 쓰는거니깐 알아서 늘겠지



### 정리


![이미지](/assets/images/Pasted%20image%2020260224101216.png)

JVM 메모리 영역에서 GC에 의해 관리되지 않는 메모리 > DirectBuffer등 네이티브 메모리.
Netty 같은것들이 최근 성능 향상을 위해 Direct Memory 사용한다고 함.
GC에 의해 관리되지 않다보니 별도로 관리가 필요할 수 있음.

ByteBuffer를 사용해서 jvm heap 영역의 buffer를 ByteBuffer.allocate()로 생성하면 Java GC가 알아서 해주겠지만, ByteBuffer.allocateDirect()를 사용하면 DirectBuffer 가 Kernel buffer를 만들어줌.
즉 JVM에서 관리해주지 않음.

우선 해당 문제는 DirectMemorySize 상한을 늘려서 해결하였음. 데이터 스트리밍 시 메가단위 json 파일을 옮기다보니 스케줄러에 사용되어야 하는 메모리가 부족해서 그런듯 함.(기본 10메가)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: openapi-servlet
spec:
  replicas: 1
  revisionHistoryLimit: 1
  selector:
    matchLabels:
      app: openapi-servlet
  template:
    metadata:
      labels:
        app: openapi-servlet
    spec:
      containers:
        - image: muyaho/openapi-servlet:2.1
          name: openapi-servlet
          ports:
            - containerPort: 80
          env:
            - name: JAVA_OPTS
              value: "-XX:MaxDirectMemorySize=64M
```




Native Memory의 경우 GC에 의해 정리되는 대상이 아니다보니 PhantomReference 사용해서 GC 한다.


![이미지](/assets/images/Pasted%20image%2020260224101227.png)


### UNSAFE

JNI 사용해서 memory syscall 호출, 즉 OS 영역 접근 ex) Unsafe.allocateMemory(), Unsave.freeMemory()


### Deallocator

![이미지](/assets/images/Pasted%20image%2020260224101233.png)

DirectByteBuffer 내부 클래스
![이미지](/assets/images/Pasted%20image%2020260224101239.png)

PhantomReference를 상속, ReferenceQueue 사용하여 clean 함.
여기서 PhantomReference, ReferenceQueue는 자바 GC에서 사용되는 그거임
![이미지](/assets/images/Pasted%20image%2020260224101246.png)

간단하게 넘어가면 Reference 되지 않는 공간에 있으면 GC가 실행될 때 ex) Stop the world
JVM 힙 영역에 있던 객체들은 ReferenceCount가 없으면 죽여버리는것처럼 ReferenceQueue를 등록해놓고, Native Memory를 정리해야 할 때가 오면 ReferenceQueue를 통해 참조하고 있는 메모리를 제거함
객체가 Reference가 없어지는 경우(RefenceCount가 0) GC가 정리하는것 처럼.

### PhantomReference를 통해 참조하고있는데 ?

그러라고 만든거임. PhantomRefence는 레퍼런스카운트에 안들어간다. Strongly Reachable, Weakly Reachable 외에 Phantomly Reference라고 따로 있음. 즉 Phantomly Reference만 남았다 > 제거대상
Phantomly Reference는 반드시 Reference Queue 사용 함.
GC 가 구동되면 다음 순으로 정리함
1. soft references
2. weak references
3. finalize
4. phantom references
5. 메모리 회수


### PhantomReference는 그럼 어떤 사이클을 타는거냐?

다음시간에…

### 그래서 왜 OutOfMemoryError가 났는가

인과관계를 정리하면 다음과 같다.

1. Netty는 성능을 위해 I/O 시 `ByteBuffer.allocateDirect()`로 Direct Memory를 할당함
2. Direct Memory는 JVM 힙이 아니라서 GC가 직접 수거하지 않음
3. 대신 `DirectByteBuffer`가 PhantomReference + ReferenceQueue를 통해 정리됨
4. **핵심**: 이 정리는 GC가 구동될 때(Stop-the-world)에야 비로소 일어남
5. MB 단위의 JSON 응답을 스트리밍할 때 Netty가 Direct Buffer를 빠르게 대량 할당함
6. GC가 충분히 자주 돌기 전에 할당량이 MaxDirectMemorySize(기본 ~10MB)에 도달
7. 더 이상 예약할 수 없어 `Cannot reserve N bytes of direct buffer memory` OOM 발생

**간헐적으로 나는 이유**: GC 타이밍에 따라 다름. GC가 먼저 돌아서 PhantomReference 정리가 선행되면 OOM이 안 나고, 요청이 몰리거나 GC 주기가 길어지면 그 사이에 Direct Memory가 한계에 도달해 OOM이 남. 처음에는 괜찮다가 나중에 나는 것도 같은 이유 — 메모리가 누적되다가 임계값을 넘는 것.

결국 **할당 속도 > 해제 속도** 구간이 생기면 터지는 구조이고, MaxDirectMemorySize를 늘리는 것은 그 구간의 여유를 확보하는 것.


[Reference Count를 통한 Netty의 ByteBuf memory 관리](https://effectivesquid.tistory.com/entry/Reference-Count%EB%A5%BC-%ED%86%B5%ED%95%9C-Netty%EC%9D%98-ByteBuf-memory-%EA%B4%80%EB%A6%AC)
[메모리 모니터링과 원인 분석 | 인사이트리포트 | 삼성SDS](https://www.samsungsds.com/kr/insights/1232762_4627.html)
[[Java Memory Profiling에 대하여] ① JVM 메모리 이해와 케이스 스터디](https://m.post.naver.com/viewer/postView.nhn?volumeNo=23726161&memberNo=36733075)
[Direct Memory in Java](https://junhyunny.github.io/java/jvm/direct-memory-in-java/)
[Virtual Thread의 기본 개념 이해하기](https://d2.naver.com/helloworld/1203723)
[Java Phantom Reachable, Phantom Reference 란](https://luckydavekim.github.io/development/back-end/java/phantom-reference-in-java/)
