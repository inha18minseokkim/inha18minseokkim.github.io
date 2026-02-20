---
title: "언럭키 CQRS 패턴 (20251010)"
date: 2025-10-10
tags: [아키텍처, CQRS, Spring, 백엔드, 주식서비스]
---

![이미지](/assets/images/Pasted%20image%2020260220151620.png)

[BFF(Backend-For-Frontend)](https://www.notion.so/BFF-Backend-For-Frontend-24d2f38ca96880808fe6fd3378cafe98?pvs=21)

여기서 위와 같은 구조로 주식 서비스를 만들고 있고 현재 ant-service 를 만들면서 해외주식 가격정보를 제공해주려고 하고 있다.

이번 PM(20251108) 때 몇 가지 대규모 개선을 하려고 하는데 기존 unlisted-stock-service에 있는 고객 관련 로직들을 모두 stock-customer-service로 이관하고 비상장주식 데이터를 제공하는 로직만 unlisted-stock-service에 남길 예정

ASIS)

unlisted-stock : 비상장주식서비스 관심 등록, 푸시 등록, 비상장주식 조회순위집계, 비상장주식서비스 데이터 제공

stock-customer : 주식둘러보기 관심등록, 공통 푸시 등록, 랭킹 집계

TOBE)

unlisted-stock : 비상장주식서비스 데이터 제공

stock-customer: 주식 서비스 내의 모든 고객들의 관심정보 관리, 푸시정보 관리, 조회 랭킹 집계

ipo-service(공모주 메이트) 서비스에 있는 푸시 등록도 추후에 stock-customer 서비스로 뺄 예정이다.

그러다보니 궁극적으로

CRUD를 수행하는 서비스: stock-customer

R만 수행하는 서비스 : ipo,unlisted,listed,overseas,etf

가 되어버렸다

뭔가 예전에 배웠던 CQRS 패턴과 유사해졌다.

### CQRS 패턴에 대한 설명

> CQRS(Command Query Responsibility Segregation) 패턴은 시스템에서 데이터의 쓰기(Command)와 읽기(Query) 작업을 명확히 분리하는 소프트웨어 아키텍처 패턴입니다. 이 패턴은 명령을 처리하는 모델과 조회를 처리하는 모델을 분리하여 각 작업에 최적화된 설계를 할 수 있도록 하여 성능, 확장성, 보안성, 그리고 복잡성 관리 측면에서 이점을 제공합니다.

Command = 시스템의 상태를 변경하는 작업

Query = 시스템의 상태를 조회하는 작업

![이미지](/assets/images/Pasted%20image%2020260220151634.png)

그래서 위와같이 정석적인 패턴은 한 프로젝트 내에서 같은 DB를 바라볼 때 Datasource를 분리해서 각각의 로직을 최적화한다. 보통 읽기에 대한 트래픽이 거의 90프로 이상임

# 향후 주식서비스 개선

stock-customer 서비스에만 AWS Aurora 쓰기 마스터를 주고 나머지 파드에는 읽기전용 슬레이브를 데이터소스로 준다. 그러면 최적화 가능

### 성능 관점 최적화

![이미지](/assets/images/Pasted%20image%2020260220151639.png)

실제로 IO가 일어나는 부분에서 쓰기 부분과 읽기 부분을 분리해서 읽는 부분이 event driven으로 준실시간으로 받으면 좋음. 단, 계정처리와 같이 데이터 일관성이 중요한 경우 생각해볼 필요가 있다.

### AWS Aurora DB Cluster

![이미지](/assets/images/Pasted%20image%2020260220151644.png)

- **Primary DB**
    - read, write 모두 가능
    - 클러스터당 하나씩만 존재
- **Secondary DB**
    - read만 가능
    - 최대 15개까지 지원하고, 하나의 엔드포인트만 애플리케이션에서 연결해도 여러 Secondary DB들로 로드밸런싱을 해준다.
    - Secondary DB들은 별도의 가용영역에 위치하므로, **고가용성을 유지**한다.
    - Primary DB가 죽어도 자동으로 Secondary DB가 승격되는 failover 기능을 가지고 있다.

### 비용 관점 최적화

읽는게 쓰는것보다 싸다.

- **예시 요약 (Aurora Standard 기준, 30일간)**

|**작업 유형**|**1초당 I/O 수**|**예상 비용 (USD)**|
|---|---|---|
|읽기 (Read I/O)|350|$181.44|
|쓰기 (Write I/O)|100|$51.84|

보통은 한 프로젝트 내에서 데이터소스를 분리해버리는데 이 프로젝트는 어쩌다보니 프로젝트 단위로 데이터소스를 분리할 수 있게 되었다,,,, 추후 기회가 된다면 AWS Aurora로 db를 마이그레이션 할 때 위와 같은 패턴을 사용할 예정
## 향후 주식서비스 개선

Aurora 마스터-슬레이브 구조를 활용해서:

- **Write**: Master DB로만 라우팅
- **Read**: Slave(Read Replica)로 라우팅

### 성능 관점 최적화

I/O 분리 및 이벤트 기반 구조로 개선하면:

- 읽기 요청이 많은 주식 시세 조회 → Read Replica로 분산
- 데이터 변경 이벤트 발행 → 이벤트 기반 캐시 갱신
- 쓰기 성능에 영향 없이 읽기 처리량 수평 확장 가능

---

어쩌다 보니 CQRS를 구현하게 된 케이스인데, 이런 식으로 자연스럽게 패턴이 생겨나는 경우가 많은 것 같다. 처음부터 CQRS를 설계 목표로 잡기보다, 읽기/쓰기 요구사항이 달라지는 시점에 분리를 고민하는 게 현실적인 것 같다.
