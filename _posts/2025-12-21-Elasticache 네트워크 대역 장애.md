---
title: "Elasticache 네트워크 대역 장애"
date: 2025-12-21
tags:
  - AWS
  - 인프라
  - 캐싱
category:
  - 실무경험
---
동기들 모아놓고 점심 청첩장 모임하다가 갑자기 게임 서비스쪽 장애가 나서 호다닥 뛰어올라갔다

### 증상

Redis timeout 뜨고 Health check 실패하면서 서비스에 503 Service unavailable 띄움
  - 돈나무 서비스, 주간 투자왕 서비스 즉 gme-valkey 를 사용하고 있던 온라인 서비스들이 커넥션을 맺지 못함 

## 원인파악


하지만 13시 05분 부터 해당 서비스들이 95% 이상 실패하였는데 정작 트래픽 유입은 평소보다 적었던 상황

## 답변


### Elasticache for Valkey Spec

Instance Type : cache.t4g.medium ( 문제 발생 시점 ) → cache.m5.large
mode : Cluster Mode Disabled
Multi AZ: No
Auto Failover : Yes
이전부터 NetworkBandwidthOutAllowanceExceeded (EC2 네트워크 대역폭 초과) 계속 나고 있었음.
그런데 왜 16일에 하필 점심시간에 장애가 터졌냐?

T타입 인스턴스는 Burstable 인스턴스,
기본(Baseline) 네트워크 대역폭 초과하는  트래픽이 발생하는 경우 크레딧 소진해서 일시적으로 최대 전송 용량까지 확장됨.
  - 트래픽이 Baseline 이하인경우 크레딧이 충전
  - Baseline 초과 트래픽 발생 시 크레딧을 소진하여 Bursting
기존에는 운좋게 안나고 있다가 16일 그 날은 기존 대비 더 오랜 시간동안 지속적으로 트래픽 초과 발생 

NetworkBytesOut > 트래픽 증가하다가 13시 5분(크레딧 소진 시점) 부터 일정 수준 유지됨
  - 그러니깐 초과하던 패킷들 다 드랍된거
  - 그래서 어플리케이션 입장에서는 패킷들 다 드랍되니 Service Unavailable 판단한 듯

### 실제 지표상으로는

12시 반부터 30분 동안 20기가바이트 이상 데이터가 지속적으로 전송,, 13시 5분쯤 까지는 크레딧으로 버티다가 크레딧 소진되었다고 함


## 개선방향


### Infra

- NetworkBandwidthInAllowanceExceeded / workBandwidthOutAllowanceExceeded 이거 모니터링 지표에 추가
- NetworkConntrackAllowanceExceeded > 0 알림 추가
  - 동시에 추적 가능한 네트워크 연결 수 (conntrack) 한도 초과한 경우
  - 초과 시 keep-alive, timeout 설정 및 커넥션 풀 조정
- NetworkPacketsPerSecondAllowanceExceeded > 0 알림 추가
  - 초당 처리 가능 패킷 수 한계 초과 이벤트
- Elasticache 아키텍쳐 변경 검토
  - 지금 현재 비용 이슈로 단일 인스턴스로만 하고 있어서.. 센티넬 형식으로 바꿔?

### Application

- 돈나무 서비스 - 코드 값을 레디스에 저장한 것을 로컬 캐시로 내릴 필요 있음
  - 어쩌다가 이런식으로 레디스를 30분동안 20기가나 찔렀는지 알아봄.
  - 카드 프레임워크 & 오라클 테이블 기반으로 만들어놓은 서비스를 마이그레이션 한 것임
  - 기존 코드 테이블과 비즈니스 데이터를 mybatis 원쿼리로 조인 하던 방식에서 쿼리를 풀려고 하다 보니 코드 테이블 select 하는 로직을 레디스로 넣음
  - 그러다보니 공통 코드 정보를 레디스에서 get 해올 때 한 번의 기능 호출에도 get을 2~3번씩 해버림 
    - > 예전부터 눈여겨봤던 장애요인이었는데 결국 터짐..
  - 로컬캐시를 왜 못 쓴 이유 > 관리자화면에서 코드 테이블 바꿨는데 캐시 갱신주기가 달라버리면 안된다고 해서 레디스 썼다 함
  - 처방)

  - 이거 한번 활용해보라고 함

- 주간 투자왕 서비스 - redis ttl strategy 켜야함
  - 주간 투자왕은 kotlin arrow 사용해서 cache miss or redis timeout 10ms 이상이면 그냥 db 가서 조회 해오는 기능까지는 만들어놨는데 켜놓질 않음.
  - 켜놓지 않은 이유는 Aurora Postgresql를 처음 써보다 보니 부하 주는게 좀 부담스러워서 캐시로 막아놓고 어느정도 추이를 보고 타임아웃 설정을 하려고 했는데 캐시가 먼저 터져버림;;
  - 다음 주 쯤에 timeout 설정하면 캐시 fail에도 서비스가 죽진 않을 예정

 

### 20260209 추가 - 유사 사례 식별

[이구위크 전시 장애 대응기: Redis에는 무슨 일이 있었나](https://techblog.musinsa.com/%EC%9D%B4%EA%B5%AC%EC%9C%84%ED%81%AC-%EC%A0%84%EC%8B%9C-%EC%9E%A5%EC%95%A0-%EB%8C%80%EC%9D%91%EA%B8%B0-redis%EC%97%90%EB%8A%94-%EB%AC%B4%EC%8A%A8-%EC%9D%BC%EC%9D%B4-%EC%9E%88%EC%97%88%EB%82%98-5599562d76b9)

