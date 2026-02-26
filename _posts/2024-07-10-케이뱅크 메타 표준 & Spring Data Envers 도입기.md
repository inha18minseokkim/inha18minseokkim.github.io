---
title: "케이뱅크 메타 표준 & Spring Data Envers 도입기"
date: 2024-07-10
tags: [미지정]
category:
  - 실무경험
---

### 이 방법을 개발 한 이유


```java
@Override
@Transactional
public SetMemberPushInfoResult setMemberPushInfo(SetMemberPushInfoCriteria criteria) {
    GetMemberInfoResult memberDto = memberService.getMember(GetMemberCriteria.builder().customerId(criteria.customerId()).build());
    Member member = memberRepository.findById(memberDto.customerId()).orElseThrow();

    Optional<Push> push = pushRepository.findById(PushId.builder().member(member).stockPushAlertTypeCode(criteria.stockPushAlertTypeCode().getCodeNumber()).build());
    if(push.isEmpty())
        pushRepository.save(Push.builder()
                .member(member)
                .stockPushAlertTypeCode(criteria.stockPushAlertTypeCode().getCodeNumber())
                .assetManagementPushAlertYn(criteria.assetManagementPushAlertYn()).build()
        );
    else
        push.get().setAssetManagementPushAlertYn(criteria.assetManagementPushAlertYn());

    PushHistory historyResult = pushHistoryRepository.save(PushHistory.builder()
            .member(member)
            .stockPushAlertTypeCode(criteria.stockPushAlertTypeCode().getCodeNumber())
            .assetManagementPushAlertYn(criteria.assetManagementPushAlertYn()).build()
    );

    return mapper.toSetMemberPushInfoResult(historyResult);
}
```

부끄럽긴 하지만 옛날 코드를 예시로 들고옴.(비상장주식 알림 서비스, 도메인에 로직 넣는 리팩토링 이전 코드임)
여기서 푸시 변경 히스토리를 원장에 직접 insert 해야 하는데, 코드가 더러워보인다. 변경에 대한 이력을 처리하는 로직은 다 똑같고, 정보보호팀의 경우 이력을 db에 관리하는지만 보고 어떤 포맷으로 관리하는지는 보지 않기 때문에 envers를 사용하여 자동화하기로 함.

### 케이뱅크 메타 표준


```lua
spring:
  jpa:
    properties:
      org:
        hibernate:
          envers:
            revision_table_name: TB_STK_RVSN_INFO_X
            revision_field_name: rvsn_hst_val
            revision_timestamp_field_name: rvsn_hst_dttm
            revision_type_field_name: rvsn_tp_val
```

케이뱅크 메타 표준에 따라 테이블 이름 컬럼을 만들어야 하기 때문에 envers 에서 기본으로 제공하는 테이블명과 컬럼명을 쓰지 못한다. ddl 바꿀 수 있는 명세를 찾았다.


```lua
@Entity
@RevisionEntity
@Table(name = "TB_STK_RVSN_INFO_X")
@SequenceGenerator(
        name = "sq_stk_rvsn_info_x_01",
        sequenceName = "sq_stk_rvsn_info_x_01",
        allocationSize = 100
)
data class StockRevision(
        @Id
        @GeneratedValue(strategy = GenerationType.SEQUENCE, generator = "sq_stk_rvsn_info_x_01")
        @RevisionNumber
        @Column(name = "dat_id")
        val id: Int = 0,

        @RevisionTimestamp
        @Column(name = "amnn_base_seq_nbr")
        val timestamp: Long = 0L
) : TimeStamp(), Serializable
```

revision 테이블에 대한 명세도 메타표준을 따라야 하기 때문에 컬럼 이름을 바꿔줘야 한다. 


```java
@Entity
@Audited(targetAuditMode = RelationTargetAuditMode.NOT_AUDITED)
@AuditTable(value="TB_STK_FNCL_STMT_H")
@AuditOverride(forClass = TimeStamp.class)
@SuperBuilder
@Getter
@Builder
@AllArgsConstructor
@NoArgsConstructor
@Table(name="TB_STK_FNCL_STMT_M",uniqueConstraints = {@UniqueConstraint(columnNames = {"base_dt","itms_cd_nbr","tp_id","rpt_id","acnt_id"})})
@SequenceGenerator(name="sq_stk_fncl_stmt_m_01",sequenceName="sq_stk_fncl_stmt_m_01",allocationSize = 20)
public class FinancialStatement extends TimeStamp implements Serializable {
    @Id
    @Column(name="dat_id")
    @GeneratedValue(strategy= GenerationType.SEQUENCE, generator = "sq_stk_fncl_stmt_m_01")
    private Long dataId;
    @Column(name="base_dt")
    private LocalDate baseDate;
    @ManyToOne
    @JoinColumn(name="itms_cd_nbr",referencedColumnName = "itms_cd_nbr",foreignKey = @ForeignKey(ConstraintMode.NO_CONSTRAINT))
    private ListedStock listedStock;
    @Column(name="tp_id")
    private String typeId; //유형식별자
    @Column(name="rpt_id")
    private String reportId; //보고서식별자
    @Column(name="acnt_id")
    private String accountId; //회계식별자
    @Column(name="kor_nm")
    private String koreanName; //회계한글명
    @Column(name="val_amt")
    private Double value; //가액금액
    public static FinancialStatement emptyEntity() {
        return FinancialStatement
                .builder().build();
    }
    public Long getLongValue() {
        return value == null ? null : value.longValue();
    }
}
```


원천정보

```lua
    @OneToMany(cascade = CascadeType.PERSIST)
    @JoinColumn(name="itms_cd_nbr",referencedColumnName = "itms_cd_nbr"
            ,foreignKey = @ForeignKey(ConstraintMode.NO_CONSTRAINT),insertable = false,updatable = false)
    @JsonIgnore
    @NotAudited
    private List<ListedStockPrice> prices;

    @OneToMany(cascade = CascadeType.PERSIST)
    @JoinColumn(name="itms_cd_nbr",referencedColumnName = "itms_cd_nbr"
            ,foreignKey = @ForeignKey(ConstraintMode.NO_CONSTRAINT),insertable = false,updatable = false)
    @JsonIgnore
    @NotAudited
    private List<FinancialRatio> financialRatios;

    @OneToMany(cascade = CascadeType.PERSIST)
    @JoinColumn(name="itms_cd_nbr",referencedColumnName = "itms_cd_nbr"
            ,foreignKey = @ForeignKey(ConstraintMode.NO_CONSTRAINT),insertable = false,updatable = false)
    @JsonIgnore
    @NotAudited
    private List<FinancialStatement> financialStatements;

    @OneToMany(fetch = FetchType.LAZY,cascade = CascadeType.MERGE)
    @JoinColumn(name="itms_cd_nbr",referencedColumnName = "itms_cd_nbr"
            ,foreignKey = @ForeignKey(ConstraintMode.NO_CONSTRAINT),insertable = false,updatable = false)
    @NotAudited
    private List<Summary> summary;
```

컬럼 매핑이 자유롭지 않기  때문에 매핑 이력정보는 하지 않음. 그냥 원천 이력정보만 저장

이런식으로 DDL 생성됨. 실제로는 foreign constraint 적용 안할 예정

```sql
create table public.tb_stk_fncl_stmt_cd_h
(
    dat_id        bigint  not null,
    rvsn_hist_val integer not null
        constraint fkob9b3peke42oj6l1vveigjdg8
            references public.tb_stk_rvsn_info_x,
    rvsn_tp_val   smallint,
    acnt_id       varchar(255),
    acn_itm_nm    varchar(255),
    acn_path_nm   varchar(255),
    bsns_tp_val   varchar(255),
    cl_lvl        bigint,
    fnsm_tp_cd    varchar(255),
    prns_acnt_id  varchar(255),
    prns_rpt_id   varchar(255),
    rpt_id        varchar(255),
    primary key (dat_id, rvsn_hist_val)
);

alter table public.tb_stk_fncl_stmt_cd_h
    owner to minseokkim23;


```

revisionTable 의 경우 메타 표준(이력 컬럼 6개)를 맞춘 스펙은 아니긴 한데 배치 테이블 처럼 스프링 앱 실행을 위한 테이블이라서 변경 이력에 대한 테이블의 변경 이력을 기록하는건 아닌것 같아서 설득.

SuperClass 이력 남길 때

```lua
@Entity
@Audited(targetAuditMode = RelationTargetAuditMode.NOT_AUDITED)
@AuditTable(value="TB_STK_LI_STCK_SMR_H")
@AuditOverride(forClass = TimeStamp.class)
@AllArgsConstructor
@NoArgsConstructor
@Builder
@Table(name="TB_STK_LI_STCK_SMR_M")
@Getter
@Slf4j
public class Summary extends TimeStamp implements Serializable {
        @Id
        @Column(name="itms_cd_nbr")
```

@AuditOverride 사용 하면 케이뱅크 공통 엔티티 사용가능.
relation에 대한 변경이력은 남기지 않음. 바뀔일이 없고 FK를 지정하지 않기 때문(메타 시스템에서 외래키따위는 없음)


### 언제 쓸까

1. 계정계 컴플라이언스 요건 자동화
  1. 계정계 포털같은 곳에서 원장을 변경하는 경우 그 변경 이력에 대한 테이블을 유지하고 있어야 함
2. 대고객 처리성 업무
  1. 고객 관련 정보를 변경할 때 마다 변경 이력을 관리해야 한다(보안 체크리스트에 있음)
    1. 공모주 메이트 푸시 알림 동의
    2. 관심 주식 등록 등등

### 쓸 때 조심해야 할 것

1. 배치성 대량 데이터 적재하는 경우 사용에 유의(데이터 변동분에 대해 꼭 변경이력을 db에 저장해야하나? 파일로 기록하면 되지 않을까?)
2. spring transaction level 신경쓰기
  - 현재 이 envers는 jpa audit와 같은 트랜잭션 레벨에서 작동해야 정상적으로 작동함.

