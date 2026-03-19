---
title: "샤딩 활용 N Parallel workflow > Aggregate"
date: 2025-12-22
tags:
  - 개발
  - 기술
category:
  - 실무경험
---
개발 관련 내용 정리.
![이미지](/assets/images/Pasted%20image%2020260301003546.png)

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



![이미지](/assets/images/Pasted%20image%2020260301003552.png)
