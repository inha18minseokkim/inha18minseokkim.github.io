---
title: "Spring batch + FlowJob"
date: 2023-10-30
tags: [미지정]
---

### SimpleJob

마지막 Step의 BatchStatus값을 최종 BatchStatus로 반영
Step실패하는 경우 해당 Step의 Status가 해당 Job의 최종 Status

### FlowJob

Flow내의 ExitStatus값을 FlowExecutionStatus로 반영
마지막 Flow의 FlowExecutionStatus 값을 최종 Job의 Status로 반영

그러므로 아무리 SimpleJob에서 뭘 해봐야 특정 Step이 실패하는 경우 다른 Step으로 넘어가거나 할 수가 없다..

```java
new JobBuilder("NaverReceiveJob",jobRepository)
                        .start(preTasklet()).on("COMPLETED")
                        .to(firstStep)
                        .from(preTasklet()).on("*").end()
                        .next(secondStep)
                        .build().build()
```

.on의 경우
해당 패턴과 매칭되는 경우 다음 동작을 지정 가능
*의 경우 → 와일드카드
?의 경우 → 1개 와일드카드
그러므로 위의 Job의 경우
preTasklet 스텝 시작으로 해당 Status가 COMPLETED 이면 firstStep으로 감
그거 아니고 나머지 케이스는 모두 그냥 끝(end)
그거 아니면 secondStep 실행
이런식이다

### ExitStatus

JobExecution과 StepExecution의 속성임. Job/Step 실행된 결과
기본적으로 ExitStatus = BatchStatus
아 그리고

![](https://prod-files-secure.s3.us-west-2.amazonaws.com/c38aebd7-2834-4fac-b2fc-a2f0c17ce81d/ef7ea095-f100-4f04-869b-e753883b4f09/Untitled.png)

이렇게 보이는데 on에서 COMPLETED로 하드코딩하고 와일드카드 쓰길래 뭔가 했는데

![](https://prod-files-secure.s3.us-west-2.amazonaws.com/c38aebd7-2834-4fac-b2fc-a2f0c17ce81d/743838fb-0e52-4d32-a10b-1252c3a0b903/Untitled.png)

이런식으로 생성자 호출해서  만드는게 가능했다..

### ExitStatus의 equals 오버라이딩


![](https://prod-files-secure.s3.us-west-2.amazonaws.com/c38aebd7-2834-4fac-b2fc-a2f0c17ce81d/28dd311b-9160-4701-ae2f-05dd80fbdcb0/Untitled.png)


### ExitStatus의 toString 오버라이딩


![](https://prod-files-secure.s3.us-west-2.amazonaws.com/c38aebd7-2834-4fac-b2fc-a2f0c17ce81d/1439e364-199e-4154-8eb5-c436c2d32d1d/Untitled.png)

생성자 호출 시 exitCode(필수),existDescription(선택) 으로 똑같으면 되는듯

![](https://prod-files-secure.s3.us-west-2.amazonaws.com/c38aebd7-2834-4fac-b2fc-a2f0c17ce81d/4821adb2-608b-459c-89fa-55e2b1e38f57/Untitled.png)

그러므로 이런식으로 하면 됨. 다양한 exitStatus 별로 Step 분기 치기 가능

이건 Status는 COMPLETED이지만 exitStatus는 Muyaho로 반영
BATCH_STEP_EXECUTION 테이블에도 exit_code = Muyaho, status = COMPLETED,FAILED,STARTED,UNKNOWN 이런식으로