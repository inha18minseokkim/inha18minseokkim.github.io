---
title: "Supercharge Lambda functions for security and performance"
date: 2025-12-01
tags: [미지정]
category:
  - 기타
---
람다 핸들러 밖에 공통 빼놓으면 재사용 가능(db커넥션같은거)

1769메가바이트 메모리당 1 vcpu 줌


![](attachment:2c483636-9a3d-476b-ab1a-87d6caab214c:image.png)

람다 사용할때 total performance와 cost 사이의 sweet spot 찾는게 중요할듯
  - 돌려봤을 때 갑자기 비용이 급격히 증가하거나 실행시간이 굳이 더 빨라지지 않는다면 거기서 더이상 할당하지않는걸로..

lambda snapstart > environment initialize 도커 레이어링마냥 언어 레이어까지는 미리 세팅해준다는 뜻인듯. 자바 파이썬닷넷 특정 버전 이상버전만 지원해줌


**주요 내용**
- 메모리 할당은 비용과 성능 모두에 직접적인 영향을 미칩니다.
- 메모리가 더 많다고 해서 항상 비용 효율성이 더 좋아지는 것은 아닙니다.
- 데이터 기반 최적화는 작업 부하에 가장 적합한 지점을 식별하는 데 도움이 됩니다.
- 정기적인 튜닝을 통해 코드가 진화함에 따라 최적의 구성이 보장됩니다.
- 다양한 최적화 전략은 다양한 비즈니스 요구 사항을 충족합니다.
- AWS Compute Optimizer는 프로덕션 사용 패턴을 기반으로 지속적인 권장 사항을 제공합니다.

**이 워크숍에서 Compute Optimizer를 사용하지 않는 이유:** Compute Optimizer는 추천을 생성하기 위해 최소 14일 분의 과거 지표 데이터가 필요합니다. 워크숍 함수가 새로 생성되었기 때문에 사용 가능한 과거 데이터가 충분하지 않습니다. 하지만 프로덕션 Lambda 함수의 경우, Compute Optimizer는 오늘 배운 최적화 기법을 보완하는 훌륭한 도구입니다.

축하합니다! Lambda 함수를 강화하여 보안과 성능을 강화하는 워크숍을 완료하셨습니다.
**당신이 배운 것**
이 워크숍에서는 네 가지 주요 최적화 기술을 살펴보았습니다.
**1. 실행 환경 재사용** Lambda 실행 환경의 작동 방식과 리소스 초기화를 최적화하는 방법을 배웠습니다. 데이터베이스 연결을 핸들러 함수 외부로 이동함으로써 환경 재사용을 통해 지연 시간을 줄이고 성능을 향상시켰습니다.
**2. 매개변수 및 자격 증명 관리** AWS Secrets Manager와 AWS Systems Manager Parameter Store를 사용하여 안전한 자격 증명 관리를 구현했습니다. AWS 매개변수 및 비밀 Lambda 확장 기능을 활용하여 API 호출을 줄이고 로컬 캐싱을 통해 보안과 성능을 모두 향상시켰습니다.
**3. Lambda SnapStart** Lambda SnapStart를 사용하여 콜드 스타트 시간을 획기적으로 줄이는 방법을 알아냈습니다. `@register_before_snapshot`및 를 사용하여 런타임 후크를 구현함으로써 `@register_after_restore`컴퓨팅 집약적인 작업, 정적 파일 로딩 및 네트워크 연결에 대한 초기화를 최적화했습니다.
**4. 람다 파워 튜닝** AWS 람다 파워 튜닝 도구를 사용하여 함수에 맞는 최적의 메모리 구성을 찾았습니다. 다양한 메모리 설정에서 성능 및 비용 지표를 분석하여 컴퓨팅 집약적 워크로드와 메모리 집약적 워크로드 모두에서 지연 시간과 비용 효율성의 균형을 맞추는 방법을 학습했습니다.
**주요 내용**
- **실행 환경을 재사용하면**
  - 반복적인 초기화를 피할 수 있어 대기 시간과 비용을 크게 줄일 수 있습니다.
- **캐싱 확장을 통한 안전한 자격 증명 관리**
  - 로 보안 태세와 성능이 모두 향상됩니다.
- **SnapStart는**
  - 초기화가 많은 함수에서 콜드 스타트를 줄이는 데 매우 효과적입니다.
- **데이터 기반 메모리 최적화는**
  - 성능과 비용의 적절한 균형을 찾는 데 도움이 됩니다.
- **다양한 작업 부하에는 각기 다른 최적화 전략이 필요합니다**
  - . 즉, 컴퓨팅 집약적 작업에 효과적인 전략이 메모리 집약적 작업에는 효과적이지 않을 수 있습니다.
**다음 단계**
서버리스 최적화 여정을 계속하려면 다음을 수행하세요.
1. **이러한 기술을**
  - 프로덕션 Lambda 함수에 적용하세요.
2. 
  - CloudWatch 메트릭 및 로그를 사용하여 **성능 모니터링**
3. 
  - 작업 부하가 진화함에 따라 **반복하고 최적화하세요.**
4. **추가 자료 탐색**
  - :
  - [AWS Lambda 모범 사례](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)
  - [AWS Lambda 파워 튜닝 GitHub](https://github.com/alexcasalboni/aws-lambda-power-tuning)
  - [AWS Lambda SnapStart 문서](https://docs.aws.amazon.com/lambda/latest/dg/snapstart.html)
  - [AWS Well-Architected 프레임워크 - 서버리스 렌즈](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/welcome.html)
이 워크숍에 참여해주셔서 감사합니다!