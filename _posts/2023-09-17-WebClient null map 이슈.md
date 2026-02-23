---
title: "WebClient null map 이슈"
date: 2023-09-17
tags: [미지정]
---

### 문제상황


```javascript
public class AnnounceDefaultResponse implements Serializable {
    private String status;
    private String message;
    private String page_no;
    private Integer page_count;
    private Integer total_count;
    private Integer total_page;
    private List<AnnounceDefaultElement> list;
}
```


```javascript
public class AnnounceDefaultElement implements Serializable {
    //법인구분	    법인구분 : Y(유가), K(코스닥), N(코넥스), E(기타)
    private String corp_cls;
    //종목명(법인명)	공시대상회사의 종목명(상장사) 또는 법인명(기타법인)
    private String corp_name;
    //고유번호	    공시대상회사의 고유번호(8자리)
    private String corp_code;
    //종목코드	    상장회사의 종목코드(6자리)
    private String stock_code;
    //보고서명	    공시구분+보고서명+기타정보
    private String report_nm;
    //접수번호	    접수번호(14자리)
    private String rcept_no;
    //공시 제출인명	    공시 제출인명
    private String flr_nm;
    //접수일자	    공시 접수일자(YYYYMMDD)
    private String rcept_dt;
    //비고
    private String rm;
}
```

다음과 같이 body를 설정해놓음

```java
public Mono<AnnounceDefaultResponse> getCurrentCorpAnnounce(CorpInfo corpInfo,String beginDate,String endDate) {
        String url = UriComponentsBuilder.fromHttpUrl("https://opendart.fss.or.kr/api/list.json")
                .queryParam("crtfc_key",opendartSecret)
                .queryParam("corp_code",corpInfo.getCorpCode())
                .queryParam("bgn_de",beginDate)
                .queryParam("end_de",endDate)
                .queryParam("last_report_at","Y")
                .build().toUriString();
        log.info(url);
        WebClient webClient = WebClient.builder().baseUrl(url)
                .defaultHeader(HttpHeaders.CONTENT_TYPE, MediaType.APPLICATION_ATOM_XML_VALUE).build()
                ;
        Mono<AnnounceDefaultResponse> result = webClient.get().retrieve()
                .bodyToMono(AnnounceDefaultResponse.class);
        log.info(result.toString());
        return result;
    }
```

response 전문

```json
{"status":"000","message":"정상","page_no":1,
	"page_count":10,"total_count":95,"total_page":10,
"list":
[{"corp_code":"00126380","corp_name":"삼성전자","stock_code":"005930","corp_cls":"Y","report_nm":"임원ㆍ주요주주특정증권등소유상황보고서","rcept_no":"20230912000215","flr_nm":"조미선","rcept_dt":"20230912","rm":""},
{"corp_code":"00126380","corp_name":"삼성전자","stock_code":"005930","corp_cls":"Y","report_nm":"최대주주등소유주식변동신고서","rcept_no":"20230911800401","flr_nm":"삼성전자","rcept_dt":"20230911","rm":"유"},
{"corp_code":"00126380","corp_name":"삼성전자","stock_code":"005930","corp_cls":"Y","report_nm":"주식등의대량보유상황보고서(일반)","rcept_no":"20230908000465","flr_nm":"삼성물산","rcept_dt":"20230908","rm":""},
{"corp_code":"00126380","corp_name":"삼성전자","stock_code":"005930","corp_cls":"Y","report_nm":"대규모기업집단현황공시[분기별공시(대표회사용)]","rcept_no":"20230831000163","flr_nm":"삼성전자","rcept_dt":"20230831","rm":"공"},
{"corp_code":"00126380","corp_name":"삼성전자","stock_code":"005930","corp_cls":"Y","report_nm":"특수관계인과의보험거래","rcept_no":"20230818000486","flr_nm":"삼성전자","rcept_dt":"20230818","rm":"공"},
{"corp_code":"00126380","corp_name":"삼성전자","stock_code":"005930","corp_cls":"Y","report_nm":"특수관계인과의보험거래","rcept_no":"20230818000484","flr_nm":"삼성전자","rcept_dt":"20230818","rm":"공"},
{"corp_code":"00126380","corp_name":"삼성전자","stock_code":"005930","corp_cls":"Y","report_nm":"주식등의대량보유상황보고서(일반)","rcept_no":"20230818000461","flr_nm":"삼성물산","rcept_dt":"20230818","rm":""},
{"corp_code":"00126380","corp_name":"삼성전자","stock_code":"005930","corp_cls":"Y","report_nm":"반기보고서 (2023.06)","rcept_no":"20230814002534","flr_nm":"삼성전자","rcept_dt":"20230814","rm":""},
{"corp_code":"00126380","corp_name":"삼성전자","stock_code":"005930","corp_cls":"Y","report_nm":"지급수단별ㆍ지급기간별지급금액및분쟁조정기구에관한사항","rcept_no":"20230814001602","flr_nm":"삼성전자","rcept_dt":"20230814","rm":"공"},
{"corp_code":"00126380","corp_name":"삼성전자","stock_code":"005930","corp_cls":"Y","report_nm":"동일인등출자계열회사와의상품ㆍ용역거래변경","rcept_no":"20230814001577","flr_nm":"삼성전자","rcept_dt":"20230814","rm":"공"}
]}
```


```java
AnnounceDefaultResponse(status=000, message=정상, page_no=1, page_count=10, total_count=95, total_page=10, 
list=[
AnnounceDefaultElement(corp_cls=null, corp_name=null, corp_code=null, stock_code=null, report_nm=null, rcept_no=null, flr_nm=null, rcept_dt=null, rm=null), 
AnnounceDefaultElement(corp_cls=null, corp_name=null, corp_code=null, stock_code=null, report_nm=null, rcept_no=null, flr_nm=null, rcept_dt=null, rm=null), 
AnnounceDefaultElement(corp_cls=null, corp_name=null, corp_code=null, stock_code=null, report_nm=null, rcept_no=null, flr_nm=null, rcept_dt=null, rm=null), 
AnnounceDefaultElement(corp_cls=null, corp_name=null, corp_code=null, stock_code=null, report_nm=null, rcept_no=null, flr_nm=null, rcept_dt=null, rm=null), 
AnnounceDefaultElement(corp_cls=null, corp_name=null, corp_code=null, stock_code=null, report_nm=null, rcept_no=null, flr_nm=null, rcept_dt=null, rm=null), 
AnnounceDefaultElement(corp_cls=null, corp_name=null, corp_code=null, stock_code=null, report_nm=null, rcept_no=null, flr_nm=null, rcept_dt=null, rm=null), 
AnnounceDefaultElement(corp_cls=null, corp_name=null, corp_code=null, stock_code=null, report_nm=null, rcept_no=null, flr_nm=null, rcept_dt=null, rm=null), 
AnnounceDefaultElement(corp_cls=null, corp_name=null, corp_code=null, stock_code=null, report_nm=null, rcept_no=null, flr_nm=null, rcept_dt=null, rm=null), 
AnnounceDefaultElement(corp_cls=null, corp_name=null, corp_code=null, stock_code=null, report_nm=null, rcept_no=null, flr_nm=null, rcept_dt=null, rm=null), 
AnnounceDefaultElement(corp_cls=null, corp_name=null, corp_code=null, stock_code=null, report_nm=null, rcept_no=null, flr_nm=null, rcept_dt=null, rm=null)
])
```



원인
Getter가 없어서
해결방안

```java
@ToString
@Getter
@NoArgsConstructor
public class AnnounceDefaultElement implements Serializable {
    //법인구분	    법인구분 : Y(유가), K(코스닥), N(코넥스), E(기타)
    private String corp_cls;
    //종목명(법인명)	공시대상회사의 종목명(상장사) 또는 법인명(기타법인)
    private String corp_name;
    //고유번호	    공시대상회사의 고유번호(8자리)
    private String corp_code;
    //종목코드	    상장회사의 종목코드(6자리)
    private String stock_code;
    //보고서명	    공시구분+보고서명+기타정보
    private String report_nm;
    //접수번호	    접수번호(14자리)
    private String rcept_no;
    //공시 제출인명	    공시 제출인명
    private String flr_nm;
    //접수일자	    공시 접수일자(YYYYMMDD)
    private String rcept_dt;
    //비고
    private String rm;
}
```

Getter를 선언해주면 된다
