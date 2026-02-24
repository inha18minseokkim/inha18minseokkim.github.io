---
title: BatchListWriting
date: 2023-10-17
tags:
  - Spring
  - Batch
---
Chunk 프로세스에서 리스트를 Write 하고 싶다..

```java
@Configuration
@RequiredArgsConstructor
public class ApiReceiveStepConfiguration {
    private final NaverApiReceive apiReceive;
    private final TargetProductMapper targetProductMapper;
    private final EntityManagerFactory entityManagerFactory;
    private final DataSource dataSource;
    @Bean
    public Step targetProductReceiveStep(JobRepository jobRepository,
                                         PlatformTransactionManager platformTransactionManager,
                                         TargetProductRepository targetProductRepository
    ) {
        return new StepBuilder("TargetProductReceiveStep",jobRepository)
                .<TargetProduct, List<ApiReceiveRaw>>chunk(100,platformTransactionManager)
                .reader(targetProductItemReader(targetProductRepository))
                .processor(compositeProcessor())
                .writer(targetItemWriter())
                .build();
    }

    @Bean
    public ItemReader<TargetProduct> targetProductItemReader(TargetProductRepository repository) {
        RepositoryItemReader<TargetProduct> itemReader = new RepositoryItemReader<>();
        itemReader.setRepository(repository);
        itemReader.setMethodName("findAll");
        itemReader.setPageSize(1);
        HashMap<String, Sort.Direction> sorts = new HashMap<>();
        sorts.put("productId", Sort.Direction.DESC);
        itemReader.setSort(sorts);
        return itemReader;
    }

    @Bean
    public ItemProcessor<TargetProduct,List<ApiReceiveRaw>> compositeProcessor() {
        CompositeItemProcessor<TargetProduct, List<ApiReceiveRaw>> objectObjectCompositeItemProcessor = new CompositeItemProcessor<>();
        objectObjectCompositeItemProcessor.setDelegates(Arrays.asList(targetItemReceiveProcessor(),targetItemMappingProcessor()));
        return objectObjectCompositeItemProcessor;
    }

    @Bean
    public ItemProcessor<TargetProduct, List<ApiReceiveItem>> targetItemReceiveProcessor() {
        return (TargetProduct target) -> {
            ApiReceiveResponse apiReceiveResponse = apiReceive.requestFromEntity(target, 1);
            return apiReceiveResponse.getItems();
        };
    }

    @Bean
    public ItemProcessor<List<ApiReceiveItem>, List<ApiReceiveRaw>> targetItemMappingProcessor() {
        return (List<ApiReceiveItem> target) -> target.stream().map(targetProductMapper::from).toList();
    }
    @Bean
    public JdbcBatchItemWriter<ApiReceiveRaw> batchItemWriter() { //public으로 나와있지 않으면 안됨. 빈 매핑 안됨.
        JdbcBatchItemWriter<ApiReceiveRaw> build = new JdbcBatchItemWriterBuilder<ApiReceiveRaw>()
                .dataSource(dataSource)
                .sql("INSERT INTO ApiReceiveRaw (\n" +
                        "    brand, category1, category2, category3, category4, hprice, image, link, lprice, maker, mallName, productId, productType, receiveDate, title\n" +
                        ") VALUES (\n" +
                        "    :brand, :category1, :category2, :category3, :category4, :hprice, :image, :link, :lprice, :maker, :mallName, :productId, :productType, :receiveDate, :title\n" +
                        ") ON DUPLICATE KEY UPDATE\n" +
                        "    hprice = VALUES(hprice),\n" +
                        "    image = VALUES(image),\n" +
                        "    link = VALUES(link),\n" +
                        "    lprice = VALUES(lprice),\n" +
                        "    maker = VALUES(maker),\n" +
                        "    mallName = VALUES(mallName),\n" +
                        "    productType = VALUES(productType),\n" +
                        "    receiveDate = VALUES(receiveDate),\n" +
                        "    title = VALUES(title)")
                .beanMapped()
                .build();
        return build;
    }
    @Bean
    public ItemWriter<List<ApiReceiveRaw>> targetItemWriter() {
        ItemWriter<List<ApiReceiveRaw>> objectJpaListWriter = new BatchListWriter<>(batchItemWriter());
        return objectJpaListWriter;
    }
}
```

ItemReader<TargetProduct> → ItemProcessor<TargetProduct, List<ApiReceiveRaw>> → ItemWriter<ApiReceiveRaw>
중간에 차원이 하나 늘어남. 기본적인 ItemWriter들로는 구현이 안될 듯(내가 모르는 무언가가 있을 수는 있음)

Generic 사용한 공통 유틸리티를 하나 만들어봄(개별 Item을 write 하는 ItemWriter를 주입시킴)

```java
public class BatchListWriter<T> implements ItemWriter<List<T>> {
    private final JdbcBatchItemWriter<T> itemWriter;
    public BatchListWriter(JdbcBatchItemWriter<T> _itemWriter){
        this.itemWriter = _itemWriter;
    }
    @Override
    public void write(Chunk<? extends List<T>> items) {
        List<T> currentList = new ArrayList<>();
        for(List<T> subList : items){
            currentList.addAll(subList);
        }
        try {
            itemWriter.write(new Chunk<>(currentList));
        } catch (Exception e) {
            throw new RuntimeException(e);
        }
    }
}
```


아니면 이런식으로 Consumer 함수 인터페이스를 구현해준다(repository를 사용)

```java
@Bean
public ItemWriter<List<MultiDimensionalRate>> itemWriter() {
    return chunk -> {
        List<MultiDimensionalRate> collect = chunk.getItems().stream().flatMap(List::stream).collect(Collectors.toList());
        repository.insertObjectBatch(collect);
		};
}
```

해당 repository는 다음과 같이 구현

```java
public class MultiDimensionalRateRepository {
    private final JdbcTemplate jdbcTemplate;
    public void insertObjectBatch(List<MultiDimensionalRate> rateList) {
        log.info(rateList.toString());
        String sql = "insert into MultiDimensionalRentLoanRateInfo (loadYearMonth, creditGrade, jobCode, houseCode, ageCode, incomeCode,\n" +
                "                                              debtCode, averageLoanRate, averageLoanRat2, bankName, loanCount,\n" +
                "                                              loanAmount, maxLoanRate, minLoanRate)\n" +
                "values (?,?,?,?,?,?,?,?,?,?,?,?,?,?)";
        jdbcTemplate.batchUpdate(sql, new BatchPreparedStatementSetter() {
            @Override
            public void setValues(PreparedStatement ps, int i) throws SQLException {
                MultiDimensionalRate dto = rateList.get(i);
                ps.setString(1, dto.getLoadYearMonth());
                ps.setLong(2, dto.getCreditGrade());
                ps.setString(3, dto.getJobCode());
                ps.setString(4, dto.getHouseCode());
                ps.setLong(5, dto.getAgeCode());
                ps.setLong(6, dto.getIncomeCode());
                ps.setLong(7, dto.getDebtCode());
                ps.setDouble(8, dto.getAverageLoanRate());
                ps.setDouble(9, dto.getAverageLoanRate2());
                ps.setString(10, dto.getBankName());
                ps.setLong(11, dto.getLoanCount());
                ps.setLong(12, dto.getLoanAmount());
                ps.setDouble(13, dto.getMaxLoanRate());
                ps.setDouble(14, dto.getMinLoanRate());
            }

            @Override
            public int getBatchSize() {
                return rateList.size();
            }
        });

    }
}
```

[https://velog.io/@qotndus43/Batch-Insert](https://velog.io/@qotndus43/Batch-Insert) 참고
