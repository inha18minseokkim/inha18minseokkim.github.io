---
title: "**Building the Future Trading Platform leveraging AI and AWS**"
date: 2025-12-04
tags:
  - AWS
  - 기술
category:
  - 실무경험
---
AWS re:Invent 2025 세션 노트 정리.
![](attachment:c68f7155-c998-4c26-b287-7e182a3b63af:image.png)

브로커 딜러 회사 LPL Financial
자산운용 하는것같음
70~80개의 시스템 있음 다른 시스템 마켓센터에도 의존하고 핀테크 기구에도 의존함. 그래서 복잡함.
스케일업만 하면 퍼포먼스 올라가도록 설계하는게 목표였대

![](attachment:c57997bb-84e9-4d7c-9a7e-d4000d4c7fef:image.png)

컴플라이언스도 많아 항상 빨라야해 실패하면 안된다

![](attachment:467e00c6-80cf-41ef-a322-ee9502f9afeb:image.png)

마이그레이션안하고 진짜 새로 만들었다 ㄷㄷ


![](attachment:014fdeca-1426-4b73-8e71-ae7c357de520:image.png)

클라우드 전환 > 오토스케일링 가능 > 회복탄력성 확보 > 선제적 스케일링 순으로 진행


![](attachment:b3916bfb-9bf9-4c00-96df-d212617e64aa:image.png)

온프렘 의존 줄여서 멀티리전 멀티존 했다 
와시 여기도 대고객 접점은 클라우드네 인생

읽기로 dynamo 사용 의존 줄이려고 카프카 씀

차세대는 온프렘 없앤다고 함

![](attachment:79375798-3eee-4cfb-8fe3-e241fc0e68a9:image.png)


데이터를 어케 일관적으로 유지하지 멀티리전에서 > 가장 큰 문제였음
리퀘스트에 대한 오케스트레이션을 어떻게 조정하지? 멀티리전 active active인 상태에서

![](attachment:a43db6d6-88e2-4225-bb3f-14d28a349ebc:image.png)

고객 자산관리할때 리밸런서 있음

매분마다 수십만 수백만개 계좌 체크함
이걸 다 청크로 미니배치 화 시킴 이걸 메세지 브로커에 넣어(guarantee deliver) 
  - 이걸 리밸런싱함 EKS 오토스케일링에 쓰려고
200개 이상의 체크를 수행함 리밸런싱할때,, 실패하면 다시 큐 뒤에 넣고 그런거 함

![](attachment:9793ccfd-d30e-40bd-91a7-3d762b33b377:c0d030fa-9749-4cfe-96df-ba7bd443abcf.png)

이상탐지같은거할때 AI 쓰는듯

![](attachment:88aee680-aa32-4a45-8f4d-e78e16ca49f1:5fc4cd43-e333-4cc1-91b6-464f5ac0c353.png)

ETF 타입 분류할때도 AI 쓴다(새로상장된거 카테고라이징)


![](attachment:77f50d85-0b29-48e5-9648-e7a2b5e717f3:image.png)

람다로 데이터 학습하는 작업 돌리고 이거 sagemaker에서 학습
sagemaker에서 모델 배포하고 이 모델을 람다가 호출하는데
해당 람다는 실시간 데이터 피드로부터 이벤트 받아서 실행되는듯
실행되면 etf 분류는 rds에 들어가고 이상탐지는 alert system에 들어가고 

![](attachment:6fe472c9-eba7-44da-bf09-e4a2fe57e8b9:image.png)

리밸런싱 할때 세금 상한 걸어놓고 리밸런싱 할 수 있도록도 함 ㄷㄷ
변수가 50개 정도 있는데 이걸 조절해서 세금 문제 없이 리밸런싱해야함
그래서 멀티 에이전트 씀
리밸런싱 에이전트는 리밸런싱 하고 검증 에이전트는 해당 결과 보고 검증함 approve 하면 트레이딩 에이전트가 트레이딩 함 검증에서 실패하면 리밸런싱 에이전트에 피드백 보내서 다시 제출받음

