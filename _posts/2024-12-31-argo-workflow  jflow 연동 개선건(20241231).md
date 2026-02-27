---
title: "argo-workflow <> jflow 연동 개선건(20241231)"
date: 2024-12-31
tags:
  - 인프라
  - 개발
category:
  - 기술
---
Argo Workflow(jflow)를 활용한 워크플로우 구성 정리.
### ASIS


```java
argo submit loop-sequence.yaml --watch
```

이정도 기본 명령어만 들어있는데 

![](https://prod-files-secure.s3.us-west-2.amazonaws.com/c38aebd7-2834-4fac-b2fc-a2f0c17ce81d/f04ede96-3f16-45d2-b447-efcca0961b3e/image.png)

watch 옵션을 걸어놓으면 위 코드가 계속 1초에 한번씩 찍힘. 그러다보니 8시간 이상 도는 작업은 로그사이즈가 270메가 넘어가서 jflow 상 작업 에러 떨어지고 jflow에서 실제 파드 내부에서 어떤 작업을 수행했는지는 안보임.

### TOBE


```java
**argo submit loop-sequence.yaml --watch --log | sed -r "s/\x1b\[[0-9;]*[mGKH]//g"**
```

—log 옵션을 넣으면 위 화면 갱신이 되지 않고 실제 파드 내부의 로그를 보여주는 옵션이 있었다 (와!)
뒤 sed 구문은 argo workflow에서 stdout 할 때 ANSI 코드(특수문자, 콘솔에 색깔넣기등)가 들어있어서 정상적인 문자열만 콘솔상에서 보여지도록 함.

![](https://prod-files-secure.s3.us-west-2.amazonaws.com/c38aebd7-2834-4fac-b2fc-a2f0c17ce81d/b05ac2e1-0177-461e-b339-2abdf37bd48d/image.png)


위 개선으로 두 가지 목적 달성
1. jflow에서 로그 볼 수 있음
2. jflow에서 장시간 작업으로 인해 로그 파일 사이즈가 방대해지는 문제 해결
  1. 8시간 이상 도는 경우 jflow에서 NOK 로 떨어지는(하지만 실제로 작업은 도는 중) 문제 해결 가능 기대

2025 1월 운영적용 완료