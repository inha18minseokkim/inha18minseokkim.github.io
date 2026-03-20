---
title: "MDD + MVC에서 DDD + Hexagonal로 — 과감하게 리팩토링한 이유"
date: 2026-03-20
tags:
  - Kotlin
  - Spring
  - 아키텍처
  - DDD
category:
  - 기술
---

이번 리팩토링은 단순한 패키지 구조 정리가 아님.

팀이(사실상 혼자지만) **어떤 방식으로 서비스를 만들고, 누구와 어떤 언어로 커뮤니케이션하는지**에 대한 고민의 결과임.

결론부터 말하면, 기존의 **Model Driven Design(MDD) + MVC** 구조를 **Domain Driven Design(DDD) + Hexagonal Architecture** 로 전면 전환했음. 이 리팩토링으로 모든 서비스의 레이어 구조를 통일했고, 다음 단계인 **Gradle 멀티모듈 도입**의 기반도 마련했음.

---

## ASIS: MDD + MVC 구조가 가져온 문제

기존 코드는 전형적인 **테이블 주도(Table-Driven)** 설계였음.
JPA 엔티티가 컨트롤러까지 흘러다니고, 서비스 계층은 엔티티를 감싸는 `*Result` DTO를 생산하는 역할에 그쳤음.

```
Controller
  └── Service
        └── Repository
              └── JPA Entity  ← 사실상 모든 레이어의 핵심 타입
```

이 구조 자체가 나쁜 건 아님. 오히려 특정 상황에서는 매우 효율적이기도 함.

> 같은 회사 다른 팀은 여전히 MDD + MVC를 표준으로 쓰고 있고, 이는 합리적인 선택임.
> 그 팀은 **계정계 레거시 시스템**과 밀접하게 협업하는데,
> 계정계는 오랜 시간 테이블 스키마 중심으로 설계되어 있고, 해당 팀도 테이블 구조 기준으로 커뮤니케이션함.
> 데이터 모델이 곧 업무 언어인 환경에서는 MDD가 오히려 자연스러움.

하지만 우리 팀의 상황은 달랐음.

---

## 우리 팀은 왜 달랐나

우리 서비스는 증권 도메인을 다루는 신규 서비스임.
기획자, 사업 담당자와 나누는 대화의 언어는 테이블이 아닌 **도메인**임.

- "공모주 청약 일정을 보여줘"
- "관심 종목을 추가하면 푸시를 받을 수 있어야 해"
- "비상장 주식의 조회 랭킹을 집계해줘"

이 언어들은 어떤 테이블에서 SELECT 하는지와 전혀 무관함.
기획 문서, 슬랙 메시지, 데일리 스탠드업 모두 **도메인 언어**로 이루어짐.

MDD 구조에서는 이 간극을 계속 번역해야 했음.
비즈니스 언어를 코드로 옮기는 과정에서 도메인 개념이 흐릿해졌고,
새 기능을 추가할 때마다 "이게 어느 테이블 담당이지?"를 먼저 묻게 됐음.

---

## TOBE: DDD + Hexagonal Architecture

### 도메인 모델이 중심이 된다

리팩토링 후의 핵심 원칙은 하나임.
**"도메인 모델이 어떤 레이어에도 의존하지 않는다."**

```
api/          ← HTTP 입출력, 서비스 조합
  └── domain/ ← 순수 비즈니스 모델 (JPA, Spring 의존 없음)
       ↑
infrastructure/ ← JPA Entity, Mapper, Repository, HTTP Client
```

`domain/` 패키지의 클래스들은 Spring 어노테이션도, JPA 어노테이션도 없음.
비즈니스 규칙만 담긴 순수한 Kotlin 클래스임.
덕분에 도메인 로직은 인프라 교체와 무관하게 테스트하고 검증할 수 있음.

### 기존 *Result DTO의 소멸

MDD 구조에서는 리포지터리가 반환하는 값을 감싸기 위해 `*Result` DTO가 필요했음.

```kotlin
// Before: Result DTO가 레이어 사이를 떠다님
class OverseasStockResult(val symbolId: String, val name: String, ...)
class PriceResult(val close: BigDecimal, ...)
```

이것들을 모두 **도메인 모델로 승격**시켰음.

```kotlin
// After: 도메인 모델이 비즈니스 개념을 직접 표현
class OverseasStock(val symbolId: String, val name: String, ...)
class Price(val close: BigDecimal, ...)
```

클래스 이름 자체가 비즈니스 언어가 됨.
새 팀원이 코드를 열었을 때 "이게 어떤 데이터인지" 바로 알 수 있음.

### JPA 매퍼 계층의 도입

도메인 모델이 JPA 엔티티와 분리되면서, 그 사이를 잇는 **Mapper 계층**을 `infrastructure/jpa/mapper/`에 명시적으로 만들었음.

```
infrastructure/
  jpa/
    entity/   ← DB 구조에 맞춘 JPA 엔티티
    mapper/   ← Entity → 도메인 모델 변환 책임
    repository/
```

인프라 세부사항(컬럼명, 타입 변환)이 도메인 밖으로 완전히 격리됨.

### api/\<domain\>/ 구조로 레이어 통일

기존에는 `controller/`, `domain/service/`, `domain/dto/`가 분산되어 있었음.
이를 도메인별 `api/<domain>/` 구조로 통일했음.

```
api/
  stock/
    OverseasStockController.kt
    OverseasStockService.kt
    dto/
      OverseasStockGetCriteria.kt   ← 인바운드 조건
      OverseasStockGetResponse.kt   ← 컨트롤러 응답
  price/
  rank/
  financial/
  ...
```

도메인별로 Controller-Service-DTO가 한 곳에 모임.
새 도메인이 추가될 때 어디에 뭘 만들어야 하는지 고민할 필요가 없음.

---

## 레이어 통일 완료

이번 리팩토링으로 아래 6개 서비스의 내부 패키지 구조가 전부 동일해졌음.

| 서비스 | 이전 구조 | 이후 구조 |
|---|---|---|
| etf-service | controller/ + domain/ | api/\<domain\>/ + domain/ |
| overseas-stock-service | controller/ + domain/service/dto/ | api/\<domain\>/ + domain/ |
| listed-stock-service | (기준 구조) | 변경 없음 |
| stock-customer-service | api/\<domain\>/ (MVC) | RESTful URI + 컨텍스트 기반 customerId |
| ipo-service | — | 변경 없음 |
| unlisted-stock-service | — | 변경 없음 |

**모든 서비스가 같은 언어로 코드를 작성하게 됐음.**
새 서비스를 추가할 때도, 다른 서비스 코드를 읽을 때도 동일한 사고방식으로 접근 가능.

---

## 다음 단계: Gradle 멀티모듈 (`feat-multi-module`)

레이어를 통일했으니 이제 물리적 구조도 통합할 준비가 됐음.

### 왜 하나의 레포지터리로 합치나

우리 팀은 **도메인 경계는 명확하지만, 담당자는 적음.**
서비스마다 별도 레포지터리를 유지하면 다음 비용이 따라옴.

- 공통 코드(컨텍스트, 필터, 유틸, 예외 처리)가 서비스마다 복제됨
- Spring Boot 버전, Kotlin 버전이 서비스마다 제각각
- 공통 코드 한 줄 수정에 6개 서비스 PR 생성 필요

그렇다고 하나의 모노리식 서비스로 합치면 장애가 전파됨.
도메인별로 배포 단위는 분리해야 함.

**Gradle 멀티모듈**은 이 두 가지를 동시에 해결함.

### 모듈 구조

```
stock-service/                    ← 루트 프로젝트
├── stock-common/                 ← 공통 코드 (모든 도메인 모듈이 의존)
├── etf/                          ← ETF 도메인 모듈
├── ipo/                          ← 공모주 도메인 모듈
├── listed-stock/                 ← 국내주식 도메인 모듈
├── overseas-stock/               ← 해외주식 도메인 모듈
├── stock-customer/               ← 고객(관심종목/Hit/Push) 도메인 모듈
├── unlisted-stock/               ← 비상장주식 도메인 모듈
└── stock-app/                    ← 실행 모듈 (SpringBootApplication + application.yml)
```

의존 관계는 단순함.

```
stock-app → [모든 도메인 모듈]
각 도메인 모듈 → stock-common
도메인 모듈 간 직접 의존: 금지
```

도메인 모듈끼리 직접 참조하지 않음.
공유해야 하는 타입은 반드시 `stock-common`을 거침.
이 규칙 하나가 컴파일 타임에 **장애 전파 범위**를 물리적으로 차단함.

### stock-common 설계 원칙

`stock-common`에는 **순수한 코드만** 들어감.

```
stock-common/
  code/       Nation, Securities, YN, ErrorCode, OrderCode ... 열거형
  context/    CommonContext, CommonContextHolder
  exception/  GlobalExceptionHandler, ErrorResponse
  filter/     CommonContextFilter, LoggingFilter
  log/        LoggerFactory
  util/       DateUtils, PriceUtils, ConvertUtils, MarketCloseUtil
```

**Spring 설정 클래스(Config)는 stock-common에 없음.**
CacheConfig, JpaConfig, RedisConfig 같은 설정은 도메인마다 다르기 때문에 각 도메인 모듈 안의 `config/` 패키지에서 직접 관리함.

**CacheType도 stock-common에 없음.**
캐시 항목은 도메인마다 다름. ETF의 캐시와 공모주의 캐시를 하나의 enum에 우겨넣으면 한 모듈의 변경이 다른 모듈에 영향을 줌. 각 도메인 모듈이 자신만의 `code/CacheType`을 소유함.

이 원칙 덕분에 `stock-common`은 **외부 프레임워크에 가능한 한 구애받지 않는** 라이브러리가 됨.

---

## 정리

| | ASIS | TOBE |
|---|---|---|
| **설계 방식** | MDD (테이블/모델 중심) | DDD (도메인 개념 중심) |
| **패키지 구조** | controller/ + domain/service/dto/ | api/\<domain\>/ + domain/ + infrastructure/ |
| **인프라 격리** | 엔티티가 서비스까지 노출 | JPA 매퍼로 격리, 도메인은 순수 |
| **커뮤니케이션 언어** | 테이블/컬럼명 | 비즈니스 도메인 용어 |
| **물리 구조** | 6개 독립 프로젝트 | (예정) 단일 멀티모듈 프로젝트 |
| **공통 코드** | 6벌 복제 | (예정) stock-common 단일 관리 |

DDD와 Hexagonal 아키텍처가 항상 옳은 선택은 아님.
테이블 기반 레거시와 깊이 통합해야 하는 환경에서는 MDD + MVC가 더 자연스러울 수 있음.

우리가 이 구조를 선택한 이유는 단 하나임.
**코드에서 대화하는 언어가 도메인이기 때문.**
코드와 비즈니스가 같은 언어를 쓸 때, 설계는 자연스럽게 따라옴.
