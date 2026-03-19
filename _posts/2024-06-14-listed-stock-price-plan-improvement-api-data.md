---
title: 상장주식시세 기획안 개선 + API 기준 데이터 정리
date: 2024-06-14
tags:
  - 주식서비스
  - 기획
  - 개발
category:
  - 실무경험
  - 투자홈
---
기획안 개선 + 적재 API 정리(주식시세)

![이미지](/assets/images/Pasted%20image%2020260226144711.png)




![이미지](/assets/images/Pasted%20image%2020260226144716.png)



![이미지](/assets/images/Pasted%20image%2020260226144718.png)

- [ ] 종목기준정보조회
  - GetStockSymbols(entities="")

```java
{'date': {2321: '2024-06-13T00:00:00'},
 'symbol': {2321: 'KRX:252670'},
 'entity_name': {2321: 'KODEX 200선물인버스2X'},
 'exchange': {2321: 'KRX'},
 'market': {2321: 'KOSPI'},
 'symbol_nice': {2321: 'NICE:HT9173'},
 'ceo': {2321: '구성훈'},
 'business_rid': {2321: ''},
 'company_rid': {2321: ''},
 'tel': {2321: '02-3774-7600'},
 'fax': {2321: ''},
 'website': {2321: 'www.samsungfund.com'},
 'email': {2321: ''},
 'zipcode': {2321: '100716'},
 'address_land_lot': {2321: '서울 중구 태평로2가 150번지 삼성생명빌딩 23층 삼성자산운용'},
 'address_road_name': {2321: '서울 중구 세종대로 55, 23층 삼성자산운용'},
 'group_id': {2321: 'EF'},
 'company_type_l1': {2321: '8'},
 'company_type_l2': {2321: '000'},
 'company_type_size': {2321: '0'},
 'conglomerate_id': {2321: ''},
 'industry_id': {2321: None},
 'industry_name': {2321: None},
 'fs_type': {2321: '00'},
 'fiscal_year_end': {2321: 12.0},
 'business_area': {2321: ''},
 'date_founded': {2321: None},
 'date_listed': {2321: '2016-09-22T00:00:00'},
 'shares_outstanding': {2321: 655000000},
 'trading_halted': {2321: 0}}
```

- [ ] 실시간종목가격조회(15분,for redis & spring scheduler)
- [ ] 일종목가격조회(영업일1회, 장마감후,for spring batch)
  - GetStockPrices(entities="")

```java
{'date': '2024-06-14T00:00:00',
 'symbol': 'KRX:000020',
 'entity_name': '동화약품',
 'open': 8260,
 'high': 9200,
 'low': 8070,
 'close': 8500,
 'volume': 1508746,
 'value': 13182436010,
 'change': 320,
 'change_rate': 0.03909999877214432,
 'shares_outstanding': 27931470,
 'market_cap': 237417495000,
 'trading_halted': 0}
```

- [ ] 재무비율조회(일1회)
  - 삼성전자 EPS BPS PER PBR DPS 배당수익률 2010-01-01-2024-06-10

```java
{'date': '2016-01-04T00:00:00',
 'symbol': 'KRX:005930',
 'entity_name': '삼성전자',
 'EPS 2010-01-01-2024-06-10': 153105,
 'BPS 2010-01-01-2024-06-10': 953266,
 'PER 2010-01-01-2024-06-10': 8.229999542236328,
 'PBR 2010-01-01-2024-06-10': 1.3200000524520874,
 'DPS 2010-01-01-2024-06-10': 20000,
 '배당수익률 2010-01-01-2024-06-10': 1.600000023841858}
```

- [ ] 컨센서스조회(재무비율)
  - SearchFirmFundamentalsForecasts(symbols=KRX:005930, last_only=True, accounting_types=\"K\")

```java
{'stock_code': '005930',
 'forecast_date': '202412',
 'accounting_type': 'K',
 'inst_code': '126106',
 'name_ko': '하이투자증권',
 'name_en': 'HI INVESTMENT & SECURITIES',
 'bps': None,
 'csd_bps': 55941.0,
 'csd_ebitda': nan,
 'csd_eps': 4889.0,
 'csd_ev_ebitda': 4.400000095367432,
 'csd_pbr': 1.399999976158142,
 'csd_per': 15.800000190734863,
 'csd_roe': 91.0,
 'date': '20240520',
 'ebitda': None,
 'eps': None,
 'ev_ebitda': None,
 'pbr': None,
 'per': None,
 'revenue_growth': None,
 'roe': None,
 'seq': 6,
 'unit_code': '02',
 'revenue': None,
 'operating_income': None,
 'ordinary_profit': None,
 'net_income': None,
 'continuing_profit': None,
 'csd_revenue': 302311997440000.0,
 'csd_operating_income': 44259999744000.0,
 'csd_net_income': 33211000832000.0,
 'csd_continuing_profit': 47382999040000.0}
```

- [ ] 기업설명조회(일1회)
  - GetCompanyBusinessSummary(entities=[KRX:005930,KRX:000660])

```java
{'symbol': 'KRX:000660',
 'entity_name': 'SK하이닉스',
 'summary_title': 'SK그룹의 종합반도체 기업',
 'summary_content_1': '- 동사는 SK그룹 산하 SK텔레콤이 하이닉스반도체를 인수하여 2012년 3월 SK하이닉스로 출범시킨 메모리반도체 전문 생산 기업임.',
 'summary_content_2': '- 경기도 이천시와 충청북도 청주시, 중국 우시와 충칭에 생산공장을 설치 및 가동하고 있으며, 다수의 해외 판매법인과 사무소를 두고 있음.',
 'summary_content_3': '- 주력 생산 제품은 DRAM, NAND Flash 및 MCP와 같은 메모리 반도체 제품이며, 시스템 LSI 분야인 CIS 사업에 재진출하여 종합반도체로 그 영역을 확대하고 있음.',
 'status_title': '매출 감소 및 적자전환',
 'status_content_1': '- AI용 HBM과 고용량 DDR5의 수요 호조에도 전방 IT 제품의 수요 위축, 빅테크 업체들의 데이터센터 및 서버 관련 투자 축소, 메모리 가격의 하락 등으로 매출 규모는 전년대비 축소.',
 'status_content_2': '- 공급 과잉에 따른 DRAM 및 NAND 가격의 하락세 등으로 영업이익 전년대비 적자전환, 이자비용 및 장기투자자산평가손실 증가 등의 금융수지 저하되며 순이익도 적자전환.',
 'status_content_3': '- AI 시장 개화에 따른 HBM, DDR5 등 차세대 메모리의 수요 확대와 엔비디아 내 시장 지배력 지속, 전략적 공급 축소에 따른 ASP 상승, HBM3E의 수율 안정화 등으로 외형 성장 및 수익성 개선 전망.',
 'updated_at': '1970-01-01T00:00:00'}
```

