---
title: "**Behind the scenes: How AWS drives operational excellence & reliability**"
date: 2025-12-01
tags:
  - AWS
  - 기술
category:
  - 기술
---
카페에서 뭐 이벤트 한다고 뿌림 > 커피 살려고 했다 > 커피머신 고장나서 못팜 ㅅㄱ 흔한 패턴

Excellence란> Bias for Action과 Insist on Highest Standards 사이. Perfection이라고 안함

[AWS Fault Isolation Boundaries - AWS Fault Isolation Boundaries](https://docs.aws.amazon.com/whitepapers/latest/aws-fault-isolation-boundaries/abstract-and-introduction.html) 이거 읽어봐

AWS Well-architected framework 이거 읽어봐

Operational Excellence - aws 쓰는 이유
observability> incident response> review system > readiness > observability

좋은 의도는 의미가 없다. 메커니즘이 작동할 뿐이다. 시스템은 매커니즘으로 동작해야 한다.

Readiness
  - operational readiness template 만들어놓고 안지키면 알람 걸어놓음
Continuous Testing, Continuous Load Test
Game Days
  - 이상한 시뮬레이션 열심히 돌려봄 - AWS Fault Injection Service 
Change Management
Release Excellence

![](attachment:f074288f-9560-4ef0-9a77-188bbbc38c35:image.png)


Observabililty
  - 안쪽에 상태를 더 잘 보이게 해야함
  - 표준화 해놓고 그거 지키면 클라우드워치에서 다 대시보드로 제공가능함

Open Standard
  - aws는 otel 기반으로 다 되어있음.

![](attachment:a1d5a7e2-8f0b-43c6-8645-2c6264196314:image.png)



![](attachment:2ddd739d-15eb-440a-9db2-2c51094a7c99:image.png)

테스트 절차에 대해 설명해놓은것이긴한데 ㄹㅇ로 내결함성이랑 완성도 생각하면 저렇게 해야할듯. 하지만 조직 인력 이슈가 만만찮을듯 하다..


![](attachment:43c0dca1-030e-456a-8cd4-5a4fb3d81b41:image.png)



![](attachment:efc5fa78-dc73-4131-889a-6fd7c0a24f3b:image.png)

프로덕트 종류가 많아지고 규모가 커지고 조직이 많아짐에따라 계속 반복될 수 있는 착오를 반복하지 않게 하기 위해서 저러한 프로세스를 설계한 것 같다. 특히 테스트 절차와 CD, 오류 발생 시 MCP 사용하여 유사사례 탐색 등.. 
말미에도 이야기했지만 조직에 따라서 company own Operational Excellence를 설계하는것이 중요할 것 같다. 말단 프로덕트냐 영향도가 높은 프로덕트냐.. 무결성이 중요한가 변경속도가 중요한가 등등..

[Best Observability workshop](https://workshops.aws/categories/Observability)

