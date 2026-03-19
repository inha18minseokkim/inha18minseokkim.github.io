---
title: EDB 성능 튜닝 - 식품물가 아키텍처 개선기
date: 2024-02-01
tags:
  - DB
  - Redis
  - 성능최적화
  - 케이뱅크
category:
  - 실무경험
  - 생활시세
---

식품물가 서비스의 DB 의존도를 낮추고 Java 애플리케이션으로 책임을 분산시킨 아키텍처 개선 과정을 정리한다.

---

## AS-IS: DB가 다 해먹는 구조

기존 식품물가 시스템은 **DB 올인원 스타일**이었다.

| 항목 | 설명 |
|------|------|
| 상품 매핑 | KAMIS 상품코드 + 지역코드 JOIN → 케이뱅크 노출지역으로 GROUP BY |
| 통계 처리 | 일간/주간/월간/반기/연간 평균을 **모두 DB에서 계산**하여 통계 테이블에 적재 |
| 상품 관계 | 내부상품코드 ↔ KAMIS 상품코드 매핑도 DB JOIN으로 처리 |

예를 들어 "배추"라는 내부상품 하나에 봄배추, 고랭지배추, 가을배추, 월동배추가 매핑되어 있는데, 이 모든 연산을 DB가 혼자 끙끙대며 처리하고 있었다.

---

## TO-BE: Java에게 일 좀 시키자

개선된 구조에서는 **DB의 짐을 Java가 나눠 든다**.

| 항목 | 변경 내용 |
|------|----------|
| DB 역할 | 일간 평균만 통계 테이블에 적재 (여기까지만!) |
| Java 역할 | 365일치 데이터를 가져와서 주간/월간/반기/연간 통계 직접 계산 |
| 관계 처리 | 내부상품코드 : KAMIS 상품 = 1 : N 관계를 Java에서 GROUP BY + AVG |

---

## 트레이드오프: Connection Pool vs Cache

Entity 기반으로 객체 연관관계를 다루다 보니 **DB Connection Pool 호출이 잦아졌다**.

하지만 걱정 마시라. **Persistent Context + Redis Cache** 콤보로 성능을 챙길 예정이다.

---

## 현실의 벽: 프론트가 안 바뀐다

코드를 보면 일/주/월/반년/연간 데이터를 **한 방에 다 뿌려준다**.

> "API 분리해서 호출하면 안 돼요?"
> "프론트 로직 못 바꿔요."
> "...네."

어쩔 수 없이 한 번에 조회해야 하는 상황. SQL 실행 계획 분석 + Redis Cache가 답이다.

---

## 문제의 쿼리

```sql
SELECT
    ip1_0.id,
    ip1_0.additional_description,
    ip1_0.inner_category_id,
    ip1_0.is_available,
    ip1_0.is_main_material,
    ip1_0.is_seasonal,
    ip1_0.order_sequence,
    ip1_0.product_name,
    ip1_0.season_end_date,
    ip1_0.season_start_date,
    ppi1_0.base_date,
    AVG(ppi1_0.price)
FROM
    user_group_code ugc1_0,
    user_code uc1_0,
    inner_product ip1_0
JOIN
    base_product bp1_0 ON bp1_0.inner_product_id = ip1_0.id
LEFT JOIN
    processed_price_info ppi1_0 ON ppi1_0.base_product_id = bp1_0.id
WHERE
    ip1_0.is_available = true
    AND (ppi1_0.base_date BETWEEN '20240101' AND '20240120' OR ppi1_0.base_date IS NULL)
    AND (ppi1_0.base_range = 'DAY' OR ppi1_0.base_range IS NULL)
    AND (ppi1_0.region_info_id = uc1_0.code_detail_name OR ppi1_0.region_info_id IS NULL)
    AND ugc1_0.id = 'FDPREGN1101'
    AND uc1_0.user_group_code_id = 'FDPREGN1101'
GROUP BY
    ip1_0.id, ppi1_0.base_date
```

![쿼리 실행 계획](/assets/images/Pasted%20image%2020260228171243_5de92d08.png)

---

## 성능 개선 전략

| 전략 | 설명 |
|------|------|
| 인덱스 튜닝 | 기존 식품물가와 유사하게 인덱스 구성 후 실행 계획 분석 |
| Redis Cache | 자주 조회되는 데이터는 캐싱으로 DB 부하 감소 |
| 쿼리 단순화 | API별 쿼리 분리 대신 최대 2개 쿼리로 통합 |

> 로컬 환경은 데이터가 적어서 일단 캐싱만으로도 충분하다. 운영은... 두고 보자.