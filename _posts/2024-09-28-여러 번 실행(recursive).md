---
title: "여러 번 실행(recursive)"
date: 2024-09-28
tags: [미지정]
category: 기타
---
요청받은 이유:
1분 5분에 한 번 잡을 실행할 일이 있는데
jflow에서 runJobParam.sh를 1분/5분에 한 번 씩 호출해서 job submit을 하면 workflow에 로그쌓이는 속도나 퍼포먼스 측면에서 별로 안좋다고 해서
submit 한 번으로 주기적 크론잡 효과를 내려고 함.
다만 여기서 크론잡을 사용할 수 없는 이유(20240928 기준)는
1. jflow를 거치지 않는 경우 영업일 판단 불가
2. 현재 크론잡을 위한 스크립트가 마련되어 있지 않음


```javascript
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  generateName: recursive-limit-
spec:
  entrypoint: main
  arguments:
    parameters:
      - name: iteration
        value: "1"  # 1부터 도는 변수
  templates:
    - name: main
      inputs:
        parameters:
          - name: iteration
      steps:
        - - name: execute-step
            template: print-message
            arguments:
              parameters:
                - name: iteration
                  value: "{{inputs.parameters.iteration}}"
        # Recursive step - call itself if the iteration count is less than 5
        - - name: recursive-call
            template: main
            arguments:
              parameters:
                - name: iteration
                  value: "{{=asInt(inputs.parameters.iteration) + 1}}" # 1씩 증가
            when: "{{inputs.parameters.iteration}} < 5"  # 5보다 크면 그만

    - name: print-message
      inputs:
        parameters:
          - name: iteration
      container:
        image: busybox
        command: [sh, -c]
        args: ["echo Iteration: {{inputs.parameters.iteration}}"]

```




![](https://prod-files-secure.s3.us-west-2.amazonaws.com/c38aebd7-2834-4fac-b2fc-a2f0c17ce81d/d2cbcaa1-925b-4cae-9ae8-134a673573eb/image.png)

이런식으로 다섯 번 실행되고 각각 잡마다 interval을 주는 식으로 해야할듯 일단은… 건의해보자