---
title: "법정동코드 + 주소 → GPS 좌표 변환 (vWorld API)"
date: 2023-05-01
tags: [Spring, Java, 삽질, 공공API, 부동산]
---

법정동코드 + 주소를 GPS 좌표로 변환해주는 오픈 API를 발견했다.

[vWorld 지오코더 API](https://www.vworld.kr/dev/v4dv_geocoderguide2_s002.do)

parcel(지번), road(도로명)으로 구분 가능하다.

## Python 예제

```python
import requests

apiurl = "http://api.vworld.kr/req/address?"
params = {
    "service": "address",
    "request": "getcoord",
    "crs": "epsg:4326",
    "address": "역삼동 832-3",
    "format": "json",
    "type": "parcel",
    "key": "YOUR_API_KEY"
}
response = requests.get(apiurl, params=params)
if response.status_code == 200:
    print(response.json())
```

응답 예시:

```json
{
  "response": {
    "status": "OK",
    "input": { "type": "parcel", "address": "역삼동 832-3" },
    "result": {
      "crs": "EPSG:4326",
      "point": {
        "x": "127.030707693455",
        "y": "37.4923581728869"
      }
    }
  }
}
```

동 + 지번만으로 좌표 조회 가능 (시군구는 선택).

## Java 테스트

```java
@Test
void 좌표컨트롤러정상작동여부() throws Exception {
    CoordinateDTO out = coordinateController.getCoordinate("신매동", "10-31", "수성구");
    Assertions.assertEquals(35.8359798259163, out.getLAT());
    Assertions.assertEquals(128.717796437585, out.getLOT());
}

@Test
void 좌표컨트롤러정상작동여부2() throws Exception {
    CoordinateDTO out = coordinateController.getCoordinate("구로동", "104-3", "");
    Assertions.assertEquals(37.4969780445254, out.getLAT());
    Assertions.assertEquals(126.891005369285, out.getLOT());
}
```

모두 테스트 통과 (실제 위치와 일치).

## 결과 활용

2023년 4월분 오피스텔 전월세 거래내역 + GPS 좌표를 조회해봤다. 현재 거주 중인 오피스텔도 데이터에 잡힌다.

```sql
SELECT count(*) FROM tb_coordinate;
SELECT count(DISTINCT sigungu, dong, jibun) FROM tb_studio_rent;
```

두 카운트를 비교해보니 누락된 좌표가 없다. 국토교통부 API의 커버리지가 생각보다 훨씬 좋다.

## 주의사항

Spring Service에서 vWorld API 호출 시 **UTF-8 인코딩**을 반드시 처리해야 한다. 인코딩 없이 요청하면 한글 주소가 제대로 전달되지 않는다.
