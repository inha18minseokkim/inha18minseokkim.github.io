---
title: 주식서비스 LANGRAPH
date: 2025-04-29
tags:
  - AI/ML
  - 주식서비스
  - 기술
category:
  - 기술
  - AI/ML
---
AI/ML을 활용한 금융 데이터 처리 및 RAG 구현 정리.
랭체인 연습용으로 한번 만들어 봄

```python
from langgraph.graph import END, MessageGraph
api_key = "sk-~"
from langchain_core.messages import HumanMessage
from langchain.chat_models import ChatOpenAI
llm = ChatOpenAI(temperature=0.0,model="gpt-3.5-turbo",api_key=api_key)

```

Function Calling의 경우 OpenAI 포맷이 표준이라 deepseek, ollama는 흉내는 낼 수 있는데 완벽한 지원은 안되는 듯 함.

![이미지](/assets/images/Pasted%20image%2020260301223457.png)

이런식으로 간단하게 만들어볼 예정

간단한 prompt 작성

```python
from langchain.prompts import PromptTemplate
prompt_template_detect_symbol = """
당신은 주식서비스 챗봇입니다. 대부분 itms_cd_nbr이 필요로 할텐데, 사용자가 itms_cd_nbr(숫자 6자리)를 주는 경우는 바로 해당 itms_cd_nbr를 사용해서 함수를 호출하면 되겠지만 그렇지 않는 경우 사용자가 말한 주식한글명을 tool을 사용해서 6자리 itms_cd_nbr로 변환해서 다시 툴을 호출해야 합니다.
"""
prompt_detect_symbol = PromptTemplate.from_template(prompt_template_detect_symbol)
```

종목코드6자리가 존재하고 존재하지 않는다면 종목코드를 찾아서 반환하는 함수
  - 없다면 유사도점수가 0.6이상인 종목 중에 제일 유사한 놈을 반환

```python
import requests
import difflib
from langchain.tools import tool

@tool
def symbol_to_code(stock_name: str) -> str:
    """
    주어진 종목명을 종목코드로 변환한다.
    정확히 일치하는 종목명이 없으면 가장 유사한 종목명을 찾아준다.

    :param stock_name: 예) '삼성전자'
    :return: 종목코드 예) '005930'
    """
    response = requests.get("http://localhost:38080/listed-stock-service/listed-stock/v2/")
    items = response.json

    # 종목명 -> 종목코드 매핑
    name_to_code = {item["stckKorNm"]: item["itmsCdNbr"] for item in items}
    names = list(name_to_code.keys)

    # 1. 완전 일치하는 경우
    if stock_name in name_to_code:
        return name_to_code[stock_name]

    # 2. 유사도가 가장 높은 종목명 찾기
    close_matches = difflib.get_close_matches(stock_name, names, n=1, cutoff=0.6)

    if close_matches:
        closest_name = close_matches[0]
        return name_to_code[closest_name]

    raise ValueError(f"'{stock_name}'와 일치하거나 비슷한 종목명을 찾을 수 없습니다.")
```


![이미지](/assets/images/Pasted%20image%2020260301223504.png)

코어시스템 api 를 호출하는 함수를 만들어줌. 함수에 대한 description 작성해서 랭체인 llm 클라이언트가 판단하도록 한다.

```python
from langchain.tools import tool
from pydantic import BaseModel
from typing import Optional
import requests

def to_query_params(request: dict) -> str:
    return "&".join(f"{k}={v}" for k, v in request.items if v is not None)

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
    ).json

```

만들어놓은 함수를 아래와같이 래핑해줌.

```python

tools = {
    "get_listed_stock_past_financial_statements" : get_listed_stock_past_financial_statements,
    "get_listed_stock_financial_ratio" : get_listed_stock_financial_ratio,
    "get_listed_stock_financial_statement" : get_listed_stock_financial_statement,
    "get_listed_stock_v2" : get_listed_stock_v2,
    "get_listed_stock_summary_v2" : get_listed_stock_summary_v2,
    "get_latest_price" : get_latest_price,
    "get_latest_prices" : get_latest_prices,
    "get_price_difference" : get_price_difference,
    "get_prices" : get_prices,
    "get_rank" : get_rank
}
```

어떤 툴을 고를지 선택하는 함수

```python
from typing import TypedDict
from langchain.schema import SystemMessage, HumanMessage
import json

class StockQueryState(TypedDict):
    query: str
    stock_code: Optional[str]
    stock_name: Optional[str]
    tool_name: Optional[str]
    result: Optional[dict]

def choose_tool(state: StockQueryState) -> StockQueryState:
    tool_names = list(tools.keys)
    tool_list = "\n".join(f"- {name}" for name in tool_names)
    print(f"choose_tool : {state}")

    system_prompt = f"""
사용자의 질문에 가장 적절한 API 툴을 하나 선택하세요. 아래는 가능한 툴입니다:

{tool_list}

툴 이름만 JSON 형식으로 출력하세요. 예: {{"tool": "get_listed_stock_summary"}}
"""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=state["query"]),
    ]

    result = llm.invoke(messages)
    tool_name = json.loads(result.content)["tool"]

    return {
        **state,
        "tool_name": tool_name,
    }

```

선택된 함수(json 타입으로 함수명과 파라미터를 받음)을 invoke 하는 함수

```python
def call_selected_tool(state: StockQueryState) -> StockQueryState:
    print(f"call_selected_tool : {state}")
    tool = tools[state["tool_name"]]
    result = tool.invoke(state["stock_code"])
    print(f"call_selected_tool : {tool} {result} ")
    return {
        **state,
        "result": result,
    }
```

결과값 가져와서 json 형식으로 체크&뽑아냄

```python
def extract_stock_info(state: StockQueryState) -> StockQueryState:
    system_prompt = """
다음 사용자의 질문에서 종목코드(code) 또는 종목명(name)을 하나만 추출해서 JSON 형식으로 출력하세요.

- 종목코드는 6자리 숫자입니다.
- 종목명이 있으면 정확한 이름을 추출하세요.
- 종목코드가 있으면 code에, 종목명이 있으면 name에 넣으세요.
- 둘 다 없으면 null로 설정하세요.

예시 입력: "삼성전자 재무비율 알려줘"
예시 출력: {"name": "삼성전자", "code": null}
"""
    print(f"extract_stock_info :  {state}")
    messages = [
        SystemMessage(content=system_prompt.strip),
        HumanMessage(content=state["query"]),
    ]
    result = llm.invoke(messages)
    data = json.loads(result.content)

    return {
        **state,
        "stock_code": data.get("code"),
        "stock_name": data.get("name"),
    }

```

그래프 형식으로 조합

```python
# 분기 조건
def decide_after_extract(state: StockQueryState):
    print(f"decide_after_extract : {state}")
    if state.get("stock_code"):
        return "choose_tool"
    elif state.get("stock_name"):
        return "symbol_to_code"
    else:
        return END

graph.add_conditional_edges("extract_stock_info", decide_after_extract)

graph.add_edge("symbol_to_code", "choose_tool")
graph.add_edge("choose_tool", "call_tool")
graph.add_edge("call_tool", END)

# 컴파일
final_graph = graph.compile
```



![이미지](/assets/images/Pasted%20image%2020260301223512.png)


![이미지](/assets/images/Pasted%20image%2020260301223516.png)


![이미지](/assets/images/Pasted%20image%2020260301223523.png)

종목코드가 필요하지 않은 함수에서 종목코드를 변환하려고 했는데 대상 종목이 없으니깐 아무것도 안하고 그래프가 끝나버림
즉 함수를 호출 할 때 종목코드가 필요한 함수면 종목코드를 찾으려는 시도를 하고, 종목코드가 없으면 쿼리에서 종목코드를 추출하려는 시도를 해야 함. 종목 코드가 필요없는 함수면 바로 choose_tool을 실행해야 함.
그래서 조금 업무를 수정해서 다음과 같이 구현완료함.(중간에 주식 종목 이름으로 보이는것들은 모두 인식해서 종목코드로 변환하는 로직을 넣음)

![이미지](/assets/images/Pasted%20image%2020260301223527.png)


### 문제점

AI라고 해서 모든 것을 다 해주지는 않는다. 오히려 이건 비선형처리기구라고 생각하는게 편할듯.
스프링 MVC 패턴처럼 뭔가 정형화된 패턴이 있을 것이라 기대를 했는데 그런 요건은 아닌 것  같다. 
프롬프트를 짜고 함수를 콜해서 데이터를 가져오는 작업은 뭔가 백엔드 코어 시스템을 만드는것이 아니라 프론트 화면을 만드는 느낌과 같음. 
위 다이어그램처럼 질문을 던지면 DB에서 알아볼 수 있도록 변환하던가 , 변환한다면 대상 값들은 무엇인지, 각각 어떤 함수를 사용해야 하고 어떤 api를 호출해서 llm에 던져서 결과를 받을것인지 등 특정 요건에 맞춰서 커스텀하게 들어가는 영역들이 상당히 많은 것 같음.
  - 위 예시의 경우 정보 메세지를 자연어로 쿼리하는게 목적이면 function call로 호출하는것보다 RAG 파이프라인을 만드는 것이 덜 품 들 것 같다
    - 물론 RAG로 했을 때 할루시네이션 문제가 있긴 하다.

### 좋은점

구현을 하면 어떻게든 다 구현된다.
RAG 할루시네이션이나 오작동이 걱정된다면 어떻게든 다 Function call로 구현을 하면 될 것 같다. 
