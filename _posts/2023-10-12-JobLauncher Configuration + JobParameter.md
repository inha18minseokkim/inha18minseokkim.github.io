---
title: "JobLauncher Configuration + JobParameter"
date: 2023-10-12
tags:
  - 개발
  - 기술
category:
  - 실무경험
---
개발 관련 내용 정리.
```javascript
@Configuration
@RequiredArgsConstructor
@Slf4j
public class JobConfiguration {
    @Value("${loanYearMonth}")
    private String loanYearMonth;
    private final MultiDimensionalRateReceive receiver;

    private final DataSource dataSource;
    private final JobRepository jobRepository;
    private final PlatformTransactionManager platformTransactionManager;
    private final MultiDimensionalRateRepository repository;
    private static int requestCount = 0;
    @Bean
    public JobParameters jobParameters {
        return new JobParametersBuilder.addString("loanYearMonth",loanYearMonth)
                .addLocalDateTime("executeDate", LocalDateTime.now)
                .toJobParameters;
    }
    @Bean
    public JobExecution jobExecution throws Exception {
        return jobLauncher.run(
                new JobBuilder("multiDimensionalRateJob",jobRepository)
                        .start(multiDimensionalRateStep)
                        .build
                ,jobParameters);
    }
    @Bean
    public JobLauncher jobLauncher throws Exception {
        TaskExecutorJobLauncher taskExecutorJobLauncher = new TaskExecutorJobLauncher;
        taskExecutorJobLauncher.setJobRepository(jobRepository);
        taskExecutorJobLauncher.setTaskExecutor(new SimpleAsyncTaskExecutor);
        taskExecutorJobLauncher.afterPropertiesSet;
        return taskExecutorJobLauncher;
    }
    @Bean
    public Step multiDimensionalRateStep {
        return new StepBuilder("multiDimensionalRateStep",jobRepository)
                .<MultiDimensionalRateRequest,List<MultiDimensionalRate>>chunk(100,platformTransactionManager)
                .reader(requestCodeReader)
                .processor(compositeProcessor)
                .writer(itemWriter)
        .build;
    }
    @Bean
    public ItemReader<MultiDimensionalRateRequest> requestCodeReader {
        String sqlStatement = "select" +
                "\n 100 as numOfRows" +
                "\n,1 as pageNo" +
                "\n," +loanYearMonth + " as loanYm" +
                "\n,ageCode as age" +
                "\n,creditGrade as cbGrd" +
                "\n,debtCode as debt" +
                "\n,houseCode as houseTycd" +
                "\n,incomeCode as income" +
                "\n,jobCode as jobCd" +
                "\nfrom" +
                "    \nAgeInfo,CreditBreauInfo,DebtInfo,HouseTypeInfo,IncomeInfo,JobInfo"
                + "\nwhere HouseTypeInfo.description like '%오피%'\n" +
                "  and AgeInfo.ageCode between 2 and 2\n" +
                "  and DebtInfo.debtCode <= 1\n" +
                "  and IncomeInfo.incomeCode <= 4 and 5";
        log.info(sqlStatement);
        return new JdbcCursorItemReaderBuilder<MultiDimensionalRateRequest>
                .fetchSize(1)
                .dataSource(dataSource)
                .rowMapper(new BeanPropertyRowMapper<>(MultiDimensionalRateRequest.class))
                .sql(sqlStatement)
                .name("jdbcCursorItemReader")
                .build;
    }

    @Bean
    public ItemProcessor<MultiDimensionalRateRequest,List<MultiDimensionalRate>> compositeProcessor {
        CompositeItemProcessor<MultiDimensionalRateRequest, List<MultiDimensionalRate>> objectObjectCompositeItemProcessor = new CompositeItemProcessor<>;
        objectObjectCompositeItemProcessor.setDelegates(Arrays.asList(itemReceiveProcessor,itemConvertProcessor));
        return objectObjectCompositeItemProcessor;
    }

    @Bean
    public ItemProcessor<MultiDimensionalRateRequest, List<Map.Entry<MultiDimensionalRateRequest,MultiDimensionalRateItem>>> itemReceiveProcessor {
        return item -> {
            MultiDimensionalRateResponse multiDimensionalRateResponse = receiver.apiReceive(item);
            if(requestCount % 3 == 2){
                Thread.sleep(500);
            }
            requestCount++;
            if(!multiDimensionalRateResponse.getHeader.getResultCode.equals("00"))
                throw new RuntimeException("API 수신 실패" + item);
            return multiDimensionalRateResponse.getBody.getItems
                    .stream.map((element) ->
                            (Map.Entry<MultiDimensionalRateRequest,MultiDimensionalRateItem>)new AbstractMap.SimpleEntry<MultiDimensionalRateRequest,MultiDimensionalRateItem>(item,element)).toList;
        };
    }
    private Long parseLong(String target){
        try{
            return Long.parseLong(target);
        } catch (NullPointerException e){
            return 0L;
        }
    }
    private Double parseDouble(String target){
        try{
            return Double.parseDouble(target);
        } catch (NullPointerException e){
            return 0.0;
        }
    }
    @Bean
    public ItemProcessor<List<Map.Entry<MultiDimensionalRateRequest,MultiDimensionalRateItem>>,List<MultiDimensionalRate>> itemConvertProcessor {
        return item -> item.stream
                .map(
                        (Map.Entry<MultiDimensionalRateRequest,MultiDimensionalRateItem> fromItem) -> {
                            MultiDimensionalRateRequest key = fromItem.getKey;
                            MultiDimensionalRateItem value = fromItem.getValue;
                        return MultiDimensionalRate.builder
                        .loadYearMonth(key.getLoanYm)
                        .creditGrade(parseLong(key.getCbGrd))
                        .jobCode(key.getJobCd)
                        .houseCode(key.getHouseTycd)
                        .ageCode(Long.parseLong(key.getAge))
                        .incomeCode(Long.parseLong(key.getIncome))
                        .debtCode(Long.parseLong(key.getDebt))
                        .averageLoanRate(parseDouble(value.getAvgLoanRat))
                        .averageLoanRate2(parseDouble(value.getAvgLoanRat2))
                        .bankName(value.getBankNm)
                        .loanCount(parseLong(value.getCnt))
                        .loanAmount(parseLong(value.getLoanAmt))
                        .maxLoanRate(parseDouble(value.getMaxLoanRat))
                        .minLoanRate(parseDouble(value.getMinLoanRat))
                        .build;})
                .toList;
    }

    @Bean
    public ItemWriter<List<MultiDimensionalRate>> itemWriter {
        return chunk -> {
            List<MultiDimensionalRate> collect = chunk.getItems.stream.flatMap(List::stream).collect(Collectors.toList);
            repository.insertObjectBatch(collect);
        };
    }

}
```

하나의 @Configuration Bean에서 잡 실행 환경 구성
@Value 사용하여 ApplicationArguments로 부터 인자 주입(Command Line Args에서 받아옴)
주입받은 후 Step 빌드 Job 빌드
JobExecution 빌드

```javascript
@Bean
    public JobExecution jobExecution throws Exception {
        return jobLauncher.run(
                new JobBuilder("multiDimensionalRateJob",jobRepository)
                        .start(multiDimensionalRateStep)
                        .build
                ,jobParameters);
    }
```

해당 빈을 등록하면 jar 어플리케이션 실행 시 해당 빈 등록하며 실행.
JobParameter를 사용하여 JobExecution을 빌드하지 않으면 Job Instance 테이블에서 같은 Job Id를 식별하지 못하므로 JobParameter에 현재 시간, Argument 정도 넣어서 빌드


### 다만 이 기능은 개발 테스트 할 때나 유용하지(그마저도 풀을 늘리면 되는데 아직 그게 없음) 실제로 운영환경에서 사용하려면 내부 논의가 필요할 듯 함(똑같은 잡을 여러 번 실행 가능함에 통제절차가 존재하지 않음)
