---
title: "Python + Argo Event (결과 : 원하는대로 안됨)"
date: 2025-01-14
tags: [미지정]
category: 기술
---

한 4달전쯤에 KEDA 대신에 Argo Event를 사용하여 이벤트 기반으로 파드를 기동시켜보기로 했지만, KEDA는 컨슈머그룹상의 LAG를 이벤트로 보는 반면, Argo Event의 EventSource는 레코드 자체를 이벤트로 consume 하여 서로 다른 목적임을 확인하였다.
  - 재정리) KEDA(Kubernetes Event Driven Autoscaler)의 문제는 1 : n 을 지원하지 않음.
    - 즉 trigger가 kafka topic 일때 N개의 토픽중 하나라도 조건을 만족하면(lagThreshold) HPA 되도록 설정은 할 수 있지만, 그 토픽에 관한 메타정보를 넘겨받는 구조는 아니다(workload manipulation을 지원하지 않는다는 KEDA 개발자의 친절한 피셜)
    - 파일을 n개 만들면 되긴 하지만 현재 yml 리소스 배포 정책상 1프로젝트 1파일이라 별도의 Kubernetes Object yml 파일을 배포할 수 있는 방법이 없다.
그러다가 4달뒤 지금 갑자기 아이디어가 생각났다.
“컨슈머 그룹이 다르면 되잖아”
즉 이벤트를 발생시키는 컨슈머그룹의 오프셋과 실제로 데이터를 저장하는 컨슈머그룹의 오프셋을 다르게 가져가면 된다는 생각으로

다시 시작

![](https://prod-files-secure.s3.us-west-2.amazonaws.com/c38aebd7-2834-4fac-b2fc-a2f0c17ce81d/6f6d6eb6-ea65-4170-8968-47b31a6a4e2e/image.png)





## EventSource


```yaml
apiVersion: argoproj.io/v1alpha1
kind: EventSource
metadata:
  name: listed-stock-etl-kafka
spec:
  kafka:
    ListedStockPrice:
      url: 카프카브로커:29092
      topic: ListedStockPrice
      connectionBackoff:
        duration: 10s
        steps: 5
      consumerGroup:
        groupName: ListedStockPrice1
        oldest: false
      lagThreshold: 100
    ListedStockConsolidatedAnnual:
      url: 카프카브로커:29092
      topic: ListedStockConsolidatedAnnual
      consumerGroup:
        groupName: ListedStockConsolidatedAnnual1
      lagThreshold: 100
```

Argo Event에서 어떤 이벤트를 발생 시키는 소스를 설정한다. 즉 위 두 토픽에서 컨슈머그룹 기준으로 Lag 가 100개 이상이면 해당 이벤트가 발생한다.

## Sensor


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

우선 개발의 편의를 위해 토픽이름 = 이벤트이름  으로 만들어놨다.
eventsource를 바라보고 있다가 (여기서는 kafka topic’s lagthreshold) 조건이 충족하는 경우 sensor를 누르게 되는데, KEDA와는 다르게 어떤 이벤트에 의해서 트리거가 눌렸는지에 대한 메타정보가 있다.(즉 여기서는 어떤 토픽에 의해 버튼이 눌렸는지)
그래서 실행을 해본 결과

### Lag가 천개면 파드가 천개 생성되었다(덕분에 맥미니를 재기동했다 ㅜㅜ)



## RateLimit 할 수는 없을까?



```java
      consumerGroup:
        groupName: ListedStockPrice
        oldest: false
      limitEventsPerSecond: 1
```

이런식으로 Trigger에 rateLimit을 걸 수 있다(bitBucket). 1초에 1개씩만 RateLimit를 하면 100초에 1000개의 토픽이 발행되었을 때, 1번의 이벤트가 발행되는것이 아니라(Filter) 시간이 얼마나 걸리든 1000개의 이벤트가 모두 발행되는 형식이다(RateLimit)

이벤트 소스에서 웹훅과 카프카가 같이 있는것을 봤을 때 알아차려야 했다.
 
