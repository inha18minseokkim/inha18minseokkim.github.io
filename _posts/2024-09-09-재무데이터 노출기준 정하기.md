---
title: "재무데이터 노출기준 정하기"
date: 2024-09-09
tags:
  - 재무
  - 주식서비스
category:
  - 재테크
---
재무 데이터 분석 및 투자 관련 내용 정리.
![이미지](/assets/images/Pasted%20image%2020260226160436.png)


### Diff:

1. 재무정보 리스트 사라짐. 최근년도 재무정보만 보여줌
2. 재무비율 api 종류 달라짐(compute → rest)

재무제표 보여주는 기준 정리 완료(BM에게 그냥 정리해서 가르쳐주고 이해시키는걸로)
[[2024-09-09-주권상장법인 사업보고서 제출기한]]

1. 연결재무제표 우선 수집/노출
2. 연결재무제표 없는 기업의 경우 별도재무제표  수집/노출
  1. 밑에 IFRS연결인지 별도인지 분간시켜주는 코드 필요
3. 없으면 안보여주는 화면 필요 ex) 주식아닌 상장된 증권들


### 테이블 분리/추가 필요 또는 코드로 분리해야함.


![이미지](/assets/images/Pasted%20image%2020260226160440.png)

좌 연결 우 별도
딥서치 재무계정코드 기준으로 둘 다 똑같은 코드를 사용하고 있어(아니그럼 코드를 왜쓰는거야) 연결재무제표 테이블과 개별재무제표 테이블이 별도로 필요할 것 같음
또는 코드로 분기쳐야할듯 ⇒ 분기치는 값은 내가 직접 정해야함.

국내재무요약정보(SK하이닉스)

```java
"2023": {
    "assets": 100330165000000,
    "liabilities": 46826413000000,
    "equity": 53503752000000,
    "sales": 32765719000000,
    "operating_income": -7730313000000,
    "gross_net_income": -9137547000000,
    "net_income": null
}
```

asset > 자산, liabilities > 부채 > equity > 자본 까지는 ok
sales > 매출액
operating_income > 영업이익
gross_net_income > ?
net_income > 당기순이익 근데 왜 null임 이게 gross net income이 당기순이익인것같은데

![이미지](/assets/images/Pasted%20image%2020260226160955.png)

왜 gross_net_income 이라고 하지..? 이런 용어는 들어본 적 없음..매출 총 이익..? 네이버 사전 쓴건가
  - gross profit : 매출총이익 = 매출 - 매출원가

해외재무요약정보(애플)

```java
"data": [
    {
        "symbol": "AAPL",
        "name": "Apple Inc",
        "name_ko": "애플",
        "reported_currency": "USD",
        "fiscal_end_date": "2023-09-30",
        "revenue": "379352000000",
        "gross_profit": "169148000000",
        "operating_profit": "114301000000",
		    "net_income": "96995000000",
        "asset": "352583000000",
        "liability": "290437000000",
        "equity": "62146000000"
    },
```

revenue : 매출
gross_profit : 매출총이익 = 매출 - 매출원가
operating_profit : 영업이익?
net_income : 당기 순이익
