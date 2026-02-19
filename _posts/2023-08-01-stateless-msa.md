---
title: "Stateless - MSA"
date: 2023-08-01
tags: [MSA, 아키텍처, 백엔드, 인턴]
---

## 멱등성

같은 요청을 여러 번 해도 결과가 동일한 성질. Stateless 설계의 기반이 되는 개념이다.

---

## Stateless

리퀘스트 사이에서 어떠한 정보도 유지하지 않고, 사용하지 않는 시스템을 의미한다.

각각의 Request는 독립적이다. 시스템 내의 어떠한 context나 정보도 있지 않다. (이전에 왔던 리퀘스트들에 대한 정보 또한 없다)

예시: HTTP Request는 기본적으로 Stateless이기 때문에 세션과 쿠키를 사용하여 사용자가 웹사이트를 옮길 때마다 일일이 로그인을 하지 않아도 되게 만든다.

### 분산 환경에서 괜찮은 메커니즘

상태 정보를 공유하지 않아 서버 내부에서 replicated될 수 있고 distributed 될 수 있다.

왜냐? **DATA inconsistency의 문제가 없기 때문**. 왜? 시스템 내에 어떠한 context나 정보도 없으니까!

### Advantages of Stateless Container on MSA

Stateless 하다는 것은, 다음과 같은 특징 및 장점을 지니고 있다.

1. **쉬운 수평적 확장** - 내부에 데이터가 없다 → replica를 여러개 생성해도 데이터 일관성에 문제가 없다. 여러개 복사해놓고 라우터로 묶어서 트래픽 관리가 가능하다.
2. **Fault Tolerance** - 내부에 데이터가 없다 → 실패하면 그냥 껐다 키면 됨. 로딩할 것도 없어서 금방 켜짐 (Kubernetes나 EKS에서 container fail시 그냥 재부팅함)
3. **빠르고 간단한 배포** - monolithic한 환경과 대조적으로 특정한 dependency 없이 배포 가능.
4. **보안성** - shared information이 없기 때문에 공격으로부터 안전.
5. **유연성** - 실체화된 모듈(극단적인 예로 싱글톤 객체의 특정한 데이터)이 아니라 추상화된 인터페이스에 의존되게 설계하면 기능을 수정해야 할 때 다른 dependency를 고려할 필요 없이 해당 부분만 수정하면 된다. 마치 레고 블록을 뺐다가 꽂는 것처럼.

### Stateful한 인스턴스 예시

1. **DB** - 데이터를 저장하고 있기 때문
2. **사용자 세션 정보를 가진 서버** - 사용자 데이터 정보를 가지고 있기 때문

등 불가피하게 데이터를 저장해야 하는 경우는 Stateful할 수밖에 없음.

---

## MSA 분리 전략

따라서 MSA를 조직할 때 "어디까지 분리를 해야 하나?"라는 질문의 첫 번째 Step은:

> **"Stateful 영역과 Stateless 영역을 나누자"**

우리가 달성하기 위한 주요 목적(Fault Tolerance, Simple Deployment, Horizontal Scaling)은 Stateless 조건을 충족할 때 달성된다고도 할 수 있다.

### 예시: 공모주 청약 알림 서비스

예를 들어, 행내 한 서비스가 다음과 같다.

![이미지](/assets/images/Pasted%20image%2020260219225957.png)

가장 간단한 예시이다. 왜냐하면 JDBC 드라이버나 String Util 같은 기본적인 라이브러리 말고는 큰 dependency가 없기 때문에 MSA로 옮길 수 있는 가장 간단한 모듈인 것 같다.

해당 배치는 서버 내부의 일부 파일에 불과하며, JFlow에 스케줄되어 있다. Stateful한 영역, Stateless한 영역, 외부 dependency를 고려하여 서비스 컨테이너를 구성하면 다음과 같이 나눌 수 있다고 생각한다.

![이미지](/assets/images/Pasted%20image%2020260219230004.png)

REST 통신 기반으로 구성한다 (코드 내부는 그냥 메모리간 이동, IPC).

EAI, PUSH모듈, 프론트, 메세지큐는 지금 우리가 초점맞추고 있는 도메인 밖의 컨테이너들일 것이다 (인프라 내 공통 기능). 이것들을 제외하고 공모주 푸시 알림 서비스 도메인에 관련된 요소들만 보면 오렌지색 상자 두 개 내부의 것들이다. 여기서 잘게 더 쪼개야 한다.

![이미지](/assets/images/Pasted%20image%2020260219230013.png)

Stateless한 모듈 부분과 Stateful한 데이터 부분으로 나눌 수 있다. 동작 매커니즘에 있어서도 어색한 것이 없다. 특정 컨테이너에서 싱글톤 객체(Stateful)와 팩토리 메서드로 생성되는 일회성 객체(Stateless)의 관계와 비슷한 것 같다.

---

## 마이크로서비스 크기 결정

다만 stateless하게 나눈 게 다가 아닐 수도 있고, 내부에 세부적인 기능에 따라 또 나눠도 무방하다.

어느 정도 바운드에서 분리를 하느냐에 대해 국룰?이 나올 것 같긴 한데, 해당 문건 포함 어느 문서를 보더라도 **상황, 환경에 따라 다르다**고 한다.

> Getting microservice size right is an art. One thing to watch for is that each team should own a reasonable number of microservices. If your team has five people but twenty microservices, then this is a red flag. On the other hand, if your team works on just one microservice that's also shared by five other teams, then this could be a problem, too.

**요약: Case by Case**

대체로 5인 한 팀에 2~3개 정도 서비스를 운용한다고 하니.. (+아마존 피자 법칙)

그래도 어느 정도 결정적인 역할을 하는 것을 찾아보기 위해서 그 다음 내용은...

**네트워크다!!!** 대체로 네트워크 속도 <<<< IPC 버스 속도이기 때문에 REST 통신과 함수 내부 호출에서 또 갈릴 것 같아 리서치해본다.

### 온라인 서점 예시

Here are some ways you could break up your hypothetical online bookstore into microservices:

- **Reviews** - stores book ratings and reviews entered by users.
- **User Account** - manages user signup and account details, such as changing their password.
- **Inventory** - provides data about which books are in stock.
- **Transactions** - handles payment processing and sending receipts.
- **Cart** - keeps track of what the user has put in their cart and the checkout flow.
- **Marketplace** - serves the logic for the user to navigate around the site.

도메인별로 쪼개는 게 가장 많이 알려진 해이긴 하다.
