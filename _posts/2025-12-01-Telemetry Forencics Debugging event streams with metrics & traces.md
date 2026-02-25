---
title: "Telemetry Forencics: Debugging event streams with metrics & traces"
date: 2025-12-01
tags: [미지정]
category: 기타
---
buildup session
1
dynamodb > sqs 넣을 때
aws sqs 크기는 1메가 넘어가면 오류남
이제 모든 증거를 수집하고 원인을 이해했으니, 근본 원인을 이해하고 이벤트 기반 아키텍처에서 이러한 유형의 오류가 발생하는 이유를 알아보겠습니다.
**서비스 할당량 이해**
근본 원인은 이벤트 처리 파이프라인 전반의 서비스 한도 불일치에 있습니다.

| Service | Maximum Message/Item Size | Notes |
| --- | --- | --- |
| **DynamoDB Item** | 400 KB | Can store large items |
| **DynamoDB Streams** | Inherits DynamoDB quotas | Can contain 400KB records |
| **EventBridge Pipes** | Inherits target quota | Can transform/amplify payload |
| **SQS Standard Queue** | 1 MiB (1,048,576 bytes) | **Bottleneck** when combined with transformation |
| **SQS FIFO Queue** | 1 MiB (1,048,576 bytes) | Same quota as standard |

**중요한 문제:** EventBridge Pipe의 입력 변환기가 페이로드 데이터를 복제하여 약 4배 증폭을 발생시킵니다. 300KB DynamoDB 항목이 1.2MB 변환된 메시지로 변환되어 SQS의 1MiB 할당량을 초과합니다.
**문제의 사슬**
우리 시나리오에서는 정확히 무슨 일이 일어나는지 살펴보겠습니다.

![](https://static.us-east-1.prod.workshops.aws/104f493c-c8a1-46cf-adfe-b266a36d819a/static/images/silent-disappear/flow.png?Key-Pair-Id=K36Q2WVO3JP7QD&Policy=eyJTdGF0ZW1lbnQiOlt7IlJlc291cmNlIjoiaHR0cHM6Ly9zdGF0aWMudXMtZWFzdC0xLnByb2Qud29ya3Nob3BzLmF3cy8xMDRmNDkzYy1jOGExLTQ2Y2YtYWRmZS1iMjY2YTM2ZDgxOWEvKiIsIkNvbmRpdGlvbiI6eyJEYXRlTGVzc1RoYW4iOnsiQVdTOkVwb2NoVGltZSI6MTc2NTIxMDcxNX19fV19&Signature=RMkeTx7HtcBriew2KRStigCjJrgvtGBN8O3OQLbY2WGFpaLlJPKjCzp6n%7EPg-%7EE1PjZILxnej70Ndf-35%7EKTvQ4nST-S9mYQV6Pw4TH9OFb70b9AR148VFQ9lkxJ31Ak38u4odS%7EZyX2ayB5C4uQ2mdx1VMUvlZBUqYl1TAz6mQLdikC1hNndXQQnXh0sFiqcil0IruI5bFj-nQo2%7E2Bh7uszjlfY%7Ei7rr8AYMP2hVXwLBtqCiWQMQSVZkhPZARhCendujGRKFHZFIV%7ErFtFWGzz9AJOKY4jR5pn7BTuH2aT-LpNBXtRtWZycQrJdAM1CfZ0%7EY5Kj0o9DenMev0qyg__)

EventBridge Pipes에는 입력을 변환하고 보강하는 로직이 있습니다. 작은 페이로드에서는 작동할 수 있지만, 이미 최대 크기에 가까운 페이로드에서는 작동하지 않습니다.
**솔루션 전략**
**전략 1: 페이로드 변환**
대용량 페이로드를 필수 데이터만 포함하도록 변환:

```kotlin
{
  "productId": "PROD-004",
  "eventType": "UPDATE",
  "timestamp": "2024-01-15T10:30:00Z",
  "changesSummary": "description, specifications",
  "detailsLocation": "s3://bucket/details/PROD-004.json"
}
```

**전략 2: 참조 패턴**
대용량 데이터를 외부에 저장하고 참조를 전달합니다.

```kotlin
{
  "type": "large_payload_reference",
  "s3_bucket": "large-payloads",
  "s3_key": "products/2024/01/15/PROD-004.json",
  "original_size_bytes": 358400,
  "product_id": "PROD-004"
}
```

**전략 3: 서비스 선택**
탑재량 요구 사항에 따라 서비스를 선택하세요.
**예를 들어, 페이로드가 256KB를** 초과하지 않는 경우 SNS, EventBridge를 사용할 수 있습니다 . 또한 Amazon Kinesis Data Streams를 사용할 수 있습니다. Kinesis Data Streams는 이제 최대 [10MiB 의 레코드 크기를 지원합니다. ](https://aws.amazon.com/blogs/big-data/amazon-kinesis-data-streams-now-supports-10x-larger-record-sizes-simplifying-real-time-data-processing/)기존 1MiB 할당량보다 10배 증가한 1MiB 용량으로, 별도의 처리 로직 없이도 더 큰 페이로드를 허용하여 데이터 파이프라인을 간소화합니다. SQS는 최대 1MiB의 페이로드 크기를 지원합니다.
**마지막 생각**
이는 안정적인 이벤트 기반 시스템 구축의 중요한 측면, 즉 서비스 할당량을 이해하고 계획하는 것을 보여주었습니다. 여러분이 해결한 페이로드 크기 문제는 겉보기에 단순한 아키텍처에도 미묘한 장애 모드가 존재할 수 있음을 보여주는 한 가지 예일 뿐입니다.
주요 내용은 다음과 같습니다.
1. **방어적으로 설계하세요**
  - - 할당량이 충족될 것이라고 가정하세요
2. **포괄적으로 모니터링하세요**
  - - 침묵 속의 실패가 가장 위험합니다.
3. **현실적으로 테스트하세요**
  - - 실제 운영과 유사한 데이터와 시나리오를 사용하세요
4. **성장 계획**
  - - 오늘날의 작은 탑재물은 내일의 큰 탑재물이 될 수 있습니다.
이러한 원칙을 적용하면 예상치 못한 상황을 원활하게 처리할 수 있는 더욱 견고하고 안정적인 이벤트 기반 시스템을 구축할 수 있습니다.
**관련 자료**
- [EventBridge 파이프 문서](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-pipes.html)
- [SQS 메시지 크기](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-message-metadata.html)
- [DynamoDB 스트림](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Streams.html)
- [Lambda를 EventBridge 파이프 강화로 사용](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-pipes-event-enrichment.html)
- [AWS 서비스 할당량](https://docs.aws.amazon.com/general/latest/gr/aws-service-information.html)
2
dynamo wcu 가 2밖에 안되어서 kinesis> dynamo 갈 때 힘들어함
**이 사례는 가장 느린 구성 요소가 전체 처리량을 결정하는** 클래식 스트리밍 아키텍처 패턴을 보여줍니다 .
아니면 그냥 온디맨드 모드 써
이제 모든 증거를 분석했으니 근본 원인을 파악하고 해결책을 구현해 보겠습니다.
**근본 원인**
조사 결과 근본적인 문제인 **DynamoDB 쓰기 용량 병목 현상이 밝혀졌습니다.**
**문제의 사슬**
우리 시스템에서 정확히 무슨 일이 일어나고 있는지 알려드리겠습니다.
시스템에 초당 500건의 트랜잭션이 Kinesis 스트림으로 전송되는 대용량 입력으로 시작되는 연쇄적 장애가 발생하고 있습니다. 이후 쓰기 용량 단위(WCU)가 2개로 구성된 DynamoDB 테이블의 쓰기 용량이 부족하여 심각한 병목 현상이 발생합니다. 이로 인해 시스템이 초당 500건의 레코드를 쓰려고 하지만 초당 2건의 쓰기만 처리할 수 있는 심각한 용량 불일치가 발생합니다. 이로 인해 DynamoDB 속도 조절로 인해 Lambda 함수 지연이 발생하는 연쇄적 현상이 발생하고, 이는 Kinesis 스트림에 처리 백로그를 생성하여 전체 파이프라인으로 확산됩니다.
**숫자 이해하기**

| 요소 | 용량 | 수요 | 결과 |
| --- | --- | --- | --- |
| 키네시스 스트림 | 2개의 샤드(초당 2000개 레코드) | 500TPS | ✅ 충분함 |
| 람다 함수 | 1000개의 동시 실행 | ~50명 동시 접속 | ✅ 충분함 |
| DynamoDB 테이블 | 2 WCU(2개 쓰기/초) | 500TPS | ❌ **병목 현상** |

**수정**
작업 부하에 맞게 DynamoDB 테이블의 쓰기 용량 단위를 늘립니다.
**1단계: DynamoDB 용량 업데이트**
1. [DynamoDB 콘솔을](https://console.aws.amazon.com/dynamodb/) 엽니다
2. 탐색 창에서 **테이블을 선택하세요**
3. **case2-trade-table** 테이블을 선택하세요
4. 읽기/쓰기 용량 섹션에서 **편집을**
  - 클릭하여 용량을 편집합니다.
5. **쓰기 용량 단위(WCU)를 2**
  - 에서 **50** 으로 업데이트
6. **변경 사항 저장을** 선택하세요
**메모**
수정 사항을 적용한 후 지표가 안정화될 때까지 몇 분 정도 기다리세요. 처리량이 증가하여 정상적인 운영이 재개되면 처리 지연이 해결될 것입니다.
**2단계: 수정 확인**
다음 측정 항목을 모니터링하여 수정 사항이 작동하는지 확인하세요.

```kotlin
# Check Iterator Age returns to normal
aws cloudwatch get-metric-statistics --namespace AWS/Lambda --metric-name IteratorAge --dimensions Name=FunctionName,Value=case2-trade-processor-function --start-time $(date -u -d '10 minutes ago' +%Y-%m-%dT%H:%M:%S) --end-time $(date -u +%Y-%m-%dT%H:%M:%S) --period 60 --statistics Maximum --region us-west-2 --query 'Datapoints | sort_by(@, &Timestamp) | reverse(@) | [0:15].[Timestamp,Maximum]' --output table
```


**예상 결과:**
- 반복자 연령이 1000ms 이하로 떨어집니다.
- DynamoDB 제한 이벤트 중지
- 람다 지속 시간이 정상 수준으로 감소합니다.
- 처리 백로그가 지워졌습니다

![](https://static.us-east-1.prod.workshops.aws/104f493c-c8a1-46cf-adfe-b266a36d819a/static/images/latency-forensics/Resolved.png?Key-Pair-Id=K36Q2WVO3JP7QD&Policy=eyJTdGF0ZW1lbnQiOlt7IlJlc291cmNlIjoiaHR0cHM6Ly9zdGF0aWMudXMtZWFzdC0xLnByb2Qud29ya3Nob3BzLmF3cy8xMDRmNDkzYy1jOGExLTQ2Y2YtYWRmZS1iMjY2YTM2ZDgxOWEvKiIsIkNvbmRpdGlvbiI6eyJEYXRlTGVzc1RoYW4iOnsiQVdTOkVwb2NoVGltZSI6MTc2NTIxMDcxNX19fV19&Signature=RMkeTx7HtcBriew2KRStigCjJrgvtGBN8O3OQLbY2WGFpaLlJPKjCzp6n%7EPg-%7EE1PjZILxnej70Ndf-35%7EKTvQ4nST-S9mYQV6Pw4TH9OFb70b9AR148VFQ9lkxJ31Ak38u4odS%7EZyX2ayB5C4uQ2mdx1VMUvlZBUqYl1TAz6mQLdikC1hNndXQQnXh0sFiqcil0IruI5bFj-nQo2%7E2Bh7uszjlfY%7Ei7rr8AYMP2hVXwLBtqCiWQMQSVZkhPZARhCendujGRKFHZFIV%7ErFtFWGzz9AJOKY4jR5pn7BTuH2aT-LpNBXtRtWZycQrJdAM1CfZ0%7EY5Kj0o9DenMev0qyg__)

이 그래프에서 볼 수 있듯이 반복 연령은 감소 추세를 보이고 있으며 람다 처리 기간도 단축되었습니다.
**스트리밍 파이프라인 병목 현상 이해**
**이 사례는 가장 느린 구성 요소가 전체 처리량을 결정하는** 클래식 스트리밍 아키텍처 패턴을 보여줍니다 .
**용량 계획 공식**
스트리밍 파이프라인의 경우 각 구성 요소가 최대 부하를 처리할 수 있는지 확인하세요.
`Required Capacity = Peak TPS × Safety Margin × Processing Time`
**예:**
- 최대 TPS: 500
- 안전 마진: 1.2(20% 버퍼)
- 처리 시간: 1초
- **필요한 DynamoDB WCU**
  - : 500 × 1.2 = 600 WCU
**주요 학습 내용**
**1. 전체 파이프라인 모니터링**
분산 시스템에서 효과적인 문제 해결을 위해서는 증상이 처음 나타나는 위치에만 집중하기보다는 모든 구성 요소를 포괄적으로 모니터링해야 합니다. 성능 문제를 조사할 때 반복자 수명(Iterator Age)과 같은 지표는 근본 원인 자체보다는 더 심각한 문제의 징후일 수 있다는 점을 이해하는 것이 중요합니다. 체계적인 접근 방식은 아키텍처 전체의 데이터 흐름을 추적하여 병목 현상을 파악하는 것입니다. 다운스트림 구성 요소의 문제는 업스트림 서비스의 성능 저하로 나타날 수 있기 때문입니다. 이러한 전체적인 모니터링 방식은 문제의 영향 지점부터 실제 원인까지 추적하여 근본적인 문제가 지속되는 동안 증상을 치료하지 못하도록 방지합니다.
**2. 용량 계획이 중요합니다**
적절한 용량 계획은 안정적인 스트리밍 아키텍처의 기반을 형성하며, 평균적인 트래픽 패턴보다는 최대 워크로드 시나리오를 처리할 수 있도록 모든 구성 요소의 크기를 조정해야 합니다. 이 계획 프로세스는 버스트 용량 요구 사항을 고려하고 트래픽 변동에 동적으로 대응할 수 있는 자동 확장 메커니즘을 구현해야 합니다. 또한, 효과적인 용량 계획에는 적절한 안전 마진을 설정하고 용량 사용 패턴을 정기적으로 검토하여 향후 증가 및 예상치 못한 트래픽 급증을 예측하는 것이 포함됩니다. 이러한 포괄적인 접근 방식이 없다면, 아무리 잘 설계된 시스템이라도 가장 취약한 구성 요소의 용량을 초과하는 트래픽 볼륨에 직면하면 장애가 발생하여 전체 파이프라인에 걸쳐 연쇄적인 장애가 발생할 수 있습니다.
**3. 서비스 할당량 이해**
각 AWS 서비스에는 스트리밍 아키텍처를 설계할 때 고려해야 할 특정 처리량 특성과 할당량이 있습니다. Amazon DynamoDB에서는 [온디맨드 모드 와 ](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/capacity-mode.html#capacity-mode-on-demand)및 [프로비저닝 모드 ](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/capacity-mode.html#capacity-mode-provisioned)다양한 워크로드 요구 사항을 충족하기 위해 테이블을 구성합니다. 기본적으로 Lambda는 AWS 리전의 모든 함수에 대해 총 1,000개의 동시 실행 할당량을 계정에 제공합니다. 함수가 더 많은 요청을 수신함에 따라 Lambda는 계정의 동시 실행 할당량(소프트 할당량)에 도달할 때까지 실행 환경 수를 자동으로 확장합니다.
**4. 연쇄 효과**
분산 아키텍처에서 성능 병목 현상은 한 구성 요소의 제약 조건이 전체 시스템으로 확산되는 도미노 효과를 발생시켜, 전체 처리량에 심각한 영향을 미칠 수 있는 업스트림 백업을 유발합니다. 느린 구성 요소 하나에 과부하가 걸리면 파이프라인의 모든 선행 구성 요소가 대기열에 들어가 대기하게 되어, 전체 시스템 성능이 가장 약한 연결의 성능과 거의 같아집니다. 스트리밍 파이프라인의 이러한 상호 연결성 때문에 개별 구성 요소 지표에만 집중하기보다는 엔드 투 엔드 지연 시간을 모니터링하는 것이 필수적입니다. 지역적인 성능 문제가 수집부터 최종 처리까지 전체 데이터 흐름을 검토할 때만 드러나는 시스템 전체의 문제를 가릴 수 있기 때문입니다.
**예방 전략**
**1. 자동 크기 조정**
이 시나리오에서는 DynamoDB 자동 크기 조정을 활성화하여 트래픽 급증을 처리할 수 있습니다.
`1
2
3
4
5
6
7
8
9
10
{
  "TableName": "TABLE_NAME",
  "BillingMode": "PROVISIONED",
  "ProvisionedThroughput": {
    "ReadCapacityUnits": 5,
    "WriteCapacityUnits": 100
  },
  "AutoScalingEnabled": true,
  "TargetUtilization": 70
}`
고려해 볼 만한 대안은 DynamoDB 온디맨드 모드를 사용하는 것입니다. 온디맨드 모드는 대부분의 DynamoDB 워크로드에 기본으로 권장되는 처리량 옵션입니다. DynamoDB는 처리량 관리의 모든 측면을 처리하며, 용량 계획 없이도 가장 까다로운 워크로드를 수용할 수 있도록 자동으로 확장됩니다. 자세한 내용은 [여기를 참조하세요.](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/on-demand-capacity-mode.html)
**2. 모니터링 및 알림**
다음에 대한 CloudWatch 알람을 설정합니다.
- 반복자 연령 > 5000ms
- DynamoDB 제한 이벤트
- 람다 지속시간이 증가합니다
**3. 부하 테스트**
고객에게 영향을 미치기 전에 용량 문제를 파악하기 위해 실제 운영 환경과 유사한 데이터로 정기적으로 테스트를 실시합니다.
**결론**
이 지연 시간 포렌식 사례는 겉보기에 정상인 시스템이 어떻게 심각한 성능 병목 현상을 감출 수 있는지 보여줍니다. 핵심은 **스트리밍 아키텍처에서 가장 느린 구성 요소의 속도에 따라 성능이 결정된다는** 것입니다 .
증상(높은 반복자 연령)부터 근본 원인(DynamoDB 제한)까지 체계적으로 증거를 추적하여 규정 위반 및 상당한 재정적 벌금으로 이어질 수 있는 용량 계획 문제를 식별하고 해결했습니다.
**사건 상태:** 해결됨 ✅
**관련 자료**
- [DynamoDB 자동 확장](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/AutoScaling.html)
- [람다 이벤트 소스 매핑](https://docs.aws.amazon.com/lambda/latest/dg/invocation-eventsourcemapping.html)
- [Kinesis 데이터 스트림 모니터링](https://docs.aws.amazon.com/kinesis/latest/dev/monitoring.html)
- [스트리밍 애플리케이션을 위한 CloudWatch 메트릭](https://docs.aws.amazon.com/kinesis/latest/dev/monitoring-with-cloudwatch.html)

3
[시간 초과 관계는 Lambda 시간 초과가 실제 처리 시간보다 크거나 같아야 하며 SQS 가시성 시간 초과 가이드](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-visibility-timeout.html) 에 설명된 AWS 모범 사례에 따라 서버리스 아키텍처에서 매우 중요합니다.[ ](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-visibility-timeout.html)[중복 처리를 방지하기 위해 SQS 가시성 제한 시간은 Lambda 제한 시간의 최소 6배여야 합니다. 권장되는 구성 설정에는 Lambda 제한 시간을 처리 시간과 버퍼 시간( Lambda 구성 설명서](https://docs.aws.amazon.com/lambda/latest/dg/configuration-function-common.html) 참조)을 더한 값 이상으로 설정하는 것이 포함됩니다.[ ](https://docs.aws.amazon.com/lambda/latest/dg/configuration-function-common.html)), 비즈니스 요구 사항에 맞춰 처리 시간을 최적화하고, 가시성 제한 시간이 6배의 Lambda 제한 시간 규칙을 따르도록 보장합니다. 예방 전략에는 현실적인 처리 시간으로 테스트하고, 부하가 걸리는 상황에서 제한 시간 구성을 검증하고, [AWS Lambda 모범 사례 에서 권장하는 대로 Lambda 제한 시간 초과에 대한 CloudWatch 알람을 설정하는 것이 포함되어야 합니다. ](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)그리고 SQS 메시지 재시도 횟수를 모니터링하여 시간 초과 관련 문제를 조기에 감지합니다.

이제 원인을 파악했으니 중복 처리 문제에 대한 해결책을 구현해 보겠습니다.
**근본 원인 요약**
Lambda가 시간 초과되면 SQS는 이를 실패로 간주하고 메시지를 다시 시도하여 중복 처리가 발생합니다.
**문제** : 람다 타임아웃(30초) < 처리 시간(40초) = 중복 처리!
**고치다**
이 문제는 두 가지 방법으로 해결할 수 있습니다.
**옵션 1: 람다 처리 기간 늘리기(시간 초과 증가)**
모든 처리를 완료하기 위한 여유 공간을 확보하기 위해 람다 타임아웃을 늘려야 할 수도 있습니다.
1. [AWS Lambda 콘솔을](https://console.aws.amazon.com/lambda/) 엽니다
  - .
2. 탐색 창에서 **함수를case3-func-orders-processor**
  - 선택한 다음
  - 라는 함수를 선택합니다 .
3. **구성편집을**
  - 탭을 선택 하고 일반 구성에서
  - 선택합니다 .
4. 제한 시간을 `60`**저장합니다**
  - 초로 업데이트하고 변경 사항을
  - .
**옵션 2: 람다 함수에서 sleep 코드를 삭제합니다.**
Lambda 함수의 슬립 코드가 실수로 추가된 경우, Lambda 함수에 슬립 코드가 있는 것은 안티 패턴이므로 이를 제거할 수 있습니다.
1. [AWS Lambda 콘솔을](https://console.aws.amazon.com/lambda/) 엽니다
  - .
2. 탐색 창에서 **함수를case3-func-orders-processor**
  - 선택한 다음
  - 라는 함수를 선택합니다 .
3. **코드**
  - 탭을 선택하세요 .
4. 36번째 줄과 37번째 줄을 삭제하고 **배포를**
  - 선택합니다 .
**수정 사항을 테스트하세요**
1. 다음 명령을 Cloudshell에 복사하여 붙여넣으세요.
`1
aws lambda invoke --function-name case3-sqs-test-message-sender response.json`
1. Lambda 함수 로그 확인
`1
2
3
4
LOG_NAME=$(aws cloudformation describe-stack-resource --stack-name a-3-double-trouble --logical-resource-id MessageProcessorFunction --query "StackResourceDetail.PhysicalResourceId" --output text)

# Query the logs
aws logs tail /aws/lambda/${LOG_NAME} --since 10m`
이제 로그에 "주문 order-123456789가 완료로 표시됨"이라는 메시지가 표시됩니다.
1. DynamoDB 테이블을 확인하세요
`1
2
3
DDB_TABLE=$(aws cloudformation describe-stack-resource --stack-name a-3-double-trouble --logical-resource-id ProcessingTable --query "StackResourceDetail.PhysicalResourceId" --output text)

aws dynamodb scan --table-name $DDB_TABLE`
수정 사항이 적용된 후에는 DynamoDB 테이블에 COMPLETED 상태로 새 레코드가 표시됩니다.
**수정 후 예상 결과**
Lambda 함수가 이제 30초의 제한 시간 내에 성공적으로 완료되므로, 시간 초과 없이 주문이 한 번만 처리되는 단일 처리 시도를 관찰해야 합니다. 메시지는 재시도 없이 성공적으로 처리되므로, 시간 초과-재시도 주기로 인해 발생하던 중복 처리 문제가 해결됩니다.
**주요 학습 내용**
[시간 초과 관계는 Lambda 시간 초과가 실제 처리 시간보다 크거나 같아야 하며 SQS 가시성 시간 초과 가이드](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-visibility-timeout.html) 에 설명된 AWS 모범 사례에 따라 서버리스 아키텍처에서 매우 중요합니다.[ ](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-visibility-timeout.html)[중복 처리를 방지하기 위해 SQS 가시성 제한 시간은 Lambda 제한 시간의 최소 6배여야 합니다. 권장되는 구성 설정에는 Lambda 제한 시간을 처리 시간과 버퍼 시간( Lambda 구성 설명서](https://docs.aws.amazon.com/lambda/latest/dg/configuration-function-common.html) 참조)을 더한 값 이상으로 설정하는 것이 포함됩니다.[ ](https://docs.aws.amazon.com/lambda/latest/dg/configuration-function-common.html)), 비즈니스 요구 사항에 맞춰 처리 시간을 최적화하고, 가시성 제한 시간이 6배의 Lambda 제한 시간 규칙을 따르도록 보장합니다. 예방 전략에는 현실적인 처리 시간으로 테스트하고, 부하가 걸리는 상황에서 제한 시간 구성을 검증하고, [AWS Lambda 모범 사례 에서 권장하는 대로 Lambda 제한 시간 초과에 대한 CloudWatch 알람을 설정하는 것이 포함되어야 합니다. ](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)그리고 SQS 메시지 재시도 횟수를 모니터링하여 시간 초과 관련 문제를 조기에 감지합니다.
**사건 상태:** 해결됨 ✅
**관련 자료**
- [SQS 가시성 시간 초과](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-visibility-timeout.html)
- [람다 타임아웃 구성](https://docs.aws.amazon.com/lambda/latest/dg/configuration-function-common.html)
- [AWS Lambda 모범 사례](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)

4
**데이터 구조 이해**
이 조사에서 가장 중요한 교훈은 작업 중인 데이터 구조를 깊이 이해하는 것의 중요성입니다. OFD 메시지는 실패한 레코드를 단순히 일대일로 표현하는 것이 아니라, 단일 배치에서 여러 실패한 레코드를 저장할 수 있는 컨테이너입니다. 이러한 아키텍처 세부 사항은 AWS 관점에서는 논리적이지만, 메시지 경계에 대한 가정을 하는 개발자에게는 큰 걸림돌이 될 수 있습니다. 항상 실제 페이로드 구조를 검토하고 선택한 AWS 서비스가 데이터를 어떻게 배치하고 그룹화하는지 이해하는 데 시간을 투자하십시오.
이제 근본 원인을 파악했으니, 완전한 해결책을 이해하고 수정 사항을 구현해 보겠습니다.
**근본 원인 분석**
미스터리는 데이터가 누락된 것이 아니라 **해석이 누락된** 것이었습니다 . 근본적인 문제는 심각한 오해에 있습니다. **메시지 경계 ≠ 레코드 경계입니다** .
**실패 시 대상 동작 이해**
이 문제의 근본 원인은 AWS Lambda가 Kinesis 레코드를 처리하고 오류를 처리하는 방식에서 비롯됩니다. Lambda는 Kinesis에서 처리할 레코드 배치를 수신하면 이를 단일 작업 단위로 처리합니다. 해당 배치 내의 레코드에 처리 오류가 발생하면 전체 배치가 실패한 것으로 간주됩니다. 바로 이 지점에서 복잡성이 시작됩니다.
AWS의 On-Failure Destination(OFD) 메커니즘은 실패한 전체 배치를 나타내는 단일 SQS 메시지를 생성하여 이러한 배치 실패를 포착합니다. 즉, Lambda 함수가 5개의 레코드를 처리하던 중 5개가 모두 실패한 경우, OFD는 5개의 개별 SQS 메시지를 생성하지 않고, 실패한 5개 레코드에 대한 정보가 포함된 하나의 메시지를 생성합니다.
**해결 방법: 적절한 배치 처리**
이 솔루션을 구현하려면 OFD 메시지 처리 방식에 근본적인 변화가 필요합니다. 각 SQS 메시지를 단일 실패 레코드로 처리하는 대신, redrive Lambda는 각 메시지에 개별적인 주의가 필요한 여러 실패 레코드가 포함되어 있을 수 있다는 점을 이해해야 합니다. 즉, OFD 메시지 페이로드를 구문 분석하여 각 실패 레코드를 개별적으로 추출하고 처리함으로써 재처리된 레코드 수와 처리 로직이 실패의 실제 범위를 정확하게 반영하도록 해야 합니다.
**현재 (잘못된) 논리:**
`1
2
3
4
5
def lambda_handler(event, context):
    for record in event['Records']:  # SQS messages
        # Process each SQS message as 1 record
        retry_single_record(record)
        increment_retry_count(1)  # ❌ Wrong count`
**고정된(올바른) 논리:**
`1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
def lambda_handler(event, context):
    for sqs_message in event['Records']:  # SQS messages
        # Parse the OFD message payload
        ofd_payload = json.loads(sqs_message['body'])
        batch_size = ofd_payload['KinesisBatchInfo']['batchSize']
        
        # Process each failed record individually
        for i in range(batch_size):
            try:
                # Simulate fetching and processing a record
                logger.info(f"Fetched and processed record {i + 1} of {batch_size} from failed batch {message_id}")
            
                # Simulate fetching the failed records from Kinesis
                # In reality, this would query Kinesis shards around the failure timestamp
                
                increment_retry_count(1)  # ✅ Correct count per record
                
            except Exception as e:
                logger.error(f"Failed to fetch/process record {i}: {e}")
                break`
**완전한 코드**
**메트릭 수정 이해**
올바른 논리를 사용하면 이제 측정 항목이 올바르게 정렬됩니다.
**수정 전:**

| 대본 | 실패한 기록 | OFD 메시지 | 보고된 재시도 | 실제 재시도 횟수 |
| --- | --- | --- | --- | --- |
| 5개 묶음 실패 | 5 | 1 | 1 | 1 ❌ |
| 3개 배치 실패 | 15 | 3 | 3 | 3 ❌ |

**수정 후:**

| 대본 | 실패한 기록 | OFD 메시지 | 보고된 재시도 | 실제 재시도 횟수 |
| --- | --- | --- | --- | --- |
| 5개 묶음 실패 | 5 | 1 | 5 | 5 ✅ |
| 3개 배치 실패 | 15 | 3 | 15 | 15 ✅ |

**주요 학습 내용**
**데이터 구조 이해**
이 조사에서 가장 중요한 교훈은 작업 중인 데이터 구조를 깊이 이해하는 것의 중요성입니다. OFD 메시지는 실패한 레코드를 단순히 일대일로 표현하는 것이 아니라, 단일 배치에서 여러 실패한 레코드를 저장할 수 있는 컨테이너입니다. 이러한 아키텍처 세부 사항은 AWS 관점에서는 논리적이지만, 메시지 경계에 대한 가정을 하는 개발자에게는 큰 걸림돌이 될 수 있습니다. 항상 실제 페이로드 구조를 검토하고 선택한 AWS 서비스가 데이터를 어떻게 배치하고 그룹화하는지 이해하는 데 시간을 투자하십시오.
**일괄 처리를 위한 설계**
AWS Lambda와 Kinesis의 통합은 본질적으로 배치 중심적이며, 오류 처리 및 재시도 로직은 이러한 현실을 염두에 두고 설계되어야 합니다. 장애는 고립된 상황에서 발생하는 것이 아니라 OFD 메시지로 그룹화된 레코드 배치에서 발생합니다. 재시도 메커니즘은 이러한 배치 구조를 이해하고 적절하게 처리하여 배치 장애와 개별 레코드 처리 간의 변환 과정에서 데이터가 손실되지 않도록 해야 합니다.
**종합적인 모니터링**
서버리스 아키텍처에서 효과적인 모니터링을 위해서는 여러 세부 수준에서 지표를 추적해야 합니다. 메시지 수준 지표는 메시징 인프라의 상태를 알려주고, 레코드 수준 지표는 실제 데이터 처리량을 알려줍니다. 이러한 다양한 지표 유형 간의 불일치에 대한 알림을 설정하면 고객에게 영향을 미치기 전에 이러한 문제를 파악하는 데 도움이 될 수 있습니다. 모니터링의 목표는 데이터 처리 파이프라인의 실제 상황을 정확하게 반영하는 것입니다.
**결론**
이 사례는 서버리스 배치 처리의 미묘하지만 중요한 문제를 보여줍니다. "사라진 레코드"는 실제로 사라진 것이 아니라, 제대로 파싱되지 않은 배치 구조 내부에 숨겨져 있었습니다.
핵심 통찰력: **실패 시 대상은 개별 레코드가 아닌 실패한 레코드의 일괄 처리를 캡처합니다** . 재드라이브 로직에서 메시지 1개당 레코드 1개로 가정하면 전체적인 상황을 파악하지 못하고 중요한 데이터 재시도에 대한 손실이 발생할 수 있습니다.
redrive Lambda에서 적절한 일괄 처리를 구현함으로써 다음이 보장됩니다.
- 모든 실패한 레코드는 실제로 다시 시도됩니다.
- 메트릭은 레코드 수준 처리를 정확하게 반영합니다.
- 안정적인 데이터 처리를 통해 고객 신뢰 유지
**사건 상태:** 해결됨 ✅
**관련 자료**
- [람다 이벤트 소스 매핑 오류 처리](https://docs.aws.amazon.com/lambda/latest/dg/invocation-eventsourcemapping.html#invocation-eventsourcemapping-async)
- [Kinesis Lambda 통합](https://docs.aws.amazon.com/lambda/latest/dg/with-kinesis.html)
- [람다 이벤트 소스로서의 SQS](https://docs.aws.amazon.com/lambda/latest/dg/with-sqs.html)
- [서버리스에서의 오류 처리 패턴](https://aws.amazon.com/blogs/compute/error-handling-patterns-in-amazon-api-gateway-and-aws-lambda/)

5

높은 iterator age > 이거 처리 속도보다 쌓이는속도가 높다는거

이제 핫 파티션 문제를 파악했으니 근본 원인을 살펴보고 수정 방법을 구현해 보겠습니다.
**근본 원인:**
조사 결과 근본적인 문제인 **핫 파티션 문제가 밝혀졌습니다.**
**문제: 잘못된 파티션 키 분배**
이 문제를 일으키는 adv2-func-order-producer 람다 함수 코드를 살펴보겠습니다.
`1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
def send_batch(stream_name, batch_id, records_per_batch):
    """Send a batch of records to create hot partition"""
    records = []
    
    for i in range(records_per_batch):
        record_data = {
            'batch_id': batch_id,
            'record_id': i,
            'timestamp': int(time.time() * 1000),
            'data': f'record_{batch_id}_{i}'
        }
        
        # PROBLEMATIC CODE (lines 23-26)
        records.append({
            'Data': json.dumps(record_data),
            'PartitionKey': 'HOT_PARTITION'  # Force all to same shard
        })`
여기서 문제는 16번째 줄에 있습니다. 모든 레코드가 동일한 파티션 키를 사용하여 `'HOT_PARTITION'`모든 데이터가 단일 샤드에 저장되도록 강제합니다.
**Kinesis 파티셔닝 이해**
Amazon Kinesis Data Streams는 파티셔닝 메커니즘을 사용하여 수신 레코드를 스트림 내의 여러 샤드에 분산합니다. 프로듀서가 Kinesis에 레코드를 전송하면 Kinesis는 파티션 키에 해시 함수를 적용하여 해당 레코드를 수신할 샤드를 결정합니다. 이 프로세스는 "샤드 = 해시(파티션 키) % 샤드 수" 공식을 따르며, 파티션 키가 동일한 레코드는 항상 동일한 샤드로 일관되게 라우팅됩니다. 이러한 결정론적 동작은 파티션 내 데이터 순서를 유지하는 데 필수적일 뿐만 아니라, 파티션 키 선택이 샤드에 데이터가 얼마나 균등하게 분산되는지에 직접적인 영향을 미친다는 것을 의미합니다. 각 샤드는 수신 데이터의 경우 초당 1,000개 레코드 또는 초당 1MB라는 특정 용량 제한을 가지므로, 최적의 성능을 위해서는 적절한 파티션 키 선택이 매우 중요합니다.
**수정**
정적 파티션 키를 분산 방식으로 교체합니다.
**1단계: 생산자 기능 코드 업데이트**
1. **adv2-func-order-producer를** 엽니다.
2. 23-26행을 28-31행으로 바꾸세요:
`1
2
3
4
5
6
7
8
9
10
11
# REMOVE THIS (Hot Partition):
# records.append({
#     'Data': json.dumps(record_data),
#     'PartitionKey': 'HOT_PARTITION'  # Force all to same shard
# })

# REPLACE WITH THIS (Distributed):
records.append({
    'Data': json.dumps(record_data),
    'PartitionKey': str(uuid.uuid4())  # Random distribution
})`
**전체 코드:**
**2단계: 변경 사항 배포**
**변경 사항을 배포하려면 '배포'를** 선택하세요 . 수정 사항이 배포되었지만, 수정 사항의 효과가 반영되기까지 몇 분 정도 걸릴 수 있습니다.
**3단계: 수정 확인**
대시보드로 이동하여 다음 측정 항목을 모니터링하여 수정 사항을 확인하세요.
1. **샤드 분포**
  - : 이제 4개의 모든 샤드가 데이터를 수신해야 합니다.
2. **람다 동시성 : **
  - [동시 실행을](https://docs.aws.amazon.com/lambda/latest/dg/lambda-concurrency.html) 4개로 늘려야 함
3. **쓰기 제한**
  - : 99%에서 거의 0%로 낮아져야 합니다.
4. **반복자 연령**
  - : 백로그가 지워짐에 따라 감소해야 함
5. **처리량**
  - : 20,000 TPS로 복귀해야 함
**결론**
이 사례는 간단한 파티션 키 오류가 스트리밍 시스템에서 어떻게 극적인 성능 저하를 초래할 수 있는지 보여줍니다. 핫 파티션 문제는 Kinesis 구현에서 가장 흔한 문제 중 하나이며, 주로 다음과 같은 원인으로 발생합니다.
- 정적 또는 낮은 카디널리티 파티션 키 사용
- Kinesis가 데이터를 어떻게 분배하는지 이해하지 못함
- 현실적인 데이터 패턴을 사용한 테스트가 부족합니다.
균등한 분할 키 분배를 구현함으로써 시스템을 최대 성능으로 복구하고 모든 샤드에서 균등한 활용을 보장할 수 있습니다.
**사건 상태:** 해결됨 ✅
**관련 자료**
- [Kinesis Data Streams 주요 개념](https://docs.aws.amazon.com/kinesis/latest/dev/key-concepts.html)
- [쓰기 처리량 최적화](https://aws.amazon.com/blogs/big-data/optimize-write-throughput-for-amazon-kinesis-data-streams/)
- [Kinesis 스케일링 및 리샤딩](https://docs.aws.amazon.com/kinesis/latest/dev/kinesis-using-sdk-java-resharding.html)
- [Kinesis 데이터 스트림 모니터링](https://docs.aws.amazon.com/kinesis/latest/dev/monitoring.html)
**이전의**





축하합니다! 까다로운 서버리스 포렌식 조사를 성공적으로 완료했습니다. 각 시나리오는 분산 시스템의 운영 문제를 진단하고 해결하는 데 중요한 기술을 보여주었습니다.
**1. 침묵의 사라짐 - 보이지 않는 실패**
SQS의 1MB 메시지 제한을 초과하는 대용량 페이로드를 처리할 때 EventBridge Pipes가 자동으로 실패하는 현상을 발견했습니다. 조사 결과, 입력 변환기가 페이로드 크기를 4배까지 증폭시켜 명확한 오류 징후 없이 메시지가 거부되는 현상이 나타났습니다. 이 시나리오는 EventBridge Pipes 로그를 모니터링하고 데이터 변환 파이프라인에서 서비스 할당량을 파악하는 것의 중요성을 강조했습니다.
**2. 지연 포렌식 - 용량 병목 현상**
반복자 연령 증가 증상의 근본 원인을 추적해 보니, 바로 DynamoDB 쓰기 용량 제한이었습니다. Kinesis와 Lambda는 정상으로 보였지만, DynamoDB 쓰기 용량 단위(WCU 2개 대비 TPS 500개)가 부족하여 스트리밍 파이프라인 전체에 연쇄 효과가 발생했습니다. 이 사례는 가장 느린 구성 요소가 전체 시스템 처리량을 어떻게 결정하는지 잘 보여줍니다.
**3. 더블 트러블 - 타임아웃 트랩**
Lambda 시간 초과 설정 오류로 인해 시간 초과(30초)가 실제 처리 시간(40초)보다 짧을 때 중복 처리가 발생하는 방식을 파악했습니다. SQS는 실패한 메시지를 재시도하여 중복 주문과 비즈니스 영향을 발생시킵니다. 이 시나리오는 Lambda 시간 초과, 처리 시간, 그리고 SQS 가시성 시간 초과 설정 간의 중요한 관계를 보여주었습니다.
**고급 시나리오**
**4. 사라지는 기록의 미스터리 - 일괄 처리의 함정**
실제 재시도 동작과 일치하지 않는 On-Failure Destination(OFD) 지표와 관련된 복잡한 사례입니다. 람다 로그가 깨끗하고 SQS 메시지 처리가 성공했음에도 불구하고, 레코드가 재시도 파이프라인에서 이상하게 사라지고 있습니다. 이 조사는 일괄 처리 실패와 개별 레코드 처리 간의 고급 상관 관계 분석을 통해 람다 이벤트 소스 매핑 일괄 동작과 적절한 재시도 로직 구현의 복잡성을 밝혀냅니다.
**5. 샤드 가해자 - 핫 파티션 문제**
이 고급 조사는 4개의 샤드에 걸쳐 20,000 TPS를 처리하는 Kinesis 스트리밍 파이프라인의 처리량이 40% 감소하는 문제를 다룹니다. 샤드 수준 지표를 사용하여 핫 파티션 문제를 식별하고, 파티션 키 분배가 스트림 성능에 미치는 영향을 이해하고, 적절한 데이터 분배 전략을 구현하는 방법을 배웁니다. 이 시나리오는 겉보기에 정상으로 보이는 시스템이 파티션 수준에서 심각한 성능 병목 현상을 어떻게 감출 수 있는지 보여줍니다.
이러한 고급 시나리오는 핵심 사례의 기초적인 포렌식 기술을 기반으로 구축되어 더욱 복잡한 장애 모드를 도입하고 AWS 서비스 내부와 분산 시스템 동작에 대한 심층적인 이해가 필요합니다.
**자원**
- [AWS Well-Architected 프레임워크 - 안정성 기둥](https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/welcome.html)
- [분산 추적을 위한 AWS X-Ray](https://docs.aws.amazon.com/xray/latest/devguide/aws-xray.html)
- [CloudWatch Logs Insights 쿼리 구문](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/CWL_QuerySyntax.html)
- [AWS 서비스 할당량 문서](https://docs.aws.amazon.com/general/latest/gr/aws-service-information.html)