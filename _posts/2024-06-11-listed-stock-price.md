---
title: 상장주식시세
date: 2024-06-11
tags:
  - 기획
  - 주식서비스
category:
  - 실무경험
  - 투자홈
---


![이미지](/assets/images/Pasted%20image%2020260226144624.png)


![이미지](/assets/images/Pasted%20image%2020260226144629.png)



![이미지](/assets/images/Pasted%20image%2020260226144633.png)

매 15분 마다 갱신
거래량, 많이 오른, 많이 내린, 시가총액 기준 정렬 필요
많이 오른, 많이 내린 > 기준점이 어디인지 문의 필요
  - ⇒ 전 거래일 종가 대비 현재가 기준. 
몇개까지 보여줄지
  - 15분 마다 갱신하는 경우 Redis에 위 테이블과 집계 결과 저장할 예정


![이미지](/assets/images/Pasted%20image%2020260226144637.png)

기준가 4200원 > 실시간 가격 (15분)
기준일자 : 그냥 현재시각으로 할까, 기준가가 반영되어있는 마지막으로 할까
1개월 가격 > 오늘부터 30일 전까지 가격
3개월 가격 > 오늘부터 90일 전까지 가격

|  | date | symbol | entity_name | exchange | market | symbol_nice | ceo | business_rid | company_rid | tel | ... | conglomerate_id | industry_id | industry_name | fs_type | fiscal_year_end | business_area | date_founded | date_listed | shares_outstanding | trading_halted |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 2024-05-30T00:00:00 | KRX:000020 | 동화약품 | KRX | KOSPI | NICE:350605 | 유준하 | 1108100102 | 1101110043870 | 02-2021-9300 | ... | E25 | KRI:10C2121000 | 완제 의약품 제조업 | 00 | 12.0 | 의약품 제조,판매,수출입 | 1897-09-25T00:00:00 | 1976-03-24T00:00:00 | 27931470 | 0 |


![이미지](/assets/images/Pasted%20image%2020260226144641.png)


![이미지](/assets/images/Pasted%20image%2020260226144645.png)

흐름도

![이미지](/assets/images/Pasted%20image%2020260226144649.png)

앞에는 카카오페이 마이데이터 제휴화면이고 종목 정보 보기 > 여기서 케이뱅크 앱 URL 타고 들어올 예정

![이미지](/assets/images/Pasted%20image%2020260226144652.png)
