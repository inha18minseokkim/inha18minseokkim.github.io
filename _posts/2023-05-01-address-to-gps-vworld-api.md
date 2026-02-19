---
title: "법정동코드 + 주소 → GPS 좌표 변환 (vWorld API)"
date: 2023-05-01
tags: [Spring, Java, 삽질, 공공API, 부동산]
---
[](https://www.vworld.kr/dev/v4dv_geocoderguide2_s002.do)[https://www.vworld.kr/dev/v4dv_geocoderguide2_s002.d](https://www.vworld.kr/dev/v4dv_geocoderguide2_s002.d)

법정동코드 + 주소 → GPS 좌표 변환해주는 오픈 API

![이미지](/assets/images/Pasted%20image%2020260219170525.png)
parcel(지번), road(도로명)으로 구분 가능

```python
import requests
apiurl = "<http://api.vworld.kr/req/address?">
params = {
    "service": "address",
    "request": "getcoord",
    "crs": "epsg:4326",
    "address": "역삼동 832-3",
    "format": "json",
    "type": "parcel",
    "key": "34254EFE-975B-3455-9D12-8AEBA654BDE7"
}
response = requests.get(apiurl, params=params)
if response.status_code == 200:
    print(response.json())
```

response

```json
{'response': 
{'service': 
{'name': 'address', 
'version': '2.0', 
'operation': 'getcoord', 
'time': '33(ms)'}, 
'status': 'OK', 
'input': {'type': 'parcel', 'address': '역삼동 83'}, 
'refined': 
{'text': '서울특별시 강남구 역삼동 832-3', 
'structure': 
{'level0': '대한민국', 'level1': '서울특별시', 
'level2': '강남구', 
'level3': '', 
'level4L': '역삼동',8320003', 
'level4A': '역삼1동', 
'level4AC': '1168064000', 
'level5': '832-3', '
detail': '강남역 쉐르빌'}}, 
'result': 
{'crs': 'EPSG:4326', 'point': {'x': '127.030707693455', 4923581728869'}}}}
```

동 + 지번 만으로 좌표 조회 가능(시군구는 선택)

```java
@Test
void 좌표컨트롤러정상작동여부() throws Exception {
    CoordinateDTO out = coordinateController.getCoordinate("신매동","10-31","수성구");
    Assertions.assertEquals(35.8359798259163,out.getLAT());
    Assertions.assertEquals(128.717796437585,out.getLOT());
}
@Test
void 좌표컨트롤러정상작동여부2() throws Exception {
    CoordinateDTO out = coordinateController.getCoordinate("구로동","104-3","");
    Assertions.assertEquals(37.4969780445254,out.getLAT());
    Assertions.assertEquals(126.891005369285,out.getLOT());
}
```

모두 테스트 통과(실제 위치와 같음)

![Untitled](https://s3-us-west-2.amazonaws.com/secure.notion-static.com/4f38a985-2b5e-4222-b622-bd3137499935/Untitled.png)

2023년 4월 분에 대한 오피스텔 전월세 거래내역 + gps 좌표

![Untitled](https://s3-us-west-2.amazonaws.com/secure.notion-static.com/99a930fd-56d4-4bcb-98a2-1e2b6ab233dc/Untitled.png)

현재 거주중인 오피스텔도 보임(2023년 1월 조회해보면 본인 계약건도 나올듯

![Untitled](https://s3-us-west-2.amazonaws.com/secure.notion-static.com/92593bb7-d5af-4ec2-980a-330b40e62024/Untitled.png)

지번에 따라서 미세하게 좌표 바뀜

```sql
select count(*) from tb_coordinate;
select count(distinct sigungu,dong,jibun) from tb_studio_rent;
```

두 코드 비교 결과, 누락된 좌표가 없음(국토교통부 ㄷㄷㄷㄷㄷ)

코드 예시(Spring Service) *주의 : UTF-8 인코딩 하지 않으면 문제 생길수도 있음..요청이 제대로 안간다거나

```java
package com.example.realestatemarket.coordinate;

import com.google.gson.Gson;
import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.reflect.TypeToken;
import jakarta.persistence.criteria.CriteriaBuilder;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.http.converter.StringHttpMessageConverter;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.util.UriComponentsBuilder;
import org.springframework.web.util.UrlPathHelper;

import java.net.MalformedURLException;
import java.net.URISyntaxException;
import java.net.URL;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import static org.aspectj.apache.bcel.generic.BasicType.getType;

@Service
public class CoordinateService {
    private Logger log = LoggerFactory.getLogger(CoordinateService.class);
    @Autowired
    private CoordinateRepository coordinateRepository;
    @Value("${landPortal.secret}")
    private String serviceKey;
    private RestTemplate restTemplate;

    public CoordinateService(){
        restTemplate = new RestTemplate();
        restTemplate.getMessageConverters()
                .add(0, new StringHttpMessageConverter(StandardCharsets.UTF_8));
    }
    public CoordinateDTO getCoordinateByDB(CoordinateEntity in) throws Exception {
        List<CoordinateEntity> outArr = coordinateRepository.getCoordinateInfo(in);
        log.info(String.valueOf(outArr.size()));
        if(outArr.size() == 0) throw new Exception("좌표 조회 실패");
        CoordinateDTO out = new CoordinateDTO();
        out.setLOT(outArr.get(0).getLOT());
        out.setLAT(outArr.get(0).getLAT());
        return out;
    }
    public CoordinateDTO getCoordinateByApi(CoordinateEntity in) throws MalformedURLException, URISyntaxException {
        String dong = in.getDong();
        String sigungu = in.getSigungu();
        String jibun = in.getJibun();
        String apiurl = "<http://api.vworld.kr/req/address?">;
        String requestAddress = String.format("%s %s %s",sigungu,dong,jibun);
//        UriComponentsBuilder builder = UriComponentsBuilder.fromUriString(apiurl)
//                .queryParam("service", "address")
//                .queryParam("request", "getcoord")
//                .queryParam("crs", "epsg:4326")
//                .queryParam("format", "json")
//                .queryParam("type", "parcel")
//                .queryParam("key", serviceKey)
//                .queryParam("address", requestAddress);
        StringBuilder sb = new StringBuilder("<https://api.vworld.kr/req/address>");
        sb.append("?service=address");
        sb.append("&request=getCoord");
        sb.append("&format=json");
        sb.append("&crs=" + "epsg:4326");
        sb.append("&key=" +  serviceKey);
        sb.append("&type=" + "parcel");
        sb.append("&address=" + URLEncoder.encode(requestAddress, StandardCharsets.UTF_8));
        //log.info(builder.toUriString());
        //log.info(String.valueOf(new URL(sb.toString()).toURI()));
        //log.info(requestAddress);
        log.info(serviceKey);//new URL(sb.toString()).toURI()
        ResponseEntity<String> response = restTemplate.getForEntity(new URL(sb.toString()).toURI(), String.class);
        if (response.getStatusCode() == HttpStatus.OK) {
            log.info(response.getBody());
        }
        CoordinateDTO out = new CoordinateDTO();
        try{
            Gson gson = new Gson();
            log.info("GSon 파싱 실행");
            JsonObject jsonObject = gson.fromJson(response.getBody(), JsonObject.class);

            log.info(jsonObject.toString());
            String status = String.valueOf(jsonObject.getAsJsonObject("response").get("status"));
            log.info(status);
            if(status.equals("\\"OK\\"")){
                JsonObject obj = jsonObject.getAsJsonObject("response").getAsJsonObject("result").getAsJsonObject("point");
                log.info(obj.toString());
                double x = Double.parseDouble(String.valueOf(obj.get("x")).replace("\\"",""));
                double y = Double.parseDouble(String.valueOf(obj.get("y").getAsDouble()).replace("\\"",""));
                log.info(String.valueOf(x));
                log.info(String.valueOf(y));
                out.setLAT(y);
                out.setLOT(x);
            }else{
                throw new Exception("좌표 없음");
            }
        }catch(Exception e){
            log.info(e.getMessage());
        }
        return out;
    }
    public void saveCoordinateEntity(String dong,String sigungu, String jibun, CoordinateDTO dto){
        CoordinateEntity out = new CoordinateEntity();
        out.setDong(dong);
        out.setSigungu(sigungu);
        out.setJibun(jibun);
        out.setLAT(dto.getLAT());
        out.setLOT(dto.getLOT());
        coordinateRepository.save(out);
    }

    public int saveCoordinateEntity(CoordinateEntity coordinateEntity) {
        log.info("CRUD 좌표 저장 실행");
        try{
        coordinateRepository.save(coordinateEntity);
        log.info(coordinateEntity.toString());
        }catch(Exception e){
            log.error(e.getMessage());
            return 0;
        }
        return 1;
    }
}
```
