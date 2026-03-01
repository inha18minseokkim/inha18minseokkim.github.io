---
title: EKS-IDCkafka-openApi 수신 구조 잡기
date: 2024-06-25
tags:
  - Kafka
  - HTTP
  - 아키텍처
  - 케이뱅크
category:
  - 실무경험
  - MSA표준
---

행 내에서 해당 문제를 해결하기 위해 Kafka를 사용하기로 했음.


### KAFKA 스펙(Kbank IDC)

- kafka connect 사용 가능
- 7.9.1버전, kraft 사용
- 용량 꽤 괜찮음(1mb 100tps 버팀)
  - 다만 우리 파일 용량 1메가 넘음.
- openapi에 카프카 전용 servlet 따로 띄움
- broker 앞에 L4 있음(round robin), 3 브로커중에 하나
  - 하지만 브로커에서 다른 브로커로 뿌리는게 아니라 L4에서 지정하기 때문에 브로커 3개 방화벽신청 필요
  - 케이뱅크 내부 DNS를 찔러야 함. 
  - [Docker container 실행 - docker run (2)](https://hongl.tistory.com/119)
  - msa 상 pod에서 DNS 등록해줘야함
    - ⇒(20240711) Dockerfile 상에서 호스트를 등록해도 helm chart에서 강제로 값 주입하기 때문에 helm chart 값 요청 드려야 함.

KafkaItemReader 배치처리 가능
토픽 네이밍 룰
  - PUB_CXM_FDS_G_실제이름
  - PUB_출발지_도착지_그룹여부_실제이름
  - 아직 표준은 아님
    - 출발지 도착지는 애매함(도착지가?) 

오픈 API에서 consume 하는 토픽은 하나, 나가는 토픽은 n개(stk,exr,….)

elink 신규 설명회에서 배치 기능이 있다고 했는데 확인해 봐야 함.

카프카 스펙은 이렇게 되어있으니 작업 시작

![](/assets/images/Pasted%20image%2020260228171248_10ade41b.png)


[Kafka with Kbank MSA + 표준 스케줄러]({% post_url 2024-07-11-Kafka with Kbank MSA + 표준 스케줄러 %})
[Charset 인코딩 문제, 유량제어 문제]({% post_url 2024-07-16-Charset 인코딩 문제, 유량제어 문제 %})
[failing offset 문제와 데이터 수신 및 적재용으로 kafka 구성에 대해]({% post_url 2024-08-13-failing offset 문제와 데이터 수신 및 적재용으로 kafka 구성에 대해 %})
[EKS - IDC kafka - openApi 그대로 구현해보기(절망 프로젝트)]({% post_url 2024-09-04-EKS - IDC kafka - openApi 그대로 구현해보기(절망 프로젝트) %})
[다중 파티션 고도화]({% post_url 2024-09-09-다중 파티션 고도화 %})
[후회합니다 죄송합니다]({% post_url 2024-08-19-후회합니다 죄송합니다 %})
[Public 망에서 작업(희망사항)]({% post_url 2024-10-10-Public 망에서 작업(희망사항) %})

[아키텍쳐협의회 회의록(20241219)]({% post_url 2025-01-28-아키텍쳐협의회 회의록(20241219) %})