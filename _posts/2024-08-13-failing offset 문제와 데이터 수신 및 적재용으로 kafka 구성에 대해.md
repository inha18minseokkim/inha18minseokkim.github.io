---
title: "failing offset 문제와 데이터 수신 및 적재용으로 kafka 구성에 대해"
date: 2024-08-13
tags:
  - Kafka
  - 개발
  - 이슈정리
category:
  - 기술
---
Kafka failing offset 이슈 해결 경험 정리.
# 현상

kafka를 통해 데이터를 Sub 하는 경우 적재는 정상인데 특정 Offset 구간에서 계속 반복, 에러는 아니지만 작업하고 WARN 메세지로 group id의 파트가 더 이상 아니므로 마지막 오프셋에서 시작한다 함.

# 사유

Offset commit interval (10분 기본값) 을 초과하여 특정 토픽을 여러 개(500개 기본값) 물고 작업을 하는 경우 DB 처리가 오래 걸리는 탓에 500개 처리하는 동안 10분이 넘어가서 브로커가 킥, kafka consumer group 에서 추방 당함.

# 해결방안

1. [max.poll.ms](http://max.poll.ms) 조정
2. 한 번에 처리되는 레코드 양 조절
보다는 kafka를 사용한 데이터 적재에 있어서 아직 경험이 없어 오토커밋 끄고 수동커밋으로 하기로 함. 한 번에 처리되는 레코드 양은 줄이고 각각의 메세지에 대해서 한번 처리하고 Offset 수동 ack 하는 방식으로
왜냐하면 kafka를 업무단의 EDM용으로 사용하는 것이 아닌 ETL 과 비슷한 방식으로 사용하기 위함.
  - 현재 데이터서비스팀에서 Kafka ETL 솔루션이 있는데 우리가 쓸 수는 없음 ㅜㅜ
EDM으로 사용하기 위한 용도와 ETL로 사용하기 위한 방법을 분리해서 생각해야 할 듯.

[Kafka 컨슈머 그룹에서 "Offset commit cannot be completed" 에러 발생 원인과 해결 방법](https://wiki.yowu.dev/ko/dev/Kafka/kafka-consumer-group-offset-commit-error-reasons-and-solutions)
[[Kafka] 컨슈머의 Poll 동작과정 및 max.poll.records 에 대한 오해](https://devoong2.tistory.com/entry/Kafka-컨슈머의-Poll-동작과정-및-maxpollrecords-에-대한-오해)


# 과연 현재 방법이 최선인가

현재는 이런식으로 구성되어있음

```java
@Component
@Slf4j
@RequiredArgsConstructor
public class ListedStockPriceListener {
    private final ListedStockPriceTransformer transformer;
    private final ObjectMapper objectMapper;
    private final ListedStockPriceRepository listedStockPriceRepository;
    @KafkaListener(topics = "ListedStockPrice",groupId = "ListedStockPrice")
    @Transactional
    public void listen(ConsumerRecord<String, OpenApiResponseDto> data) throws IOException {
        JsonNode jsonNode = objectMapper.readValue(data.value.responseBodyArr, JsonNode.class);
        JsonNode detail = jsonNode.get("detail");
        log.info("{}",detail);
        TypeReference<List<ListedStockPriceOriginalDto>> typeReference = new TypeReference<> {
        };
        List<ListedStockPriceOriginalDto> listedStockPriceOriginalDtos = objectMapper.convertValue(jsonNode.get("data"), typeReference);
        List<ListedStockPrice> listedStockPrices = transformer.convertToListedStockPrice(listedStockPriceOriginalDtos);
        listedStockPriceRepository.saveAll(listedStockPrices);
    }
}
```

1. topic안에 있는 json을 꺼내서 파싱
2. 케이뱅크 메타 기준에 맞게 Dto 변경(transform, 필드명 및 타입 변환)
3. 적재(upsert)

일단 현재 케이뱅크 MSA 환경에서는 이게 최선인듯 한데..
1. topic안에 있는 json을 꺼내서 파싱
2. 케이뱅크 메타 기준에 맞게 Dto 변경(transform, 필드명 및 타입 변환)
3. json 리스트를 파일 형태로 저장
4. 후속 배치가 파일을 읽어서 적재(upsert)
이게 더 낫지 않을까?? 대량 데이터를 적재하는것(이걸 데이터서비스팀에서 안하고 여기서 할까라는 의문은 들지만 색다른 과제가 재미있을것이라는 원영적 사고 중)이 처음이다 보니 쉽지 않음.
  - 주식데이터 수집 파이프라인을 내가 구축하고 검증도 내가함
    - 수집방법 데이터 모델링 수집시기주기 대외작업 검증…
    - 해놓으면 카프카에서 데이터서비스팀이 긁어감
  - 근데 투자온도 산출하는 모델 만드는건 데이터서비스팀에서 함
