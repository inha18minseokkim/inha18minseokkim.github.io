---
title: "실패해도 계속 실행 잡 2(개선버전)"
date: 2024-10-02
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

![](/assets/images/Pasted%20image%2020260228171328_53caeba0.png)

순차적으로 작업 실행,
실패해도 계속 실행됨
다만 recursive 가 아니라 for loop라 좀 더 깔끔함
output을 가지고 뭘 할게 아니라면 그냥 이게 좋은듯

```java
#max_iteration 입력 하면 n번 돔, 실패해도 다음 스텝 계속 
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  generateName: listed-stock-job-parallelism-tolerant-
  annotations:
    job_name: "{{workflow.parameters.job_name}}"
spec:
  entrypoint: main
  arguments:
    parameters:
      - name: job_name #디폴트 없음. 파라미터 입력안하면 무조건 실행하지마
      - name: max_iteration
        value: "{{inputs.parameters.max_iteration}}"  # 얼마나 돌지 결정
  templates:
    - name: main
      parallelism: 1
      inputs:
        parameters:
          - name: max_iteration
          - name: job_name
      steps:
        - - name: "{{workflow.parameters.job_name}}"
            template: workflow-one
            arguments:
              parameters:
                - name: max_iteration
                  value: "{{inputs.parameters.max_iteration}}"
                - name: job_name
                  value: "{{inputs.parameters.job_name}}"
            continueOn:
              failed: true
              error: true
            withSequence:
              start: 0
              end: "{{=asInt(inputs.parameters.max_iteration)}}"
    - name: workflow-one
      container:
        image: muyaho/listed-stock-pub-job:latest
        env:
          - name: JOB_NAME
            value: "{{workflow.parameters.job_name}}"

```

