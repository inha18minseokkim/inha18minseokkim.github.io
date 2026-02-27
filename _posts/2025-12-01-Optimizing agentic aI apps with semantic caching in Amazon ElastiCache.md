---
title: "Optimizing agentic aI apps with semantic caching in Amazon ElastiCache"
date: 2025-12-01
tags:
  - AWS
  - 기술
category:
  - 기술
---
AWS re:Invent 2025 세션 노트 정리.
Friction
Scale, Speed, Cost 이게 큰 문제

넣을때 거래 하나를 위해 ***context***[, ](https://www.google.com/search?sca_esv=c302aaa6c87d965b&rlz=1C5CHFA_enKR1053KR1053&sxsrf=AE3TifMbenPUo89siTC9JHq7tuin6f5JHA:1764624091723&q=context,+query+processing,+tool+execution,+response&spell=1&sa=X&ved=2ahUKEwiyxpiBqZ2RAxUrJUQIHeF2HzEQkeECKAB6BAgREAE)***query***[ ](https://www.google.com/search?sca_esv=c302aaa6c87d965b&rlz=1C5CHFA_enKR1053KR1053&sxsrf=AE3TifMbenPUo89siTC9JHq7tuin6f5JHA:1764624091723&q=context,+query+processing,+tool+execution,+response&spell=1&sa=X&ved=2ahUKEwiyxpiBqZ2RAxUrJUQIHeF2HzEQkeECKAB6BAgREAE)***processing***[, ](https://www.google.com/search?sca_esv=c302aaa6c87d965b&rlz=1C5CHFA_enKR1053KR1053&sxsrf=AE3TifMbenPUo89siTC9JHq7tuin6f5JHA:1764624091723&q=context,+query+processing,+tool+execution,+response&spell=1&sa=X&ved=2ahUKEwiyxpiBqZ2RAxUrJUQIHeF2HzEQkeECKAB6BAgREAE)***tool***[ ](https://www.google.com/search?sca_esv=c302aaa6c87d965b&rlz=1C5CHFA_enKR1053KR1053&sxsrf=AE3TifMbenPUo89siTC9JHq7tuin6f5JHA:1764624091723&q=context,+query+processing,+tool+execution,+response&spell=1&sa=X&ved=2ahUKEwiyxpiBqZ2RAxUrJUQIHeF2HzEQkeECKAB6BAgREAE)***execution***[, ](https://www.google.com/search?sca_esv=c302aaa6c87d965b&rlz=1C5CHFA_enKR1053KR1053&sxsrf=AE3TifMbenPUo89siTC9JHq7tuin6f5JHA:1764624091723&q=context,+query+processing,+tool+execution,+response&spell=1&sa=X&ved=2ahUKEwiyxpiBqZ2RAxUrJUQIHeF2HzEQkeECKAB6BAgREAE)***response*** 총 네 개의 관문을 거쳐야함

복잡해지면서 비용최적화 테크닉 필요함. 모델 바꾸거나 캐싱하거나 그래야함
싱글에이전트면 그냥 한번 llm 타고 데이터소스 찌르면 되는데
멀티에이전트 프레임워크에서는 패턴이 다양해짐
supervisor, network, hierarchical, sequential 패턴이 있는데 오늘은 시퀀셜

![](attachment:c9e7d0e7-a6e2-4ffd-b1a2-d2882ee97343:image.png)


예시
planner agent는 특정 문장을 각각의 스탭으로 decompose 해주는 에이전트
search agent는 지도로 뭐 찾거나 뒤짐
review agent는 또 데이터베이스 뒤져
availability agent는 또 뒤져서 식당 이용가능한지
response agent는 merge 해서 응답 냄
스케일이 커지면서 각 에이전트마다 질문 응답 패턴이 비슷해지고 있음
이거 캐시 포인트임

![](attachment:35fe317c-e5f8-4ad9-8bef-163995a43ae3:image.png)

옛날에는 select * from~으로 쿼리 캐싱을 했음.

valkey 머신러닝 ai에서도 쓸 수 있음. 
11/17 부터 발키가 벡터 서치 가능하도록 되었다 > 오!
그래서 RAG 시멘틱서치 시멘틱 캐시 에이전트 메모리 다 쓸 수 있음 발키를

![](attachment:35b39da5-821b-4bb6-a79f-493ef3d6ea25:bc66311e-9cc8-483c-b270-71ded237bf9b.png)

시맨틱캐시가 뭐냐 그래서
sql 텍스트 사용하는게 아니라 유저 질문의 시맨틱을 인덱스로 사용하는것

질문을 시맨틱으로 변환 > 시맨틱 서치 > 벡터거리가 가까운게 있으면 쓰면됨, 없으면 다시 새로운 응답 생성하고 캐시 넣기

시맨틱을 그러면 어떻게 자연어에서 변환하냐? 시멘틱거리 = 그냥 벡터거리 비슷하면 같은 군집으로 클러스터링되는 그거 말하는거임 ㅇㅇ
아마존 베드락에서 사용할 수 있는 타이탄 임베딩 모델 쓰면됨 ㅇㅇ
  - 텍스트가 아니라 멀티모달 임베딩도 가능 
파운데이션모델보다 임베딩 모델이 750배 이상 쌈

근데 스케일링하면 문제생김
KNN 문제 생김, 다 찾을려고 하면 존나느려짐 : 75년된 문제
그래서 대신에 ANN 문제로 그냥 대충 찾으면 됨
  - 제일 가까운거 못찾아줄 수는 있어도 (일단 베스트정답 안찾아줄 수는 있어도) 잘못된 응답은 아니기 때문에 그냥 빨리 줘
  - ANN 알고리즘 종류는 존나많음 대충 찾아보면됨
컴퓨터과학 하면 공간 시간 트레이드오프 문제 있음 여기에 품질까지

Hierarchical Navigable Small World - 알고리즘임
그래프 만들어서 가까운애들은 연결되어있음
레이어를 만듦
아무튼 로그시간임

![](attachment:30a5ba8f-cb86-49a7-94df-15e7644598ba:3ee7ff81-a0fb-4437-a64c-7cb593c17322.png)


스텝이 점점 많아지면서 모든 스텝에서 퀄리티는 중요해짐
ex) 각 스텝이 recall시 accuracy 0.9 이면 3스텝되면 0.73됨
99퍼 되어야함

valkey k v 저장소인데 어케 시맨틱 저장함?
엘라스팈캐시 캐시는 키밸류스토어인데 관념적으로 테이블과 같다고 생각하면됨

![](attachment:55c0e9ee-ab87-4d32-aa6e-51f82e59d144:c98b1d3b-830e-4a11-b57b-5d1be0826b0f.png)


![](attachment:ed333dc7-6200-4355-adc4-f16674d34aad:bad918f8-3797-49ce-bb06-96a8faddd196.png)

엘라스팈캐시 비싸니깐 캐시에는 정답지 키 : 벡터, 레퍼런스만 저장해놓고 정답은 따로 저장. S3 Dynamo 등등…


![](attachment:9605711c-4e73-4c48-ab60-fbf41b74bd14:d35c8b22-50b6-4196-ac0e-3960ce16da52.png)

기존 valkey와 같이 ttl 설정도 가능.예전에 milvus에서 인덱스 구조 잡고 사용했던거랑 비슷하게 사용하면 되는듯


![](attachment:e2ad90ba-4082-4362-a362-e18b3a201eab:e05df37d-073a-44f0-ac37-b5a60521f17d.png)




![](attachment:ec2201f0-fe92-401a-8170-f966094f0ae5:d57e855e-c091-4870-a14d-f51afa371872.png)

위 사진 가져온이유는 재사용 + ANN 사례를 더 잘 보여주는 단적인 예라고 생각해서 가져옴. 7시 


근데 재사용 하는건좋은데 각 스탭마다 가지고 왔던 값의 ttl이 다를 수 있음. 서치에이전트 응답은 30일 ttl 가져가도 되고 리뷰나 영업여부 에이전트는 ttl 짧게가져가야하고(금방금방 바뀌니깐) 이런식일 수 있음. 이런건 업무를 어떻게 잘 쪼개냐에 따라 달라지는듯 
similaity threshold, higher similarity : 히트율이 낮음, 그래서 더 후레쉬함

[Lower cost and latency for AI using Amazon ElastiCache as a semantic cache with Amazon Bedrock | Amazon Web Services](https://aws.amazon.com/ko/blogs/database/lower-cost-and-latency-for-ai-using-amazon-elasticache-as-a-semantic-cache-with-amazon-bedrock/)