---
title: "Jflow - Control M AWS 연동"
date: 2025-07-16
tags:
  - 인프라
  - 개발
category:
  - 기술
---
행의 Control M 과 AWS 솔루션을 연결해보자

# 왜?

현재 배치 자원은 EKS 노드자원을 사용하고 있음. 온라인 자원과 공유하고 있어서 별로 좋지 않음.
그리고 Control M에 로그를 출력하고 성공 결과를 동기적으로 리턴하기 위해 argo-workflow를 사용하고 있음. 본래 argo-workflow는 DAG나 Event-Driven을 사용해야 진가가 발휘되는데 현재는 컨엠 발사대 그 이상 이하도 아님. 즉 작성해야 할 yaml 파일만 까다로워지고 있음.
그러므로 현재 행 정기작업 컴플라이언스를 준수하기 위해서 Jflow에 정기작업 실행 기록과 통제가 남아야 한다면 Jflow > Control M 연동 구조에 AWS 를 붙이는 구조를 검토해봐야 함.

### MVP

1. EKS 노드자원 분리
2. argo-workflow.yaml 파일 작성 및 유지보수 허들 > argo-workflow 가급적이면 쓰지 마
  1. argo workflow, airflow 등이 좋은 정기작업관리 오픈소스이긴 하지만 행내에서 Control M 이 아니면 별도로 컴플라이언스 감사를 받아야 하기 때문에 트리거 및 작업정보관리는 Control M이 한다. 이건 정책이 바뀌지 않는 이상 도입불가
3. 

## Control M Plugin

[Control-M for Kubernetes Compatibility](https://documents.bmc.com/supportu/K8S/9.0.21.315/en-US/Documentation/K8S_Compatibility.htm)
[Control-M 리소스 배포 - AWS 권장 가이드](https://docs.aws.amazon.com/ko_kr/prescriptive-guidance/latest/control-m-batch-scheduler/deploy-control-m-resources.html)
컨트롤엠에서 EKS 플러그인을 사용할 수 있다. 크게 두 가지 형태가 있을 듯
1. 현재 Control M 의 버전 업그레이드, 솔루션 패치를 적용해서 EKS 대응을 한다
2. EKS 내에 Control M ns를 만들어 pod 띄움(argo workflow와 같음)
  - argo와 같은점은 작업 에이전트가 EKS 노드자원을 활용한다는 것이고, 다른점은 실제 실행되는 인스턴스는 AWS 자원이라는 점
크게 다음과 같은 허들이 있음
1. 기존 Control M 솔루션 패치 해야 함
2. Jflow에서 패치 된 Control M 을 트리거링할 수 있도록 해야 함.
  1. 이 건은 Jflow 개발한 회사한테 물어봐야할듯  

AWS 내에서 건드는건 어떻게든 하면 되는데 위 두 가지 허들은 인프라담당자, 솔루션구매사와 협의가 필요한 영역이기 때문에 쉽지 않을 수 있음. 따라서 우선 현재 실행 구조에서 AWS Lambda, Batch를 호출하는 구조를 미리 POC 해 두자.


## AWS Lambda



## AWS Batch
