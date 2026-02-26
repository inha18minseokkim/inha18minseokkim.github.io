---
title: "JPA: Query Based vs Domain Based / @NotFound Ignore vs Exception"
date: 2024-04-29
tags:
  - JPA
  - QueryDSL
category:
  - 기술
---

리팩토링 수행 간 문제 인식. 아마 마이그레이션을 할 때 한번 씩 생길 수 있을 문제인것같음.

## 예시 도메인 Entity

고객 Entity

```javascript
@Getter
@Setter
@Entity
@Table(name = "TB_STK_MBRS_INFO")
@NoArgsConstructor
@SuperBuilder
public class Member extends TimeStamp {
    @Id
    @Column(name = "cust_id")
    private String customerId;
    @Column(name="efctv_yn")
    @Enumerated(EnumType.STRING)
    private YNCode effectiveYn;
    @OneToMany(cascade = CascadeType.PERSIST)
    @JoinColumn(name="cust_id",referencedColumnName = "cust_id"
            ,foreignKey = @ForeignKey(ConstraintMode.NO_CONSTRAINT))
    @JsonIgnore
    private List<InterestStock> interestStocks;

    public static Member createNewMember(String customerId){
        return Member.builder().customerId(customerId)
                .effectiveYn(YNCode.Y)
                .interestStocks(new ArrayList<>())
                .build();
    }
    public List<UnListedStock> getCurrentInterestStocks() {
        return interestStocks.stream()
                .filter(interestStock -> interestStock.getInterestYn() == YNCode.Y)
                .filter(interestStock -> interestStock.getUnListedStock().isAvailable())
                .map(InterestStock::getUnListedStock)
                .toList();
    }
    public boolean isInterest(String itemCodeNumber){
        return interestStocks.stream()
                .filter(InterestStock::isInterest)
                .map(InterestStock::getUnListedStock)
                .filter(UnListedStock::isAvailable)
                .anyMatch(unListedStock -> unListedStock.getItemCodeNumber().equals(itemCodeNumber));
    }
    public InterestStock setInterestStock(UnListedStock unListedStock,YNCode isInterest){
        Optional<InterestStock> result = interestStocks.stream().filter(element -> element.getUnListedStock().equals(unListedStock)).findAny();
        if(result.isPresent()){
            result.get().setInterestYn(isInterest);
            return result.get();
        }
        else {
            InterestStock newInterestStock = InterestStock.builder().member(this)
                    .unListedStock(unListedStock)
                    .interestYn(isInterest)
                    .lineUpSequence(9999L)
                    .build();
            interestStocks.add(newInterestStock);
            return newInterestStock;
        }
    }
}

```

비상장주식 Entity

```javascript
@Entity
@Getter
@Setter
@SuperBuilder
@AllArgsConstructor
@NoArgsConstructor
@Table(name="TB_STK_NOLI_STCK_M")
public class UnListedStock extends TimeStamp {
    @Id
    @Column(name = "itms_cd_nbr")
    private String itemCodeNumber;
    @Column(name = "stck_kor_nm")
    private String stockKoreanName;
    @Column(name = "ovcn_ds_cd")
    @Enumerated(EnumType.STRING)
    private OvcnInfo ovcnDistinctionCode;
    @Column(name = "use_yn")
    @Enumerated(EnumType.STRING)
    private YNCode useYn;
    @Column(name="hmpg_url")//원링크url
    private String homePageUrl;

    public boolean isAvailable() {
        return useYn.equals(YNCode.Y);
    }

    @OneToMany
    @JoinColumn(name="itms_cd_nbr", referencedColumnName = "itms_cd_nbr",
        foreignKey = @ForeignKey(ConstraintMode.NO_CONSTRAINT))
    @JsonIgnore
    private List<InterestStock> interestStocks;
    
    public List<Member> getCurrentInterestMembers(){
        return interestStocks.stream().filter(interestStock -> interestStock.isInterest())
                .map(InterestStock::getMember).toList();
    }
    public InterestStock setInterestStock(Member member, YNCode isInterest){
        Optional<InterestStock> result = interestStocks.stream().filter(interestStock -> interestStock.getMember().equals(member)).findAny();
        if(result.isPresent()){
            result.get().setInterestYn(isInterest);
            return result.get();
        } else{
            InterestStock newInterestStock = InterestStock.builder().member(member)
                    .unListedStock(this)
                    .interestYn(isInterest)
                    .lineUpSequence(9999L)
                    .build();
            interestStocks.add(newInterestStock);
            return newInterestStock;
        }
    }
}

```

관심주식 Entity

```javascript
@Entity
@Getter
@Setter
@Builder
@AllArgsConstructor
@NoArgsConstructor
@Table(name = "TB_STK_INTE_NOLI_STCK",uniqueConstraints = {@UniqueConstraint(name= "IX_STK_INTE_NOLI_STCK_01" ,columnNames = {"cust_id","itms_cd_nbr"})})
@SequenceGenerator(name = "sq_stk_inte_noli_stck_01", sequenceName = "sq_stk_inte_noli_stck_01", allocationSize = 1)
public class InterestStock extends TimeStamp {
    @Id
    @GeneratedValue(strategy = GenerationType.SEQUENCE, generator = "sq_stk_inte_noli_stck_01")
    @Column(name="dat_id")
    private Long dataId;
    @ManyToOne
    @JoinColumn(name="cust_id",referencedColumnName = "cust_id"
            ,foreignKey = @ForeignKey(ConstraintMode.NO_CONSTRAINT))
    private Member member;
    @ManyToOne
    @JoinColumn(name="itms_cd_nbr",referencedColumnName = "itms_cd_nbr"
            ,foreignKey = @ForeignKey(ConstraintMode.NO_CONSTRAINT))
    private UnListedStock unListedStock;
    @Column(name = "lnp_sqn")
    private Long lineUpSequence;
    @Column(name = "inte_yn")
    @Enumerated(EnumType.STRING)
    private YNCode interestYn;

    public boolean isInterest() {
        return interestYn.equals(YNCode.Y);
    }
}

```

이런식으로 되어 있을 때 

interestStock 엔티티가 존재하는데 DB에서 ManyToOne 으로 매핑되어있는 Member row를 날려버리면 EntityNotFoundException이 뜬다.
왜냐하면 UnListedStock::getCurrentInterestMembers → getMember 하다가  Member에 대한 row가 존재하지 않으면 에러터짐

## 해결방법

크게 세 가지 해결법이 있을 것 같다(세가지 다 적용 가능, 배타적 X)
1. delete 시 Soft Delete 사용(위 코드에서는 effectiveYn을 N으로 바꾸고 filter에서 N을 걸러냄)
2. @NotFound(action = NotFoundAction.IGNORE) 사용
3. 이걸 논의하지 않는 것

@NotFound  Ignore 하고 싶지만 위 상황을 피하는 것이지 오류가 없는건 아니기 때문에 더 위험하다고 판단.
그리고 아마 조회할때는 괜찮겠지만 설정할 때 문제 생길것.

사실 처음 설계할 때 row delete를 하는 경우를 두지 않았기 때문에 그냥 둬도 됨.
운영에서도 select만 가능하기 때문에 문제 일어날 일 없음.

## 쿼리 기반 어플리케이션이 아니기 때문에

문제는 크게 세 가지 상황에서 일어날 것
1. ITISM으로 직접 원장 변경 작업을 요청할 경우
2. BXM → MSA 환경으로 계속 마이그레이션 할 때 기존 업무에서 놓친 경우
3. Mybatis나 JDBC를 이용한 DB 변경
1, 2번은 잘 안일어나니 차치하고
3번의 경우
기존 BXM 프레임워크에서 Mybatis 쿼리 기반으로 작업을 하는 경우에는 대부분 Inner Join + 외래키 없음 방식으로 데이터를 관리했기 때문에 데이터가 없다 → 그냥 넣는다 이런식으로 처리가 가능했지만
테이블은 그대로 두고 도메인을 가지고 작업을 하는 환경으로 들어옴
단위테스트 용이성과 컬럼 변경에 대한 영향도 문제 때문에 외래키 참조를 걸지 않은 상태이므로(케이뱅크 메타시스템에서 외래키를 지원하지 않기도 하지만)
Spring Data JPA를 거치지 않은 DB 변경은 잘못될 수 있다.
단적인 예시로 delete를 JPA로 하는 경우→ 하이버네이트가 persist 하면서 연관된 데이터를 날리던가 할 것.
하지만 JPA가 아니라 하이버네이트가 모르는 경우 지워놓고 하이버네이트에서 Select 하는 경우 문제 생길 것.
JPA를 사용한 이상 Mybatis를 기술적으로 자유롭게 사용할 수 있지만, 비즈니스적으로는 제약이 있을 수 있다.
