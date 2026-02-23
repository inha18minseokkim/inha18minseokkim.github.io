---
title: "Generic + WebClient"
date: 2023-10-01
tags: [미지정]
---
Generic Type을 선언한 클래스
다만 Generic의 경우 Compile 타임에 타입을 결정해야 한다. 
[https://stackoverflow.com/questions/14670839/how-to-set-the-generic-type-of-an-arraylist-at-runtime-in-java](https://stackoverflow.com/questions/14670839/how-to-set-the-generic-type-of-an-arraylist-at-runtime-in-java)
> You can't.
런타임에서 타입을 결정하고 싶으면 다형성을 고려해야 할 것 → 지금 할 일 요약 : Generic으로 상위 인터페이스 타입을 선언해놓고 런타임에서 활용할 예정

해결해야 할 사항
20가지 정도 되는 공시자료(응답 타입은 같은데 세부 element가 다름)를 한 함수에다 받아보고 싶다

금감원 공시자료 20종을 받기 위해 Generic 리스트를 선언

```java
@Getter
@ToString
public class AnnounceEssentialResponse {
    private String status;
    private String message;
    private List<Object> list;
}
```

응답 예시) 유상증자

```java
{"status":"000","message":"정상",
"list":[{"rcept_no":"20190221000921",
"corp_cls":"K","corp_code":"00378363",
"corp_name":"3S","nstk_ostk_cnt":"376,265",
"nstk_estk_cnt":"-","fv_ps":"500","bfic_tisstk_ostk":"44,395,878",
"bfic_tisstk_estk":"-","fdpp_fclt":"-","fdpp_bsninh":"-","fdpp_op":"783,393,850",
"fdpp_dtrp":"-","fdpp_ocsa":"-","fdpp_etc":"3,000,000","ic_mthn":"제3자배정증자",
"ssl_at":"-","ssl_bgd":"-","ssl_edd":"-"}]}
```

응답예시) 감자

```java
{"status":"000","message":"정상",
"list":[{"rcept_no":"20190513000176","corp_cls":"Y","corp_code":"00121932",
"corp_name":"미원상사","bddd":"2019년 05월 13일","od_a_at_t":"0","od_a_at_b":"3",
"adt_a_atn":"불참","fv_ps":"5,000","crstk_ostk_cnt":"-","crstk_estk_cnt":"-",
"bfcr_cpt":"29,291,895,000","atcr_cpt":"6,635,191,500",
"bfcr_tisstk_ostk":"5,034,823","atcr_tisstk_ostk":"5,034,823",
"bfcr_tisstk_estk":"-","atcr_tisstk_estk":"-","cr_rt_ostk":"90","cr_rt_estk":"-",
"cr_std":"2019년 07월 29일","cr_mth":"액면금액 감소(5,000원->500원)",
"cr_rs":"배당가능재원의 확보","crsc_gmtsck_prd":"2019년 06월 27일",
"crsc_trnmsppd":"2019년 05월 29일 ~ 2019년 05월 31일",
"crsc_osprpd":"2019년 06월 28일 ~ 2019년 07월 29일",
"crsc_trspprpd":"2019년 07월 26일 ~ 2019년 08월 12일",
"crsc_osprpd_bgd":"-","crsc_osprpd_edd":"-","crsc_trspprpd_bgd":"-","crsc_trspprpd_edd":"-","crsc_nstkdlprd":"2019년 08월 12일","crsc_nstklstprd":"2019년 08월 13일","cdobprpd_bgd":"2019년 06월 28일","cdobprpd_edd":"2019년 07월 29일","ospr_nstkdl_pl":"KEB하나은행 증권대행부","ftc_stt_atn":"미해당"}]}
```

이런 식으로 응답은 같음. list 안에 들어가는 element의 종류가 모두 다름
그래서 타입이 다 달라서 Object로 선언함
사실 따지고보면 다 Object의 하위클래스이므로 너무 날로먹는것 같은 느낌이 들기 때문에
해당 도메인 영역을 한정하기 위해 다음과 같은 인터페이스로 바꿔주고싶다. EssentialResponseElement는 안에 아무것도 없고 Default 메서드 하나 있음

```java
public interface EssentialResponseElement {
    public default EssentialResponseElement getRefinedElement() {
        //EssentialElement를 구현하는 하위클래스 인스턴스 생성
        EssentialResponseElement essentialResponseElement = null;
        try {
            essentialResponseElement = this.getClass().getConstructor().newInstance();
        } catch (InstantiationException e) {
            throw new RuntimeException(e);
        } catch (IllegalAccessException e) {
            throw new RuntimeException(e);
        } catch (InvocationTargetException e) {
            throw new RuntimeException(e);
        } catch (NoSuchMethodException e) {
            throw new RuntimeException(e);
        }
        //각 필드에서 셋팅해줌(하위 클래스의 필드를 따름)
        for(Field field : this.getClass().getDeclaredFields()) {
            if(field.getType().equals(String.class)){
                field.setAccessible(true);
                try {
                    String o = (String)field.get(this);
                    if(o == null) continue;
                    //숫자 및 없는 정보는 null로 만들기 위한 정제작업
                    field.set(essentialResponseElement,o.replace("-","")
                            .replace(",","").trim());
                } catch (IllegalAccessException e) {
                    throw new RuntimeException(e);
                }
            }
        }
        //this 가 아닌 복사된 객체 리턴(함수형 인터페이스 사용 기대)
        return essentialResponseElement;
    }
}
```

해당 default 메서드는 객체를 정제하는 공통 메서드임(일단 여기 만들어놨는데 적절한 위치는 아닌것같음, 고민하는중)


```java
@Getter
@ToString
public class AnnounceEssentialResponse {
    private String status;
    private String message;
//이렇게 바꿔주고싶은데 webFlux에서 JSON 변환할 때 Object 아니면 에러나서 못바꿈
    private List<EssentialResponseElement> list;
}
```

해당 인터페이스를 구현하는 DTO를 구현해주면 된다.

```java
@ToString
@Getter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class AnnouncePaidIncreaseElement implements EssentialResponseElement {
    //	접수번호
    private String rcept_no;
    //	법인구분
    private String corp_cls;
    //	고유번호
    private String corp_code;
    //	회사명
    private String corp_name;
    //	신주의 종류와 수(보통주식 (주))
    private String nstk_ostk_cnt;
    //	신주의 종류와 수(기타주식 (주))
    private String nstk_estk_cnt;
    //	1주당 액면가액 (원)
    private String fv_ps;
    //	증자전 발행주식총수 (주)(보통주식 (주))
    private String bfic_tisstk_ostk;
    //	증자전 발행주식총수 (주)(기타주식 (주))
    private String bfic_tisstk_estk;
    //	자금조달의 목적(시설자금 (원))
    private String fdpp_fclt;
    //	자금조달의 목적(영업양수자금 (원))
    private String fdpp_bsninh;
    //	자금조달의 목적(운영자금 (원))
    private String fdpp_op;
    //	자금조달의 목적(채무상환자금 (원))
    private String fdpp_dtrp;
    //	자금조달의 목적(타법인 증권 취득자금 (원))
    private String fdpp_ocsa;
    //	자금조달의 목적(기타자금 (원))
    private String fdpp_etc;
    //	증자방식
    private String ic_mthn;
    //	공매도 해당여부
    private String ssl_at;
    //	공매도 시작일
    private String ssl_bgd;
    //	공매도 종료일
    private String ssl_edd;
}
```


선언해놓고 webFlux에서 다음과 같이 받아옴

```java
Mono<AnnounceEssentialResponse> result = webClient.get().retrieve()
          .bodyToMono(AnnounceEssentialResponse.class);
  AnnounceEssentialResponse block = result.block();
  List<Object> list = block.getList();
  ObjectMapper objectMapper = new ObjectMapper();
  log.info(list.toString());
  return list.stream().map(object -> objectMapper.convertValue(object, responseClass));
```

EssentialResponseElement타입에 선언되어있는 필드는 없지만 objectMapper를 사용하여 살려준 다음 EssentialResponseElement의 하위타입 클래스로 타입 변환해줌

responseClass는 AnnouncePaidIncreaseElement.class 인 Class 타입 변수임.
