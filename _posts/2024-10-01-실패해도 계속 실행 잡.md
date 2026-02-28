---
title: "실패해도 계속 실행 잡"
date: 2024-10-01
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

![](/assets/images/Pasted%20image%2020260228171327_2d5ea84f.png)


```javascript
#job_name을 받아서 step 이름이랑 안에서 도커 이미지 파라미터 물고 실행할 수 있게끔 만듬
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  generateName: listed-stock-job-
  annotations:
    job_name: "{{workflow.parameters.job_name}}"
spec:
  entrypoint: main
  arguments:
    parameters:
      - name: job_name #디폴트 없음. 파라미터 입력안하면 무조건 실행하지마
      - name: iteration
        value: "1"  # 1부터 도는 변수
      - name: max_iteration
        value: "{{inputs.parameters.max_iteration}}"  # 얼마나 돌지 결정
  templates:
    - name: main
      inputs:
        parameters:
          - name: iteration
          - name: max_iteration
          - name: job_name
      steps:
        - - name: "{{workflow.parameters.job_name}}"
            template: workflow-one
            arguments:
              parameters:
                - name: iteration
                  value: "{{inputs.parameters.iteration}}"
                - name: max_iteration
                  value: "{{inputs.parameters.max_iteration}}"
                - name: job_name
                  value: "{{inputs.parameters.job_name}}"
            continueOn:
              failed: true
              error: true
        - - name: recursive-call
            template: main
            arguments:
              parameters:
                - name: iteration
                  value: "{{=asInt(inputs.parameters.iteration) + 1}}" # 1씩 증가
                - name: max_iteration
                  value: "{{inputs.parameters.max_iteration}}"
                - name: job_name
                  value: "{{inputs.parameters.job_name}}"
            when: "{{inputs.parameters.iteration}} < {{inputs.parameters.max_iteration}}"  # max보다 크면 그만
    - name: workflow-one
      container:
        image: muyaho/listed-stock-pub-job:latest
        env:
          - name: JOB_NAME
            value: "{{workflow.parameters.job_name}}"

```

contineOn: failed 넣으면 됨
