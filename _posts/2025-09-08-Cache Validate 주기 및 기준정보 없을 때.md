---
title: "Cache Validate 주기 및 기준정보 없을 때 "
date: 2025-09-08
tags: [미지정]
category: 기타
---

![](attachment:547a3115-e2d7-449b-9431-4c896aa04905:image.png)

정상일 때(타겟 데이터 NVDA) 
  - 당일가격 잘 가져옴, 167.02

![](attachment:6da1d22d-6c30-4511-9cc7-ddf023e4b48d:image.png)

누락시(타겟데이터 에스유엔피)
  - 이름은 주고 가격은 안줌(상폐 이슈로 가격은 없지만 고객이 등록해놓은 경우 이름은 보여줘야함)


![](attachment:f635855e-2e37-43d5-92d8-7fba846f5e1c:image.png)

내관심 기준 으로도 에스유엔피 가격 미노출 이름 노출 확인

### Cache Invalidate Test


![](attachment:3a5e370f-d896-4a59-b083-f6518a772ef6:image.png)

9월 5일자 NVDA 가격 데이터 지우고 Cache Invalidate 주기까지 기다림
정상 작동 확인(mediation 및 overseas-stock-service)

### 채널에 넣을 요구사항(이슈사항)


![](attachment:fe4e3072-9feb-4e1f-b6be-ef0463da23e3:image.png)

1. 가격을 null로 주면 채널 쪽 최신 가격 invalidate 필요할 듯(171.66달러는 고객 디바이스 기준으로 캐싱된 데이터) > 알고보니 mediation 파드에서 캐시갱신이 잘 일어나지 않았던 것,
2. 해당 엘리먼트 눌렀을 때 캐시값이 사라지도록 해야함
3. 저렇게 생긴애들 상세 진입 못하는 로직 넣어야함. 현재 4XX 에러 내려주는중


![](attachment:b25c66c9-4fda-41a3-8f11-6c7bbe0f5e12:image.png)
