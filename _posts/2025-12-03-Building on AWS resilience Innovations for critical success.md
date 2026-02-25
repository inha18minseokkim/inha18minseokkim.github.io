---
title: "**Building on AWS resilience: Innovations for critical success**"
date: 2025-12-03
tags: [미지정]
category: 기술
---
Region must be isolated
  - 38개 리전있는데 그냥 독립적으로 움직인다고 생각해야함
하나 실패해도 나머지는 무조건 가야함
테스트 빡세게 함 카오스테스팅 게임데이 이거 첫날 들은거랑맥락비슷하네 ㅇㅇ

IAM - Globally Consistent, Used during build time
  - central source of truth
STS - Local and Stateless, Used during runtime
  - STS에 대해서는 좀 더 공부해보기
STS가 처음에는 us 리전에 엔드포인트 몰려있어서 리전 디펜던시 발생했었음,, 이제 각 리전에 다 배포되어서 리전이 그냥 독립적으로 동작함
[AWS STS 글로벌 엔드포인트, 기본적으로 활성화된 리전에서 로컬로 요청 처리 - AWS](http://aws.amazon.com/ko/about-aws/whats-new/2025/04/aws-sts-global-endpoint-requests-locally-regions-default/)
Near perfect transparency - route53에서 리전 요청 해당 리전으로 가급적이면 돌아가도록 해놓음

resilience to az impairment 
람다 콜할때
  - 람다는 되게 많은 컴퓨팅자원 위에서 실행되는데 그거중에 인스턴스 노드 하나가 다운은 안되고 시원찮으면…
  - your 9’s arent’ my 9’s
    - 너는 하나 죽어도 9지만 그게 내꺼면 난 0임
  - 차라리 그냥 실패하면 상관없는데 gray failure면 찾기힘듬.. 느리긴하지만 응답을 주긴 해서
  - 그래서 healthcheck 시 shallow 와 deep을 나눔.. 근데 그 사이에 스윗 스팟 찾는게 힘들어
  - 노드중에 error response가 outlier인걸 찾아
  - 클라우드워치로 매트릭 수집하다가 unhealthy instance 임계치 넘는애가 있으면 경고

![](attachment:0113d033-ab54-4838-a62b-6c45c19234e5:image.png)


![](attachment:3719de88-3e00-482b-bbec-c5d6de246e3b:image.png)


zonal shift

![](attachment:80033fe5-cde0-4482-98a2-6f48dfa9eaab:image.png)

elb가 신호 각 az에 분산시켜주는듯
한번 시프트할때 az 하나씩 시프트 가능
존 변경하면 알아서 elb가 스케일링하는 대상 존 조절해줌
zonal autoshift도 가능 설정해놓으면 뭔가 이상치 있을때 자동으로 존을 옮겨줌
[Zonal autoshift – Automatically shift your traffic away from Availability Zones when we detect potential issues | Amazon Web Services](https://aws.amazon.com/ko/blogs/aws/zonal-autoshift-automatically-shift-your-traffic-away-from-availability-zones-when-we-detect-potential-issues/)

test rigorously
  - 이건 뭐 재해복구훈련 같은거인듯 
  - 게임데이 만들어서 테스트 리전 만들어 온갖짓을 다해봄


stable > vulnerable > trigger시 metastable

![](attachment:df6f01fe-629d-4a52-a25a-cc57c9400672:image.png)

fifo 상황에서 너무 메세지가 오래되면 어차피 실패하는데 계속 쌓이기만하고 새로 들어오는것도 계속 실패할거임.. 이게 metastable 뭔가 일은 많이하는데 다실패함



![](attachment:cccdea14-7674-4d89-a979-321ce52320f8:image.png)

