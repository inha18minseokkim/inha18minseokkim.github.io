---
title: "맥북 M1 에어에 딥시크 올리기 - Apple Silicon vs NVIDIA 구조 차이"
date: 2025-02-01
tags: [LLM, DeepSeek, Ollama, MacOS, Apple Silicon, 삽질]
---

딥시크(DeepSeek)가 오픈소스로 공개되고 나서, 로컬에서 LLM을 돌려보고 싶어서 맥북 M1 에어에 올려봤다.

## Apple Silicon vs x86+NVIDIA 구조 차이

LLM을 로컬에서 돌리기 전에 하드웨어 구조 차이를 이해해야 한다.

| 항목 | Apple Silicon (ARM + 통합 GPU) | x86 + NVIDIA GPU |
|------|-------------------------------|-----------------|
| CPU 아키텍처 | ARM 기반 (Apple 설계) | Intel x86 |
| GPU | 온칩 GPU (SoC 내 통합) | 외장 GPU (PCIe 연결) |
| 메모리 구조 | 통합 메모리 (UMA) | 분리 메모리 (Discrete) |
| 메모리 접근 | CPU/GPU 메모리 공간 공유 | CPU ↔ GPU 간 데이터 복사 필요 |

### x86 + NVIDIA 구조 (분리형)

- CPU와 GPU는 물리적으로 분리
- GPU는 자신만의 VRAM(GDDR6 등)을 갖고 있으며 PCIe를 통해 CPU와 통신
- CPU RAM과 GPU VRAM 간에 **명시적 데이터 복사** 필요 (`cudaMemcpy()` 등)

### Apple Silicon 구조 (통합형)

- CPU, GPU, Neural Engine, RAM을 **단일 패키지로 통합**
- 모든 연산 장치가 **하나의 메모리 풀(shared DRAM)**을 사용
- 데이터 복사가 불필요 → **Zero-Copy 연산 가능**
- 메모리 접근이 빠르고 전력 효율이 높음

### 결론: 맥의 장점과 한계

**장점**: 통합 메모리 덕분에 16GB RAM을 VRAM처럼 쓸 수 있다. NVIDIA VRAM 16GB짜리 GPU가 수백만원인데, 맥북 M1 16GB는 훨씬 저렴하게 동급 VRAM을 활용할 수 있다.

**한계**: NVIDIA CUDA 생태계를 사용하지 못한다. 학습 속도는 NVIDIA GPU에 비해 답이 없으므로 **추론 전용**으로 사용해야 한다.

![이미지](/assets/images/Pasted%20image%2020260220141405.png)
![이미지](/assets/images/Pasted%20image%2020260220141412.png)
한 줄 요약 : 싼 가격에 gpu 메모리를 "사용은" 할 수 있다.

---

## Ollama로 딥시크 실행하기

다행히 Ollama를 사용하면 LLM 한정으로 별다른 문제없이 돌아간다.

```python
from langchain_ollama import ChatOllama

llm = ChatOllama(model="deepseek-llm:7b")
```

7b 모델이 약 4GB 정도라서 통합 메모리 16GB 맥북에서도 돌아간다.

### LangChain과 연동 시 주의사항

OpenAI 모델과 달리 딥시크 모델은 Function Calling 전용으로 튜닝된 게 아니어서 Agent 방식이 다르다:

```python
# OpenAI 방식 (딥시크에서는 잘 안 됨)
# from langchain.agents import create_openai_functions_agent
# agent = create_openai_functions_agent(llm, tools, prompt_template)

# 딥시크/로컬 LLM 방식
from langchain.agents import initialize_agent
from langchain.agents.agent_types import AgentType

agent_executor = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True
)
```

```python
result = agent_executor.invoke({"input": "give me an info of 005930"})
```

deepseek 13b Qwen 튜닝 기준 Function Call 사용 어느 정도 가능. ollama 8b 모델도 쓸 수는 있지만 매우 느리다.

---

## M1 에어의 한계

솔직히 말하면 맥북 M1으로는 LLM 로컬 실행이 너무 느리다.

- 딥시크 7b: 그나마 됨
- 라마 8b: Function Call 시 800초 소요 (...)
- 딥시크 13b: 느리지만 그나마 사용 가능

![이미지](/assets/images/Pasted%20image%2020260220141519.png)
긱벤치 OpenCL 기준
![이미지](/assets/images/Pasted%20image%2020260220141533.png)
![이미지](/assets/images/Pasted%20image%2020260220141538.png)
![이미지](/assets/images/Pasted%20image%2020260220141545.png)

M4 에어였다면 임베드 AI 구축을 충분히 할 수 있겠지만, M1 에어는 적절하지 않다. 긱벤치 GPU 점수 차이가 꽤 난다.

**결론:** M1 맥북으로는 가볍게 API 테스트용 추론 정도가 한계. 실제 활용하려면 M3/M4 이상이거나, 개발 서버에 NVIDIA GPU를 붙이는 게 낫다.
