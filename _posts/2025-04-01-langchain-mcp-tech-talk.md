---
title: "[Tech Talk] 케이뱅크 주식 MSA 서비스를 활용한 LangChain + MCP"
date: 2025-04-01
tags: [LangChain, MCP, LLM, Python, AI, 케이뱅크, 발표]
---

사내 Tech Talk에서 발표한 내용 정리. 케이뱅크 주식 MSA 서비스를 AI와 연동하는 방법에 대해 다루었다.

## LangChain이란?

LLM 애플리케이션을 개발하고 연결하는 데 사용되는 프레임워크.

## MCP란?

MCP(Model Context Protocol)는 LLM에 컨텍스트 정보를 제공하는 표준화된 프로토콜이다. USB-C처럼 연결하면 LLM이 도구를 찾아 자동으로 사용할 수 있다.

## 왜 이게 필요한가?

### 문제 1: 모델의 학습 데이터 한계

순차적으로 학습된 LLM(o4-mini, o3, GPT-4.1 등)은 다음 데이터를 처리할 수 없다:

- 오늘의 주가
- 내부 데이터베이스의 실시간 정보
- 도메인 특화 데이터

### 문제 2: 전문 도메인 지식 부족 + 벡터 모델의 한계

LLM은 범용적이지만, 도메인 특화 응용에는 한계가 있다. 파인튜닝은:

1. 자원을 많이 소모함
2. 매일 새 데이터를 튜닝할 수 없음

### 문제 3: 출력 결과의 안정성과 통제 가능성 (핵심)

"삼성전자 최신가격 알려줘"라고 물으면 LLM이 그냥 만들어내면? → 잘못된 정보 → 금감원 제재.

**목적:** 기존 애플리케이션/API에서 정해진 방법대로 처리하고, AI는 호출 결정만.

---

## 자연어를 벡터화하는 원리

### 임베딩(Embedding)

텍스트를 벡터화해 컴퓨터가 효율적으로 처리하는 방식. 문서를 토큰 단위로 나눠서 임베딩한다.

### 코사인 유사도(Cosine Similarity)

두 벡터 간의 유사도를 측정. 자매품으로 유클리드 거리, 맨해튼 거리, 자카드 유사도, 피어슨 상관계수 등이 있다.

---

## 케이뱅크 listed-stock-service를 Tool로 등록

케이뱅크 주식 서비스의 API를 LangChain Tool로 등록하면, LLM이 필요할 때 자동으로 호출할 수 있다.

함수를 기능 단위로 쪼개서 세밀한 툴 활용이 가능하다:

```python
# State 정의
class StockQueryState(TypedDict):
    query: str
    entity: str
    symbol_code: str
    selected_tool: str
    params: dict
    result: Any

# 엔티티 추출 (예: "삼성전자" 추출)
def extract_stock_info(state: StockQueryState) -> StockQueryState:
    ...

# 엔티티명 → 종목코드 변환 (예: "삼성전자" → "005930")
def symbol_to_code(state: StockQueryState) -> StockQueryState:
    ...

# 어떤 툴을 사용할지 선택
def choose_tool(state: StockQueryState) -> StockQueryState:
    ...

# 선택한 툴에서 파라미터 추출
def extract_function_parameter(state: StockQueryState) -> StockQueryState:
    ...

# 선택한 툴 실행
def call_selected_tool(state: StockQueryState) -> StockQueryState:
    ...
```

LangGraph로 이 함수들을 그래프 형태로 선후행 연결해서 실행 흐름을 명시적으로 정의한다.

---

## LangChain에서 MCP 활용

MCP는 USB-C처럼 LLM과 외부 도구를 표준화된 방식으로 연결한다:

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("stock-service")

@mcp.tool()
def get_stock_price(ticker: str) -> dict:
    """케이뱅크 주식 서비스에서 실시간 주가 조회"""
    return listed_stock_service.get_price(ticker)
```

`streamable-http`로 MCP 서버를 기동할 수 있고, 예제에서는 stdio 방식을 사용했다.

---

## 결론

> 단일 툴 호출은 강하나 다중 조합 추론에는 설계가 필요하다.

명시적 흐름 설계나 LangGraph 등으로 보완해야 한다.

**"AI가 알아서"는 어느 정도까지만 가능하다:**

- 간단한 툴 호출: LLM 혼자 잘 처리
- 조건부 논리 (if 삼성전자이면 A 툴, else B 툴): 명시적 설계 필요
- 완전 자유 입력: LangGraph 등 보완 필수

이 구조의 핵심 가치는 **기존 시스템의 신뢰성을 유지하면서 AI의 유연성을 더하는 것**이다.
