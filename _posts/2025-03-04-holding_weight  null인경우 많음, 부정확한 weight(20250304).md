---
title: "holding_weight >> null인경우 많음, 부정확한 weight(20250304)"
date: 2025-03-04
tags: [미지정]
category:
  - 기타
---

```java
{
                "name": "Meta Platforms Inc",
                "name_ko": "메타 플랫폼스",
                "exchange": "NASDAQ",
                "name_short": "Meta Platforms",
                "country_code": "us",
                "exchange_code": "META",
                "holdings_type": "company",
                "holdings_value": null,
                "holdings_shares": null,
                "holdings_weight": "22.63",
                "holding_isin_code": "US30303M1027",
                "holdings_industry": [
                    {
                        "name": "SERVICES-COMPUTER PROGRAMMING, DATA PROCESSING, ETC.",
                        "name_ko": "서비스-컴퓨터 프로그래밍, 데이터 처리 등",
                        "country_code": "us"
                    },
                    {
                        "name": "Internet Content",
                        "name_ko": "인터넷 콘텐츠",
                        "country_code": "us"
                    },
                    {
                        "name": "Information",
                        "name_ko": "정보",
                        "country_code": "us"
                    }
                ],
                "holding_company_id": 493,
                "holdings_market_cap": 1492290186963
            }
```

정상케이스, VOX ETF가 메타를 22.63프로 들고있음

증권식별번호로 들어가있는경우는 거래소 상장안되어있고 현물,금이나 회사끼리 체결한 스왑일 수 있음. 
그러면 비중제공이 어렵다 치더라도 컬럼의 의미를 알기 힘듬.

![](attachment:e6f52b04-54c7-4584-b3dd-5330ac339938:image.png)

아니면 holdings가 구성종목이 아니라 다른 의미인가?


### 이슈 예시1

[https://api-v2.deepsearch.com/v1/etfs/227570?api_key=ZGVtb19hcGk6ZGVtb19hcGkx](https://api-v2.deepsearch.com/v1/etfs/227570?api_key=ZGVtb19hcGk6ZGVtb19hcGkx)
원화현금 weight 100프로인데 나머지 주식들이 있음. 부정확한 정보
**api response json**

```java
{
    "detail": {
        "message": "success",
        "code": "SUCCESS",
        "ok": true
    },
    "data": {
        "name": "TIGER 우량가치",
        "country_code": "kr",
        "exchange": "KRX",
        "symbol": "227570",
        "issuer_name": "미래에셋자산운용",
        "category": "주식-전략-가치",
        "etf_type": "수익증권형",
        "tax_type": "비과세",
        "replication_type": "실물",
        "active_or_passive": "패시브",
        "fee": 0.35,
        "trace_index_leverage_inverse_type": "일반",
        "trace_index_calulate_institute_name": "FnGuide",
        "trace_index_name": "FnGuide 퀄리티밸류 지수",
        "listed_date": "2015-09-23T00:00:00Z",
        "listed_shares": 450000,
        "description": "이 ETF는 국내 주식을 주된 투자대상자산으로 하며, \"FnGuide 퀄리티 밸류 지수\" 수익률 추종을 목적으로 합니다.\n FnGuide가 발표하는 “FnGuide 퀄리티 밸류 지수”는 유가증권시장에 상장된 시가총액 상위 300위 이내 종목 중, 4개의 밸류 팩터 및 4개의 퀄리티 팩터 값을 더하여 산출한 값 기준으로 상위 50종목으로 지수를 구성하며 연 2회 정기변경을 실시합니다.",
        "warning": "이 ETF의 수익률은 보수 또는 비용 등 이 ETF의 순자산가치에 부의 영향을 미치는 다양한 이유로 인하여 기초지수 수익률과 괴리(추적오차)가 발생할 수 있습니다.\n 개인투자자는 보유 ETF를 거래소에서 매도하는 방법으로만 현금화가 가능하므로 보유수익증권을 판매회사 또는 지정참가회사에 환매 신청할 수 없으며, 거래소의 거래 상황에 따라 동 ETF의 순자산가치와 거래가격이 다르게 형성될 수 있습니다.\n 상품에 대한 자세한 내용은 집합투자업자 인터넷 홈페이지(http://www.tigeretf.com) 또는 금융감독원 전자공시시스템의 투자설명서를 통해 확인하시기 바랍니다.",
        "etf_holdings": [
            {
                "name": "원화현금",
                "name_ko": null,
                "exchange": "KRD010010001",
                "name_short": null,
                "exchange_code": "KRD010010001",
                "holdings_type": null,
                "holdings_value": null,
                "holdings_shares": null,
                "holdings_weight": 100.0,
                "holding_isin_code": "KRD010010001",
                "holdings_industry": null,
                "holding_company_id": null,
                "holdings_market_cap": null,
                "country_code": "kr"
            },
            {
                "name": "HANWHA LIFE",
                "name_ko": "한화생명",
                "exchange": "KRX",
                "name_short": "한화생명",
                "exchange_code": "088350",
                "holdings_type": "company",
                "holdings_value": null,
                "holdings_shares": "2568",
                "holdings_weight": null,
                "holding_isin_code": "KR7088350004",
                "holdings_industry": [
                    {
                        "name": "보험",
                        "name_ko": "보험",
                        "country_code": "kr"
                    }
                ],
                "holding_company_id": 10415,
                "holdings_market_cap": null,
                "country_code": "kr"
            },
            {
                "name": "DWEC",
                "name_ko": "대우건설",
                "exchange": "KRX",
                "name_short": "대우건설",
                "exchange_code": "047040",
                "holdings_type": "company",
                "holdings_value": null,
                "holdings_shares": "1968",
                "holdings_weight": null,
                "holding_isin_code": "KR7047040001",
                "holdings_industry": [
                    {
                        "name": "건설업",
                        "name_ko": "건설업",
                        "country_code": "kr"
                    }
                ],
                "holding_company_id": 9083,
                "holdings_market_cap": null,
                "country_code": "kr"
            },
            {
                "name": "Hanwha General Ins",
                "name_ko": "한화손해보험",
                "exchange": "KRX",
                "name_short": "한화손해보험",
                "exchange_code": "000370",
                "holdings_type": "company",
                "holdings_value": null,
                "holdings_shares": "1608",
                "holdings_weight": null,
                "holding_isin_code": "KR7000370007",
                "holdings_industry": [
                    {
                        "name": "보험",
                        "name_ko": "보험",
                        "country_code": "kr"
                    }
                ],
                "holding_company_id": 10422,
                "holdings_market_cap": null,
                "country_code": "kr"
            },
            {
                "name": "SKNetworks",
                "name_ko": "SK네트웍스",
                "exchange": "KRX",
                "name_short": "SK네트웍스",
                "exchange_code": "001740",
                "holdings_type": "company",
                "holdings_value": null,
                "holdings_shares": "1597",
                "holdings_weight": null,
                "holding_isin_code": "KR7001740000",
                "holdings_industry": [],
                "holding_company_id": 10207,
                "holdings_market_cap": null,
                "country_code": "kr"
            },
            {
                "name": "HYUNDAI G.F. HOLDINGS",
                "name_ko": "현대지에프홀딩스",
                "exchange": "KRX",
                "name_short": "현대지에프홀딩스",
                "exchange_code": "005440",
                "holdings_type": "company",
                "holdings_value": null,
                "holdings_shares": "1358",
                "holdings_weight": null,
                "holding_isin_code": "KR7005440003",
                "holdings_industry": [
                    {
                        "name": "남북경협",
                        "name_ko": "남북경협",
                        "country_code": "kr"
                    },
                    {
                        "name": "지주회사",
                        "name_ko": "지주회사",
                        "country_code": "kr"
                    }
                ],
                "holding_company_id": 10240,
                "holdings_market_cap": null,
                "country_code": "kr"
            },
            {
                "name": "TONGYANG LIFE",
                "name_ko": "동양생명",
                "exchange": "KRX",
                "name_short": "동양생명",
                "exchange_code": "082640",
                "holdings_type": "company",
                "holdings_value": null,
                "holdings_shares": "1188",
                "holdings_weight": null,
                "holding_isin_code": "KR7082640004",
                "holdings_industry": [
                    {
                        "name": "보험",
                        "name_ko": "보험",
                        "country_code": "kr"
                    }
                ],
                "holding_company_id": 10385,
                "holdings_market_cap": null,
                "country_code": "kr"
            },
            {
                "name": "LX HOLDINGS",
                "name_ko": "LX홀딩스",
                "exchange": "KRX",
                "name_short": "LX홀딩스",
                "exchange_code": "383800",
                "holdings_type": "company",
                "holdings_value": null,
                "holdings_shares": "981",
                "holdings_weight": null,
                "holding_isin_code": "KR7383800000",
                "holdings_industry": [
                    {
                        "name": "지주회사",
                        "name_ko": "지주회사",
                        "country_code": "kr"
                    }
                ],
                "holding_company_id": 11115,
                "holdings_market_cap": null,
                "country_code": "kr"
            },
            {
                "name": "DGB Financial Group",
                "name_ko": "DGB금융지주",
                "exchange": "KRX",
                "name_short": "DGB금융지주",
                "exchange_code": "139130",
                "holdings_type": "company",
                "holdings_value": null,
                "holdings_shares": "766",
                "holdings_weight": null,
                "holding_isin_code": "KR7139130009",
                "holdings_industry": [
                    {
                        "name": "지주회사",
                        "name_ko": "지주회사",
                        "country_code": "kr"
                    }
                ],
                "holding_company_id": 10727,
                "holdings_market_cap": null,
                "country_code": "kr"
            },
            {
                "name": "LG Uplus",
                "name_ko": "LG유플러스",
                "exchange": "KRX",
                "name_short": "LG유플러스",
                "exchange_code": "032640",
                "holdings_type": "company",
                "holdings_value": null,
                "holdings_shares": "626",
                "holdings_weight": null,
                "holding_isin_code": "KR7032640005",
                "holdings_industry": [
                    {
                        "name": "로봇",
                        "name_ko": "로봇",
                        "country_code": "kr"
                    },
                    {
                        "name": "반려동물",
                        "name_ko": "반려동물",
                        "country_code": "kr"
                    },
                    {
                        "name": "VR/AR",
                        "name_ko": "VR/AR",
                        "country_code": "kr"
                    },
                    {
                        "name": "스마트팩토리",
                        "name_ko": "스마트팩토리",
                        "country_code": "kr"
                    },
                    {
                        "name": "키오스크",
                        "name_ko": "키오스크",
                        "country_code": "kr"
                    },
                    {
                        "name": "사물인터넷",
                        "name_ko": "사물인터넷",
                        "country_code": "kr"
                    },
                    {
                        "name": "자율주행",
                        "name_ko": "자율주행",
                        "country_code": "kr"
                    },
                    {
                        "name": "태양광",
                        "name_ko": "태양광",
                        "country_code": "kr"
                    },
                    {
                        "name": "전기차",
                        "name_ko": "전기차",
                        "country_code": "kr"
                    },
                    {
                        "name": "빅데이터",
                        "name_ko": "빅데이터",
                        "country_code": "kr"
                    }
                ],
                "holding_company_id": 8755,
                "holdings_market_cap": null,
                "country_code": "kr"
            },
            {
                "name": "HDC HOLDINGS",
                "name_ko": "HDC",
                "exchange": "KRX",
                "name_short": "HDC",
                "exchange_code": "012630",
                "holdings_type": "company",
                "holdings_value": null,
                "holdings_shares": "580",
                "holdings_weight": null,
                "holding_isin_code": "KR7012630000",
                "holdings_industry": [
                    {
                        "name": "지주회사",
                        "name_ko": "지주회사",
                        "country_code": "kr"
                    }
                ],
                "holding_company_id": 10148,
                "holdings_market_cap": null,
                "country_code": "kr"
            },
            {
                "name": "NICE INFO",
                "name_ko": "NICE평가정보",
                "exchange": "KRX",
                "name_short": "NICE평가정보",
                "exchange_code": "030190",
                "holdings_type": "company",
                "holdings_value": null,
                "holdings_shares": "579",
                "holdings_weight": null,
                "holding_isin_code": "KR7030190003",
                "holdings_industry": [
                    {
                        "name": "핀테크",
                        "name_ko": "핀테크",
                        "country_code": "kr"
                    },
                    {
                        "name": "남북경협",
                        "name_ko": "남북경협",
                        "country_code": "kr"
                    },
                    {
                        "name": "솔루션",
                        "name_ko": "솔루션",
                        "country_code": "kr"
                    },
                    {
                        "name": "클라우드컴퓨팅",
                        "name_ko": "클라우드컴퓨팅",
                        "country_code": "kr"
                    },
                    {
                        "name": "사물인터넷",
                        "name_ko": "사물인터넷",
                        "country_code": "kr"
                    },
                    {
                        "name": "인공지능",
                        "name_ko": "인공지능",
                        "country_code": "kr"
                    },
                    {
                        "name": "빅데이터",
                        "name_ko": "빅데이터",
                        "country_code": "kr"
                    }
                ],
                "holding_company_id": 10379,
                "holdings_market_cap": null,
                "country_code": "kr"
            },
            {
                "name": "CheilWorldwide",
                "name_ko": "제일기획",
                "exchange": "KRX",
                "name_short": "제일기획",
                "exchange_code": "030000",
                "holdings_type": "company",
                "holdings_value": null,
                "holdings_shares": "375",
                "holdings_weight": null,
                "holding_isin_code": "KR7030000004",
                "holdings_industry": [
                    {
                        "name": "광고대행",
                        "name_ko": "광고대행",
                        "country_code": "kr"
                    }
                ],
                "holding_company_id": 10369,
                "holdings_market_cap": null,
                "country_code": "kr"
            },
            {
                "name": "GS E&C",
                "name_ko": "GS건설",
                "exchange": "KRX",
                "name_short": "GS건설",
                "exchange_code": "006360",
                "holdings_type": "company",
                "holdings_value": null,
                "holdings_shares": "375",
                "holdings_weight": null,
                "holding_isin_code": "KR7006360002",
                "holdings_industry": [
                    {
                        "name": "건설업",
                        "name_ko": "건설업",
                        "country_code": "kr"
                    }
                ],
                "holding_company_id": 10138,
                "holdings_market_cap": null,
                "country_code": "kr"
            },
            {
                "name": "SBHC",
                "name_ko": "세아베스틸지주",
                "exchange": "KRX",
                "name_short": "세아베스틸지주",
                "exchange_code": "001430",
                "holdings_type": "company",
                "holdings_value": null,
                "holdings_shares": "339",
                "holdings_weight": null,
                "holding_isin_code": "KR7001430008",
                "holdings_industry": [
                    {
                        "name": "로봇",
                        "name_ko": "로봇",
                        "country_code": "kr"
                    },
                    {
                        "name": "신재생에너지",
                        "name_ko": "신재생에너지",
                        "country_code": "kr"
                    },
                    {
                        "name": "인공지능",
                        "name_ko": "인공지능",
                        "country_code": "kr"
                    },
                    {
                        "name": "사이버 보안",
                        "name_ko": "사이버 보안",
                        "country_code": "kr"
                    },
                    {
                        "name": "전기차",
                        "name_ko": "전기차",
                        "country_code": "kr"
                    },
                    {
                        "name": "빅데이터",
                        "name_ko": "빅데이터",
                        "country_code": "kr"
                    },
                    {
                        "name": "수소차",
                        "name_ko": "수소차",
                        "country_code": "kr"
                    }
                ],
                "holding_company_id": 9874,
                "holdings_market_cap": null,
                "country_code": "kr"
            }
        ],
        "market_info": {
            "nav": 12148.79,
            "aum": 5466954693.0,
            "trade_volume": 2903,
            "trade_value": 35144770.0,
            "market_cap": 5092500000.0,
            "yield_1d": 0.17,
            "yield_1w": 3.8099,
            "yield_1m": 7.8257,
            "yield_3m": 8.4041,
            "yield_ytd": 8.4041,
            "yield_1y": 8.4041,
            "flows_1w": 658643792.0,
            "flows_3m": -1716488018.0,
            "flows_1m": -1576660322.0,
            "flows_1y": -2757197285.0,
            "flows_ytd": -1523535681.0,
            "volume_1w": 17564,
            "volume_1m": 330459,
            "update_date": "2025-02-20",
            "dividend": null,
            "dividend_yield_1y": 3.298969072164949
        }
    }
}
```


![](attachment:83932c16-b004-4d63-b47c-b2d120d617f5:image.png)


### 이슈 예시2

[https://api-v2.deepsearch.com/v1/etfs/131890?api_key=ZGVtb19hcGk6ZGVtb19hcGkx](https://api-v2.deepsearch.com/v1/etfs/131890?api_key=ZGVtb19hcGk6ZGVtb19hcGkx)
마찬가지
**api response json**

```java
{
    "detail": {
        "message": "success",
        "code": "SUCCESS",
        "ok": true
    },
    "data": {
        "name": "ACE 삼성그룹동일가중",
        "country_code": "kr",
        "exchange": "KRX",
        "symbol": "131890",
        "issuer_name": "한국투자신탁운용",
        "category": "주식-전략-기업그룹",
        "etf_type": "수익증권형",
        "tax_type": "비과세",
        "replication_type": "실물",
        "active_or_passive": "패시브",
        "fee": 0.15,
        "trace_index_leverage_inverse_type": "일반",
        "trace_index_calulate_institute_name": "FnGuide",
        "trace_index_name": "MKF SAMs EW 지수",
        "listed_date": "2010-09-17T00:00:00Z",
        "listed_shares": 500000,
        "description": "1좌당 순자산가치의 변동률을 기초지수인 MKF SAMs EW(Equal Weighted) 지수의 변동률과 유사하도록 투자신탁재산을 운용하는 것을 목표로 합니다.\n\nFnGuide가 산출하는 MKF SAMs EW 지수는 정기변경일 기준으로 상호출자제한기업집단으로 지정된 삼성그룹에 소속된 계열회사로 장기적으로 재무안정성이 좋고 신용위험이 낮은 종목을 구성종목으로 선정합니다. 지수의 산출은 정기변경 시점에 구성종목의 편입비중이 동일 비중이 되도록하는 동일가중(Equal Weight) 방식을 채용하고 있습니다.\n\nMKF SAMs EW 지수는 매월 첫 영업일에 정기변경을 실시합니다. 다만, 지수구성종목 중에서 상장폐지, 관리종목 지정, 피흡수, 합병 등의 사유로 구성종목으로서 부적당하다고 인정되는 경우 수시로 변경될 수 있습니다.\n\n이 투자신탁은 기초지수인 MKF SAMs EW 지수를 구성하고 있는 종목에 대부분을 투자하는 것을 원칙으로 합니다. 다만, 자산운용회사가 추적오차의 최소화, 시장충격, 매매정지 등의 사유로 필요하다고 판단하는 경우, 해당 지수구성종목의 개별주식선물, 주가지수선물 등의 파생상품에 투자할 수도 있으며, 신규 편입 예정종목에도 투자할 수 있습니다. \n\n지수에 대한 자세한 내용은 에프엔가이드 지수소개 홈페이지(http://www.fnindex.co.kr)를 통해 확인하시기 바랍니다.",
        "warning": "이 투자신탁의 수익률은 다양한 이유(투자신탁 운용과 관련된 제반 비용, 현금배당, 구성종목의 교체/비중변경/부도)로 기초지수인 MKF SAMs EW 지수의 수익률과 괴리(추적오차)가 발생할 수 있습니다. \n\n이 경우 자산운용회사는 추적오차를 최소화하기 위하여 투자신탁 관련비용의 최소화, 추적오차를 감안한 편입 종목수 조정 등의 다양한 보완방안을 실행할 예정이나, 불가피하게 최소한의 추적오차가 발생할 가능성이 있음을 유의하셔야 합니다.\n\n상품에 대한 자세한 내용은 자산운용사 홈페이지(http://www.kindexetf.com) 또는 금융감독원 전자공시시스템의 투자설명서를 통해 확인하시기 바랍니다.",
        "etf_holdings": [
            {
                "name": "원화현금",
                "name_ko": null,
                "exchange": "KRD010010001",
                "name_short": null,
                "exchange_code": "KRD010010001",
                "holdings_type": null,
                "holdings_value": null,
                "holdings_shares": null,
                "holdings_weight": 100.0,
                "holding_isin_code": "KRD010010001",
                "holdings_industry": null,
                "holding_company_id": null,
                "holdings_market_cap": null,
                "country_code": "kr"
            },
            {
                "name": "SamsungHvyInd",
                "name_ko": "삼성중공업",
                "exchange": "KRX",
                "name_short": "삼성중공업",
                "exchange_code": "010140",
                "holdings_type": "company",
                "holdings_value": null,
                "holdings_shares": "8647",
                "holdings_weight": null,
                "holding_isin_code": "KR7010140002",
                "holdings_industry": [
                    {
                        "name": "미세먼지",
                        "name_ko": "미세먼지",
                        "country_code": "kr"
                    },
                    {
                        "name": "로봇",
                        "name_ko": "로봇",
                        "country_code": "kr"
                    },
                    {
                        "name": "키오스크",
                        "name_ko": "키오스크",
                        "country_code": "kr"
                    },
                    {
                        "name": "사물인터넷",
                        "name_ko": "사물인터넷",
                        "country_code": "kr"
                    },
                    {
                        "name": "웨어러블",
                        "name_ko": "웨어러블",
                        "country_code": "kr"
                    },
                    {
                        "name": "인공지능",
                        "name_ko": "인공지능",
                        "country_code": "kr"
                    },
                    {
                        "name": "자율주행",
                        "name_ko": "자율주행",
                        "country_code": "kr"
                    },
                    {
                        "name": "태양광",
                        "name_ko": "태양광",
                        "country_code": "kr"
                    },
                    {
                        "name": "전기차",
                        "name_ko": "전기차",
                        "country_code": "kr"
                    },
                    {
                        "name": "빅데이터",
                        "name_ko": "빅데이터",
                        "country_code": "kr"
                    }
                ],
                "holding_company_id": 9817,
                "holdings_market_cap": null,
                "country_code": "kr"
            },
            {
                "name": "CheilWorldwide",
                "name_ko": "제일기획",
                "exchange": "KRX",
                "name_short": "제일기획",
                "exchange_code": "030000",
                "holdings_type": "company",
                "holdings_value": null,
                "holdings_shares": "6575",
                "holdings_weight": null,
                "holding_isin_code": "KR7030000004",
                "holdings_industry": [
                    {
                        "name": "광고대행",
                        "name_ko": "광고대행",
                        "country_code": "kr"
                    }
                ],
                "holding_company_id": 10369,
                "holdings_market_cap": null,
                "country_code": "kr"
            },
            {
                "name": "SamsungE&A",
                "name_ko": "삼성E&A",
                "exchange": "KRX",
                "name_short": "삼성E&A",
                "exchange_code": "028050",
                "holdings_type": "company",
                "holdings_value": null,
                "holdings_shares": "6258",
                "holdings_weight": null,
                "holding_isin_code": "KR7028050003",
                "holdings_industry": [],
                "holding_company_id": 10370,
                "holdings_market_cap": null,
                "country_code": "kr"
            },
            {
                "name": "HtlShilla",
                "name_ko": "호텔신라",
                "exchange": "KRX",
                "name_short": "호텔신라",
                "exchange_code": "008770",
                "holdings_type": "company",
                "holdings_value": null,
                "holdings_shares": "2830",
                "holdings_weight": null,
                "holding_isin_code": "KR7008770000",
                "holdings_industry": [],
                "holding_company_id": 10251,
                "holdings_market_cap": null,
                "country_code": "kr"
            },
            {
                "name": "SAMSUNG CARD",
                "name_ko": "삼성카드",
                "exchange": "KRX",
                "name_short": "삼성카드",
                "exchange_code": "029780",
                "holdings_type": "company",
                "holdings_value": null,
                "holdings_shares": "2726",
                "holdings_weight": null,
                "holding_isin_code": "KR7029780004",
                "holdings_industry": [],
                "holding_company_id": 10467,
                "holdings_market_cap": null,
                "country_code": "kr"
            },
            {
                "name": "SamsungSecu",
                "name_ko": "삼성증권",
                "exchange": "KRX",
                "name_short": "삼성증권",
                "exchange_code": "016360",
                "holdings_type": "company",
                "holdings_value": null,
                "holdings_shares": "2500",
                "holdings_weight": null,
                "holding_isin_code": "KR7016360000",
                "holdings_industry": [
                    {
                        "name": "증권",
                        "name_ko": "증권",
                        "country_code": "kr"
                    }
                ],
                "holding_company_id": 10386,
                "holdings_market_cap": null,
                "country_code": "kr"
            },
            {
                "name": "SamsungElec",
                "name_ko": "삼성전자",
                "exchange": "KRX",
                "name_short": "삼성전자",
                "exchange_code": "005930",
                "holdings_type": "company",
                "holdings_value": null,
                "holdings_shares": "2079",
                "holdings_weight": null,
                "holding_isin_code": "KR7005930003",
                "holdings_industry": [
                    {
                        "name": "반도체",
                        "name_ko": "반도체",
                        "country_code": "kr"
                    },
                    {
                        "name": "미세먼지",
                        "name_ko": "미세먼지",
                        "country_code": "kr"
                    },
                    {
                        "name": "로봇",
                        "name_ko": "로봇",
                        "country_code": "kr"
                    },
                    {
                        "name": "반려동물",
                        "name_ko": "반려동물",
                        "country_code": "kr"
                    },
                    {
                        "name": "스마트팩토리",
                        "name_ko": "스마트팩토리",
                        "country_code": "kr"
                    },
                    {
                        "name": "스마트폰",
                        "name_ko": "스마트폰",
                        "country_code": "kr"
                    },
                    {
                        "name": "키오스크",
                        "name_ko": "키오스크",
                        "country_code": "kr"
                    },
                    {
                        "name": "신재생에너지",
                        "name_ko": "신재생에너지",
                        "country_code": "kr"
                    },
                    {
                        "name": "가전제품",
                        "name_ko": "가전제품",
                        "country_code": "kr"
                    },
                    {
                        "name": "의료기기",
                        "name_ko": "의료기기",
                        "country_code": "kr"
                    },
                    {
                        "name": "사물인터넷",
                        "name_ko": "사물인터넷",
                        "country_code": "kr"
                    },
                    {
                        "name": "웨어러블",
                        "name_ko": "웨어러블",
                        "country_code": "kr"
                    },
                    {
                        "name": "인공지능",
                        "name_ko": "인공지능",
                        "country_code": "kr"
                    },
                    {
                        "name": "2차전지",
                        "name_ko": "2차전지",
                        "country_code": "kr"
                    },
                    {
                        "name": "자율주행",
                        "name_ko": "자율주행",
                        "country_code": "kr"
                    },
                    {
                        "name": "태양광",
                        "name_ko": "태양광",
                        "country_code": "kr"
                    },
                    {
                        "name": "전기차",
                        "name_ko": "전기차",
                        "country_code": "kr"
                    },
                    {
                        "name": "빅데이터",
                        "name_ko": "빅데이터",
                        "country_code": "kr"
                    },
                    {
                        "name": "수소차",
                        "name_ko": "수소차",
                        "country_code": "kr"
                    }
                ],
                "holding_company_id": 9837,
                "holdings_market_cap": null,
                "country_code": "kr"
            },
            {
                "name": "S-1",
                "name_ko": "에스원",
                "exchange": "KRX",
                "name_short": "에스원",
                "exchange_code": "012750",
                "holdings_type": "company",
                "holdings_value": null,
                "holdings_shares": "1861",
                "holdings_weight": null,
                "holding_isin_code": "KR7012750006",
                "holdings_industry": [],
                "holding_company_id": 10378,
                "holdings_market_cap": null,
                "country_code": "kr"
            },
            {
                "name": "SAMSUNG LIFE",
                "name_ko": "삼성생명",
                "exchange": "KRX",
                "name_short": "삼성생명",
                "exchange_code": "032830",
                "holdings_type": "company",
                "holdings_value": null,
                "holdings_shares": "1375",
                "holdings_weight": null,
                "holding_isin_code": "KR7032830002",
                "holdings_industry": [
                    {
                        "name": "보험",
                        "name_ko": "보험",
                        "country_code": "kr"
                    }
                ],
                "holding_company_id": 10416,
                "holdings_market_cap": null,
                "country_code": "kr"
            },
            {
                "name": "SAMSUNG SDS",
                "name_ko": "삼성에스디에스",
                "exchange": "KRX",
                "name_short": "삼성에스디에스",
                "exchange_code": "018260",
                "holdings_type": "company",
                "holdings_value": null,
                "holdings_shares": "982",
                "holdings_weight": null,
                "holding_isin_code": "KR7018260000",
                "holdings_industry": [
                    {
                        "name": "로봇",
                        "name_ko": "로봇",
                        "country_code": "kr"
                    },
                    {
                        "name": "스마트팩토리",
                        "name_ko": "스마트팩토리",
                        "country_code": "kr"
                    },
                    {
                        "name": "블록체인",
                        "name_ko": "블록체인",
                        "country_code": "kr"
                    },
                    {
                        "name": "키오스크",
                        "name_ko": "키오스크",
                        "country_code": "kr"
                    },
                    {
                        "name": "신재생에너지",
                        "name_ko": "신재생에너지",
                        "country_code": "kr"
                    },
                    {
                        "name": "클라우드컴퓨팅",
                        "name_ko": "클라우드컴퓨팅",
                        "country_code": "kr"
                    },
                    {
                        "name": "사물인터넷",
                        "name_ko": "사물인터넷",
                        "country_code": "kr"
                    },
                    {
                        "name": "인공지능",
                        "name_ko": "인공지능",
                        "country_code": "kr"
                    },
                    {
                        "name": "사이버 보안",
                        "name_ko": "사이버 보안",
                        "country_code": "kr"
                    },
                    {
                        "name": "2차전지",
                        "name_ko": "2차전지",
                        "country_code": "kr"
                    },
                    {
                        "name": "태양광",
                        "name_ko": "태양광",
                        "country_code": "kr"
                    },
                    {
                        "name": "소프트웨어",
                        "name_ko": "소프트웨어",
                        "country_code": "kr"
                    },
                    {
                        "name": "전기차",
                        "name_ko": "전기차",
                        "country_code": "kr"
                    },
                    {
                        "name": "빅데이터",
                        "name_ko": "빅데이터",
                        "country_code": "kr"
                    }
                ],
                "holding_company_id": 10380,
                "holdings_market_cap": null,
                "country_code": "kr"
            },
            {
                "name": "SAMSUNG C&T",
                "name_ko": "삼성물산",
                "exchange": "KRX",
                "name_short": "삼성물산",
                "exchange_code": "028260",
                "holdings_type": "company",
                "holdings_value": null,
                "holdings_shares": "971",
                "holdings_weight": null,
                "holding_isin_code": "KR7028260008",
                "holdings_industry": [],
                "holding_company_id": 10353,
                "holdings_market_cap": null,
                "country_code": "kr"
            },
            {
                "name": "SamsungElecMech",
                "name_ko": "삼성전기",
                "exchange": "KRX",
                "name_short": "삼성전기",
                "exchange_code": "009150",
                "holdings_type": "company",
                "holdings_value": null,
                "holdings_shares": "871",
                "holdings_weight": null,
                "holding_isin_code": "KR7009150004",
                "holdings_industry": [
                    {
                        "name": "반도체",
                        "name_ko": "반도체",
                        "country_code": "kr"
                    },
                    {
                        "name": "로봇",
                        "name_ko": "로봇",
                        "country_code": "kr"
                    },
                    {
                        "name": "스마트팩토리",
                        "name_ko": "스마트팩토리",
                        "country_code": "kr"
                    },
                    {
                        "name": "키오스크",
                        "name_ko": "키오스크",
                        "country_code": "kr"
                    },
                    {
                        "name": "신재생에너지",
                        "name_ko": "신재생에너지",
                        "country_code": "kr"
                    },
                    {
                        "name": "사물인터넷",
                        "name_ko": "사물인터넷",
                        "country_code": "kr"
                    },
                    {
                        "name": "웨어러블",
                        "name_ko": "웨어러블",
                        "country_code": "kr"
                    },
                    {
                        "name": "자율주행",
                        "name_ko": "자율주행",
                        "country_code": "kr"
                    },
                    {
                        "name": "태양광",
                        "name_ko": "태양광",
                        "country_code": "kr"
                    },
                    {
                        "name": "전기차",
                        "name_ko": "전기차",
                        "country_code": "kr"
                    }
                ],
                "holding_company_id": 9838,
                "holdings_market_cap": null,
                "country_code": "kr"
            },
            {
                "name": "SAMSUNG SDI CO.,LTD.",
                "name_ko": "삼성SDI",
                "exchange": "KRX",
                "name_short": "삼성SDI",
                "exchange_code": "006400",
                "holdings_type": "company",
                "holdings_value": null,
                "holdings_shares": "493",
                "holdings_weight": null,
                "holding_isin_code": "KR7006400006",
                "holdings_industry": [
                    {
                        "name": "스마트팩토리",
                        "name_ko": "스마트팩토리",
                        "country_code": "kr"
                    },
                    {
                        "name": "스마트그리드",
                        "name_ko": "스마트그리드",
                        "country_code": "kr"
                    },
                    {
                        "name": "신재생에너지",
                        "name_ko": "신재생에너지",
                        "country_code": "kr"
                    },
                    {
                        "name": "웨어러블",
                        "name_ko": "웨어러블",
                        "country_code": "kr"
                    },
                    {
                        "name": "2차전지",
                        "name_ko": "2차전지",
                        "country_code": "kr"
                    },
                    {
                        "name": "전기차",
                        "name_ko": "전기차",
                        "country_code": "kr"
                    }
                ],
                "holding_company_id": 9827,
                "holdings_market_cap": null,
                "country_code": "kr"
            },
            {
                "name": "SamsungF&MIns",
                "name_ko": "삼성화재",
                "exchange": "KRX",
                "name_short": "삼성화재",
                "exchange_code": "000810",
                "holdings_type": "company",
                "holdings_value": null,
                "holdings_shares": "327",
                "holdings_weight": null,
                "holding_isin_code": "KR7000810002",
                "holdings_industry": [
                    {
                        "name": "보험",
                        "name_ko": "보험",
                        "country_code": "kr"
                    }
                ],
                "holding_company_id": 10417,
                "holdings_market_cap": null,
                "country_code": "kr"
            }
        ],
        "market_info": {
            "nav": 18251.44,
            "aum": 9125721820.0,
            "trade_volume": 1032,
            "trade_value": 18897020.0,
            "market_cap": 9097500000.0,
            "yield_1d": -0.87,
            "yield_1w": 1.9328,
            "yield_1m": 7.0294,
            "yield_3m": 6.7782,
            "yield_ytd": 6.7782,
            "yield_1y": 6.7782,
            "flows_1w": 2095468619.0,
            "flows_3m": 4073923404.0,
            "flows_1m": 583520075.0,
            "flows_1y": 202143917.0,
            "flows_ytd": 4157564741.0,
            "volume_1w": 65266,
            "volume_1m": 71764,
            "update_date": "2025-02-20",
            "dividend": null,
            "dividend_yield_1y": 2.198406155537235
        }
    }
}
```


![](attachment:53e8f069-91a1-461a-8f3e-b7a1c5b8819a:image.png)
