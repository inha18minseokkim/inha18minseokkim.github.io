---
title: "Langchain Tool > MCP 프로토콜 활용(Langchain MCP Adapters)"
date: 2025-05-16
tags:
  - AI/ML
  - 기술
category:
  - 기술
---
Langchain과 Langraph로 간단한 함수 매핑을 만들면서 도구를 연결하기 상당히 귀찮았음.
Langchain MCP Adapters를 활용해서 매핑해봄

```python
from mcp.server.fastmcp import FastMCP

from pydantic import BaseModel
from typing import Optional
# from example.McpMain import listed_stock_mcp
import requests

listed_stock_mcp = FastMCP("listed_stock")

def to_query_params(request: dict) -> str:
    return "&".join(f"{k}={v}" for k, v in request.items if v is not None)

@listed_stock_mcp.tool
def get_listed_stock_past_financial_statements(itms_cd_nbr: str, target_financial_statement: str):
    """
    과거 재무제표를 조회한다.
    :param
        itms_cd_nbr(str) : 6자리 종목코드번호 ex)005930
        target_financial_statement(str) : SALES, OPERATING_PROFIT, NET_INCOME, ASSET, LIABILITY, EQUITY 중 하나

    """
    return requests.get(
        f"http://localhost:38080/listed-stock-service/listed-stock/v1/{itms_cd_nbr}/financial/statement/past/{target_financial_statement}"
    ).json

@listed_stock_mcp.tool
def get_listed_stock_financial_ratio(itms_cd_nbr: str):
    """
    재무비율을 조회한다.
    :param
        itms_cd_nbr(str) : 6자리 종목코드번호 ex)005930

    """
    return requests.get(
        f"http://localhost:38080/listed-stock-service/listed-stock/v1/financial/ratio/{itms_cd_nbr}"
    ).json

@listed_stock_mcp.tool
def get_listed_stock_financial_statement(itms_cd_nbr: str):
    """
    최신 재무제표를 조회한다.
    :param
        itms_cd_nbr(str) : 6자리 종목코드번호 ex)005930
    """
    return requests.get(
        f"http://localhost:38080/listed-stock-service/listed-stock/v1/financial/statement/latest/{itms_cd_nbr}"
    ).json

@listed_stock_mcp.tool
def get_listed_stock_v2(itms_cd_nbr: str):
    """
    상장주식 상세정보 (v2)를 조회한다.
    :param
        itms_cd_nbr(str) : 6자리 종목코드번호 ex)005930
    """
    return requests.get(
        f"http://localhost:38080/listed-stock-service/listed-stock/v2/{itms_cd_nbr}"
    ).json

@listed_stock_mcp.tool
def get_listed_stock_summary_v2(itms_cd_nbr: str):
    """
    상장주식 요약정보 (v2)를 조회한다.
    :param
        itms_cd_nbr(str) : 6자리 종목코드번호 ex)005930
    """
    return requests.get(
        f"http://localhost:38080/listed-stock-service/listed-stock/v2/{itms_cd_nbr}/summary"
    ).json

@listed_stock_mcp.tool
def get_latest_price(itms_cd_nbr: str):
    """
    최신 가격 정보를 조회한다.
    :param
        itms_cd_nbr(str) : 6자리 종목코드번호 ex)005930
    """
    return requests.get(
        f"http://localhost:38080/listed-stock-service/listed-stock/v2/{itms_cd_nbr}/price/latest"
    ).json

@listed_stock_mcp.tool
def get_latest_prices:
    """
    모든 종목의 최신 가격 정보를 조회한다.

    """
    return requests.get(
        "http://localhost:38080/listed-stock-service/listed-stock/v2/prices/latest"
    ).json

@listed_stock_mcp.tool
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
    ).json

@listed_stock_mcp.tool
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
    ).json


from mcp.server.fastmcp import FastMCP

from pydantic import BaseModel
from typing import Optional
# from example.McpMain import listed_stock_mcp
import requests

listed_stock_mcp = FastMCP("listed_stock")

def to_query_params(request: dict) -> str:
    return "&".join(f"{k}={v}" for k, v in request.items if v is not None)

@listed_stock_mcp.tool
def get_listed_stock_past_financial_statements(itms_cd_nbr: str, target_financial_statement: str):
    """
    과거 재무제표를 조회한다.
    :param
        itms_cd_nbr(str) : 6자리 종목코드번호 ex)005930
        target_financial_statement(str) : SALES, OPERATING_PROFIT, NET_INCOME, ASSET, LIABILITY, EQUITY 중 하나

    """
    return requests.get(
        f"http://localhost:38080/listed-stock-service/listed-stock/v1/{itms_cd_nbr}/financial/statement/past/{target_financial_statement}"
    ).json

@listed_stock_mcp.tool
def get_listed_stock_financial_ratio(itms_cd_nbr: str):
    """
    재무비율을 조회한다.
    :param
        itms_cd_nbr(str) : 6자리 종목코드번호 ex)005930

    """
    return requests.get(
        f"http://localhost:38080/listed-stock-service/listed-stock/v1/{itms_cd_nbr}/financial/ratio"
    ).json

@listed_stock_mcp.tool
def get_listed_stock_financial_statement(itms_cd_nbr: str):
    """
    최신 재무제표를 조회한다.
    :param
        itms_cd_nbr(str) : 6자리 종목코드번호 ex)005930
    """
    return requests.get(
        f"http://localhost:38080/listed-stock-service/listed-stock/v1/{itms_cd_nbr}/financial/statement/latest"
    ).json

@listed_stock_mcp.tool
def get_listed_stock_v2(itms_cd_nbr: str):
    """
    상장주식 상세정보 (v2)를 조회한다.
    :param
        itms_cd_nbr(str) : 6자리 종목코드번호 ex)005930
    """
    return requests.get(
        f"http://localhost:38080/listed-stock-service/listed-stock/v2/{itms_cd_nbr}"
    ).json

@listed_stock_mcp.tool
def get_listed_stock_summary_v2(itms_cd_nbr: str):
    """
    상장주식 요약정보 (v2)를 조회한다.
    :param
        itms_cd_nbr(str) : 6자리 종목코드번호 ex)005930
    """
    return requests.get(
        f"http://localhost:38080/listed-stock-service/listed-stock/v2/{itms_cd_nbr}/summary"
    ).json

@listed_stock_mcp.tool
def get_latest_price(itms_cd_nbr: str):
    """
    최신 가격 정보를 조회한다.
    :param
        itms_cd_nbr(str) : 6자리 종목코드번호 ex)005930
    """
    return requests.get(
        f"http://localhost:38080/listed-stock-service/listed-stock/v2/{itms_cd_nbr}/price/latest"
    ).json

@listed_stock_mcp.tool
def get_latest_prices:
    """
    모든 종목의 최신 가격 정보를 조회한다.

    """
    return requests.get(
        "http://localhost:38080/listed-stock-service/listed-stock/v2/prices/latest"
    ).json

@listed_stock_mcp.tool
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
    ).json

@listed_stock_mcp.tool
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
    ).json



@listed_stock_mcp.tool
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
    ).json


if __name__ == "__main__":
    listed_stock_mcp.run(transport="stdio")
@listed_stock_mcp.tool
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
    ).json


if __name__ == "__main__":
    listed_stock_mcp.run(transport="stdio")
```

간단한 예제부 이렇게 만들어주고

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI

api_key = "<OPENAI_API_KEY>"
model = ChatOpenAI(temperature=0.0,model="gpt-3.5-turbo",api_key=api_key)

server_params = StdioServerParameters(
    command="python",
    args=["./example/McpMain.py"],  # 경로 수정 필수
)
print("A")
async with stdio_client(server_params) as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize
        print("session initialized")
        tools = await load_mcp_tools(session)
        print("mcp tool loaded")
        agent = create_react_agent(model, tools)
        print("agent created")
        result = await agent.ainvoke({"messages": "삼성전자 최신가격 알려줘"})
```



```python
{'messages': [HumanMessage(content='삼성전자 최신가격 알려줘', additional_kwargs={}, response_metadata={}, id='17d27c48-a240-45bc-a735-4f84f4eb975d'), AIMessage(content='', additional_kwargs={'tool_calls': [{'id': 'call_3WCAKkOoMuLqcRmPaQXuiy1q', 'function': {'arguments': '{"itms_cd_nbr":"005930"}', 'name': 'get_latest_price'}, 'type': 'function'}], 'refusal': None}, response_metadata={'token_usage': {'completion_tokens': 20, 'prompt_tokens': 780, 'total_tokens': 800, 'completion_tokens_details': {'accepted_prediction_tokens': 0, 'audio_tokens': 0, 'reasoning_tokens': 0, 'rejected_prediction_tokens': 0}, 'prompt_tokens_details': {'audio_tokens': 0, 'cached_tokens': 0}}, 'model_name': 'gpt-3.5-turbo-0125', 'system_fingerprint': None, 'id': 'chatcmpl-BXqE8YG96RDuM8MRld4rT0vMH4rp2', 'finish_reason': 'tool_calls', 'logprobs': None}, id='run-378e2875-31d9-467a-9e3c-89689c7015c5-0', tool_calls=[{'name': 'get_latest_price', 'args': {'itms_cd_nbr': '005930'}, 'id': 'call_3WCAKkOoMuLqcRmPaQXuiy1q', 'type': 'tool_call'}], usage_metadata={'input_tokens': 780, 'output_tokens': 20, 'total_tokens': 800, 'input_token_details': {'audio': 0, 'cache_read': 0}, 'output_token_details': {'audio': 0, 'reasoning': 0}}), ToolMessage(content='{\n  "instUpdtDttm": [\n    2025,\n    3,\n    27,\n    0,\n    0\n  ],\n  "itmsCdNbr": "005930",\n  "stckKorNm": "삼성전자",\n  "stprAmt": 60900,\n  "hiprAmt": 62000,\n  "loprAmt": 60800,\n  "clprAmt": 61800,\n  "vlm": 20389790,\n  "valeAmt": 1256946000000,\n  "chngPriceAmt": 400,\n  "chngRate": 0.65,\n  "aissStckCnt": 5919637922,\n  "mrktPriceTlam": 365833623579600,\n  "txStopYn": "N",\n  "scrtsDsVal": "ETF"\n}', name='get_latest_price', id='674fce6b-c1f8-468e-a1c8-f5511e5c7e43', tool_call_id='call_3WCAKkOoMuLqcRmPaQXuiy1q'), AIMessage(content='삼성전자의 최신 가격은 61,800원입니다. 전일 대비 400원 상승하여 0.65% 상승했습니다. 거래량은 20,389,790주이며 거래대금은 1,256,946,000,000원입니다.', additional_kwargs={'refusal': None}, response_metadata={'token_usage': {'completion_tokens': 80, 'prompt_tokens': 1002, 'total_tokens': 1082, 'completion_tokens_details': {'accepted_prediction_tokens': 0, 'audio_tokens': 0, 'reasoning_tokens': 0, 'rejected_prediction_tokens': 0}, 'prompt_tokens_details': {'audio_tokens': 0, 'cached_tokens': 0}}, 'model_name': 'gpt-3.5-turbo-0125', 'system_fingerprint': None, 'id': 'chatcmpl-BXqE9Tszq6Vz8vxQgF1GDX4twEE9z', 'finish_reason': 'stop', 'logprobs': None}, id='run-3a74acf1-8b88-4c3f-9995-e3d1eb127bf2-0', usage_metadata={'input_tokens': 1002, 'output_tokens': 80, 'total_tokens': 1082, 'input_token_details': {'audio': 0, 'cache_read': 0}, 'output_token_details': {'audio': 0, 'reasoning': 0}})]}
```


### 🧠 Assistant Tool 호출


```json
{
  "tool_call": {
    "name": "get_latest_price",
    "args": {
      "itms_cd_nbr": "005930"
    }
  }
}
```


---


### 🔧 Tool 응답 (get_latest_price)


---


### 🤖 최종 Assistant 응답

**삼성전자의 최신 가격은 61,800원입니다.**
전일 대비 **400원 상승하여 0.65% 상승**했습니다.
거래량은 **20,389,790주**, 거래대금은 **1,256,946,000,000원**입니다.

여기서 궁금했던점은 삼성전자 > 005930을 어떻게 매핑했는지..이다 GPT 3.5버전이 나왔을 시점에는 LG CNS가 비상장이었으니 LG CNS에 대한 질문을 해보면

![](attachment:99ba12ff-4a18-4c9e-978c-6ea3d2c76361:image.png)

LG CNS가 갑자기 셀트리온으로 바뀌어버림
또한 멀티 스텝 호출이 안되는것같은데

![](attachment:4f55be65-2dd8-4c97-b059-ecbddf0e6785:image.png)

결국 하나의 기능을 호출하는데 MCP는 최적인것같고, 특정 업무에 특화된 호출 파이프라인 설계는 불가피해 보임.
