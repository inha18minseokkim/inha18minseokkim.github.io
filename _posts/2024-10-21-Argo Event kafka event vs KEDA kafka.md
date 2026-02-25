---
title: Argo Event kafka event vs KEDA kafka
date: 2024-10-21
tags:
  - argo
  - KEDA
  - MSA
  - EDA
---
KEDA를 사용해서 Kafka Lag 를 처리하는 방식에 대해 고민중이었는데,
 Argo Event를 사용해서 Lag가 쌓임 > Argo workflow를 하나 띄워서 데이터를 consume 하고 처리 적재 하면 되지 않을까 라는 생각을 했음.

```yaml
apiVersion: argoproj.io/v1alpha1
kind: EventBus
metadata:
  name: default
spec:
  nats:  # NATS is a lightweight, high-performance messaging system
    native:
      replicas: 3  # Number of replicas for the NATS service
```


```yaml
apiVersion: argoproj.io/v1alpha1
kind: EventSource
metadata:
  name: listed-stock-etl-kafka
spec:
  kafka:
    ListedStockPrice:
      url: 125.176.39.143:29092
      topic: ListedStockPrice
#      partition: "0"
      connectionBackoff:
        duration: 10s
        steps: 5
      consumerGroup:
        groupName: ListedStockPrice1
        oldest: false
      lagThreshold: 100
```


```yaml
apiVersion: argoproj.io/v1alpha1
kind: Sensor
metadata:
  name: listed-stock-kafka-sensor
spec:
  dependencies:
    - name: ListedStockPrice
      eventSourceName: listed-stock-etl-kafka
      eventName: ListedStockPrice
    - name: ListedStockConsolidatedAnnual
      eventSourceName: listed-stock-etl-kafka
      eventName: ListedStockConsolidatedAnnual
  triggers:
    - template:
        name: listed-stock-kafka-trigger
        argoWorkflow:
          operation: submit
          source:
            resource:
              apiVersion: argoproj.io/v1alpha1
              kind: Workflow
              metadata:
                generateName: listed-stock-sub-job-
                annotations:
                  job-name: "{{trigger.event.source}}"
              spec:
                entrypoint: process-kafka-message
                arguments:
                  parameters:
                    - name: kafkaTopic
                      value: "{{trigger.event.source}}"
                templates:
                  - name: process-kafka-message
                    steps:
                      - - name: "{{trigger.event.source}}"
                          template: workflow-one
                  - name: workflow-one
                    container:
                      image: muyaho/listed-stock-sub-job:latest
                      env:
                        - name: JOB_NAME
                          value: "{{trigger.event.source}}"

```

이런식으로 ListedStockPrice 토픽에 Lag가 쌓이면 이벤트가 발생해서 workflow가 뜰 줄 알았는데,

```yaml
home@homeui-Macmini ~ % kafka-consumer-groups  --bootstrap-server localhost:29092 --group ListedStockPrice1 --describe

GROUP             TOPIC            PARTITION  CURRENT-OFFSET  LOG-END-OFFSET  LAG             CONSUMER-ID                                 HOST
  CLIENT-ID
ListedStockPrice1 ListedStockPrice 0          925809          925809          0               sarama-c2e7bafa-6d80-4138-9632-ca916054c264 /192.168.65.1   sarama%
home@homeui-Macmini ~ %
```

workflow가 뜨지 않고 그냥 LAG가 0으로 되었다.
그러면서 sarami였나 하는 consumer 인스턴스가 consume 하고 있었음.

알고보니 KEDA 와는 결이 다른게,, KEDA는 컨슈머 그룹 상태를 모니터링 하다가 LAG가 일정 임계치 넘어가면 HPA 실행하는거고 얜 kafka topic 내용이 이벤트라 그 이벤트를 consume 해서 발생시키겠다는 마인드인것.

…
추가) 2024.12.20. 그러고 나서 깨달음
아 컨슈머 그룹을 새로 만들면 되는구나..? 다음에 계속..

