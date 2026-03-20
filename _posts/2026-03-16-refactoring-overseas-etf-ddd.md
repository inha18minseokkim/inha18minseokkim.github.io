---
title: "overseas-stock, ETF 서비스 DDD 리팩토링 작업기"
date: 2026-03-16
tags:
  - Kotlin
  - Spring
  - 아키텍처
  - DDD
category:
  - 실무경험
---

3월 둘째 주에 overseas-stock-service랑 etf-service 두 개를 DDD 레이어드 아키텍처로 뜯어고쳤음.

커밋 기준으로는 `56dec3c`, `c5157b3`, `1630184`, `c0bbca0`, `12cd6cc`, `791a132`.

---

## 문제 상황

기존 코드에서 컨트롤러가 `*Result` DTO를 그대로 받아쓰고 있었음.

```
controller/
  └── dto/  ← 서비스 Result를 직접 참조
domain/
  └── service/
        └── dto/  ← OverseasStockResult, PriceResult ...
infrastructure/
  └── reader/  ← 엔티티를 그대로 반환
```

JPA 엔티티나 인프라 타입이 애플리케이션 레이어까지 그냥 흘러올라오는 구조였음.
결과적으로:
- 도메인 로직이 서비스 DTO에 뒤섞임
- 레이어 경계가 없어서 테스트 작성이 어려움
- 새 기능 추가할 때 어느 레이어를 건드려야 하는지 헷갈림

---

## 어떻게 고쳤나

### 1. *Result DTO → 도메인 모델로 승격

`OverseasStockResult`, `PriceResult` 같은 이름들이 도메인 언어를 제대로 못 담고 있었음.
이걸 전부 도메인 모델로 바꿨음.

**overseas-stock-service 기준:**

| 삭제된 Result DTO | 대체 도메인 모델 |
|---|---|
| `OverseasStockResult` | `domain/stock/OverseasStock` |
| `SummaryGetResult` | `domain/stock/OverseasStockSummary` |
| `PriceResult` | `domain/price/Price` |
| `FinancialSummaryResult` | `domain/financial/FinancialSummary` |
| `FinancialRatioResult` | `domain/financial/FinancialRatio` |
| `AssetManagementResult` | `domain/asset/AssetManagement` |
| `IndustryResult` | `domain/industry/Industry` |

**etf-service 기준:**

| 삭제된 Result DTO | 대체 도메인 모델 |
|---|---|
| `EtfResult` | `domain/etf/Etf` |
| `PriceResult` | `domain/price/Price` |
| `AssetResult` | `domain/asset/Asset` |
| `DividendResult` | `domain/dividend/Dividend` |
| `HoldingsResult` | `domain/holdings/Holdings` |

미사용 DTO(`LatestPricesGetResult`, `RanksGetResult`)는 그냥 삭제했음.

### 2. JPA 매퍼 계층 추가

도메인 모델이 JPA 엔티티와 분리되면 그 사이를 이어주는 뭔가가 필요함.
`infrastructure/jpa/mapper/` 패키지를 새로 만들어서 엔티티 → 도메인 모델 변환을 거기다 몰아넣었음.

```
infrastructure/jpa/
  entity/
  mapper/   ← 신규
    OverseasStockJpaMapper.kt
    PriceJpaMapper.kt
    FinancialSummaryJpaMapper.kt
    ...
  repository/
```

Reader가 엔티티를 그대로 반환하던 걸 매퍼를 거쳐 도메인 모델로 내보내도록 바꿨음.
덕분에 컬럼명, 타입 변환 같은 인프라 세부사항이 도메인 밖으로 완전히 격리됨.

### 3. YN → Boolean 교체

도메인 모델에서 `YN` 열거형을 쓰는 게 어색했음. 비즈니스 의미는 그냥 Boolean인데.

```kotlin
// Before
val isExternalAudit: YN

// After
val isExternalAudit: Boolean
```

JPA 매퍼에서 `.toBoolean()` 변환을 처리하고, 서비스 코드의 YN 비교 로직은 전부 제거했음.
`OverseasStock`, `AssetManagement`, `Etf`, `Holdings`, `AssetIndustry` 등에 적용됨.

### 4. controller/ + domain/service/ → api/<domain>/ 통합

기존에는 컨트롤러랑 서비스가 각각 다른 패키지에 흩어져 있었음.

```
# Before
controller/AssetManagementController.kt
domain/service/AssetManagementService.kt
domain/service/dto/AssetManagementGetCriteria.kt

# After
api/asset/
  AssetManagementController.kt
  AssetManagementService.kt
  dto/
    AssetManagementGetCriteria.kt
    AssetManagementGetResponse.kt
```

도메인별로 Controller-Service-DTO가 한 곳에 모임.

### 5. criteria/ → dto/ 병합

초기 리팩토링에서 인바운드 조건 클래스를 `criteria/` 패키지에 따로 뒀는데,
막상 써보니 `dto/`랑 분리할 실익이 없었음. 그냥 `dto/`로 합쳤음.

```
api/asset/criteria/AssetGetCriteria.kt  →  api/asset/dto/AssetGetCriteria.kt
```

---

## 리팩토링 후 레이어 구조

```
api/ (Controller, Service, dto/)
  ↓ 도메인 모델 참조
domain/ (순수 모델, 프레임워크 의존 없음)
  ↑ 매핑 처리
infrastructure/ (JPA Entity, Mapper, Reader, Repository)
```

의존 방향 규칙:
- `api/` → `domain/` 참조 허용
- `infrastructure/` → `domain/` 참조 허용
- **`domain/` → `infrastructure/` 참조 금지**
- **`api/` → `infrastructure/` 직접 참조 금지** (Reader를 통해서만)

---

## etf-service 추가 작업: common 패키지 이동

etf-service에서 `etf/service/common/*` 패키지를 `common/*`으로 상위로 이동했음.
`EtfServiceApplication`의 `scanBasePackages`에 `common.*`을 추가해서 컴포넌트 스캔 범위를 명시적으로 잡았음.

---

이번 작업으로 overseas-stock-service, etf-service 두 개가 listed-stock-service와 동일한 패키지 구조를 갖게 됐음.
다음 작업인 Gradle 멀티모듈 전환을 위한 사전 정지 작업이기도 했음.
