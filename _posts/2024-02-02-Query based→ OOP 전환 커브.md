---
title: "Query based→ OOP 전환 커브"
date: 2024-02-02
tags: [미지정]
category: 기타
---

```sql
select #distinct a.region_info_id,c.description,d.description,e.description
    a.base_product_id, b.item_name,
    e.id,e.description
    ,avg(a.price),count(1)
from
    original_price_info a
    ,base_product b
    ,user_code c
    ,user_code d
    ,user_group_code e
where
    a.base_product_id = b.id
    and a.region_info_id = c.id
    and d.code_detail_name = c.id
    and d.user_group_code_id = e.id
    and a.base_date between '20230927' and '20230927'
    and e.code_detail_name = 'KbankRegionCode'
group by
    a.base_product_id, b.item_name,
    e.id,e.description;
select
            a.base_product_id,
            e.id,
            count(1),
            avg(a.price)
        from
            original_price_info a
        join
            base_product b
                on b.id=a.base_product_id
        join
            user_code c
                on c.id=a.region_info_id, user_group_code e, user_code d
        where
            e.code_detail_name='KbankRegionCode'
            and (
                a.base_date between '20230927' and '20230927'
                and (
                    c.id=cast(d.code_detail_name as signed)
                    and e.id=d.user_group_code_id
                )
            )
        group by
            b.id,
            e.id
;
select distinct region_info_id from original_price_info;
select base_product_id,region_info_id,count(1) from original_price_info where base_date = '20230927'
group by base_product_id,region_info_id
```


### 조건

프론트엔드 소스는 바뀌지 않음(호출하는 in, out은 변하지 않음)
백엔드 로직은 바꿀 수 있음
DB 스키마 어느정도 수정


### QueryDSL vs Native Query

입력객체

```java
@Table(uniqueConstraints = {@UniqueConstraint(columnNames = {"categoryCode","itemCode","kindCode","classCode","gradeCode"})})
public class BaseProduct {
    @Id
    @GeneratedValue
    private Long id;
    @Column(length = 3)
    private String categoryCode;    //pd_ctgr_cd
    @Column(length= 4)
    private String itemCode;            //pd_lsar_cd
    @Column(length= 3)
    private String kindCode;            //pd_knd_cd
    @Column(length=2)
    private String classCode;           //whls_rtl_dcd
    @Column(length=2)
    private String gradeCode;            //pd_grade_cd
    private String unitName;            //snog_unit_nm
    private Float unitValue;            //snog_unit_val
    private Boolean isAvailable;            //사용여부
    private String categoryName;
    private String itemName;
    private String kindName;
    private String gradeName;
    @OneToMany(mappedBy = "baseProduct",fetch = FetchType.LAZY)
    @ToString.Exclude
    private List<InnerProduct> innerProducts;
}
```


```java
@Entity
@Data
@Builder
@AllArgsConstructor
@NoArgsConstructor
public class UserGroupCode {
    @Id
    @GeneratedValue
    private Long id;
    private String codeDetailName;
    private String description;
    private Long orderSequence;
    private Boolean useInfo;
    @OneToMany
    private List<UserCode> userCodes;
}
```

input

```java
public class FindPriceListByGroupRegionCodeIn {
    private String baseDate;
    private BaseProduct targetProduct;
    private BaseRange rangeForLength;
    private BaseRange rangeForTag;
    private UserGroupCode regionGroup;
}
```


```java
public List<FindPriceListByGroupRegionCodeOut> findPriceListByGroupRegionCode(FindPriceListByGroupRegionCodeIn in){
    JPAQueryFactory query = new JPAQueryFactory(entityManager);
    QProcessedPriceInfo processedPriceInfo = QProcessedPriceInfo.processedPriceInfo;
    QUserGroupCode userGroupCode = QUserGroupCode.userGroupCode;
    QUserCode userCode1 = new QUserCode("a");
    QUserCode userCode2 = new QUserCode("b");
    QBaseProduct baseProduct = QBaseProduct.baseProduct;
    String startDate = LocalDate.parse(in.getBaseDate(), DateTimeFormatter.ofPattern("yyyyMMdd"))
            .minusDays(in.getRangeForLength().getGapDay()-1).format(DateTimeFormatter.ofPattern("yyyyMMdd"));

    List<Tuple> results = query.select(
            processedPriceInfo.baseDate,
            processedPriceInfo.price.avg()

            )
            .from(processedPriceInfo, userGroupCode, userCode2)
            .innerJoin(processedPriceInfo.baseProduct, baseProduct)
            .innerJoin(processedPriceInfo.regionInfo, userCode1)
            .where(
                    processedPriceInfo.baseRange.eq(in.getRangeForTag())
                            .and(processedPriceInfo.baseDate.between(startDate, in.getBaseDate()))
                            .and(userGroupCode.id.eq(in.getRegionGroup().getId()))
                            .and(userCode1.id.eq(userCode2.codeDetailName.castToNum(Long.class)))
                            .and(userGroupCode.id.eq(userCode2.userGroupCode.id))
            ).groupBy(
                    processedPriceInfo.baseDate
            )
            .fetch();

    return results.stream().map((element) -> FindPriceListByGroupRegionCodeOut.builder()
            .baseDate(in.getBaseDate())
            .price(element.get(processedPriceInfo.price.avg()).longValue())
            .regionGroupInfo(in.getRegionGroup())
            .baseProduct(in.getTargetProduct())
            .baseRange(in.getRangeForLength())
            .build()
    ).collect(Collectors.toList());
}
```

실제 실행 Native SQL

```sql
select
    a.base_date,
    avg(a.price)
from
    processed_price_info a
join
    base_product b
        on b.id=a.base_product_id
join
    user_code c
        on c.id=a.region_info_id, user_group_code d, user_code e
where
    a.base_range=?
    and a.base_date between ? and ?
    and d.id=?
    and c.id=cast(e.code_detail_name as signed)
    and d.id=e.user_group_code_id
group by
    a.base_date;
```


JPA + QueryDSL
  - OOP → ER-Relation 매핑의 시간을 줄여줌
  - Compile Time에 오류 탐지 가능
  - 불필요한 노가다성 작업 필요없음
단점
  - 복잡한 쿼리의 경우 상당한 공부 필요
    - 익숙하지 않다면 DSL로 한번 작성하고 기존에 익숙한 Native 쿼리로 작성 후 둘을 비교하면 일을 두 번 하는것.
  - 현재 행 Legacy에 적용하기 사실상 불가능(또는 가능하지만 굳이 기존건 전환하는걸 이렇게 해야하나 싶음)

대표적인 예시

```java
@GetMapping("/getProductDetail/{targetProductId}/{regionGroupId}")
    public GetProductDetailResponse getProductDetail(@PathVariable("targetProductId") BaseProduct baseProduct,
                                                     @PathVariable("regionGroupId") UserGroupCode userGroupCode,
                                                     @Validated MemberInfo memberInfo,
                                                 GetProductDetailRequest in
                                          ){

  log.info("사용자 처리 : {}",memberInfo);
  //여기가 맞나? 사용자 없으면 저장 다른 서비스로 분리해야할듯
  Optional<MemberInfo> memberInfoOp = memberInfoRepository.findMemberInfoByCustomerIdAndBusinessCode(memberInfo.getCustomerId(), memberInfo.getBusinessCode());
  if(memberInfoOp.isEmpty())
      memberInfoOp = Optional.of(memberInfoRepository.save(
              MemberInfo.builder().customerId(memberInfo.getCustomerId()).businessCode(memberInfo.getBusinessCode()).isAgree(false).build())
      );
  memberInfo = memberInfoOp.get();
  //이런 코드가 있는 이유 : asis의 요구사항이 TOBE Spring JPA 사상과 맞지 않다

  GetProductPriceOut productPrice = productDetailService.getProductPrice(
          GetProductPriceIn.builder()
                  .baseDate(in.getBaseDate())
                  .targetProduct(baseProduct)
                  .rangeForLength(in.getRangeForLength())
                  .rangeForTag(BaseRange.DAY)
                  .regionGroup(userGroupCode)
                  .memberInfo(memberInfo)
                  .build()
  );
  return mapper.from(productPrice);
}
```

Spring JPA의 의도대로라면
@PathVariable("targetProductId") BaseProduct baseProduct,
@PathVariable("regionGroupId") UserGroupCode userGroupCode,
와 같이 key를 가지고 select 후 객체 Entity로 캐싱해야하지만

```java
@Table(uniqueConstraints = @UniqueConstraint(name="MemberInfoUnique",columnNames = {"customerId","businessCode"}))
public class MemberInfo {
    @Id
    @GeneratedValue
    private Long id;
    @Column(length = 15)
    private String customerId;
    private String businessCode;
    private Boolean isAgree;
}
```

이런식으로 기존 PK를 고수해야 하는 상황이면 

```java
  Optional<MemberInfo> memberInfoOp = memberInfoRepository.findMemberInfoByCustomerIdAndBusinessCode(memberInfo.getCustomerId(), memberInfo.getBusinessCode());
  if(memberInfoOp.isEmpty())
      memberInfoOp = Optional.of(memberInfoRepository.save(
              MemberInfo.builder().customerId(memberInfo.getCustomerId()).businessCode(memberInfo.getBusinessCode()).isAgree(false).build())
      );
  memberInfo = memberInfoOp.get();
```

수동으로 select 후 메모리에 올려서 JPA에 활용해야 한다.

물론 기존 프로젝트에서도 현실적으로는 findById를 써야겠지만(실제로 저렇게 써도 뒷단에서는 그렇게 돌긴함) 약간 아쉬운감이 있음

이는 OOP → ER-Relation 매핑의 비용을 줄여준다는 내용과 앞뒤가 다름.

DB의 경우 백엔드 개발자의 수고로 매핑을 성공할 수 있겠지만,
채널의 호출 로직이 바뀌지 않으면(공모주의 경우 기존 소스 바꾸지 않고 백엔드만 바꿈)
결국 어디선가 OOP → ER로 바꾸는 일을 두 번 해야함

(다양한 개발 방법론을 위해 JPA를 적극 도입한다는 전제 하에) 이렇게 진행한다면 JPA + Mybatis 병존이 아닌 그냥 계속 쿼리 기반으로 개발할 것 같다. 협의 설계 모두 기존방식이면.
