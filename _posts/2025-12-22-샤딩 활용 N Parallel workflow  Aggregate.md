---
title: "샤딩 활용 N Parallel workflow > Aggregate"
date: 2025-12-22
tags: [미지정]
category:
  - 기타
---


![](attachment:edaca24f-9ade-4c35-9a3c-05fa900b0e3b:image.png)

작년에 POC 하다가 이런식으로 


```sql
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  generateName: loop-sequence-
spec:
  entrypoint: loop-sequence-example

  templates:
    - name: loop-sequence-example
      steps:
        # 0~10 병렬 실행
        - - name: hello-world-x5
            template: hello-world
            arguments:
              parameters:
                - name: idx
                  value: "{{item}}"
            withSequence:
              start: "0"
              end: "10"

        # 모든 hello-world-* 이 성공적으로 끝난 뒤 실행
        - - name: welcome
            template: welcome

    - name: hello-world
      inputs:
        parameters:
          - name: idx
      container:
        image: busybox
        command: [echo]
        args: ["hello world! {{inputs.parameters.idx}}"]

    - name: welcome
      container:
        image: busybox
        command: [echo]
        args: ["Welcome"]
```




![](attachment:878f5437-0294-4d85-b0eb-86516a3b550a:image.png)
