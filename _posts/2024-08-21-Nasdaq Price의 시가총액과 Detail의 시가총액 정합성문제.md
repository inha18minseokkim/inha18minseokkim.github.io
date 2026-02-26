---
title: "Nasdaq Price의 시가총액과 Detail의 시가총액 정합성문제"
date: 2024-08-21
tags: [미지정]
category:
  - 기술
---

![](https://prod-files-secure.s3.us-west-2.amazonaws.com/c38aebd7-2834-4fac-b2fc-a2f0c17ce81d/ca0ee8eb-5082-4202-b6bc-004ebee69045/image.png)



```java
{
    "detail": {
        "message": "success",
        "code": "SUCCESS",
        "ok": true
    },
    "data": {
        "name": "Apple Inc.",
        "name_ko": "애플",
        "name_short": "Apple",
        "symbol": "AAPL",
        "exchange": "NASDAQ",
        "listed_date": "1980-12-12",
        "business_area_en": "Technology",
        "business_area_ko": "기술",
        "road_address": "One Apple Park Way",
        "dividend_yield": 0.005,
        "ROE": 1.473,
        "PER": 34.54,
        "PBR": 45.144,
        "market_capitalization": 3348354039808.0,
        "EPS": 6.57,
        "EV_to_EBITDA": 26.119,
        "Beta": 1.244,
        "shares_outstanding": 15334099968.0,
        "business_overview": "Apple Inc. designs, manufactures, and markets smartphones, personal computers, tablets, wearables, and accessories worldwide. The company offers iPhone, a line of smartphones; Mac, a line of personal computers; iPad, a line of multi-purpose tablets; and wearables, home, and accessories comprising AirPods, Apple TV, Apple Watch, Beats products, and HomePod. It also provides AppleCare support and cloud services; and operates various platforms, including the App Store that allow customers to discover and download applications and digital content, such as books, music, video, games, and podcasts. In addition, the company offers various services, such as Apple Arcade, a game subscription service; Apple Fitness+, a personalized fitness service; Apple Music, which offers users a curated listening experience with on-demand radio stations; Apple News+, a subscription news and magazine service; Apple TV+, which offers exclusive original content; Apple Card, a co-branded credit card; and Apple Pay, a cashless payment service, as well as licenses its intellectual property. The company serves consumers, and small and mid-sized businesses; and the education, enterprise, and government markets. It distributes third-party applications for its products through the App Store. The company also sells its products through its retail and online stores, and direct sales force; and third-party cellular network carriers, wholesalers, retailers, and resellers. Apple Inc. was founded in 1976 and is headquartered in Cupertino, California.",
        "business_overview_ko": "Apple Inc.는 전 세계적으로 스마트폰, 개인용 컴퓨터, 태블릿, 착용 기기 및 액세서리를 설계, 제조 및 판매합니다. 이 회사는 스마트폰 제품군인 iPhone, 개인용 컴퓨터 제품군인 Mac, 다목적 태블릿 제품군인 iPad, 그리고 AirPods, Apple TV, Apple Watch, Beats 제품, HomePod 등을 포함한 착용 기기, 가정용 기기 및 액세서리를 제공합니다. 또한 AppleCare 지원 및 클라우드 서비스를 제공하며, 고객이 책, 음악, 비디오, 게임, 팟캐스트 등의 애플리케이션과 디지털 콘텐츠를 발견하고 다운로드할 수 있는 App Store를 운영합니다. 추가적으로, 게임 구독 서비스인 Apple Arcade, 개인 맞춤형 피트니스 서비스인 Apple Fitness+, 온디맨드 라디오 방송국과 함께 선별된 청취 경험을 제공하는 Apple Music, 구독 뉴스 및 잡지 서비스인 Apple News+, 독점 오리지널 콘텐츠를 제공하는 Apple TV+, 공동 브랜드 신용카드인 Apple Card, 현금 없는 결제 서비스인 Apple Pay 등의 다양한 서비스를 제공합니다. 또한, 지적 재산권을 라이선싱합니다. 이 회사는 소비자, 중소기업, 교육, 기업 및 정부 시장을 대상으로 하며, App Store를 통해 자사 제품용 제3자 애플리케이션을 유통합니다. 이 회사는 자사 제품을 통해 소매 및 온라인 상점, 직접 영업, 제3자 이동통신사, 도매업자, 소매업자 및 리셀러를 통해 판매합니다. Apple Inc.는 1976년에 설립되었으며, 캘리포니아주 쿠퍼티노에 본사를 두고 있습니다.",
        "korean_company_names": [],
        "korean_query": "('애플' or 'Apple') and ('AAPL'  or '주가')",
        "industries": [
            "전자 컴퓨터",
            "가전제품"
        ]
    }
}
```


```java
   "data": [
        {
            "date": "2024-08-20",
            "symbol": "AAPL",
            "entity_name": "Apple",
            "open": 225.9,
            "high": 227.17,
            "low": 225.45,
            "volume": 28053456,
            "change": 0.62,
            "value": null,
            "change_percent": 0.2745,
            "trading_halted": false,
            "market_cap": 3473326983751.6797,
            "shares_listed": 15334099968,
            "close": 226.51
        },
```


![](https://prod-files-secure.s3.us-west-2.amazonaws.com/c38aebd7-2834-4fac-b2fc-a2f0c17ce81d/9cccc3fe-7299-40d4-8c3f-510ead8d7da6/image.png)

하..
