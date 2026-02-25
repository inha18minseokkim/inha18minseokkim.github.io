---
title: Jpa FetchJoin vs BatchSize , 각각의 장단점 주의점
date: 2025-02-03
tags:
  - Spring
  - JPA
category: 기술
---

```java
@Entity
@AllArgsConstructor
@NoArgsConstructor
@Builder
@Table(name="TB_STK_LI_STCK_M")
@Getter
@Setter
@Slf4j
public class ListedStock extends TimeStamp implements Serializable {
    @Id
    @Column(name="itms_cd_nbr")
    private String itemCodeNumber;

......

		@OneToMany(cascade = CascadeType.PERSIST)
		@JoinColumn(name="itms_cd_nbr",referencedColumnName = "itms_cd_nbr"
		        ,foreignKey = @ForeignKey(ConstraintMode.NO_CONSTRAINT),insertable = false,updatable = false)
		@JsonIgnore
		private List<ListedStockPrice> prices;
```


```java
@Builder
@Entity
@AllArgsConstructor
@NoArgsConstructor
@Table(name="TB_STK_LI_STCK_DAILY_INFO_M")
@Getter
@Setter
@IdClass(ListedStockPriceId.class)
public class ListedStockPrice extends TimeStamp implements Serializable {

    @Column(name="base_dttm")
    @Id
    private LocalDate baseDate; //기준일자
    @Column(name="itms_cd_nbr")
    @Id
    private String itemCodeNumber; //종목코드번호
    @Column(name="stpr_amt")
    private Long openPrice;//시가금액
    @Column(name="hipr_amt")
    private Long highPrice; //고가금액
```

이런식으로 OneToMany 관계를 설정하는경우 Fetch Join을 주로 사용하게 된다.
fetch를 안하는 경우 select가 1+N 날라감. ex) TB_STK_LI_STCK_M 한번, TB_STK_LI_STCK_M의 itms_cd_nbr 컬럼으로 TB_STK_LI_STCK_DAILY_INFO_M에 N번
하지만 이렇게되면 주식데이이터 1년치를 가져오는 경우 큰일남.
 호출 한 번에 366번 SELECT

# Jpa 연관관계 select 시 N+1 조회 문제를 해결하는 방법

fetch Join을 사용한다(기본)
@BatchSize를 이용한다


## fetch Join의 문제점

한번에 겁나 많이 가져와서 OOM 날 수도
100% 정확한건 아니지만, 비슷한 맥락의 장애를 낸적있음 

~ToOne은 사용가능, ~ToMany는 페이징 불가때문에 사용이 좀 제한됨
페이징 처리가 안되는 이유 : 
1 : 1000 이라 100개씩 끊어서 가져오고 싶음 → 페이징으로 100개 가져옴 → 리스트에 100개만 있음 → persist 실행 시 900개 날아감
그러므로 가능하다면 ~ToOne 을 fetch join 하는것이 낫다.

## @BatchSize 설정

그러므로 100개만 가져오는건 안되고 1000개 다 가져와야 한다.
select 1000건을 날리고싶진 않으니 100개짜리 10개만 날리는 방법은 **hibernate.default_batch_fetch_size: 100을 설정하거나 ~ToMany 엔티티에 @BatchSize를 설정하면 된다.**
그러면 천개를 가져오는 대신

```java
    from
        product product0_
    where
        product0_.id in (
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
        )
```

이런식으로 in절로 찾아오게 된다.
그러고 나면 주의할 점 내지 염두할 점이 두 가지 정도 생김.
in절의 수에 따른 쿼리플랜 캐싱 문제
옵티마이저

1번의 경우 다시 생각해보니 batchsize가 정해져있는 환경에서는 그렇게 큰 문제가 되진 않을 것 같음. 
실제로 쿼리 캐싱 문제가 되려면 해당 로직을 타는 리스트의 길이가 상당히 가변적이어야 함 ex) 주문 아이템의 목록이 1개인 사람부터 1000개인 사람이 모두 존재하고, 모두 한번씩 batch fetchjoin을 사용하는 로직을 건들 경우 난다.
하지만 서비스 환경에 따라 어느정도 알아서 나쁠건 없는것같아 그냥 적음.

## **덧) JDBC preparedstatement의 캐싱 방식**

JDBC의 preparedstatement의 캐싱 방식이 있음
preparedstatement는 in절이 들어가는 select 쿼리에 대해 각 경우를 모두 캐싱한다.
`# 데이터가 1개 들어올 때 : where xxx in (?)
# 데이터가 2개 들어올 때 : where xxx in (?,?)
# 데이터가 n개 들어올 때 : where xxx in (?,?, ...)`
우리가 SELECT 절을 호출할 때 Java에서 “SELECT * FROM TABLE WHERE COL = “ + “값;” 이런식으로 호출안하고  “SELECT * FROM TABLE WHERE COL = ?;“ 을 준비한다음에 변수에 입력한다.
이렇게 하지 않고 전자 처럼 하면 모든 변수에 대한 쿼리 플랜이 캐싱됨. 

![이미지](/assets/images/Pasted%20image%2020260224083207.png)



그러니깐 JPA 에서 fetch join 시 where  in 절에서 in ( ,, ) 의 리스트 가짓수가 많아지면 쿼리플랜 캐싱에 부담이 될 수 있음!!
물론 배치사이즈를 사용하면 in list 쿼리 캐싱을 최적화함
ex) in (?) / in(?,?) / in(?,?,?) 이런식으로 100개까지 모두 캐싱하지 않고
1,2,3,4,5,6,7,8,9,10,12,25,50,100개의 케이스만 캐싱하는식으로

2번의 경우 각 dbms, 적재된 데이터 수, 옵티마이저 환경에 따라 다를 수 있지만  batchsize 를 너무 크게 주면 db에 부하가 걸릴 것임. 




[`JPA N+1튜닝과정에서 선언한 배치 사이즈와 다르게 쿼리 분할 되어 수행되는 이유`](https://42class.com/dev/jpa-batchsize/)
[`Spring Data JPA에서 FetchJoin 주의 사항`](https://velog.io/@junsu1222/Spring-Data-JPA%EC%97%90%EC%84%9C-FetchJoin-%EC%A3%BC%EC%9D%98-%EC%82%AC%ED%95%AD)
[JPA hibernate Query Plan Cache로 인한 OutOfMemory 해결](https://velog.io/@recordsbeat/JPA-hibernate-Plan-Cache%EB%A1%9C-%EC%9D%B8%ED%95%9C-OutOfMemory-%ED%95%B4%EA%B2%B0)
