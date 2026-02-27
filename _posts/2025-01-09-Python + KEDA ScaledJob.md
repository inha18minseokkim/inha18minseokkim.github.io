---
title: "Python + KEDA ScaledJob"
date: 2025-01-09
tags:
  - KEDA
  - Kubernetes
  - 인프라
category:
  - 기술
---
KEDA를 활용한 Kubernetes 오토스케일링 구현 정리.
![](https://prod-files-secure.s3.us-west-2.amazonaws.com/c38aebd7-2834-4fac-b2fc-a2f0c17ce81d/d20f12b3-95fe-4fb1-b8d5-f81520a190d6/image.png)

일단 로컬로 POC할 때는 이런식으로 프로젝트 하위에 scaled-job 폴더를 만들어서 여기다가 yaml 설정을 때려넣었다.

```yaml
apiVersion: keda.sh/v1alpha1
kind: ScaledJob
metadata:
  name: listed-stock-price-sub-job
  labels:
    my-label: listed-stock-price-sub-job           # Optional. ScaledJob labels are applied to child Jobs
  annotations:
#    autoscaling.keda.sh/paused: true        # Optional. Use to pause autoscaling of Jobs
    my-annotation: listed-stock-price-sub-job      # Optional. ScaledJob annotations are applied to child Jobs
spec:
  jobTargetRef:
    parallelism: 1                            # [max number of desired pods](https://kubernetes.io/docs/concepts/workloads/controllers/job/#controlling-parallelism)
    completions: 1                            # [desired number of successfully finished pods](https://kubernetes.io/docs/concepts/workloads/controllers/job/#controlling-parallelism)
    activeDeadlineSeconds: 600                #  Specifies the duration in seconds relative to the startTime that the job may be active before the system tries to terminate it; value must be positive integer
    backoffLimit: 6                           # Specifies the number of retries before marking this job failed. Defaults to 6
    template:
      spec:
        containers:
          - name: listed-stock-price-sub-job
            image: muyaho/python-job-example:latest
            command: [ "/bin/sh", "-c" ]
            args: [ "python ./app/listed/stock/job/ListedStockPriceSubJob.py" ]
  pollingInterval: 30                         # Optional. Default: 30 seconds
  successfulJobsHistoryLimit: 5               # Optional. Default: 100. How many completed jobs should be kept.
  failedJobsHistoryLimit: 5                   # Optional. Default: 100. How many failed jobs should be kept.
#  envSourceContainerName: {container-name}    # Optional. Default: .spec.JobTargetRef.template.spec.containers[0]
  minReplicaCount: 0                          # 0, LAG 없으면 잡 띄우지마
  maxReplicaCount: 1                          # 1, LAG 있으면 잡 띄워 하나만
#  rolloutStrategy: gradual                    # Deprecated: Use rollout.strategy instead (see below).
  rollout:
    strategy: gradual                         # Optional. Default: default. Which Rollout Strategy KEDA will use.
    propagationPolicy: foreground             # Optional. Default: background. Kubernetes propagation policy for cleaning up existing jobs during rollout.
  scalingStrategy:
#    strategy: "custom"                        # Optional. Default: default. Which Scaling Strategy to use. #이것도 0 1따린데 안씀
#    customScalingQueueLengthDeduction: 1      # Optional. A parameter to optimize custom ScalingStrategy.  #이것도 0 1 따리는 안ㄴ쓰는게 좋음
#    customScalingRunningJobPercentage: "0.5"  # Optional. A parameter to optimize custom ScalingStrategy. #min0 max1로 지정하는데 이거 소수점으로 떨구면 파드 안뜸
    pendingPodConditions:                     # Optional. A parameter to calculate pending job count per the specified pod conditions
      - "Ready"
      - "PodScheduled"
      - "AnyOtherCustomPodCondition"
    multipleScalersCalculation : "max" # Optional. Default: max. Specifies how to calculate the target metrics when multiple scalers are defined.
  triggers:
    - metadata:
        bootstrapServers: '125.176.39.143:29092'
        consumerGroup: python_data_load
        lagThreshold: '1'
        offsetResetPolicy: latest
        topic: ListedStockPrice
      type: kafka
```

python_dat_load 컨슈머 그룹으로 ListedStockPrice 토픽을 바라보면서 Lag가 1 이상인 경우 HPA를 하는 ScaledJob이다.
실시간으로 데이터를 pub 한다 → LAG가 쌓인다 → LAG가 lagThreshold 값보다 커진다 → ScaledJob 기동한다 → ConsumerGroup 상으로 Lag를 커밋하고 끝난다 → 다시 쌓인다 무한반복

실시간으로 레코드 pub

![](https://prod-files-secure.s3.us-west-2.amazonaws.com/c38aebd7-2834-4fac-b2fc-a2f0c17ce81d/5f960a73-f840-4009-babc-6dab58fe583c/image.png)


![](https://prod-files-secure.s3.us-west-2.amazonaws.com/c38aebd7-2834-4fac-b2fc-a2f0c17ce81d/7f221a2c-daa2-496a-8aff-ebab325c0457/image.png)


![](https://prod-files-secure.s3.us-west-2.amazonaws.com/c38aebd7-2834-4fac-b2fc-a2f0c17ce81d/03e453ce-5355-4f28-84a7-72129ffbde52/image.png)

lagThreshold가 1보다 크면 무조건 파드 1개가 뜸.
스프링 KafkaItemReader와 차이가 있다면 자바스프링은 main 함수 기동 시 관련된 모든 클래스,빈을 메모리에 올리지만 파이썬의 경우 파이썬 스크립트 파일과 관련된 import만 메모리에 올리는 식의 인터프리터 언어다 보니 상당히 빠르고 가볍다.

![](https://prod-files-secure.s3.us-west-2.amazonaws.com/c38aebd7-2834-4fac-b2fc-a2f0c17ce81d/9efa5361-517f-47d4-a493-3f3f3942709c/image.png)

consumer group에 파이썬 consumer가 붙은 모습
