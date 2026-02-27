---
title: "**Lambda Managed Instances: EC2 Power with Serverless Simplicity**"
date: 2025-12-04
tags:
  - AWS
  - 기술
category:
  - 기술
---
AWS re:Invent 2025 세션 노트 정리.
lmi와 원래있던람다와 다른점?
사용자 계정의 vpc > ec2 인스턴스 안에 람다 인스턴스를 돌림. 
기존 람다는 진짜 light weight & 비용효율이라고 생각하면 얘는 조금 더 관리 잘된느낌?

![](attachment:8cd9d51c-e7c3-4126-8d95-8714ee7f8153:image.png)


![](attachment:c6f335ce-bde5-42ce-8c63-3925dcc803f4:image.png)

LMI를 언제 쓸까

![](attachment:744ddd7f-888e-4ba6-b110-8c2a156ea79d:image.png)

기존 람다에서 너무 느려터지거나 호출량 많아지는데 혼자 콜드스타트하고 있거나 이런 속터지는 상황을 방지하기 위해 사용할 수 있을듯.

![](attachment:99d5882d-928a-4046-aa51-701ee66b6ce4:image.png)

이렇게보니깐 그냥 argo workflow 같다.. 독립된 컨테이너 만들어서 띄우는거..근데 클라우드인

쓰기위한 스텝은 간단함 3스텝임
Capacity Provider 지정
  - VPC Config

![](attachment:84ca165a-9c36-47f1-a553-efcdb40ab18d:image.png)

    - 3 az에 각각 서브넷 구성하는걸 가용성을 위해 권장함.
    - 당연히 인그레스는 없음
  - Instance Type Config
    - C M R 인스턴스 .large 부터 다 가능
    - function memory size보고 자동결정도 되긴함 근데 그냥 설정해주는게좋을듯
  - Instance Scaling Config
    - 인스턴스 레벨 스케일링
function 만들기
  - 기존이랑 비슷함 lim function이고 capacity provider만 지정하면됨

![](attachment:77832a18-dddc-4e9d-8562-e8f990dac913:image.png)

  - snapstart는 lmi에서 안됨
  - fractional vcpu는 안됨. 정수만 됨.  2:1 기본
그리고 실행 진행합니다

지금 람다에서 쓸수있는 이벤트 소스 다 매핑해서 사용가능

![](attachment:839431c9-90ee-41ca-be35-9015962712ff:image.png)



기존람다와 Lmi 다른점?

![](attachment:fafa1fa6-e615-4c47-a2f0-80d9388bfeef:image.png)


concurrency 실행 가능
  - 기존에는 싱글스레드 블로킹되는것처럼 문제가 있었다? 이건공부좀해보자
    - invoke 3는 invoke 1 환경에서 다시 돌아감(singly concurrent)

![](attachment:2ac11668-561e-4c04-87c6-0aec298f31d5:image.png)

  - lmi의 경우에는 multi concurrency
    - 그러니깐 snap start가 안되요 그러니깐 콜드스타트도 없어요

![](attachment:f78cd56d-5676-4d54-a76a-bac982c2ded7:image.png)

    - 그러다보니 max concurrency가 있긴함 자바는 vcpu당 32, 파이썬은 16 이런식으로
    - goodput protection 됨

![](attachment:b3125adb-c50a-4d41-a68f-4ac3f5cff048:image.png)

    - 그리고 thread safe 함
      - 기존에 single concurrent시 생겼던 문제가 없음
콜드스타트 못하는대신에 스케일 업다운 할 수 있다
  - lmi에서는 콜드스타트 없이 asynchronous backend scale 함
  - cpu threshold 넘어가면 스케일 업(ec2 를 늘리던가) 또 threshold보다 많이 작으면 스케일다운하던가 그런식으로 함

![](attachment:41428589-712d-4fb5-ad39-e28fa7305850:image.png)

  - cpu 임계관련설정은 자동 수동 다 설정가능
  - 하이퍼옵티마이징을 잘해놔서 stable workload에 적합함. 자원이 튀는일이 기존 람다보다 적음. 

![](attachment:20db8430-0b33-4f2b-aa9a-5f0b5031ed2e:image.png)

독립된 이미 만들어진 환경내에서 실행가능
  - vm level isolation

![](attachment:dcbdb0e3-5ca6-4c50-9e36-a7d716907024:image.png)

아 당연히 ec2 비용이랑 람다 호출비용 같이 듦 
  - 호출비용은 드는데 람다 런타임 비용은 안듦 이게 ec2 비용이라 보면될듯



[Introducing AWS Lambda Managed Instances: Serverless simplicity with EC2 flexibility | Amazon Web Services](https://aws.amazon.com/ko/blogs/aws/introducing-aws-lambda-managed-instances-serverless-simplicity-with-ec2-flexibility/)
