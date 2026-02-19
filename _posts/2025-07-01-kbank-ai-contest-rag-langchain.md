---
title: "케이뱅크 AI 공모전 금상 후기 - RAG 파이프라인 + LangChain 챗봇"
date: 2025-07-01
tags: [AI, LangChain, RAG, LLM, Python, 케이뱅크, 수상]
---

2025년 상반기 사내 AI 공모전에서 금상(400만원 + 싱가폴 Fintech Week 참가)을 수상했다. 출품한 내용을 정리해본다.

## 출품 주제 요약

1. RAG를 활용한 케이뱅크 주식 데이터 수집/정제/벡터화 Pipeline POC
2. 케이뱅크 주식 MSA 서비스를 호출하는 LangChain 챗봇 POC
3. Python + LLM few-shot prompting으로 주식 데이터 수집 후 케이뱅크 메타 표준 변환 프로세스 간소화

---

## 주제 1: RAG 기반 주식 정보 수집/정제/벡터화 파이프라인

### 왜 필요했나

케이뱅크 투자 서비스는 "증권사가 아닌 은행"이라는 포지셔닝을 한다. 그래서 단순 주가 정보 외에, 투자자가 쉽게 이해할 수 있는 정보성 콘텐츠를 제공하는 것이 차별화 포인트다.

문제는 이런 정보를 내부 인력이 직접 가공하면 인건비 부담이 크고, 외부 데이터 피드 업체에 의뢰하면 범위 한계가 있다는 것이다.

**구체적인 Pain Point:** 공모주 메이트 서비스에서 비상장 기업의 사업 내용 정보를 제공하고 싶었는데, 비상장 기업은 데이터 소스가 극히 제한적이다. 금감원 전자공시시스템의 증권신고서가 사실상 유일한 소스인데, 이걸 일일이 사람이 읽고 정리하기엔 너무 많다.

### RAG로 해결하기

RAG(Retrieval-Augmented Generation)를 사용하면:

- **수집**: 크롤러 + 외부 API로 자동화
- **정제**: LLM 기반 정규화 및 중요도 필터링
- **벡터화**: 임베딩 기반 벡터 DB 저장
- **노출**: LLM + 프롬프트 엔지니어링 기반 문답형 UI

작은 리소스로 고품질 투자 정보 서비스가 가능하다.

### 구현 방식

케이뱅크 MSA 환경에서 실현 가능한 방식으로 POC를 구성했다:

1. 금융감독원 공시 데이터 원본 수집
2. 기계적 파싱 및 청킹
3. 청킹된 데이터 임베딩
4. 실제 비즈니스 요건에 맞춰 응답 결과 생성

비선형적인 처리가 가능하기 때문에 다양한 비즈니스 요건을 프롬프트에 맞게 조정할 수 있다.

### 의의

**실현 가능성:** 케이뱅크 내부 IDC와 AWS 인프라 모두에서 동작 가능한 구조로 설계했다.

**확장성:** 예시는 금감원 전자공시 시스템으로 제한했지만, 딥서치 뉴스, aT 농수산물 가격 정보 등 현재 케이뱅크에서 활용 중인 다른 외부 데이터 소스도 동일한 파이프라인으로 처리할 수 있다.

---

## 주제 2: LangChain 기반 주식 서비스 챗봇

### 문제 정의

기존에 "삼성전자 최신가격 알려줘"라고 물었을 때 LLM이 그냥 답을 만들어내면 잘못된 정보가 나올 수 있다. 금융 정보는 금감원 제재 이슈가 있어서 신뢰성이 핵심이다.

**목표:** AI가 직접 정보를 만들어내는 것이 아니라, 기존 시스템(케이뱅크 MSA API)을 통해 정확한 데이터를 가져오고 AI는 그 결과를 자연어로 표현하는 것.

### LangChain을 선택한 이유

LangChain 기반의 플로우 컨트롤 구조를 채택한 이유:

1. 기존 MSA 주식 시스템의 API 재활용 가능
2. 투자 정보의 민감성과 정보 신뢰성 확보

```python
class GetListedStockSummaryRequest(BaseModel):
    itms_cd_nbr: str

@tool(args_schema=GetListedStockSummaryRequest)
def getListedStockSummary(itms_cd_nbr: str):
    """
    Use this function to get Summary Info of Stock in Korea.
    :param itms_cd_nbr(str) : 6 length number
            example) 005930, 000660
    :return: json info of company info
    """
    return requests.get(
        f"http://localhost:38080/listed-stock-service/v1/listedStock/{itms_cd_nbr}"
    ).json()
```

이런 식으로 케이뱅크 MSA 서비스의 각 API를 Tool로 등록하고, LangGraph로 플로우를 제어한다.

### 결론: LangChain은 '비선형 처리기'

핵심 메시지는 **"AI가 알아서"는 어느 정도까지만 가능하다**는 것이다.

| 케이스 | AI 처리 가능 여부 |
|--------|-----------------|
| 간단한 툴 호출 | 강함 |
| 조건부 논리 (A이면 X, B이면 Y) | 설계 필요 |
| 완전 자유 입력 처리 | LangGraph 등 보완 필요 |

또한 주제 1의 RAG 시스템과 결합하면:
1. 자체 언어모델 추론 결과를 사용할지
2. RAG 벡터 저장소에 질의할지
3. 케이뱅크 MSA 기반 API를 활용할지

이 세 가지를 AI가 판단해서 라우팅하는 구조가 만들어진다.

---

## 수상 결과

금상 + 상금 400만원 + 싱가폴 Fintech Festival 참가 기회를 얻었다. 회사 내 AI 아이디어 포상으로 AWS re:Invent Las Vegas도 이어서 참가하게 되었다.
