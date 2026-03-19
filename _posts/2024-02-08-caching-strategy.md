---
title: "캐싱 전략"
date: 2024-02-08
tags:
  - 개발
  - 기술
category:
  - 실무경험
---
개발 관련 내용 정리.
### 배경

1. 식품물가 데이터는 하루에 두 번만 갱신됨(오전 5시, 오후 3시)
2. 현재는 통계 처리된 반정규 데이터를 모두 다 DB에 저장하고 있음
  1. 서울 - 2024년 2월 13일 기준의 - 쌀(100,111,01,01,04) - 일,주,월,반년,연간 - 평균 이런식으로
  2. 그러므로 그래프에서 평단선 및 전주대비 등락을 보여줄 때 해당 데이터를 직접 가져와서 보여주는 중
  3. 데이터 쌓이는 속도가 빨라서 TOBE 버전에서는 일단위 평균만 치고 자바 소스단에서 평균침
3. 한 번에 많은 데이터를 처리함(식품의 주,월,반년,연간 가격 리스트를 한 번에 리턴해야함)
  1. 처리속도 늦으면 안됨
  2. 프론트에서 호출하는 로직을 바꿀 수 없음

### 기준

1. 서비스단에서 캐싱
2. 통계 테이블(processedPriceInfo)를 건드는 로직을 최대한 분리하여 캐싱

서비스 예시

## 1. getInnerProductPriceList

내부상품(약 104건)의 등락폭,비율,평균가격 맞춤
입력 : 지역그룹아이디,시작일자,종료일자

```java
@Override
@Cacheable(value = "ProductDetailServiceImpl.getDetailPriceList", key="#criteria")
@Transactional
public List<GetInnerProductPricesResult> getInnerProductPriceList(GetInnerProductPricesCriteria criteria) {
    UserGroupCode regionGroup = userGroupCodeRepository.findById(criteria.getRegionGroupId).orElseThrow;
    List<GetPriceDiffListOutDto> priceDiffList = processedPriceInfoReader.getPriceDiffList(
            GetPriceDiffListInDto.builder.regionGroupCodeId(criteria.getRegionGroupId)
                    .startDate(criteria.getStartDate).endDate(criteria.getEndDate)
                    .build);
    Map<String, List<GetPriceDiffListOutDto>> collect = priceDiffList.parallelStream.collect(Collectors.groupingBy(element -> element.getInnerProductId));
    List<GetInnerProductPricesResult> priceList = collect.keySet.stream.map(collect::get).map(element -> {
        //기준일자
        Optional<GetPriceDiffListOutDto> baseDatePriceInfo = element.stream.max(Comparator.comparing(elem -> elem.getBaseDate.orElse("")));
        //상품정보
        String innerProductId = baseDatePriceInfo.get.getInnerProductId;
        //현재가격
        Double currentPrice = baseDatePriceInfo.get.getPrice.orElse(0.0);
        String baseDate = baseDatePriceInfo.get.getBaseDate.orElse(criteria.getEndDate);
        //평균가격
        Double averagePrice = element.stream.collect(Collectors.averagingDouble(ele -> ele.getPrice.orElse(0.0)));
        double gapPrice = currentPrice - averagePrice;
        double gapRatio = gapPrice / averagePrice;
        return GetInnerProductPricesResult.builder
                .averagePrice(averagePrice)
                .currentPrice(currentPrice)
                .gapPrice(gapPrice)
                .gapRatio(gapRatio)
                .baseDate(baseDate)
                .innerProductId(innerProductId)
                .build;
    }).sorted((a,b) -> a.getGapRatio < b.getGapRatio ? 1 : -1).collect(Collectors.toList);
    return priceList;
}
```

이 서비스를 활용하는 기존 뷰용 짬통 서비스
입력값: 고객아이디, 지역그룹아이디, 기준일자
고객아이디가 들어가기 때문에 이 서비스에 cacheable 선언안함

```java
@Override
@Transactional
public List<GetAllProductResult> getAllProduct(GetAllProductCriteria criteria){
//모든 상품 맵 가져옴
    List<InnerProduct> allProduct = innerProductRepository.findAllByIsAvailable(true);
//가장 많이 조회한 상품 리스트 가져옴
    List<GetTopViewedInnerProductOutDto> topViewedInnerProducts = customerSearchHistoryReader.getTopViewedInnerProduct(GetTopViewedInnerProductInDto.builder
            .currentTime(LocalDateTime.now).rangeHour(12)
            .build);

//가격 가져올 범위 에서 startDate는 baseDate에서 일주일 전
    String startDate = LocalDate.parse(criteria.getBaseDate, DateTimeFormatter.ofPattern("yyyyMMdd"))
            .minusDays(6)
            .format(DateTimeFormatter.ofPattern("yyyyMMdd"));

//일주일간 가격 통계정보 가져옴 startDat - baseDate 까지 + Cacheable
    List<GetInnerProductPricesResult> innerProductPriceList = productDetailService.getInnerProductPriceList(GetInnerProductPricesCriteria.builder
            .regionGroupId(criteria.getRegionGroupId).endDate(criteria.getBaseDate).startDate(startDate).build);

//고객 관심상품정보 가져옴
    List<GetMemberInterestProductsResult> memberInterestProducts = memberService.getMemberInterestProducts(GetMemberInterestProductsCriteria.builder.customerId(criteria.getCustomerId).build);

//각각 정보 적재를 위한 맵. 해당주 상품 가격정보가 없어도 표시는 필요함
    Map<String,GetAllProductResult> resultMap = allProduct.stream.collect(Collectors.toMap(InnerProduct::getId
            ,element -> GetAllProductResult.builder
                    .innerProductId(element.getId)
                    .currentPrice(0L)
                    .innerCategoryId(element.getInnerCategory.getId)
                    .gapPrice(0L)
                    .gapPriceRatio(0.0)
                    .clickCount(0L)
                    .isRiseOrDecline(false)
                    .isCustomerInterest(false)
                    .unitValueName(element.getBaseProducts.get(0).getUnitValue + element.getBaseProducts.get(0).getUnitName)
                    .innerProductName(element.getProductName)
                    .innerCategoryName(element.getInnerCategory.getInnerCategoryName)
                    .build));
    //관심상품
    memberInterestProducts.stream.forEach(element -> {
        GetAllProductResult interestProduct = resultMap.get(element.getInnerProductId);
        interestProduct.setIsCustomerInterest(true);
    });
    //검색순위
    log.debug("시작 : {}",resultMap);
    topViewedInnerProducts.forEach(element -> {
        log.debug("중간 {}",element);
        GetAllProductResult clickProduct = resultMap.get(element.getInnerProductId);
        clickProduct.setClickCount(element.getCount);
    });
    //가격정보 하위 5개 마킹
    for(int i = 0; i < Math.min(innerProductPriceList.size,5); i++){
        if(innerProductPriceList.get(i).getGapRatio >= 0) break; //모든 상품이 다 오른 경우 스킵
        String minusInnerProduct = innerProductPriceList.get(i).getInnerProductId;
        resultMap.get(minusInnerProduct).setIsRiseOrDecline(true);
    }
    //가격정보 상위 5개 마킹
    for(int i = innerProductPriceList.size-1; i >= 0; i--){
        if(innerProductPriceList.get(i).getGapRatio <= 0) break; //모든 상품이 다 내린 경우 스킵
        String minusInnerProduct = innerProductPriceList.get(i).getInnerProductId;
        resultMap.get(minusInnerProduct).setIsRiseOrDecline(true);
    }
    //내부상품별로 현재가,등락률,등락가격 세팅
    innerProductPriceList.forEach(element -> {
        GetAllProductResult targetProduct = resultMap.get(element.getInnerProductId);
        targetProduct.setCurrentPrice(Math.round(element.getCurrentPrice));
        targetProduct.setGapPriceRatio(element.getGapRatio * 100);
        targetProduct.setGapPrice(Math.round(element.getGapPrice));
    });
    return resultMap.values.stream.toList;
}
```

고객아이디 없이 지역아이디 + 기준일자 input → 가격정보 output만 캐싱함

```java
//일주일간 가격 통계정보 가져옴 startDat - baseDate 까지 + Cacheable
    List<GetInnerProductPricesResult> innerProductPriceList = productDetailService.getInnerProductPriceList(GetInnerProductPricesCriteria.builder
            .regionGroupId(criteria.getRegionGroupId).endDate(criteria.getBaseDate).startDate(startDate).build);
```

여기서 캐싱된 정보 가져오고(최대 104 * 7건)
밑에서  해시맵으로 grouping 한 다음에(가격정보 리스트의 경우 가격이 7일간 수신이 안되어있으면 빠져버리므로 104건 모두 넣고 가격은 0으로 둠) 캐시에서 꺼내온 일주일 가격 기반으로 맵에다가 넣음 → 24시간 가장 많이 조회한 품목 맵에다 넣음 → 특정사용자의 관심상품 맵에다 넣음 → 가격 가장 많이 오른/떨어진 상품 넣음
DB조회쪽만 캐싱하고 아래 조립하는쪽은 JAVA 소스단에서 그냥 하도록 둠(For문 몇개 있어도 얼마 안돈다고 판단)


## 2. getDetailPriceList

특정 내부상품의 해당기준일자 그래프 조회(주,월,반년,연간 데이터 리스트)
입력 : 내부상품아이디,지역그룹아이디,기준일자
출력 : (주,월,반년,연간 리스트)의 평균,최대 최소가격, 기준일자, 리스트 사이즈, (기준일자,가격) 리스트

```java
@Override
@Transactional
@Cacheable(value = "ProductDetailServiceImpl.getDetailPriceList", key="#criteria")
public List<GetDetailPriceLegacyResultElement> getDetailPriceList(GetDetilPriceListCriteria criteria) {

    String latestBaseDate = criteria.getBaseDate;
    // 1년치 가격 뽑아옴
    List<FindPriceListByGroupRegionCodeOut> priceList
            = processedPriceInfoReader.findPriceListByGroupRegionCode
            (FindPriceListByGroupRegionCodeInDto.builder
                    .regionGroupCodeId(criteria.getRegionGroupId)
                    .baseDate(latestBaseDate)
                    .rangeForLength(BaseRange.YEAR)
                    .rangeForTag(BaseRange.DAY)
                    .targetInnerProductId(criteria.getInnerProductId).build);
    //조립시작, 1주일, 1개월, 6개월, 1년
    List<GetDetailPriceLegacyResultElement> list = new ArrayList<>;
    for(BaseRange baseRange : BaseRange.getDetailRangeList){
        DoubleSummaryStatistics summary = priceList.stream.limit(baseRange.getGapDay).mapToDouble(element -> element.getPrice).summaryStatistics;
        List<GetDetailPriceLegacyResultSubElement> subList = priceList.stream.limit(baseRange.getGapDay).map(element -> mapper.toSubElement(element)).collect(Collectors.toList);
        double max = summary.getMax;
        double min = summary.getMin;
        double average = summary.getAverage;
        list.add(GetDetailPriceLegacyResultElement.builder
                .basePrice(average)
                .baseRange(baseRange)
                .list(subList)
                .listSize((long)subList.size)
                .maximumPrice(max)
                .minimumPrice(min)
                .build);
    }
    return list;
}
```

특정 상품의 특정지역, 특정 일자로부터 365일 전까지 모든 가격 가져옴
  - 일자별로 정렬된 데이터 가져와서 앞에서부터 7개 30개 183개 365개로 끊음.
  - 각각의 리스트에 최대최소평균값 구해서 리턴
이 서비스를 캐싱

```java
@Override
@Transactional
public GetDetailPriceLegacyResult getDetailPriceLegacy(GetDetailPriceCriteria criteria) {
    //특정 지역그룹 특정 내부상품의 특정 날짜 가격 리스트(그래프)
    GetLatestBaseDateResult latestBaseDate = getLatestBaseDate(GetLatestBaseDate
                                                            .builder.baseDate(criteria.getBaseDate).build);
    Optional<UserGroupCode> regionGroup = userGroupCodeRepository.findById(criteria.getRegionGroupId);
    Optional<InnerProduct> innerProduct = innerProductRepository.findById(criteria.getInnerProductId);
    GetMemberResult member = memberService.getMember(GetMemberCriteria.builder
                                                    .customerId(criteria.getCustomerId)
                                                    .businessCode("001").build);


    //멤버 조회 이력 insert
    memberService.insertProductHistory(InsertProductHistoryCriteria.builder
                                    .innerProductId(criteria.getInnerProductId)
                                    .regionGroupCodeId(criteria.getRegionGroupId)
                                    .memberInfoId(member.getMemberInfo.getId)
                                    .build);
    //가격정보 기간별로 가져옴
    List<GetDetailPriceLegacyResultElement> list = productDetailService.getDetailPriceList(GetDetilPriceListCriteria.builder
                    .innerProductId(criteria.getInnerProductId)
                    .regionGroupId(criteria.getRegionGroupId)
                    .baseDate(latestBaseDate.getBaseDate)
            .build);

    return GetDetailPriceLegacyResult.builder
            .listCount((long)list.size)
            .unitName(innerProduct.get.getBaseProducts.get(0).getUnitName)
            .unitValue(innerProduct.get.getBaseProducts.get(0).getUnitValue.doubleValue)
            .innerProductId(innerProduct.get.getId)
            .regionGroupId(regionGroup.get.getId)
            .gapPrice(null)
            .basePrice(null)
            .innerProductName(innerProduct.get.getProductName)
            .baseDate(latestBaseDate.getBaseDate)
            .list(list)
            .build;
}
```

사용하는 엔티티들 가져와서 멤버 조회 이력 insert 하고 가격정보 기간별로 가져옴(캐싱한 서비스)
그리고 밑에서 조립해서 던져줌


## 3. getLatestBaseDate


```java
@Override
@Cacheable(value = "ProductServiceImpl.getLatestBaseDate",key = "#criteria")
public GetLatestBaseDateResult getLatestBaseDate(GetLatestBaseDate criteria) {
    //가격 수신 일자 기준으로 유효한 최근 일자 구함
    String maxBaseDate = processedPriceInfoReader.getMaxBaseDate(criteria.getBaseDate);
    return GetLatestBaseDateResult.builder.baseDate(maxBaseDate).build;
}
```

첫 메인화면 조회 시 가격 조회 가능한 최신 조회일자를 조회하는 서비스(일자전환용)
  - 기존) 500번대 축산물을 제외한 식품들 중에서 가장 최신 기준일자를 조회 
    - but 중간에 통계 처리 시, 새로운 품목들이 들어오는 중에 고객이 해당 일자를 조회하고 품목을 조회하는 경우 데이터들이 다 적재되지 않은 상태에서 최신일자가 바뀌고 불완전한 데이터를 조회할 수 있었음(기존 BXM에서는 캐싱 기능이 없음 + 이거 하나로 테이블을 따로 안만들었음)
  - 해당 서비스는 계속 캐시로 떠있다가 통계 적재 후 통계 배치 afterStep에서 해당 캐시 데이터를 Flush 또는 갱신 하면서 일자전환 할 생각
  -  ex)
  -  20240214 까지 데이터가 있었고 통계배치 수행함(현재 캐시값은 20240214)
    - 20240215 데이터 모두 적재 후 getInnerProductPriceList 호출(여기서 키값의 baseDate가 20240215이므로 20240214 20240215 각각 기준일자에 대한 output 모두 캐싱됨)
      - 여기서 캐시값 20240214를 날리거나 20240215로 갱신하면 자연스럽게 getInnerProductPriceList 서비스는 20240215로 들어갈것
        - 물론 통계 중간에 Redis가 날아가서 캐시가 사라지면 똑같이 문제가 생기긴 함. 
그리고 fdppoc-dataprocess 배치 수행 후 나머지 서비스도 새로 캐시 적재 필요함


이런식으로 일단 
1.  8~12시간 정도는 변하지 않고 (멱등적이고)
2. DB조회가 많이 일어나고
3. input 패턴이 몇개 없는(고객번호를 키값에 넣지않음) 경우

다만 현재 Redis는 위와같은 캐싱용이 아니라(api-gateway에서 사용할 목적이었음) 인스턴스, 메모리 모두 부족한 상황. TF원들 인지 필요
  - ⇒ 주제업무별로 레디스 레플리카 구성이 완료되어 이제 사용가능!!
