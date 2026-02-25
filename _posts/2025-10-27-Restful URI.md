---
title: Restful URI
date: 2025-10-27
tags:
  - HTTP
---

### Rest

Representational State Tranfer의 약자로 웹을 이용할때 제약조건들을 정의하는 소프트웨어 아키텍처 스타일.

### 왜 이 주제를 생각했냐?

현재 2025년 11월 8일 정기 PM 작업간 개선과제로 기존에 개발해놨던 api(대략 50개 정도)의 uri를 모두 restful 하게 뜯어고치고 있음
고치면서 정확하게 restful한 것이 무엇인지에 대해 다시한번 생각해보게 됨

### 구성요소

1. 자원(Resource) : HTTP URL
2. 자원에 대한 행위 : HTTP Method
3. 자원에 대한 표현 : Representation

즉 특정 자원을(endpoint 명세) 특정 동작을(GET,POST,DELETE,PUT) 수행하도록 한다

그러므로 다음과 같은 특징을 가짐

### **행위를 포함하지 않는다.**

uri에 행위를 사용하지 말고 메소드에 행위를 포함

```kotlin
❌ POST http://stock-customer-service.convenience.svc.cluster.local
/set-push-info
❌ GET http://stock-customer-service.convenience.svc.cluster.local
/get-push-info
```


```kotlin
⭕ POST http://stock-customer-service.convenience.svc.cluster.local
/push
⭕ GET http://stock-customer-service.convenience.svc.cluster.local
/push
```


### **전달하고자 하는 명사를 사용하되, 컨트롤 자원을 의미하는 경우 예외적으로 동사를 사용한다.**



### **파일 확장자는 URL에 포함시키지 않는다.**

파일확장자는 Http Header에 Content-type으로 명시

### 자원은 복수형으로 사용한다

실무에서 그렇다고 하는데 왜 그런지 알 것 같음
ex) 
/listed-stock-service/stock/{ticker} 보다
/listed-stock-service/stocks/{ticker} 가 stock 이라는 분류 아래 특정 리소스 ex)삼성전자 = 005930 문서를 가져오는 느낌이라고 해야하나?
  - content type이 이미지면 이미지, json이면 메타명세 등등..


### 마지막에 슬래시(/)를 포함하지 않는다.

후행 슬래시(/)는 의미가 전혀 없고 혼란을 야기할 수 있다.
URI내의 모든 문자는 리소스의 고유 ID에 포함된다. URI 가 다르면 리소스도 다르기 때문에 명확한 URI를 생성해야한다


```kotlin
❌ /listed_stock_service/stocks/
⭕ /listed-stock-service/stocks
```


### 소문자를 사용한다.

대문자는 때로 문제를 일으키는 경우가 있기 때문에 URI를 작성할 때는 소문자를 선호한다.

### **언더바(_) 대신 하이픈(-)을 사용한다.**

가독성을 위해 긴 Path를 표현하는 단어는 하이픈(-)으로 구분하는 것이 좋다.
프로그램의 글자 폰트에 따라 언더바 문자는 부분적으로 가려지거나 숨겨질수 있다.

```kotlin
❌ /listedStockService/stock/{ticker}
❌ /listed_stock_service/stock{ticker}
⭕ /listed-stock-service/stock/{ticker}
```

~~근데 케이뱅크 표준헤더는 행위 중심으로 메서드를 구분하지 않을 뿐더러 언더바와 camelCase를 모두 사용하기 때문에 MSA 환경에서 개발할 때 상당히 고역이다 ~~

### 왜 중요할까?

서비스코드 기반으로 개발을 할 때보다 도메인, 리소스 기반으로 개발을 하다 보니 재사용과 일관성에 관심을 많이 갖게 됨.
가령, 고객정보를 가질 때

```kotlin
GET /stock-customer-service/customer/get-customer
PUT /stock-customer-service/customer/insert-customer
POST /stock-customer-service/customer/update-customer
DELETE /stock-customer-service/customer/delete-customer
```

보다는

```kotlin
GET /stock-customer-service/customer
PUT /stock-customer-service/customer
POST /stock-customer-service/customer
DELETE /stock-customer-service/customer
```

이런식으로 특정 리소스에 대해 행위를 명시하는 편이 실제로 재사용이나 일관성 면에서 더욱 생산성이 높았음
특히 주식 서비스는 MSA 환경에서 대고객 노출용으로 BFF를 채택하여 백엔드 api를 활용하고 있는데,
전자처럼 Rest 규칙을 준수하지 않고 선언하는 경우 각각에 대한 명세를 따로 불필요하게 선언해야 할 뿐더러, 후에 수정 시 영향도를 고려하기가 더 힘들어짐.

그래서 2025년 11월 8일 정기 PM 때 기존에 졸속으로 개발하면서 못챙겼던 부분들을 모두 개선하기로 함.