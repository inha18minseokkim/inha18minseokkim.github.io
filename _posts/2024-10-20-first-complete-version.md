---
title: 1차 완성본
date: 2024-10-20
tags:
  - argo
  - workflow
  - CI/CD
  - 인프라
  - job
  - MSA
category:
  - 실무경험
  - MSA표준
---



```java
@RequiredArgsConstructor
@Slf4j
@Component
@ConditionalOnProperty(name = "JOB_NAME", havingValue = "listedStockPrice")
public class ListedStockPriceProducer implements ApplicationRunner {
    private final KafkaTemplate<String,Object> kafkaTemplate;
    private final ListedStockRepository listedStockRepository;
    private final ObjectMapper objectMapper;
    private final WebClient.Builder webClientBuilder;
    @Value("${INPUT_ARRAY[0]}")
    private String startDate;
    @Value("${INPUT_ARRAY[1]}")
    private String endDate;
    @Value("${INPUT_ARRAY[2]:ListedStockPrice}")
    private String targetTopic;
    @Value("${INPUT_ARRAY[3]:100}")
    private Integer pageSize;
    
```

로컬 테스트용 application.properties

```yaml
spring.application.name=listed-stock-pub-job
spring.main.web-application-type=none

server.port=8835

EXTERNAL_HOST=localhost:9092
JOB_NAME=listedStockPrice
INPUT_ARRAY[0]=20230101
INPUT_ARRAY[1]=20231231
INPUT_ARRAY[2]=ListedStockPrice
#START_DATE=20240101
#END_DATE=20241018
```

argo-workflow.yaml

```yaml
#job-name을 받아서 step 이름이랑 안에서 도커 이미지 파라미터 물고 실행할 수 있게끔 만듬
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  generateName: listed-stock-job-
  annotations:
    job-name: "{{workflow.parameters.job-name}}"
spec:
  entrypoint: main
  arguments:
    parameters:
      - name: job-name #디폴트 없음. 파라미터 입력안하면 무조건 실행하지마
      - name: input-array
  templates:
    - name: main
      steps:
        - - name: "{{workflow.parameters.job-name}}"
            template: workflow-one
    - name: workflow-one
      container:
        image: muyaho/listed-stock-pub-job:latest
        env:
          - name: JOB_NAME
            value: "{{workflow.parameters.job-name}}"
          - name: INPUT_ARRAY
            value: "{{workflow.parameters.input-array}}"
```

실행 방법 : array에 문자열 포맷으로 그대로 입력

```bash
argo submit listed-stock-job-array-input.yaml -p job-name=listedStockPrice -p input-array='["20230101","20231231","ListedStockPrice"]'
```

그러므로 jflow에서 입력할 때 input-array를 저런식으로 입력하긴해야함..

아무튼 잘 돎. jflow 연동하려면 이런식으로 짜야할 듯.

![](/assets/images/Pasted%20image%2020260228171330_08db0d59.png)

남은 과제 : 로깅, 뭐 이것도 할 수는 있으니깐 괜찮음
