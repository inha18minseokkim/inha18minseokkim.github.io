---
title: "**Inference on AWS Trainium and Amazon EKS using vLLM**"
date: 2025-12-02
tags: [미지정]
category:
  - 기술
---
tranium 칩 새로 나옴 ec2 tranium instance 사용하면됨

Qwen3 1.7B using vLLM and Amazon EKS

![](attachment:4defbf6b-a0c3-4497-bbf3-e5cb35bd29e3:image.png)


EKS 클러스터는 핵심 기능과 워크숍별 기능을 제공하기 위해 여러 가지 애드온으로 구성되어 있습니다. 현재 클러스터에서 무엇이 실행되고 있는지, 그리고 그 이유는 무엇인지 살펴보겠습니다.
[**AWS FSX CSI 드라이버**](https://catalog.workshops.aws/event/dashboard/en-US/workshop/100-introduction/01-explore-the-environment#aws-fsx-csi-driver)
[Lustre용 Amazon](https://aws.amazon.com/fsx/lustre/) FSx[ ](https://aws.amazon.com/fsx/lustre/)GenAI 워크로드에 필수적인 고성능 파일 스토리지를 제공하기 위해 EKS와 통합되며 [CSI 드라이버 ](https://github.com/kubernetes-sigs/aws-fsx-csi-driver)Kubernetes 클러스터에서 이러한 파일 시스템을 관리하기 위해 컨테이너 스토리지 인터페이스(CSI) 사양을 구현합니다.
FSx CSI 드라이버는 두 가지 주요 구성 요소로 구성됩니다.
- **컨트롤러 포드(fsx-csi-controller-*)** : FSx for Lustre 파일 시스템 프로비저닝 및 삭제와 같은 볼륨 관리 작업을 처리합니다. 일반적으로 고가용성을 위해 여러 복제본을 사용하는 배포 형태로 실행됩니다.
- **노드 포드(fsx-csi-node-*):** 클러스터의 모든 노드에서 실행되고 마운트 작업을 처리하여 해당 노드에서 실행되는 포드에서 FSx 볼륨을 사용할 수 있도록 합니다.
[**카펜터**](https://catalog.workshops.aws/event/dashboard/en-US/workshop/100-introduction/01-explore-the-environment#karpenter)
[카펜터 ](https://karpenter.sh/)쿠버네티스 클러스터에 자동 노드 확장 기능을 제공하는 오픈소스 노드 프로비저닝 프로젝트입니다. 다음과 같은 기능을 통해 클러스터 리소스 활용도를 최적화합니다.
- Pod 요구 사항에 따라 적절한 크기의 노드를 자동으로 프로비저닝
- 변화하는 애플리케이션 요구 사항에 신속하게 대응
- NodeClass를 사용하여 노드의 기본 구성 정의
- 제약 조건 및 요구 사항을 사용하여 워크로드가 실행되어야 하는 위치를 지정하기 위한 NodePool 관리
[**AWS 로드 밸런서 컨트롤러**](https://catalog.workshops.aws/event/dashboard/en-US/workshop/100-introduction/01-explore-the-environment#aws-load-balancer-controller)
AWS [로드 밸런서 컨트롤러 ](https://kubernetes-sigs.github.io/aws-load-balancer-controller/latest/)Kubernetes 클러스터용 AWS Elastic Load Balancer를 관리합니다. 다음과 같은 기능을 제공합니다.
- Kubernetes Ingress 리소스에 대한 애플리케이션 로드 밸런서(ALB) 생성
- LoadBalancer 유형의 Kubernetes 서비스 리소스에 대한 네트워크 로드 밸런서(NLB) 생성
- 포드에 대한 효율적인 라우팅을 위한 대상 그룹 바인딩 관리
- DDoS 보호를 위한 AWS Shield 지원

[**기본 클러스터 추가 기능**](https://catalog.workshops.aws/event/dashboard/en-US/workshop/100-introduction/01-explore-the-environment#default-cluster-add-ons)
다음 추가 기능은 필수 클러스터 기능을 제공합니다.
- **CoreDNS**
  - : 클러스터 DNS 확인을 처리합니다.
- **kube-proxy**
  - : Pod 네트워킹 및 로드 밸런싱을 관리합니다.
- **VPC CNI**
  - : AWS VPC IP 주소를 사용하여 Pod 네트워킹을 제공합니다.
- **EKS Pod Identity Agent**
  - : EKS Pod Identity는 Amazon EC2 인스턴스 프로필이 Amazon EC2 인스턴스에 자격 증명을 제공하는 방식과 유사하게 애플리케이션의 자격 증명을 관리하는 기능을 제공합니다.
- **Amazon CloudWatch Observability**
  - : CloudWatch Container Insights 및 애플리케이션 성능 모니터링을 통해 EKS 클러스터에 대한 포괄적인 모니터링, 로깅 및 관찰 기능을 제공합니다.



# kubectl을 사용하여 Observability Stack 탐색

이 섹션에서는 AWS Neuron 가속기를 사용하여 Amazon EKS에서 LLM 추론 워크로드를 모니터링하는 CloudWatch Container Insights 관찰 스택을 살펴보겠습니다.
**CloudWatch 컨테이너 인사이트 개요**
[이 워크숍에서는 Helm을](https://helm.sh/) 사용하여 EKS 클러스터에 CloudWatch Observability 추가 기능이 사전 설치되었습니다.[ ](https://helm.sh/)컨테이너화된 애플리케이션에서 메트릭과 로그를 자동으로 수집, 집계, 시각화하는 완전 관리형 관찰 솔루션을 제공합니다.
**주요 구성 요소**
CloudWatch Observability 추가 기능에는 함께 작동하는 여러 구성 요소가 포함되어 있습니다.
- [**CloudWatch 에이전트**](https://github.com/aws/amazon-cloudwatch-agent)
  - : 컨테이너 및 Pod 메트릭(CPU, 메모리, 네트워크, 디스크)을 수집합니다.
- [**유창한 비트**](https://fluentbit.io/)
  - : 컨테이너 로그를 수집하여 CloudWatch Logs로 전달합니다.
- [**뉴런 모니터**](https://awsdocs-neuron.readthedocs-hosted.com/en/latest/tools/neuron-sys-tools/neuron-monitor-user-guide.html)
  - : Trainium/Inferentia 노드에서 Neuron 하드웨어 메트릭을 노출합니다.
- [**CloudWatch 에이전트 운영자**](https://github.com/aws/amazon-cloudwatch-agent-operator)
  - : 관찰성 구성요소를 관리하고 조율합니다.
모든 구성 요소는 네임스페이스에서 실행되며 `amazon-cloudwatch`AWS에서 완전히 관리됩니다.
**관찰성 스택 탐색**
**모든 CloudWatch 구성 요소 보기**
먼저 클러스터에서 무엇이 실행되고 있는지 살펴보겠습니다.
`1
2
3
4
5
# View all CloudWatch components
kubectl get pods -n amazon-cloudwatch

# Check the DaemonSets
kubectl get daemonset -n amazon-cloudwatch`
여러 개의 포드가 실행되는 것을 볼 수 있습니다.
- `cloudwatch-agent-*`
  - : 각 노드에서 실행하여 메트릭을 수집합니다.
- `fluent-bit-*`
  - : 각 노드에서 실행하여 로그를 수집합니다.
- `neuron-monitor-*`
  - : Neuron 지원 노드에서만 실행
- `amazon-cloudwatch-observability-controller-manager-*`
  - : 스택 관리
**뉴런 모니터 이해**
Neuron Monitor는 CloudWatch 에이전트 운영자에 의해 자동으로 배포되어 AWS Neuron 가속기에서 하드웨어 수준 메트릭을 수집합니다.
**Neuron Monitor 리소스 보기:**
`1
2
# Check the Neuron Monitor DaemonSet
kubectl get daemonset neuron-monitor -n amazon-cloudwatch`
예상 출력:
`NAME             DESIRED   CURRENT   READY   UP-TO-DATE   AVAILABLE   NODE SELECTOR            AGE
neuron-monitor   1         1         1       1            1           kubernetes.io/os=linux   (x)h(yy)m`
`1
2
# View the Neuron Monitor service
kubectl get service neuron-monitor-service -n amazon-cloudwatch`
예상 출력:
`NAME                     TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)    AGE
neuron-monitor-service   ClusterIP   172.20.xxx.xxx   <none>        8000/TCP   4h18m`
`1
2
# See which nodes are running Neuron Monitor
kubectl get pods -l app.kubernetes.io/name=neuron-monitor -n amazon-cloudwatch -o wide`
예상 출력:
`NAME                   READY   STATUS    RESTARTS   AGE    IP            NODE                                        NOMINATED NODE   READINESS GATES
neuron-monitor-xxxx   1/1     Running   0          4h9m   10.0.xx.xxx   ip-10-0-xx-xxx.sa-east-1.compute.internal   <none>           <none>`
**뉴런 모니터 구성**
CloudWatch 에이전트 운영자는 Neuron 가속기가 있는 노드에서만 실행되도록 Neuron Monitor를 지능적으로 구성합니다.
`1
2
# View the DaemonSet configuration
kubectl get daemonset neuron-monitor -n amazon-cloudwatch -o yaml | grep -A 30 "spec:"`
**주요 구성 기능:**
**자동 노드 선택:** Neuron Monitor는 노드 친화성을 사용하여 특정 인스턴스 유형을 타겟팅합니다.
- **Trainium**
  - : trn1.2xlarge, trn1.32xlarge, trn1n.32xlarge, trn2.3xlarge, trn2.48xlarge, trn2a.48xlarge, trn2n.48xlarge, trn2u.48xlarge
- **추론**
  - : inf1.xlarge, inf1.2xlarge, inf1.6xlarge, inf1.24xlarge
**운영자 관리 라벨:**
- `app.kubernetes.io/name: neuron-monitor`
- `app.kubernetes.io/component: neuron-monitor`
- `app.kubernetes.io/managed-by: amazon-cloudwatch-agent-operator`
- `app.kubernetes.io/part-of: amazon-cloudwatch-agent`
**메모**
CloudWatch 에이전트 운영자는 Neuron Monitor를 자동으로 관리합니다. DaemonSet이 Neuron 가속기가 있는 노드에만 배포되고, 최신 상태를 유지하며, 지표 수집을 위해 CloudWatch 에이전트와 원활하게 통합되도록 보장합니다.
**뉴런 모니터 상태 확인**
Neuron Monitor가 실행 중이고 메트릭을 수집하고 있는지 확인하세요.
`1
2
3
4
5
# Get the neuron-monitor pod name
NAME=$(kubectl get pods -l app.kubernetes.io/name=neuron-monitor -n amazon-cloudwatch -o jsonpath='{.items[0].metadata.name}')

# Display the pod name
echo "Neuron Monitor pod: $NAME"`
예상 출력:
`Neuron Monitor pod: neuron-monitor-xxxx`
`1
2
# Check the pod status
kubectl get pod $NAME -n amazon-cloudwatch`
예상 출력:
`NAME                   READY   STATUS    RESTARTS   AGE
neuron-monitor-xxxx   1/1     Running   0          4h13m`
`1
2
# View the pod logs
kubectl logs -n amazon-cloudwatch $NAME --tail=20`
예상 로그 출력:
`Running neuron-monitor (9) and neuron-monitor-prometheus (10)`
이는 뉴런 모니터 수집기와 Prometheus 내보내기 프로그램이 모두 성공적으로 실행되고 있음을 나타냅니다.
**뉴런 리소스 이해**
**노드 용량 및 리소스**
노드에서 사용 가능한 Neuron 리소스를 확인하세요.
`1
2
3
4
5
6
# List all nodes with Neuron devices
kubectl get nodes -l "neuron.amazonaws.com/neuron-device=true" -o wide

# Check node capacity for Neuron resources
NODE_NAME=$(kubectl get nodes -l "neuron.amazonaws.com/neuron-device=true" -o jsonpath='{.items[0].metadata.name}')
kubectl describe node $NODE_NAME | grep -A 10 "Capacity:"`
다음과 같은 출력이 표시되어야 합니다.
`NAME                                        STATUS   ROLES    AGE    VERSION               INTERNAL-IP   EXTERNAL-IP   OS-IMAGE                       KERNEL-VERSION                   CONTAINER-RUNTIME
ip-10-0-45-129.sa-east-1.compute.internal   Ready    <none>   108m   v1.34.1-eks-113cf36   10.0.45.129   <none>        Amazon Linux 2023.8.20250915   6.12.40-64.114.amzn2023.x86_64   containerd://2.1.4
Capacity:
  aws.amazon.com/neuron:      1
  aws.amazon.com/neuroncore:  4
  cpu:                        12
  ephemeral-storage:          463508352Ki
  hugepages-1Gi:              0
  hugepages-2Mi:              0
  memory:                     130836344Ki
  pods:                       30
Allocatable:
  aws.amazon.com/neuron:      1`
**리소스 분석:**
- **aws.amazon.com/neuron**
  - : 예약 가능한 Neuron 장치 리소스(칩당 1개)
- **aws.amazon.com/neuroncore**
  - : Neuron 장치 내의 논리 컴퓨팅 유닛(trn1.2xlarge의 경우 2개)
- **aws.amazon.com/neurondevice**
  - : Physical Neuron 가속기 칩 개수
**CloudWatch 관찰성 아키텍처**
워크로드에서 CloudWatch로 메트릭이 흐르는 방식 이해:
**아키텍처 계층**
**1. 관리 계층**
- **CloudWatch Agent Operator**
  - : Neuron Monitor 및 기타 모니터링 DaemonSets를 관리합니다.
- **Controller Manager**
  - : 전체 관찰성 스택을 조율합니다.
**2. 데이터 수집 계층**
- **CloudWatch 에이전트**
  - : 모든 노드에서 실행되고, 메트릭을 수집하고, Prometheus 엔드포인트를 스크래핑합니다.
- **Fluent Bit**
  - : 모든 노드에서 실행되고 컨테이너 로그를 수집하여 전달합니다.
- **Neuron Monitor**
  - : Neuron 노드에서 실행되고 하드웨어 메트릭을 노출합니다.
**3. 메트릭 흐름**
1. Neuron Monitor는 Neuron 장치에서 하드웨어 메트릭을 수집합니다.
2. 메트릭은 포트 9010에서 Prometheus 형식으로 노출됩니다.
3. `containerInsightsNeuronMonitorScraper`
  - CloudWatch 에이전트는 작업을 사용하여 메트릭을 검색하고 스크래핑합니다.
4. CloudWatch 에이전트가 CloudWatch Metrics 서비스로 메트릭을 보냅니다.
5. **메트릭은 ContainerInsightsContainerInsights/Prometheus**
  - 및
  - 네임스페이스 아래의 CloudWatch에 나타납니다.
**4. 데이터 저장**
- 모든 메트릭 → **CloudWatch 메트릭**
- 모든 로그 → **CloudWatch 로그**
- 클러스터, 네임스페이스, 포드 및 컨테이너 차원별로 구성됨
**뉴런 모니터 서비스 엔드포인트**
Neuron Monitor 서비스는 메트릭 수집을 위한 안정적인 엔드포인트를 제공합니다.
`1
2
3
4
5
# View service details
kubectl get service neuron-monitor-service -n amazon-cloudwatch -o yaml

# Check service endpoints
kubectl get endpoints neuron-monitor-service -n amazon-cloudwatch`
이 서비스는 포트 9010에서 **헤드리스 서비스** (ClusterIP: 없음)로 구성되어 CloudWatch 에이전트가 모든 Neuron Monitor 포드에서 동적으로 메트릭을 검색하고 스크래핑할 수 있도록 합니다.
**CloudWatch 에이전트 활동**
CloudWatch 에이전트의 작동 상태를 모니터링합니다.
`1
2
# View recent CloudWatch agent activity
kubectl logs -l app.kubernetes.io/name=cloudwatch-agent -n amazon-cloudwatch --tail=100`
일반적인 운영 로그 패턴은 다음과 같습니다.
- `collect data from K8s API Server...`
  - (약 60초마다)
- `Fetch ebs volumes from ec2 api`
  - (약 5분마다)
- 모니터링 대상에 대한 스크랩 작업 구성
- 클러스터 수준 메트릭 수집을 위한 리더 선출
**요약**
이 섹션에서는 다음 내용을 살펴보았습니다.
✅ **CloudWatch 컨테이너 인사이트 구성 요소:**
- 모든 노드에서 메트릭을 수집하는 CloudWatch 에이전트
- Fluent Bit가 모든 컨테이너에서 로그를 수집합니다.
- 관찰성 스택을 관리하는 CloudWatch 에이전트 운영자
- 자동 메트릭 및 로그 수집이 활성화되었습니다.
✅ **뉴런 모니터 배포:**
- CloudWatch 에이전트 운영자에 의해 자동으로 배포 및 관리됨
- 노드 친화성을 사용하여 Neuron 지원 인스턴스 유형에서만 실행
- 포트 9010에서 헤드리스 서비스를 통해 하드웨어 메트릭 노출
- 자동 메트릭 수집을 위해 CloudWatch 에이전트와 통합됨
✅ **관찰성 아키텍처:**
- Neuron 장치에서 CloudWatch로의 메트릭 흐름을 이해했습니다.
- CloudWatch 에이전트 `containerInsightsNeuronMonitorScraper`
  - 구성이 확인되었습니다.
- Neuron Monitor Pod에 대한 검증된 Kubernetes 서비스 검색
- Neuron 리소스 유형에 대해 알아보았습니다: `neuronneuroncoreneurondevice`
  - ,
  - , 및
✅ **노드 리소스:**
- Neuron 가속기를 사용하여 식별된 노드
- Neuron 워크로드에 대한 노드 용량 검토됨
- 뉴런 노드에 적절한 포드 배치가 확인되었습니다.
**중요한**
CloudWatch 관측 스택의 모든 구성 요소는 CloudWatch 에이전트 운영자가 완벽하게 관리합니다. DaemonSet이나 구성은 운영자가 자동으로 제어하고 업데이트하므로 수동으로 수정해서는 **안 됩니다.**
**다음 단계**
다음 섹션에서는 다음을 다룹니다.
- CloudWatch Logs Insights를 사용하여 프로그래밍 방식으로 메트릭과 로그를 쿼리하고 분석합니다.
- CloudWatch 콘솔을 탐색하여 Container Insights 대시보드를 시각화합니다.
- Neuron별 성능 측정 항목을 보고 사용자 정의 시각화를 만듭니다.
- vLLM 추론 워크로드에 대한 모니터링 구성
- 사전 경고를 위해 CloudWatch 알람을 설정하세요


# AWS 콘솔에서 컨테이너 인사이트 탐색

이 섹션에서는 CloudWatch Logs Insights를 사용하여 Neuron 기반 LLM 추론 워크로드의 지표와 로그를 쿼리하고 분석합니다. 이를 통해 상세 분석 및 문제 해결을 위해 관측 가능성 데이터에 프로그래밍 방식으로 액세스할 수 있습니다.
**CloudWatch Logs Insights 개요**
CloudWatch Logs Insights를 사용하면 로그 데이터를 대화형으로 검색하고 분석할 수 있습니다. 컨테이너 로그는 Fluent Bit에서 수집되어 Kubernetes 메타데이터와 함께 CloudWatch Logs로 전달되므로 Pod, 네임스페이스 및 컨테이너별로 쉽게 필터링하고 분석할 수 있습니다.
**애플리케이션 로그 쿼리**
모든 컨테이너의 애플리케이션 로그는 원시 형식과 구조화된 형식으로 CloudWatch Logs에 저장되므로 쿼리가 더 쉽습니다.
**CloudWatch Logs Insights에 액세스**
1. **CloudWatchLogs**
  - →
  - → **Logs Insights** 로 이동합니다.

![](https://static.us-east-1.prod.workshops.aws/16fcdee6-0470-4f3c-a22c-330db97cd4b4/static/images/400-observability/CloudWatch-Logs-LogsInsights.png?Key-Pair-Id=K36Q2WVO3JP7QD&Policy=eyJTdGF0ZW1lbnQiOlt7IlJlc291cmNlIjoiaHR0cHM6Ly9zdGF0aWMudXMtZWFzdC0xLnByb2Qud29ya3Nob3BzLmF3cy8xNmZjZGVlNi0wNDcwLTRmM2MtYTIyYy0zMzBkYjk3Y2Q0YjQvKiIsIkNvbmRpdGlvbiI6eyJEYXRlTGVzc1RoYW4iOnsiQVdTOkVwb2NoVGltZSI6MTc2NTMxMzA2MX19fV19&Signature=TP9v-rrB3cm33flNz6ykrHXZwydSRwLKMDNNlp2l5EGEV%7ErpqP-U9CV1oxchZy-DC6AKJ7PPweKWIfAYgnwNvUkB8LVxMuSaQt4oObnEs5bKgaNHHkx3Dj4rasRkAgfescGDM-ACkdaXC%7EI%7Eu8K%7E3soyzkTiGO7LdyhuqbpNvJ3EEy7HSYh-rO-nlQaNTxwiqe%7Em3SwrwbqFg6q2IZ2XeRIPlT4ogxql3Eg7tFT8%7E6sKAknWws6c9Gr9jOp09t0Wx8YyCtdPsaN2fqf6raGYvg7WTjSUVroyWDvOhKtiEJ8R9qnb%7EWulaXema8HkFz8KHt198EJCG1O%7EVAoV0Xt5UA__)

2. 로그 그룹 선택:`/aws/containerinsights/aim-320/application`

![](https://static.us-east-1.prod.workshops.aws/16fcdee6-0470-4f3c-a22c-330db97cd4b4/static/images/400-observability/CloudWatch-Logs-Selection-criteria.png?Key-Pair-Id=K36Q2WVO3JP7QD&Policy=eyJTdGF0ZW1lbnQiOlt7IlJlc291cmNlIjoiaHR0cHM6Ly9zdGF0aWMudXMtZWFzdC0xLnByb2Qud29ya3Nob3BzLmF3cy8xNmZjZGVlNi0wNDcwLTRmM2MtYTIyYy0zMzBkYjk3Y2Q0YjQvKiIsIkNvbmRpdGlvbiI6eyJEYXRlTGVzc1RoYW4iOnsiQVdTOkVwb2NoVGltZSI6MTc2NTMxMzA2MX19fV19&Signature=TP9v-rrB3cm33flNz6ykrHXZwydSRwLKMDNNlp2l5EGEV%7ErpqP-U9CV1oxchZy-DC6AKJ7PPweKWIfAYgnwNvUkB8LVxMuSaQt4oObnEs5bKgaNHHkx3Dj4rasRkAgfescGDM-ACkdaXC%7EI%7Eu8K%7E3soyzkTiGO7LdyhuqbpNvJ3EEy7HSYh-rO-nlQaNTxwiqe%7Em3SwrwbqFg6q2IZ2XeRIPlT4ogxql3Eg7tFT8%7E6sKAknWws6c9Gr9jOp09t0Wx8YyCtdPsaN2fqf6raGYvg7WTjSUVroyWDvOhKtiEJ8R9qnb%7EWulaXema8HkFz8KHt198EJCG1O%7EVAoV0Xt5UA__)


![](https://static.us-east-1.prod.workshops.aws/16fcdee6-0470-4f3c-a22c-330db97cd4b4/static/images/400-observability/Cloudwatch-application-logs.png?Key-Pair-Id=K36Q2WVO3JP7QD&Policy=eyJTdGF0ZW1lbnQiOlt7IlJlc291cmNlIjoiaHR0cHM6Ly9zdGF0aWMudXMtZWFzdC0xLnByb2Qud29ya3Nob3BzLmF3cy8xNmZjZGVlNi0wNDcwLTRmM2MtYTIyYy0zMzBkYjk3Y2Q0YjQvKiIsIkNvbmRpdGlvbiI6eyJEYXRlTGVzc1RoYW4iOnsiQVdTOkVwb2NoVGltZSI6MTc2NTMxMzA2MX19fV19&Signature=TP9v-rrB3cm33flNz6ykrHXZwydSRwLKMDNNlp2l5EGEV%7ErpqP-U9CV1oxchZy-DC6AKJ7PPweKWIfAYgnwNvUkB8LVxMuSaQt4oObnEs5bKgaNHHkx3Dj4rasRkAgfescGDM-ACkdaXC%7EI%7Eu8K%7E3soyzkTiGO7LdyhuqbpNvJ3EEy7HSYh-rO-nlQaNTxwiqe%7Em3SwrwbqFg6q2IZ2XeRIPlT4ogxql3Eg7tFT8%7E6sKAknWws6c9Gr9jOp09t0Wx8YyCtdPsaN2fqf6raGYvg7WTjSUVroyWDvOhKtiEJ8R9qnb%7EWulaXema8HkFz8KHt198EJCG1O%7EVAoV0Xt5UA__)

3. 아래 쿼리를 사용하여 애플리케이션 로그를 분석하세요.
**유용한 애플리케이션 로그 쿼리**
**Neuron Monitor 로그 검색:**
`1
2
3
4
fields @timestamp, kubernetes.pod_name, log
| filter kubernetes.pod_name like /qwen*/
| sort @timestamp desc
| limit 20`
컨테이너 로그에는 쿠버네티스 메타데이터(포드 이름, 네임스페이스, 컨테이너 이름)가 자동으로 포함됩니다. 실제 로그 메시지는 필드에 있습니다 `log`.
**성능 로그 쿼리**
성능 로그 그룹에는 CloudWatch 에이전트가 수집한 Neuron 리소스 메트릭을 포함한 자세한 메트릭 데이터가 포함되어 있습니다.
**성능 로그 액세스**
1. **CloudWatchLogs**
  - →
  - → **Logs Insights** 로 이동합니다.

![](https://static.us-east-1.prod.workshops.aws/16fcdee6-0470-4f3c-a22c-330db97cd4b4/static/images/400-observability/CloudWatch-Logs-LogsInsights.png?Key-Pair-Id=K36Q2WVO3JP7QD&Policy=eyJTdGF0ZW1lbnQiOlt7IlJlc291cmNlIjoiaHR0cHM6Ly9zdGF0aWMudXMtZWFzdC0xLnByb2Qud29ya3Nob3BzLmF3cy8xNmZjZGVlNi0wNDcwLTRmM2MtYTIyYy0zMzBkYjk3Y2Q0YjQvKiIsIkNvbmRpdGlvbiI6eyJEYXRlTGVzc1RoYW4iOnsiQVdTOkVwb2NoVGltZSI6MTc2NTMxMzA2MX19fV19&Signature=TP9v-rrB3cm33flNz6ykrHXZwydSRwLKMDNNlp2l5EGEV%7ErpqP-U9CV1oxchZy-DC6AKJ7PPweKWIfAYgnwNvUkB8LVxMuSaQt4oObnEs5bKgaNHHkx3Dj4rasRkAgfescGDM-ACkdaXC%7EI%7Eu8K%7E3soyzkTiGO7LdyhuqbpNvJ3EEy7HSYh-rO-nlQaNTxwiqe%7Em3SwrwbqFg6q2IZ2XeRIPlT4ogxql3Eg7tFT8%7E6sKAknWws6c9Gr9jOp09t0Wx8YyCtdPsaN2fqf6raGYvg7WTjSUVroyWDvOhKtiEJ8R9qnb%7EWulaXema8HkFz8KHt198EJCG1O%7EVAoV0Xt5UA__)

2. 로그 그룹 선택:`/aws/containerinsights/aim-320/performance`

![](https://static.us-east-1.prod.workshops.aws/16fcdee6-0470-4f3c-a22c-330db97cd4b4/static/images/400-observability/CloudWatch-Logs-Selection-criteria.png?Key-Pair-Id=K36Q2WVO3JP7QD&Policy=eyJTdGF0ZW1lbnQiOlt7IlJlc291cmNlIjoiaHR0cHM6Ly9zdGF0aWMudXMtZWFzdC0xLnByb2Qud29ya3Nob3BzLmF3cy8xNmZjZGVlNi0wNDcwLTRmM2MtYTIyYy0zMzBkYjk3Y2Q0YjQvKiIsIkNvbmRpdGlvbiI6eyJEYXRlTGVzc1RoYW4iOnsiQVdTOkVwb2NoVGltZSI6MTc2NTMxMzA2MX19fV19&Signature=TP9v-rrB3cm33flNz6ykrHXZwydSRwLKMDNNlp2l5EGEV%7ErpqP-U9CV1oxchZy-DC6AKJ7PPweKWIfAYgnwNvUkB8LVxMuSaQt4oObnEs5bKgaNHHkx3Dj4rasRkAgfescGDM-ACkdaXC%7EI%7Eu8K%7E3soyzkTiGO7LdyhuqbpNvJ3EEy7HSYh-rO-nlQaNTxwiqe%7Em3SwrwbqFg6q2IZ2XeRIPlT4ogxql3Eg7tFT8%7E6sKAknWws6c9Gr9jOp09t0Wx8YyCtdPsaN2fqf6raGYvg7WTjSUVroyWDvOhKtiEJ8R9qnb%7EWulaXema8HkFz8KHt198EJCG1O%7EVAoV0Xt5UA__)


![](https://static.us-east-1.prod.workshops.aws/16fcdee6-0470-4f3c-a22c-330db97cd4b4/static/images/400-observability/CloudWatch-performance-logs.png?Key-Pair-Id=K36Q2WVO3JP7QD&Policy=eyJTdGF0ZW1lbnQiOlt7IlJlc291cmNlIjoiaHR0cHM6Ly9zdGF0aWMudXMtZWFzdC0xLnByb2Qud29ya3Nob3BzLmF3cy8xNmZjZGVlNi0wNDcwLTRmM2MtYTIyYy0zMzBkYjk3Y2Q0YjQvKiIsIkNvbmRpdGlvbiI6eyJEYXRlTGVzc1RoYW4iOnsiQVdTOkVwb2NoVGltZSI6MTc2NTMxMzA2MX19fV19&Signature=TP9v-rrB3cm33flNz6ykrHXZwydSRwLKMDNNlp2l5EGEV%7ErpqP-U9CV1oxchZy-DC6AKJ7PPweKWIfAYgnwNvUkB8LVxMuSaQt4oObnEs5bKgaNHHkx3Dj4rasRkAgfescGDM-ACkdaXC%7EI%7Eu8K%7E3soyzkTiGO7LdyhuqbpNvJ3EEy7HSYh-rO-nlQaNTxwiqe%7Em3SwrwbqFg6q2IZ2XeRIPlT4ogxql3Eg7tFT8%7E6sKAknWws6c9Gr9jOp09t0Wx8YyCtdPsaN2fqf6raGYvg7WTjSUVroyWDvOhKtiEJ8R9qnb%7EWulaXema8HkFz8KHt198EJCG1O%7EVAoV0Xt5UA__)

1. 아래 쿼리를 사용하여 성능 지표를 분석하세요.
**Pod 성능 쿼리**
**Neuron 리소스를 포함한 쿼리 포드 메트릭:**
`1
2
3
4
5
6
fields @timestamp, Type, PodName, Namespace, pod_cpu_utilization, pod_memory_utilization, pod_neuroncore_usage_total, pod_neuroncore_reserved_capacity
| filter Namespace = "default"
| filter PodName = "qwen"
| filter Type = "Pod"
| sort @timestamp desc
| limit 100`
**Neuron 관련 Pod 메트릭을 모두 쿼리합니다.**
`1
2
3
4
5
fields @timestamp, PodName, pod_neuroncore_limit, pod_neuroncore_request, pod_neuroncore_reserved_capacity, pod_neuroncore_usage_total, pod_cpu_utilization, pod_memory_utilization
| filter Type = "Pod"
| filter pod_neuroncore_usage_total > 0
| sort @timestamp desc
| limit 100`
**Neuron Monitor 포드 성능 모니터링:**
`1
2
3
4
5
6
fields @timestamp, Type, PodName, Namespace, pod_cpu_utilization, pod_memory_utilization, pod_number_of_container_restarts
| filter Namespace = "amazon-cloudwatch"
| filter PodName like /neuron-monitor/
| filter Type = "Pod"
| sort @timestamp desc
| limit 100`
**노드 성능 쿼리**
**노드 수준 메트릭 쿼리:**
`1
2
3
4
fields @timestamp, Type, NodeName, node_cpu_utilization, node_memory_utilization, node_network_total_bytes, node_filesystem_utilization
| filter Type = "Node"
| sort @timestamp desc
| limit 50`
**CPU 사용량이 높은 노드를 식별합니다.** 쿼리의 임계값에 따라 정의된 대로 CPU 사용량이 높지 않으면 쿼리를 실행한 후 아무런 결과도 표시되지 않습니다.
`1
2
3
4
5
fields @timestamp, NodeName, node_cpu_utilization, node_memory_utilization
| filter Type = "Node"
| filter node_cpu_utilization > 70
| sort node_cpu_utilization desc
| limit 20`
일부 로그를 관찰하기 위해 임계값을 낮추십시오.
`1
2
3
4
5
fields @timestamp, NodeName, node_cpu_utilization, node_memory_utilization
| filter Type = "Node"
| filter node_cpu_utilization > 1
| sort node_cpu_utilization desc
| limit 20`
**성능 로그에서 사용 가능한 뉴런 메트릭**
**뉴런 리소스 메트릭**
성능 로그에는 다음과 같은 Neuron 관련 필드가 포함됩니다.
- `pod_neuroncore_limit`
  - : 포드에 할당된 최대 NeuronCores
- `pod_neuroncore_request`
  - : Pod에서 요청한 NeuronCores
- `pod_neuroncore_reserved_capacity`
  - : 노드의 NeuronCores 예약 비율(%)
- `pod_neuroncore_usage_total`
  - : 포드에서 사용되는 총 NeuronCores
자세한 하드웨어 활용도 지표(코어당 활용도 백분율, 메모리 사용량, 실행 지연 시간 등)를 알아보려면 Neuron Monitor가 **ContainerInsights/Prometheus** 네임스페이스 아래 CloudWatch Metrics에 노출하는 Prometheus 지표를 쿼리합니다.
**모니터링할 주요 지표**
Neuron 워크로드를 쿼리하고 모니터링할 때 다음 측정 항목에 중점을 두세요.
**시스템 상태 지표**
**노드 수준:**
- `node_cpu_utilization`
  - : 전체 노드 CPU 사용량
- `node_memory_utilization`
  - : 전체 노드 메모리 사용량
- `node_filesystem_utilization`
  - : 디스크 사용량
- `node_network_total_bytes`
  - : 네트워크 처리량
**포드 수준:**
- `pod_cpu_utilization`
  - : Pod CPU 사용량
- `pod_memory_utilization`
  - : Pod 메모리 사용량
- `pod_number_of_container_restarts`
  - : 포드 안정성 표시기
- `pod_network_rx_bytespod_network_tx_bytes`
  - /
  - : Pod 네트워크 트래픽
**뉴런 리소스:**
- `pod_neuroncore_limit`
  - : 할당된 NeuronCores
- `pod_neuroncore_usage_total`
  - : NeuronCores 사용 중
- `pod_neuroncore_reserved_capacity`
  - : 예약된 노드 용량의 백분율
**로그의 애플리케이션 메트릭**
**오류 분석:**
- 오류 패턴 및 실패율
- Pod 수명 주기 이벤트
- 애플리케이션별 오류 메시지
**자원 추세:**
- 시간 경과에 따른 CPU 및 메모리 사용률
- NeuronCore 할당 대 사용 패턴
- 컨테이너 재시작 빈도
**요약**
이 섹션에서는 다음 내용을 알아보았습니다.
✅ **CloudWatch Logs Insights 사용** : 프로그래밍 방식으로 애플리케이션 및 성능 로그 쿼리
✅ **애플리케이션 로그 분석** : 오류 검색, Pod/네임스페이스별 필터링, 문제 조사
✅ **쿼리 성능 지표** : Neuron 리소스 활용도를 포함한 Pod 및 노드 지표 추출
✅ **Neuron 리소스 모니터링** : 성능 로그에서 NeuronCore 할당 및 사용량을 추적합니다.
✅ **사용자 정의 쿼리 작성** : 시간 기반 집계 및 상관 관계 분석 생성
**다음 단계**
다음 섹션에서는 CloudWatch 콘솔의 시각적 인터페이스를 살펴보겠습니다.
- 컨테이너 인사이트 대시보드 탐색
- 토폴로지 시각화를 위해 컨테이너 맵을 사용하세요
- 사전 구축된 성능 모니터링 뷰 살펴보기
- 대시보드 보기 필터링 및 사용자 지정
이러한 시각적 접근 방식은 여기에서 배운 프로그래밍 방식 쿼리를 보완하여 Neuron 워크로드를 모니터링하고 이해하는 여러 가지 방법을 제공합니다.


# CloudWatch 컨테이너 인사이트 대시보드 탐색

이 섹션에서는 CloudWatch Container Insights 콘솔을 탐색하여 그래픽 인터페이스를 사용하여 클러스터 지표를 시각화하고 사전 구축된 대시보드를 살펴보겠습니다.
**CloudWatch 컨테이너 인사이트에 액세스**
CloudWatch Container Insights는 EKS 클러스터의 지표를 자동으로 시각화하는 사전 구축된 대시보드를 제공합니다.
**컨테이너 인사이트로 이동**
1. 열려 있는[**Amazon CloudWatch 콘솔**](https://console.aws.amazon.com/cloudwatch/home#container-insights:infrastructure)
2. 왼쪽 탐색 창에서 **InsightsContainer Insights를 선택합니다.**
  - →
3. 상단의 드롭다운에서 EKS 클러스터 이름을 선택하세요(예: `aim-320`
  - )

![](https://static.us-east-1.prod.workshops.aws/16fcdee6-0470-4f3c-a22c-330db97cd4b4/static/images/400-observability/clusters.png?Key-Pair-Id=K36Q2WVO3JP7QD&Policy=eyJTdGF0ZW1lbnQiOlt7IlJlc291cmNlIjoiaHR0cHM6Ly9zdGF0aWMudXMtZWFzdC0xLnByb2Qud29ya3Nob3BzLmF3cy8xNmZjZGVlNi0wNDcwLTRmM2MtYTIyYy0zMzBkYjk3Y2Q0YjQvKiIsIkNvbmRpdGlvbiI6eyJEYXRlTGVzc1RoYW4iOnsiQVdTOkVwb2NoVGltZSI6MTc2NTMxMzA2MX19fV19&Signature=TP9v-rrB3cm33flNz6ykrHXZwydSRwLKMDNNlp2l5EGEV%7ErpqP-U9CV1oxchZy-DC6AKJ7PPweKWIfAYgnwNvUkB8LVxMuSaQt4oObnEs5bKgaNHHkx3Dj4rasRkAgfescGDM-ACkdaXC%7EI%7Eu8K%7E3soyzkTiGO7LdyhuqbpNvJ3EEy7HSYh-rO-nlQaNTxwiqe%7Em3SwrwbqFg6q2IZ2XeRIPlT4ogxql3Eg7tFT8%7E6sKAknWws6c9Gr9jOp09t0Wx8YyCtdPsaN2fqf6raGYvg7WTjSUVroyWDvOhKtiEJ8R9qnb%7EWulaXema8HkFz8KHt198EJCG1O%7EVAoV0Xt5UA__)

실시간 클러스터 지표가 포함된 **성능 모니터링 대시** 보드를 즉시 볼 수 있습니다 .

![](https://static.us-east-1.prod.workshops.aws/16fcdee6-0470-4f3c-a22c-330db97cd4b4/static/images/400-observability/cluster-summary.png?Key-Pair-Id=K36Q2WVO3JP7QD&Policy=eyJTdGF0ZW1lbnQiOlt7IlJlc291cmNlIjoiaHR0cHM6Ly9zdGF0aWMudXMtZWFzdC0xLnByb2Qud29ya3Nob3BzLmF3cy8xNmZjZGVlNi0wNDcwLTRmM2MtYTIyYy0zMzBkYjk3Y2Q0YjQvKiIsIkNvbmRpdGlvbiI6eyJEYXRlTGVzc1RoYW4iOnsiQVdTOkVwb2NoVGltZSI6MTc2NTMxMzA2MX19fV19&Signature=TP9v-rrB3cm33flNz6ykrHXZwydSRwLKMDNNlp2l5EGEV%7ErpqP-U9CV1oxchZy-DC6AKJ7PPweKWIfAYgnwNvUkB8LVxMuSaQt4oObnEs5bKgaNHHkx3Dj4rasRkAgfescGDM-ACkdaXC%7EI%7Eu8K%7E3soyzkTiGO7LdyhuqbpNvJ3EEy7HSYh-rO-nlQaNTxwiqe%7Em3SwrwbqFg6q2IZ2XeRIPlT4ogxql3Eg7tFT8%7E6sKAknWws6c9Gr9jOp09t0Wx8YyCtdPsaN2fqf6raGYvg7WTjSUVroyWDvOhKtiEJ8R9qnb%7EWulaXema8HkFz8KHt198EJCG1O%7EVAoV0Xt5UA__)

**서비스 보기 탐색**
서비스 보기는 클러스터에서 실행 중인 모든 서비스에 대한 자세한 성능 측정 항목을 제공합니다.
1. 왼쪽의 **성능 대시보드 보기서비스를 클릭합니다.**
  - 섹션 에서
2. **서비스 성능 모니터링 대시**
  - 보드가 표시됩니다.
이 보기에는 다음이 표시됩니다.
- **서비스 요약**
  - : 실행 중인 포드 수, 컨테이너 재시작, CPU 및 메모리 사용률
- **성능 지표**
  - : 각 서비스의 CPU 사용률, 메모리 사용률 및 네트워크 트래픽 그래프

![](https://static.us-east-1.prod.workshops.aws/16fcdee6-0470-4f3c-a22c-330db97cd4b4/static/images/400-observability/services.png?Key-Pair-Id=K36Q2WVO3JP7QD&Policy=eyJTdGF0ZW1lbnQiOlt7IlJlc291cmNlIjoiaHR0cHM6Ly9zdGF0aWMudXMtZWFzdC0xLnByb2Qud29ya3Nob3BzLmF3cy8xNmZjZGVlNi0wNDcwLTRmM2MtYTIyYy0zMzBkYjk3Y2Q0YjQvKiIsIkNvbmRpdGlvbiI6eyJEYXRlTGVzc1RoYW4iOnsiQVdTOkVwb2NoVGltZSI6MTc2NTMxMzA2MX19fV19&Signature=TP9v-rrB3cm33flNz6ykrHXZwydSRwLKMDNNlp2l5EGEV%7ErpqP-U9CV1oxchZy-DC6AKJ7PPweKWIfAYgnwNvUkB8LVxMuSaQt4oObnEs5bKgaNHHkx3Dj4rasRkAgfescGDM-ACkdaXC%7EI%7Eu8K%7E3soyzkTiGO7LdyhuqbpNvJ3EEy7HSYh-rO-nlQaNTxwiqe%7Em3SwrwbqFg6q2IZ2XeRIPlT4ogxql3Eg7tFT8%7E6sKAknWws6c9Gr9jOp09t0Wx8YyCtdPsaN2fqf6raGYvg7WTjSUVroyWDvOhKtiEJ8R9qnb%7EWulaXema8HkFz8KHt198EJCG1O%7EVAoV0Xt5UA__)

성능 그래프는 다음을 보여줍니다.
- **Pod CPU 사용률**
  - : 서비스 간 리소스 사용량
- **Pod 메모리 사용률**
  - : 메모리 소비 패턴
- **네트워크 트래픽**
  - : 각 서비스에 대한 바이트 입출력
- **노드 NeuronCore 활용도**
  - : Neuron 가속기 컴퓨팅 사용량
- **노드 NeuronCore 메모리 사용량**
  - : Neuron 장치의 메모리 소비
- **노드 NeuronCore 사용 가능 용량**
  - : 노드의 남은 NeuronCore 용량
다음으로 필터링할 수 있습니다:
- **클러스터**
  - : 드롭다운에서 클러스터를 선택하세요
- **네임스페이스**
  - : 특정 네임스페이스로 필터링
- **서비스**
  - : 개별 서비스에 대한 메트릭 보기
**컨테이너 맵 뷰 사용**
컨테이너 맵은 클러스터 리소스의 시각적 토폴로지를 제공합니다.
1. 오른쪽 상단의 **지도 보기를**
  - 클릭하세요
2. 클러스터의 리소스는 트리 형태로 표시됩니다.
지도에는 다음이 표시됩니다.
- 녹색 원은 건강한 자원을 나타냅니다.
- 다양한 크기는 리소스 활용 수준을 나타냅니다.
- 연관된 메트릭 세부 정보를 보려면 아무 객체나 클릭하세요.

![](https://static.us-east-1.prod.workshops.aws/16fcdee6-0470-4f3c-a22c-330db97cd4b4/static/images/400-observability/map.png?Key-Pair-Id=K36Q2WVO3JP7QD&Policy=eyJTdGF0ZW1lbnQiOlt7IlJlc291cmNlIjoiaHR0cHM6Ly9zdGF0aWMudXMtZWFzdC0xLnByb2Qud29ya3Nob3BzLmF3cy8xNmZjZGVlNi0wNDcwLTRmM2MtYTIyYy0zMzBkYjk3Y2Q0YjQvKiIsIkNvbmRpdGlvbiI6eyJEYXRlTGVzc1RoYW4iOnsiQVdTOkVwb2NoVGltZSI6MTc2NTMxMzA2MX19fV19&Signature=TP9v-rrB3cm33flNz6ykrHXZwydSRwLKMDNNlp2l5EGEV%7ErpqP-U9CV1oxchZy-DC6AKJ7PPweKWIfAYgnwNvUkB8LVxMuSaQt4oObnEs5bKgaNHHkx3Dj4rasRkAgfescGDM-ACkdaXC%7EI%7Eu8K%7E3soyzkTiGO7LdyhuqbpNvJ3EEy7HSYh-rO-nlQaNTxwiqe%7Em3SwrwbqFg6q2IZ2XeRIPlT4ogxql3Eg7tFT8%7E6sKAknWws6c9Gr9jOp09t0Wx8YyCtdPsaN2fqf6raGYvg7WTjSUVroyWDvOhKtiEJ8R9qnb%7EWulaXema8HkFz8KHt198EJCG1O%7EVAoV0Xt5UA__)

이 시각화는 다음과 같은 데 도움이 됩니다.
- 리소스 핫스팟을 빠르게 식별하세요
- 포드 관계 및 종속성 이해
- 한눈에 성능 문제를 파악하세요
**포드 성능 보기**
개별 포드 성능을 자세히 알아보려면:
1. **목록** 보기를 클릭하여 목록 보기로 돌아갑니다.
2. **성능 대시보드 보기Pod를 클릭합니다.**
  - 섹션 에서
3. **Pod 성능**
  - 표가 표시됩니다.

![](https://static.us-east-1.prod.workshops.aws/16fcdee6-0470-4f3c-a22c-330db97cd4b4/static/images/400-observability/pods.png?Key-Pair-Id=K36Q2WVO3JP7QD&Policy=eyJTdGF0ZW1lbnQiOlt7IlJlc291cmNlIjoiaHR0cHM6Ly9zdGF0aWMudXMtZWFzdC0xLnByb2Qud29ya3Nob3BzLmF3cy8xNmZjZGVlNi0wNDcwLTRmM2MtYTIyYy0zMzBkYjk3Y2Q0YjQvKiIsIkNvbmRpdGlvbiI6eyJEYXRlTGVzc1RoYW4iOnsiQVdTOkVwb2NoVGltZSI6MTc2NTMxMzA2MX19fV19&Signature=TP9v-rrB3cm33flNz6ykrHXZwydSRwLKMDNNlp2l5EGEV%7ErpqP-U9CV1oxchZy-DC6AKJ7PPweKWIfAYgnwNvUkB8LVxMuSaQt4oObnEs5bKgaNHHkx3Dj4rasRkAgfescGDM-ACkdaXC%7EI%7Eu8K%7E3soyzkTiGO7LdyhuqbpNvJ3EEy7HSYh-rO-nlQaNTxwiqe%7Em3SwrwbqFg6q2IZ2XeRIPlT4ogxql3Eg7tFT8%7E6sKAknWws6c9Gr9jOp09t0Wx8YyCtdPsaN2fqf6raGYvg7WTjSUVroyWDvOhKtiEJ8R9qnb%7EWulaXema8HkFz8KHt198EJCG1O%7EVAoV0Xt5UA__)

표에는 다음이 표시됩니다.
- Pod 이름과 네임스페이스
- 마디
- 최대 CPU 사용률(%)
- 최대 메모리 사용률(%)
**Pod 로그 액세스**
**자세한 Pod 로그를 보려면:**
1. 테이블에서 특정 포드를 선택하세요
2. **작업성능 로그 보기**
  - 클릭 →
3. CloudWatch Logs Insights로 리디렉션됩니다.
이렇게 하면 선택한 포드의 성능 데이터를 보여주는 미리 채워진 쿼리가 열리고, 이를 통해 시간 경과에 따른 포드의 동작을 분석할 수 있습니다.
고급 프로그래밍 방식 로그 분석 및 사용자 지정 쿼리에 대해서는 이전 섹션인 CloudWatch Logs Insights를 참조하세요.
**보기 필터링 및 사용자 지정**
왼쪽의 필터 패널을 사용하여 특정 리소스에 초점을 맞추세요.
**사용 가능한 필터**
- **클러스터**
  - : 클러스터를 선택하세요
- **네임스페이스**`defaultamazon-cloudwatchkube-system`
  - : 네임스페이스로 필터링(예:
  - ,
  - ,
  - )
- **서비스**
  - : 특정 서비스 보기
**시간 범위 옵션**
- 상단의 시간 선택기를 사용하세요(1시간, 3시간, 12시간, 1일, 3일, 1주, 사용자 지정)
- 과거 성과를 분석하기 위해 시간 범위를 조정합니다.
- 이는 표시되는 모든 시각화 및 측정 항목에 영향을 미칩니다.
**콘솔에서 Neuron Monitor 찾기**
Neuron Monitor 포드를 시각적으로 찾는 방법:
1. **성능 모니터링Pod 로 변경합니다.**
  - 보기 에서 드롭다운을 "클러스터"에서
2. 필터/검색창에 다음을 입력하세요.`neuron-monitor`
3. 뉴런 모니터 포드의 CPU, 메모리 및 네트워크 메트릭이 표시됩니다.
이는 Neuron Monitor가 실행 중이고 Neuron 지원 노드에서 메트릭을 수집하고 있음을 확인합니다.
**부하를 시뮬레이션하고 Neuron Monitor 메트릭을 확인하세요.**
1. `curl-tester`
  - 합성 부하 실행을 위한 임시 포드 배포
`1
2
3
kubectl run -it curl-tester --rm \
  --image=alpine:3.20 \
  --restart=Never -- sh`
1. 유틸리티 설치
`1
apk add curl jq`
1. `curlqwenqwen.default.svc.cluster.local`
  - 서비스 에 대해 여러 스레드를 실행합니다
  - . 서비스 DNS 엔드포인트를 확인하세요.
`1
2
3
4
5
6
7
8
9
for i in $(seq 1 2); do 
  while true; do 
    curl -s http://qwen.default.svc.cluster.local:8000/v1/completions \
      -H "Content-Type: application/json" \
      -d '{"model":"/models/Qwen3-1.7B-tp2/","prompt":"SF is a","max_tokens":50,"temperature":1}' \
      | jq -r '.choices[0].text'
    sleep 1
  done &
done`
1. `neuron-top`
  - 하나에서 포드까지 실행
`1
kubectl exec -it $(kubectl get po -l model=qwen -o name | head -n1) -- neuron-top`
몇 분 동안 실행한 후 Cloudwatch ContainerInsights에서 관련 메트릭을 찾아보세요.
**Container Insights의 주요 통찰력**
Container Insights는 다음을 자동으로 제공합니다.
✅ **클러스터 상태 개요** : 클러스터 상태 및 리소스 활용도에 대한 빠른 평가
✅ **서비스 수준 측정 항목** : 모든 서비스에 대한 CPU, 메모리 및 네트워크 성능
✅ **시각적 토폴로지** : 리소스 관계를 이해하기 위한 컨테이너 맵
✅ **포드 수준 세부 정보** : 개별 포드 성능 및 로그 액세스
✅ **사용자 정의 필터링** : 네임스페이스, 서비스 또는 워크로드별로 드릴다운
**요약**
이 섹션에서는 다음 내용을 알아보았습니다.
✅ **컨테이너 인사이트 탐색** : CloudWatch 콘솔 및 컨테이너 인사이트 대시보드에 액세스
✅ **서비스 보기 탐색** : 서비스 수준 성능 측정 항목을 시각적으로 모니터링합니다.
✅ **컨테이너 맵 사용** : 클러스터 토폴로지를 시각화하고 리소스 핫스팟을 식별합니다.
✅ **포드 성능 보기** : 개별 포드 메트릭 및 액세스 로그를 자세히 살펴보세요
✅ **필터링 및 사용자 정의** : 시간 범위 및 필터를 사용하여 특정 리소스에 집중하세요
**결론**
이 관측성 모듈에서는 Amazon EKS에서 Neuron 기반 LLM 추론 워크로드를 모니터링하기 위한 CloudWatch Container Insights를 성공적으로 살펴보았습니다. 다음 내용을 학습했습니다.
✅ **관찰성 아키텍처 이해** : CloudWatch 에이전트, Fluent Bit 및 Neuron Monitor가 함께 작동하여 메트릭 및 로그를 수집하는 방식을 살펴보았습니다.
✅ **프로그래밍 방식으로 로그 쿼리** : CloudWatch Logs Insights를 사용하여 애플리케이션 및 성능 데이터 분석
✅ **콘솔을 시각적으로 탐색** : 미리 구축된 대시보드, 성능 보기 및 컨테이너 맵을 탐색했습니다.
✅ **Neuron 리소스 모니터링** : CLI와 GUI를 통해 NeuronCore 할당, 사용량 및 포드 수준 성능 측정 항목을 추적합니다.
✅ **클러스터 토폴로지 시각화** : 여러 인터페이스를 사용하여 리소스 관계를 이해하고 성능 문제를 식별합니다.
CloudWatch Container Insights는 EKS 클러스터를 위한 완전 관리형 관측 솔루션을 제공합니다. 자동 메트릭 수집, 중앙 집중식 로그 집계, 강력한 쿼리 기능, 풍부한 시각화 기능을 통해 AWS Neuron 액셀러레이터에서 실행되는 LLM 추론 워크로드를 모니터링, 문제 해결 및 최적화하는 데 필요한 도구를 제공합니다.
이 모듈에서 구축한 관찰 기반은 최적의 성능을 유지하고, 문제를 빠르게 식별하고, 프로덕션 워크로드에 대한 정보에 입각한 확장 결정을 내리는 데 도움이 됩니다.