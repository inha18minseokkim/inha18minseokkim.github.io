---
title: "[Tech Talk] 케이뱅크 주식 MSA 서비스를 활용한 LangChain + MCP"
date: 2025-05-25
tags: [미지정]
category:
  - 재테크
---

# LangChain?

**LLM(Large Language Model) 애플리케이션을 개발하고 연결하는 데 사용되는 프레임워크**

# MCP?

(모델 컨텍스트 프로토콜) 애플리케이션이 대형 언어 모델(LLM)에 컨텍스트 정보를 제공하는 방식을 표준화하는 개방적이고 보편적인 프로토콜.

# 필요한 이유


## 모델 학습 

순차적으로 o4-mini, o3, GPT-4.1

![](attachment:9c25ca7f-e790-4e5e-8a05-f02c516d457e:image.png)

24년 1월 기준으로 학습된 모델이 배포된 모습
모델들은 다음 데이터들을 처리할 수 없음
  - 삼성전자의 2025년 5월 26일 종가
  - 2025년 5월 26일 현재 대한민국 대선 후보 리스트

## 전문 도메인 지식 부족 + 벡터 모델의 한계

(대충 엄청 큰 트리를 탐색하는 사진)
LLM은 범용적인 언어들을 기반으로 만들어진 모델이지만 우리가 흔히 응용 개발을 하려고 하는 경우 모델의 도메인이 한정적인 경우가 많음 ex) 은행 앱에 LLM을 붙이려 하는 경우
그런 경우 범용적인 모델은 불필요함
예시) 
  - 파리를 잡으려고 미사일을 사용하기
  - 덧셈 뺄셈 문제를 풀 때 인문학적 차원으로 접근해서 생각해보기
  - 난 json 형식으로 정해진 포맷을 받고싶은데 이상한 소리 함

### 파인튜닝을 사용하기에는 제한적인 이유?

(RAG라는 기술도 있긴 한데 일단 오늘은 설명안함)
1. LLM보다는 상대적으로 적은 자원으로 원하는 아웃풋을 낼 수는 있지만 그럼에도 자원을 많이 소모함
2. 위에서 봤던 이슈와 마찬가지로 매일 새로 들어오는 데이터를 튜닝 할 수는 없음

## 출력 결과의 안정성과 통제가능성(중요)

질문) 삼성전자 최신가격 알려줘
답변) 삼성전자 좋으니깐 사세요 or 잘못된 정보 > 바로 금감원 

목적 : 기존 어플리케이션/api에서 정해진 방법대로 처리하도록 하고 AI를 활용해서 해당 어플리케이션/api를 어떻게 호출할 것인지 등을 결정하도록 하자!! (A.K.A. 비선형 처리기)


# 자연어를 벡터화


### 코사인 유사도(cosine similarity)



![](attachment:89417681-569f-4205-8373-44893e8faaa0:image.png)

자매품 유클리드 거리, 맨해튼 거리, 자카드 유사도, 피어슨 상관계수 등..

### 임베딩(embedding)

텍스트를 컴퓨터가 이해하고 효율적으로 처리하기 위해 단어를 벡터화 함
문서를 토큰 단위로 나눠서 임베딩

![](attachment:66986e3b-2761-47fe-9d30-c788f73d5f08:image.png)

쿼리를 임베딩 한 것

![](attachment:1786c567-c316-4da4-80b0-aa0ed56bf22e:image.png)


### 결론



### 샘플 흐름도

여기서는 좀 더 기능을 잘 만들기 위해 Langchain의 Langgraph 를 사용해볼 예정

![](attachment:66f29676-b505-4284-a61c-9c00a3941638:image.png)



# 툴 목록

해당 툴은 단일 책임 원칙하에 성격별로 잘게 쪼개어진 케이뱅크 listed-stock-service 가져온것
함수를 기능단위로 쪼개었기 때문에 조금 더 세밀한 툴 활용 가능하여 예제 선택

```python
from langchain.tools import tool
from pydantic import BaseModel
from typing import Optional
import requests

def to_query_params(request: dict) -> str:
    return "&".join(f"{k}={v}" for k, v in request.items() if v is not None)

@tool
def get_listed_stock_past_financial_statements(itms_cd_nbr: str, target_financial_statement: str):
    """
    과거 재무제표를 조회한다.
    :param
        itms_cd_nbr(str) : 6자리 종목코드번호 ex)005930
        target_financial_statement(str) : SALES, OPERATING_PROFIT, NET_INCOME, ASSET, LIABILITY, EQUITY 중 하나

    """
    return requests.get(
        f"http://localhost:38080/listed-stock-service/listed-stock/v1/{itms_cd_nbr}/financial/statement/past/{target_financial_statement}"
    ).json()

@tool
def get_listed_stock_financial_ratio(itms_cd_nbr: str):
    """
    재무비율을 조회한다.
    :param
        itms_cd_nbr(str) : 6자리 종목코드번호 ex)005930

    """
    return requests.get(
        f"http://localhost:38080/listed-stock-service/listed-stock/v1/{itms_cd_nbr}/financial/ratio"
    ).json()

@tool
def get_listed_stock_financial_statement(itms_cd_nbr: str):
    """
    최신 재무제표를 조회한다.
    :param
        itms_cd_nbr(str) : 6자리 종목코드번호 ex)005930
    """
    return requests.get(
        f"http://localhost:38080/listed-stock-service/listed-stock/v1/financial/statement/latest/{itms_cd_nbr}"
    ).json()

@tool
def get_listed_stock_v2(itms_cd_nbr: str):
    """
    상장주식 상세정보 (v2)를 조회한다.
    :param
        itms_cd_nbr(str) : 6자리 종목코드번호 ex)005930
    """
    return requests.get(
        f"http://localhost:38080/listed-stock-service/listed-stock/v2/{itms_cd_nbr}"
    ).json()

@tool
def get_listed_stock_summary_v2(itms_cd_nbr: str):
    """
    상장주식 요약정보 (v2)를 조회한다.
    :param
        itms_cd_nbr(str) : 6자리 종목코드번호 ex)005930
    """
    return requests.get(
        f"http://localhost:38080/listed-stock-service/listed-stock/v2/{itms_cd_nbr}/summary"
    ).json()

@tool
def get_latest_price(itms_cd_nbr: str):
    """
    최신 가격 정보를 조회한다.
    :param
        itms_cd_nbr(str) : 6자리 종목코드번호 ex)005930
    """
    return requests.get(
        f"http://localhost:38080/listed-stock-service/listed-stock/v2/{itms_cd_nbr}/price/latest"
    ).json()

@tool
def get_latest_prices():
    """
    모든 종목의 최신 가격 정보를 조회한다.

    """
    return requests.get(
        "http://localhost:38080/listed-stock-service/listed-stock/v2/prices/latest"
    ).json()

@tool
def get_price_difference(itms_cd_nbr: str, fromPriceBaseDt: str):
    """
    itms_cd_nbr 종목의 fromPriceBaseDt 와 최신 가격 차이를 조회한다.
    :param
        itms_cd_nbr(str) : 6자리 종목코드번호 ex)005930
        fromPriceBaseDt(str) : 'yyyy-MM-dd' 비교 대상 가격 일자(필수)
    """
    request = {"fromPriceBaseDt" : fromPriceBaseDt}
    query_string = to_query_params(request)
    return requests.get(
        f"http://localhost:38080/listed-stock-service/listed-stock/v2/{itms_cd_nbr}/price/difference?{query_string}"
    ).json()

@tool
def get_prices(itms_cd_nbr: str, priceBaseDt: str, deltaDay: int):
    """
    특정 종목의 가격 정보를 기간별로 조회한다.
    :param
        itms_cd_nbr(str) : 6자리 종목코드번호 ex)005930
        priceBaseDt(str) : 'yyyy-MM-dd' 비교 대상 가격 일자(필수)
        deltaDay(int) :  priceBaseDt 로 부터 얼마나 과거로 갈지
    """
    request = {"priceBaseDt" : priceBaseDt, "deltaDay" : deltaDay}
    query_string = to_query_params(request)
    return requests.get(
        f"http://localhost:38080/listed-stock-service/listed-stock/v2/{itms_cd_nbr}/prices?{query_string}"
    ).json()



@tool
def get_rank(order_code: str, limitLength: int):
    """
    랭킹 데이터를 조회한다.
    :param
        order_code(enum) : "PRICE_CHANGE_DESCENDING", "VOLUME_DESCENDING", "VALUE_DESCENDING" 중 필수로 하나 선택
            enum에 대한 세부 설명:
                PRICE_CHANGE_DESCENDING -> 가격이 많이 하락한 순
                VOLUME_DESCENDING -> 거래량이 많은 순
                VALUE_DESCENDING -> 거래대금이 많은 순
        limitLength(int) : 최대 몇 개 보여줄지
    """
    request = {"limitLength" : limitLength}
    query_string = to_query_params(request)
    return requests.get(
        f"http://localhost:38080/listed-stock-service/listed-stock/v2/rank/{order_code}?{query_string}"
    ).json()

```



### 호출의 State


```python
class StockQueryState(TypedDict):
    query: str
    converted_query: str
    stock_names: List[str]
    tool_name: Optional[str]
    extracted_parameters: Dict
    result: Optional[dict]
```


### 질문에서 entity를 추출하는 기능


```python
def extract_stock_info(state: StockQueryState) -> StockQueryState:
    system_prompt = f"""
다음 사용자의 질문에서 주식 종목명을 추출해서 리스트로 리턴하세요.
- 종목명이 없으면 빈 리스트를 출력하세요
- 종목 이름을 리턴하세요. 6자리 종목 코드는 대상이 아닙니다.

1)
예시 입력: "삼성전자 재무비율 알려줘"
예시 출력: {{"stock_names" : ["삼성전자"]}}
2)
예시 입력: "SK하이닉스 최신가격 알려줘"
예시 출력: {{"stock_names" : ["SK하이닉스"]}}
3)
예시 입력: "오늘 거래량 가장 많은 종목 5가지 알려줘"
예시 출력: {{"stock_names" : []}}
4)
예시 입력: "000020 최신가격 알려줘"
예시 출력: {{"stock_names" : []}}
"""
    print(f"extract_stock_info :  {state}")
    messages = [
        SystemMessage(content=system_prompt.strip()),
        HumanMessage(content=state["query"]),
    ]
    result = llm.invoke(messages)
    data = json.loads(result.content)

    return {
        **state,
        "stock_names": data.get("stock_names"),
    }
```


### 엔티티명을 종목코드로 바꾸는 코드


```python
def symbol_to_code(state: StockQueryState) -> StockQueryState:
    """
    주어진 쿼리의 종목명을 종목코드로 변환한다.
    정확히 일치하는 종목명이 없으면 가장 유사한 종목명을 찾아준다.
    """
    response = requests.get("http://localhost:38080/listed-stock-service/listed-stock/v2/")
    items = response.json()
    name_to_code = {item["stckKorNm"]: item["itmsCdNbr"] for item in items}
    before_converted_query = state['query']
    for stock_name in state['stock_names']:
        # 종목명 -> 종목코드 매핑
        names = list(name_to_code.keys())
        # 1. 완전 일치하는 경우
        if stock_name in name_to_code:
            print(f"찾았다 {stock_name}")
            before_converted_query = before_converted_query.replace(stock_name, name_to_code[stock_name])
            continue
        # 2. 유사도가 가장 높은 종목명 찾기
        close_matches = difflib.get_close_matches(stock_name, names, n=1, cutoff=0.6)

        if close_matches:
            closest_name = close_matches[0]
            print(f"아무튼 찾았다 {closest_name}")
            before_converted_query = before_converted_query.replace(stock_name,name_to_code[closest_name])
            continue
        # 그래도 없으면 변환실패
        raise ValueError(f"'{stock_name}'와 일치하거나 비슷한 종목명을 찾을 수 없습니다.")
    return {
        **state,
        "c
```


### 질문에서 어떤 툴을 사용할지 선택하는 함수


```python
def choose_tool(state: StockQueryState) -> StockQueryState:
    tool_names = list(tools.keys())
    tool_list = "\n".join(f"- {name}" for name in tool_names)
    print(f"choose_tool : {state}")

    system_prompt = f"""
사용자의 질문에 가장 적절한 API 툴을 하나 선택하세요. 아래는 가능한 툴입니다:

{tool_list}

툴 이름만 JSON 형식으로 출력하세요. 예: {{"tool": "get_listed_stock_summary"}}
"""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=state["converted_query"]),
    ]

    result = llm.invoke(messages)
    tool_name = json.loads(result.content)["tool"]

    return {
        **state,
        "tool_name": tool_name,
    }

```


![](attachment:083cfc49-1ab0-4ed2-a94f-103882dcdab3:image.png)


### 질문에서 선택한 툴에서 필요한 파라미터를 추출하는 기능


```python
def extract_function_parameter(state: StockQueryState) -> StockQueryState:
    tool_info = tools[state['tool_name']]
    print(f"extract_function_parameter : {tool_info}")
    system_prompt = f"""
주어진 tool의 정보를 보고 주어진 query에 필요한 파라미터들을 추출해서 json 으로 반환해주세요.
요구하는 파라미터가 없는 경우 빈 json을 반환해주세요.

예시 1)
    tool :
    name='get_latest_price' description='최신 가격 정보를 조회한다.\n:param\n    itms_cd_nbr(str) : 6자리 종목코드번호 ex)005930' args_schema=<class 'langchain_core.utils.pydantic.get_latest_price'> func=<function get_latest_price at 0x11874bc70>
    query :
    005930 최신 가격 알려줘
    출력 :
        {{ "parameters" : {{"itms_cd_nbr" : "005930"}} }}
예시 2)
    tool :
    name='get_rank' description='랭킹 데이터를 조회한다.\n:param\n    order_code(enum) : "PRICE_CHANGE_DESCENDING", "VOLUME_DESCENDING", "VALUE_DESCENDING" 중 필수로 하나 선택\n    limitLength(int) : 최대 몇 개 보여줄지' args_schema=<class 'langchain_core.utils.pydantic.get_rank'> func=<function get_rank at 0x1187df1c0>
    query :
    오늘 가장 많이 오른 종목 5개 알려줘
    출력 :
        {{ "parameters" : {{"order_code" : "PRICE_CHANGE_DESCENDING", "limitLength" : 5}} }}
실제 질문)
    tool :
        {tool_info}
    query :
        {state['converted_query']}

    """
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=state["converted_query"]),
    ]

    result = llm.invoke(messages)
    parameters = json.loads(result.content)["parameters"]

    return {
        **state,
        "extracted_parameters" : parameters
    }
```


![](attachment:6e3a729a-23ae-4897-abd5-0b7f8f3490b3:image.png)


### 선택한 툴을 실행하는 함수


```python
def call_selected_tool(state: StockQueryState) -> StockQueryState:
    print(f"call_selected_tool : {state}")
    tool = tools[state["tool_name"]]
    result = tool.invoke(state["extracted_parameters"])
    print(f"call_selected_tool : {tool} {result} ")
    return {
        **state,
        "result": result,
    }
```


### 분기 조건에 따라 어떤 함수를 실행할지 결정


```python
def decide_after_extract(state: StockQueryState):
    print(f"decide_after_extract : {state}")
    if not state.get("converted_query"):
        print("decide_after_extract: symbol_to_code로 이동")
        return "symbol_to_code"
    elif state.get("stock_name"):
        print("decide_after_extract: choose_tool로 이동")
        return "choose_tool"
    else:
        print("decide_after_extract: 바로 END")
        return END
```


### 만든 함수를 그래프 형태로 선후행 수행 형태 정의


```python
from langgraph.graph import StateGraph, END

# 8. LangGraph 구성
graph = StateGraph(StockQueryState)

# 노드 추가
graph.add_node("extract_stock_info", extract_stock_info)
graph.add_node("symbol_to_code", symbol_to_code)
graph.add_node("choose_tool", choose_tool)
graph.add_node("extract_function_parameter",extract_function_parameter)
graph.add_node("call_tool", call_selected_tool)

# 흐름 정의
graph.set_entry_point("extract_stock_info")

graph.add_conditional_edges("extract_stock_info", decide_after_extract)

graph.add_edge("symbol_to_code", "choose_tool")
graph.add_edge("choose_tool", "extract_function_parameter")
graph.add_edge("extract_function_parameter","call_tool")
graph.add_edge("call_tool", END)

# 컴파일
final_graph = graph.compile()
```



## 실행


```python
response = final_graph.invoke({
    "query": "삼성전자 재무비율 알려줘"
})

print(response["result"])
```

결과

```python
extract_stock_info :  {'query': '삼성전자 재무비율 알려줘'}
decide_after_extract : {'query': '삼성전자 재무비율 알려줘', 'stock_names': ['삼성전자']}
decide_after_extract: symbol_to_code로 이동
찾았다 삼성전자
choose_tool : {'query': '삼성전자 재무비율 알려줘', 'converted_query': '005930 재무비율 알려줘', 'stock_names': ['삼성전자']}
extract_function_parameter : name='get_listed_stock_financial_ratio' description='재무비율을 조회한다.\n:param\n    itms_cd_nbr(str) : 6자리 종목코드번호 ex)005930' args_schema=<class 'langchain_core.utils.pydantic.get_listed_stock_financial_ratio'> func=<function get_listed_stock_financial_ratio at 0x11a79bc70>
call_selected_tool : {'query': '삼성전자 재무비율 알려줘', 'converted_query': '005930 재무비율 알려줘', 'stock_names': ['삼성전자'], 'tool_name': 'get_listed_stock_financial_ratio', 'extracted_parameters': {'itms_cd_nbr': '005930'}}
call_selected_tool : name='get_listed_stock_financial_ratio' description='재무비율을 조회한다.\n:param\n    itms_cd_nbr(str) : 6자리 종목코드번호 ex)005930' args_schema=<class 'langchain_core.utils.pydantic.get_listed_stock_financial_ratio'> func=<function get_listed_stock_financial_ratio at 0x11a79bc70> {'acnBaseDt': [2025, 2, 6], 'itmsCdNbr': '005930', 'bpsVal': 52002.0, 'epsVal': 2131.0, 'perVal': 25.34022, 'pbrVal': 1.038422, 'pstkDivdVal': 1444.0, 'dvdnErnnRate': 2.674074} 
{'acnBaseDt': [2025, 2, 6], 'itmsCdNbr': '005930', 'bpsVal': 52002.0, 'epsVal': 2131.0, 'perVal': 25.34022, 'pbrVal': 1.038422, 'pstkDivdVal': 1444.0, 'dvdnErnnRate': 2.674074}
```



```python
final_graph.invoke({
    "query" : "오늘 가격 가장 많이 하락한 순으로 5종목만 보여줘"
})
```


```python
extract_stock_info :  {'query': '오늘 가격 가장 많이 하락한 순으로 5종목만 보여줘'}
decide_after_extract : {'query': '오늘 가격 가장 많이 하락한 순으로 5종목만 보여줘', 'stock_names': []}
decide_after_extract: symbol_to_code로 이동
choose_tool : {'query': '오늘 가격 가장 많이 하락한 순으로 5종목만 보여줘', 'converted_query': '오늘 가격 가장 많이 하락한 순으로 5종목만 보여줘', 'stock_names': []}
extract_function_parameter : name='get_rank' description='랭킹 데이터를 조회한다.\n:param\n    order_code(enum) : "PRICE_CHANGE_DESCENDING", "VOLUME_DESCENDING", "VALUE_DESCENDING" 중 필수로 하나 선택\n        enum에 대한 세부 설명:\n            PRICE_CHANGE_DESCENDING -> 가격이 많이 하락한 순 \n            VOLUME_DESCENDING -> 거래량이 많은 순\n            VALUE_DESCENDING -> 거래대금이 많은 순\n    limitLength(int) : 최대 몇 개 보여줄지' args_schema=<class 'langchain_core.utils.pydantic.get_rank'> func=<function get_rank at 0x11aabce50>
call_selected_tool : {'query': '오늘 가격 가장 많이 하락한 순으로 5종목만 보여줘', 'converted_query': '오늘 가격 가장 많이 하락한 순으로 5종목만 보여줘', 'stock_names': [], 'tool_name': 'get_rank', 'extracted_parameters': {'order_code': 'PRICE_CHANGE_DESCENDING', 'limitLength': 5}}
call_selected_tool : name='get_rank' description='랭킹 데이터를 조회한다.\n:param\n    order_code(enum) : "PRICE_CHANGE_DESCENDING", "VOLUME_DESCENDING", "VALUE_DESCENDING" 중 필수로 하나 선택\n        enum에 대한 세부 설명:\n            PRICE_CHANGE_DESCENDING -> 가격이 많이 하락한 순 \n            VOLUME_DESCENDING -> 거래량이 많은 순\n            VALUE_DESCENDING -> 거래대금이 많은 순\n    limitLength(int) : 최대 몇 개 보여줄지' args_schema=<class 'langchain_core.utils.pydantic.get_rank'> func=<function get_rank at 0x11aabce50> {'list': [{'instUpdtDttm': [2025, 3, 27, 0, 0], 'itmsCdNbr': '308100', 'stckKorNm': '형지글로벌', 'stprAmt': 3245, 'hiprAmt': 3640, 'loprAmt': 3175, 'clprAmt': 3640, 'vlm': 190632, 'valeAmt': 674157200, 'chngPriceAmt': 840, 'chngRate': 30.0, 'aissStckCnt': 6624733, 'mrktPriceTlam': 24114028120, 'txStopYn': 'N', 'scrtsDsVal': 'ETF'}, {'instUpdtDttm': [2025, 3, 27, 0, 0], 'itmsCdNbr': '244460', 'stckKorNm': '올리패스', 'stprAmt': 3100, 'hiprAmt': 4030, 'loprAmt': 3050, 'clprAmt': 4030, 'vlm': 1118233, 'valeAmt': 4264524000, 'chngPriceAmt': 930, 'chngRate': 30.0, 'aissStckCnt': 4730285, 'mrktPriceTlam': 19063048550, 'txStopYn': 'N', 'scrtsDsVal': 'ETF'}, {'instUpdtDttm': [2025, 3, 27, 0, 0], 'itmsCdNbr': '044180', 'stckKorNm': 'KD', 'stprAmt': 679, 'hiprAmt': 828, 'loprAmt': 651, 'clprAmt': 828, 'vlm': 20645748, 'valeAmt': 16336020000, 'chngPriceAmt': 191, 'chngRate': 29.98, 'aissStckCnt': 26717799, 'mrktPriceTlam': 22122337572, 'txStopYn': 'N', 'scrtsDsVal': 'ETF'}, {'instUpdtDttm': [2025, 3, 27, 0, 0], 'itmsCdNbr': '025620', 'stckKorNm': '제이준코스메틱', 'stprAmt': 3580, 'hiprAmt': 4575, 'loprAmt': 3575, 'clprAmt': 4575, 'vlm': 1175597, 'valeAmt': 5056486000, 'chngPriceAmt': 1055, 'chngRate': 29.97, 'aissStckCnt': 4484846, 'mrktPriceTlam': 20518170450, 'txStopYn': 'N', 'scrtsDsVal': 'ETF'}, {'instUpdtDttm': [2025, 3, 27, 0, 0], 'itmsCdNbr': '011080', 'stckKorNm': '형지I&C', 'stprAmt': 1080, 'hiprAmt': 1250, 'loprAmt': 1063, 'clprAmt': 1250, 'vlm': 13803921, 'valeAmt': 16604960000, 'chngPriceAmt': 288, 'chngRate': 29.94, 'aissStckCnt': 31541686, 'mrktPriceTlam': 39427107500, 'txStopYn': 'N', 'scrtsDsVal': 'ETF'}]}
```



### Langchain Framework 에서 제공하는 MCP 호출

MCP는 usb-c와 같은 것. 연결하면 사용가능한 인터페이스를 LLM이 찾아 input에 맞는 도구를 사용할 수 있게 해줌.

```python
from mcp.server.fastmcp import FastMCP
import uvicorn
import requests


print("listed-stock-mcp initiated")
listed_stock_mcp = FastMCP("listed_stock")
print("listed-stock-mcp initiated finished")
def to_query_params(request: dict) -> str:
    return "&".join(f"{k}={v}" for k, v in request.items() if v is not None)

@listed_stock_mcp.tool()
def get_listed_stock_past_financial_statements(itms_cd_nbr: str, target_financial_statement: str):
    """
    과거 재무제표를 조회한다.
    :param
        itms_cd_nbr(str) : 6자리 종목코드번호 ex)005930
        target_financial_statement(str) : SALES, OPERATING_PROFIT, NET_INCOME, ASSET, LIABILITY, EQUITY 중 하나

    """
    return requests.get(
        f"http://localhost:38080/listed-stock-service/listed-stock/v1/{itms_cd_nbr}/financial/statement/past/{target_financial_statement}"
    ).json()

@listed_stock_mcp.tool()
def get_listed_stock_financial_ratio(itms_cd_nbr: str):
    """
    재무비율을 조회한다.
    :param
        itms_cd_nbr(str) : 6자리 종목코드번호 ex)005930

    """
    return requests.get(
        f"http://localhost:38080/listed-stock-service/listed-stock/v1/financial/ratio/{itms_cd_nbr}"
    ).json()

@listed_stock_mcp.tool()
def get_listed_stock_financial_statement(itms_cd_nbr: str):
    """
    최신 재무제표를 조회한다.
    :param
        itms_cd_nbr(str) : 6자리 종목코드번호 ex)005930
    """
    return requests.get(
        f"http://localhost:38080/listed-stock-service/listed-stock/v1/financial/statement/latest/{itms_cd_nbr}"
    ).json()

@listed_stock_mcp.tool()
def get_listed_stock_v2(itms_cd_nbr: str):
    """
    상장주식 상세정보 (v2)를 조회한다.
    :param
        itms_cd_nbr(str) : 6자리 종목코드번호 ex)005930
    """
    return requests.get(
        f"http://localhost:38080/listed-stock-service/listed-stock/v2/{itms_cd_nbr}"
    ).json()

@listed_stock_mcp.tool()
def get_listed_stock_summary_v2(itms_cd_nbr: str):
    """
    상장주식 요약정보 (v2)를 조회한다.
    :param
        itms_cd_nbr(str) : 6자리 종목코드번호 ex)005930
    """
    return requests.get(
        f"http://localhost:38080/listed-stock-service/listed-stock/v2/{itms_cd_nbr}/summary"
    ).json()

@listed_stock_mcp.tool()
def get_latest_price(itms_cd_nbr: str):
    """
    최신 가격 정보를 조회한다.
    :param
        itms_cd_nbr(str) : 6자리 종목코드번호 ex)005930
    """
    return requests.get(
        f"http://localhost:38080/listed-stock-service/listed-stock/v2/{itms_cd_nbr}/price/latest"
    ).json()

@listed_stock_mcp.tool()
def get_latest_prices():
    """
    모든 종목의 최신 가격 정보를 조회한다.

    """
    return requests.get(
        "http://localhost:38080/listed-stock-service/listed-stock/v2/prices/latest"
    ).json()

@listed_stock_mcp.tool()
def get_price_difference(itms_cd_nbr: str, fromPriceBaseDt: str):
    """
    fromPriceBaseDt 와 최신 가격 차이를 조회한다.
    :param
        itms_cd_nbr(str) : 6자리 종목코드번호 ex)005930
        fromPriceBaseDt(str) : 'yyyy-MM-dd' 비교 대상 가격 일자(필수)
    """
    request = {"fromPriceBaseDt" : fromPriceBaseDt}
    query_string = to_query_params(request)
    return requests.get(
        f"http://localhost:38080/listed-stock-service/listed-stock/v2/{itms_cd_nbr}/price/difference?{query_string}"
    ).json()

@listed_stock_mcp.tool()
def get_prices(itms_cd_nbr: str, priceBaseDt: str, deltaDay: int):
    """
    특정 종목의 가격 정보를 기간별로 조회한다.
    :param
        itms_cd_nbr(str) : 6자리 종목코드번호 ex)005930
        priceBaseDt(str) : 'yyyy-MM-dd' 비교 대상 가격 일자(필수)
        deltaDay(int) :  priceBaseDt 로 부터 얼마나 과거로 갈지
    """
    request = {"priceBaseDt" : priceBaseDt, "deltaDay" : deltaDay}
    query_string = to_query_params(request)
    return requests.get(
        f"http://localhost:38080/listed-stock-service/listed-stock/v2/{itms_cd_nbr}/prices?{query_string}"
    ).json()


from mcp.server.fastmcp import FastMCP

from pydantic import BaseModel
from typing import Optional
# from example.McpMain import listed_stock_mcp
import requests

listed_stock_mcp = FastMCP("listed_stock")

def to_query_params(request: dict) -> str:
    return "&".join(f"{k}={v}" for k, v in request.items() if v is not None)

@listed_stock_mcp.tool()
def get_listed_stock_past_financial_statements(itms_cd_nbr: str, target_financial_statement: str):
    """
    과거 재무제표를 조회한다.
    :param
        itms_cd_nbr(str) : 6자리 종목코드번호 ex)005930
        target_financial_statement(str) : SALES, OPERATING_PROFIT, NET_INCOME, ASSET, LIABILITY, EQUITY 중 하나

    """
    return requests.get(
        f"http://localhost:38080/listed-stock-service/listed-stock/v1/{itms_cd_nbr}/financial/statement/past/{target_financial_statement}"
    ).json()

@listed_stock_mcp.tool()
def get_listed_stock_financial_ratio(itms_cd_nbr: str):
    """
    재무비율을 조회한다.
    :param
        itms_cd_nbr(str) : 6자리 종목코드번호 ex)005930

    """
    return requests.get(
        f"http://localhost:38080/listed-stock-service/listed-stock/v1/{itms_cd_nbr}/financial/ratio"
    ).json()

@listed_stock_mcp.tool()
def get_listed_stock_financial_statement(itms_cd_nbr: str):
    """
    최신 재무제표를 조회한다.
    :param
        itms_cd_nbr(str) : 6자리 종목코드번호 ex)005930
    """
    return requests.get(
        f"http://localhost:38080/listed-stock-service/listed-stock/v1/{itms_cd_nbr}/financial/statement/latest"
    ).json()

@listed_stock_mcp.tool()
def get_listed_stock_v2(itms_cd_nbr: str):
    """
    상장주식 상세정보 (v2)를 조회한다.
    :param
        itms_cd_nbr(str) : 6자리 종목코드번호 ex)005930
    """
    return requests.get(
        f"http://localhost:38080/listed-stock-service/listed-stock/v2/{itms_cd_nbr}"
    ).json()

@listed_stock_mcp.tool()
def get_listed_stock_summary_v2(itms_cd_nbr: str):
    """
    상장주식 요약정보 (v2)를 조회한다.
    :param
        itms_cd_nbr(str) : 6자리 종목코드번호 ex)005930
    """
    return requests.get(
        f"http://localhost:38080/listed-stock-service/listed-stock/v2/{itms_cd_nbr}/summary"
    ).json()

@listed_stock_mcp.tool()
def get_latest_price(itms_cd_nbr: str):
    """
    최신 가격 정보를 조회한다.
    :param
        itms_cd_nbr(str) : 6자리 종목코드번호 ex)005930
    """
    return requests.get(
        f"http://localhost:38080/listed-stock-service/listed-stock/v2/{itms_cd_nbr}/price/latest"
    ).json()

@listed_stock_mcp.tool()
def get_latest_prices():
    """
    모든 종목의 최신 가격 정보를 조회한다.

    """
    return requests.get(
        "http://localhost:38080/listed-stock-service/listed-stock/v2/prices/latest"
    ).json()

@listed_stock_mcp.tool()
def get_price_difference(itms_cd_nbr: str, fromPriceBaseDt: str):
    """
    fromPriceBaseDt 와 최신 가격 차이를 조회한다.
    :param
        itms_cd_nbr(str) : 6자리 종목코드번호 ex)005930
        fromPriceBaseDt(str) : 'yyyy-MM-dd' 비교 대상 가격 일자(필수)
    """
    request = {"fromPriceBaseDt" : fromPriceBaseDt}
    query_string = to_query_params(request)
    return requests.get(
        f"http://localhost:38080/listed-stock-service/listed-stock/v2/{itms_cd_nbr}/price/difference?{query_string}"
    ).json()

@listed_stock_mcp.tool()
def get_prices(itms_cd_nbr: str, priceBaseDt: str, deltaDay: int):
    """
    특정 종목의 가격 정보를 기간별로 조회한다.
    :param
        itms_cd_nbr(str) : 6자리 종목코드번호 ex)005930
        priceBaseDt(str) : 'yyyy-MM-dd' 비교 대상 가격 일자(필수)
        deltaDay(int) :  priceBaseDt 로 부터 얼마나 과거로 갈지
    """
    request = {"priceBaseDt" : priceBaseDt, "deltaDay" : deltaDay}
    query_string = to_query_params(request)
    return requests.get(
        f"http://localhost:38080/listed-stock-service/listed-stock/v2/{itms_cd_nbr}/prices?{query_string}"
    ).json()



@listed_stock_mcp.tool()
def get_rank(order_code: str, limitLength: int):
    """
    랭킹 데이터를 조회한다.
    :param
        order_code(str) : PRICE_CHANGE_DESCENDING, VOLUME_DESCENDING, VALUE_DESCENDING 중 필수로 하나 선택
        limitLength(int) : 최대 몇 개 보여줄지
    """
    request = {"limitLength" : limitLength}
    query_string = to_query_params(request)
    return requests.get(
        f"http://localhost:38080/listed-stock-service/listed-stock/v2/rank/{order_code}?{query_string}"
    ).json()
#
@listed_stock_mcp.tool()
def get_rank(order_code: str, limitLength: int):
    """
    랭킹 데이터를 조회한다.
    :param
        order_code(str) : PRICE_CHANGE_DESCENDING, VOLUME_DESCENDING, VALUE_DESCENDING 중 필수로 하나 선택
        limitLength(int) : 최대 몇 개 보여줄지
    """
    request = {"limitLength" : limitLength}
    query_string = to_query_params(request)
    return requests.get(
        f"http://localhost:38080/listed-stock-service/listed-stock/v2/rank/{order_code}?{query_string}"
    ).json()


#
# if __name__ == "__main__":
#     listed_stock_mcp.run(transport="stdio")

if __name__ == "__main__":
    print("listed-stock-mcp server started")
    listed_stock_mcp.run(transport="streamable-http")

```

streamable-http 형식으로 MCP 서버 기동 가능(ASGI Uvicorn, FastApi 사용)
우선 예제에서는 stdio 사용

```python
model = ChatOpenAI(temperature=0.0,model="gpt-3.5-turbo",api_key=api_key)

server_params = StdioServerParameters(
    command="python",
    args=["./example/McpMain.py"],  # 경로 수정 필수
)
print("A")
async with stdio_client(server_params) as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()
        print("session initialized")
        tools = await load_mcp_tools(session)
        print("mcp tool loaded")
        agent = create_react_agent(model, tools)
        print("agent created")
        result = await agent.ainvoke({"messages": "삼성전자 재무비율 알려줘"})
```



![](attachment:151f359e-bc14-4cf5-a0ed-95a2ac82326e:image.png)


![](attachment:4d683691-0af0-456b-b892-1f9e181087a6:image.png)



### 문제점

아직까지는 AI 가 다 해주지 못한다. 
ex) 삼성전자와 LG전자중에 오늘 더 많이 오른 종목은 뭐야?


## ✅ 결론

> MCP + LangChain 구조는 단일 툴 호출에는 강하지만, 다중 툴 조합 reasoning에는 구조 설계가 필요합니다.
따라서 지금처럼 “두 종목 비교” 유형은 **단계적 흐름을 명시적으로 설계하거나**,
**LangGraph, stateful planning** 등으로 보완해줘야 가능합니다.


## ✅ 정리: “AI가 알아서”는 어느 정도까지만 가능


| 수준 | 설명 |
| --- | --- |
| 🔹 간단한 툴 호출 | 툴 이름 명확 + 자연어 설명도 잘 되면 잘 작동 |
| 🔸 조건부 논리 흐름 | LangGraph 등 구조를 짜줘야 안정적으로 작동 |
| 🔺 완전 자유 입력 처리 | 아직은 분류기 + 흐름 설계 필요 |

