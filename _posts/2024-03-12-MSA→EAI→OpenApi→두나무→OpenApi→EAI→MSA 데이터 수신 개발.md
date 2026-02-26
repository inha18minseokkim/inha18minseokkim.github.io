---
title: MSA→EAI→OpenApi→두나무→OpenApi→EAI→MSA 데이터 수신 개발
date: 2024-03-12
tags:
  - 아키텍처
  - Java
  - 케이뱅크
  - 주식서비스
category:
  - 실무경험
---

EAI 바디에 전문을 fixedLength로 파싱하지 않고 통 Json으로 받는 방식으로 개발 시작

```json
{
"totalCount": 1, // item 갯수
"publishAt": "2024-03-11 19:47:31", // 기준일
"items": [
		{
		"code": "279570", // 종목코드
		"koreanName": "케이뱅크", // 종목 한글명
		"isRegister": true, // 장외정보(종목의 비상장서비스 등록유무)
		"searchCount": 12345, // 주간 종목 검색횟수
		"marketCap": 6424387082100, // 예상시총
		"evaluatedByMedia": "4조원 ~ 5조원", // 언론에서 말하는 기업가치
		"prevPrice": 12000, // 전일 기준가격
		"prevHighPrice": 22000, // 전일 최고가격
		"52WeekHighPrice": 24000, // 52주 기준가격
		"prevLowPrice": 11000, // 전일 최저가격
		"52WeekLowPrice": 11000, // 52주 최저가격
		"changePriceValue": 1000, // 전일자대비 가격변동
		"changePriceRate": 8.4, // 전일자대비 가격변동률
		"linkUrl": "https://ustockplus.onelink.me/FwJh?pid=KB%EC%A6%9D%EA%B6%8C&c=%EC%8B%9C%EC%84%B8%EC%A1%B0%ED%9A%8C&af_js_web=true&af_force_deeplink=true&af_dp=ustockplus%3A%2F%2Fstock-detail%2Forder%3Fcode%3D279570%26referer%3Dkbank&af_web_dp=https%3A%2F%2Fustockplus.com%2Fstock%2F279570", // 원링크 url
		"state": "미정", // 종목상태. value 정의를 위한 협의가 필요
		"ipoStep": "미정", // 공모주단계 정보. value 정의를 위한 협의가 필요
		}
]
}
```

데이터는 이런식으로 온다고 함
(수정)

```javascript
{
	totalCount": 1, // item 갯수
	"publishAt": "2024-03-11 19:47:31" // 기준일
	"items": [
		{
			"code": "279570", // 종목코드
			"koreanName": "케이뱅크", // 종목 한글명
			"isRegistered": true, // 종목의 비상장서비스 등록유무
			"searchCount": 12345, // 주간 종목 검색횟수
			"marketCap": 6424387082100, // 예상시총
			"evaluatedByMedia": "4조원 ~ 5조원", // 언론에서 말하는 기업가치
			"highestPrices": {
					"yesterday": 24000, // 전일 최고가격
					"until52Week": 24000, // 52주 최고가격
			},
			"lowestPrices": {
					"yesterday": 11000, // 전일 최저가격
					"until52Week": 11000, // 52주 최저가격
				},
			"changePrices": {
					"price": 13000, // 전일 기준가격
					"value": 1000, // 전일자대비 가격변동
					"rate": 8.4, // 전일자대비 가격변동률
				},
			"linkUrl": "https://ustockplus.onelink.me/FwJh?pid=KB%EC%A6%9D%EA%B6%8C&c=%EC%8B%9C%EC%84%B8%EC%A1%B0%ED%9A%8C&af_js_web=true&af_force_deeplink=true&af_dp=ustockplus%3A%2F%2Fstock-detail%2Forder%3Fcode%3D279570%26referer%3Dkbank&af_web_dp=https%3A%2F%2Fustockplus.com%2Fstock%2F279570", // 원링크 url
		}
]
}
```

이렇게 바꿔주심

### 결론

원래는 실시간 릴레이로 가져오려 했는데 EAI이슈로 인해 파일 적재로..가져온다 ㅠㅠ
