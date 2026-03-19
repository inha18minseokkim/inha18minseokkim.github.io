---
title: "EKS Pod 배포 및 구동시 38080(server.port) already in use 발생: exec form"
date: 2025-08-12
tags:
  - Kubernetes
  - 인프라
  - 이슈정리
category:
  - 기술
---
EKS Pod 관련 이슈 해결 내용 정리.
# 상황

서비스 및 배치를 배포/기동 시 38080 already in use 문제가 발생함
분명히 독립적인 pod 단위이므로 포트 충돌이 발생하면 안될것같은데 낢

### istio proxy 문제인가

그건아님. convenience batch는 istio proxy 명시적으로 사용하지 않고있는데도 낢

### 노드 증설하고 줄어듦

노드에서 ip 할당할 때 충돌나서 문제가 생기는 것인가

### 잠정 원인

기존 Dockerfile. 구성할 때 java -jar 시 PID가 1번이 아니었음. pod 종료 시 sigTerm 요청 시 깔끔하게 안떨어져서 다음 파드가 같은 노드에서 해당 아이피를 할당받았을 때 포트 충돌의 여지가 있는 것 같음

### 조치


```python
echo 'java -javaagent:/app/agent/opent~~~~
```


```python
echo 'exec java -javaagent:/app~
```

로 바꿈. 안정적으로 프로세스를 정리해서 그런지 일단 지금까지는 동일현상 발생 안하는중


### 사유

> 자바 어플리케이션이 1번 프로세스가 되어야 함.
그렇지 않다면 Kubernetes 에서 pod 종료 시 SIGTERM을 보내는데, 1번 프로세스가 아닌 자식 프로세스라면 자식프로세스에게 SIGTERM을 전달안해줌. 그래서 프로세스 정리 안되고 있다가 SIGKILL당함.

만약

```kotlin
CMD java -jar app.jar
```

이렇게 수행하면

```kotlin
PID 1: /bin/sh -c java -jar app.jar
PID 8: java -jar app.jar
```

이렇게 됨. 1번프로세스에 SIGTERM을 날려도 8번 프로세스에 전달되지 않음. 결국 자바는 SIGTERM 못받고 10초 뒤에 SIGKILL 당함

```kotlin
CMD exec java -jar app.jar
```

이렇게 하면

```kotlin
PID 1: java -jar app.jar
```

이렇게 되므로 SIGTERM을 자바 어플리케이션이 직접 날림
상당히 흔한 사례였다..

여기서 한 술 더 뜨자면
만약 도커상황이 아닌 정상적인 리눅스 상황이면 1번 프로세스에서 자 프로세스로 init을 하고 하위 프로세스를 종료시키기 위해 SIGTERM을 잘 넘겨줌. ssh 세션 끊어서 해당 pid가 사라지면 pid1이 16을 자식으로 거두어 처리.
![이미지](/assets/images/Pasted%20image%2020260301230654.png)


하지만 pid1이 init 프로세스가 아니라 container의 java process라면 위와같이 처리를 못함.
그래서 docker script에서 CMD java -jar app.jar 이 짓을 하면
docker run 안에 /bin/sh 안에 java -jar가 되어 sh가 pid 1이 되고 java가 pid 2가 됨.
그러므로 /bin/sh 를 통해 프로세스를 실행했음으로 2번프로세스에 sigterm 못보냄. 그러므로 쿠버네티스 입장에서는 일정시간이 되어도 자원이 반환되지 않으므로 SIGKILL함. 이러면 이제 트랜잭션 처리 문제 등등 발생
하지만 CMD exec java -jar app.jar 를 하고 spring 의 server.shutdown = graceful 옵션을 설정해주면 컨테이너에서 정상적으로 자원을 반환할 수 있음

만약 다른 상황이라면?
dumb-init을 사용하면 됨.

```kotlin
FROM scratch
RUN apt install -y dumb-init
ENTRYPOINT ["/usr/bin/dumb-init","--","/app/run.sh"]
```

모든 signal을 dumb-init을 통해 signal handler에 등록하고 signal을 프로세스 세션으로 전달 가능(signal propagate)
 
앞으로 알아볼 점 : 대부분의 웹 애플리케이션은 dumb-init을 사용하지 않아도 될까?

[Perplexity](https://www.perplexity.ai/search/https-stump-blender-387-notion-5hMJtyFiT.6jF9wmV6AV0w)
[https://mateon.tistory.com/126](https://mateon.tistory.com/126)