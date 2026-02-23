---
title: "JPA 복합 키 + JoinTable 응용"
date: 2024-10-22
tags: [미지정]
---
기존에 테이블에 pk가 여러개여야 하는 경우 다음과 같이 테이블을 짰다.
시퀀스 식별자를 하나 둠. id
그리고 실질적으로 유일성 보장되어야 하는 쌍은 UniqueConstraint로 둠
아래와 같다.

```yaml
@Table(name="TB_STK_LI_STCK_DAILY_INFO_M",uniqueConstraints = {@UniqueConstraint(columnNames = {"itms_cd_nbr","base_dttm"})})
@SequenceGenerator(name="sq_stk_li_stck_daily_info_m_01",sequenceName="sq_stk_li_stck_daily_info_m_01",allocationSize = 20)
@Getter
@Setter
public class ListedStockPrice extends TimeStamp implements Serializable {
    @Id
    @Column(name="dat_id")
    @GeneratedValue(strategy = GenerationType.SEQUENCE,generator = "sq_stk_li_stck_daily_info_m_01")
    private Long dataId; //데이터식별자
    @Column(name="base_dttm")
    private LocalDate baseDate; //기준일자
    @Column(name="itms_cd_nbr")
    private String itemCodeNumber; //종목코드번호

```


이렇게 하면 id 식별하고 jparepository 사용할 때 편하니깐 쓰고 있었는데, 몇가지 의문사항이랑 문제
여기서 jparepository 사용할 때 편하다는것은, id값이 long이 아니라 클래스면 로직넣기 귀찮아져서

실질적으로 datId를 가지고 뭔가를 하는 일이 한 번도 없었다(개발 하면서).
보통 jpa에서 id 속성을 가지고  persist merge를 판단하는데 이 기능을 못쓴다
ex) findByBaseDateAndItemCodeNumber로 엔티티를 찾아서 영속성 컨텍스트에 올린 뒤 변경
spring batch 에서 JpaItemWriter 사용 시 pk가 auto generated id인데 실질적 pk에 uniqueconstraint가 걸려있으므로 dup 남. 자동 머지 안됨
그러므로 단점만 부각되는 상황인데..
원인을 생각해보니 간단했다.
> 관계의 주체가 아니므로  id는 필요없다
보통 주식의 가격을 찾을 때는 다음과 같이 찾는다 ex) 삼성전자 주식 일년치 가격
삼성전자 엔티티를 찾는다. findbyId(String) 으로 간단하게 찾음(종목코드번호 005930)

```java
@Slf4j
public class ListedStock extends TimeStamp implements Serializable {
    @Id
    @Column(name="itms_cd_nbr")//종목코드번호
    private String itemCodeNumber;
```

(도메인 기반으로 설계했다) 엔티티의 getpricesBetween 호출

```java
@OneToMany(cascade = CascadeType.PERSIST)
@JoinColumn(name="itms_cd_nbr",referencedColumnName = "itms_cd_nbr"
        ,foreignKey = @ForeignKey(ConstraintMode.NO_CONSTRAINT),insertable = false,updatable = false)
@JsonIgnore
private List<ListedStockPrice> prices;

public List<ListedStockPrice> getPricesBetween(LocalDate from,LocalDate to) {
    return prices.stream().filter(listedStockPrice -> {
        LocalDate baseDate = listedStockPrice.getBaseDate();
        if(from.equals(baseDate) || to.equals(baseDate)) return true;
        if(from.isBefore(baseDate) && to.isAfter(baseDate)) return true;
        return false;
    }).toList();
}
```

그러면 자동으로 joinColumn이 걸리면서 삼성전자 관련된 주가를 싹 가져옴
다른 도메인의 특성은 잘 모르겠지만, 일단 내가 맡고있는 로직들은 이런것이 대부분임. 
즉, 관계의 주체가 아닌 엔티티에 ID값을 강제로 부여하는것은 좋지 못한 선택이었다.

아래와 같이 만들어도 지금과 같은 상황에서는 전혀 문제가 되지 않는다.

```java
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
```

왜냐하면 ID를 빌드하기 위한 편의성이 여기서는 전혀 메리트가 없기 때문..
삼성전자 > 삼성전자 주가 리스트 로 보통 찾지
삼성전자 20241022 주가 > 삼성전자 로 찾지 않는다.
그렇기 때문에 인식에서 종된 관계에 있는 엔티티에 ID를 직접 부여하는것은 적어도 이런 업무에서는옳지 않다. 끝.
