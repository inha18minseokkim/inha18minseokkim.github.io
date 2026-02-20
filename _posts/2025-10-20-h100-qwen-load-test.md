---
title: H100 4장 + Qwen-32b-Instruct 부하테스트 - GPU 4장을 제대로 쓰는 방법
date: 2025-10-20
tags:
  - LLM
  - GPU
  - nginx
  - Docker
  - AI
---

H100 4장에 올라간 Qwen-32b-Instruct 추론 서버 부하테스트를 봐주다가 재미있는 문제를 발견해서 직접 파고들었다.

## 문제 발견

팀장님이 구성해놓은 환경을 보니 H100(한 장에 VRAM 92GB) 4장인데 추론 서버가 하나였다.

32b 모델이 VRAM 30GB 정도 쓰면, 나머지 4장 합산 VRAM인 368GB 중 330GB는 놀고 있는 셈이다.

물론 컨트롤 패널에서 4개 VRAM 점유율이 100%로 표시되지만, 이건 점유(allocate)만 해놓은 것이지 실제로 사용하는 게 아닐 수 있다. 모델 분산 로딩(Tensor Parallelism)을 4장으로 하면 각 카드에 8GB씩 분산되어 있는 구조.

**가설:** 인스턴스 4개를 띄워서 nginx로 로드밸런싱하면 처리량이 4배가 되지 않을까?

---

## 구성 방법

### GPU 분할 전략

```yaml
# docker-compose.yml (최적화 버전)
services:
  vllm-openai-1:
    image: vllm/vllm-openai:latest
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              device_ids: ['0', '1']  # GPU 0, 1번 사용
              capabilities: [gpu]
    command: ["--model", "Qwen/Qwen2.5-32B-Instruct",
              "--tensor-parallel-size", "2"]

  vllm-openai-2:
    image: vllm/vllm-openai:latest
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              device_ids: ['2', '3']  # GPU 2, 3번 사용
              capabilities: [gpu]
    command: ["--model", "Qwen/Qwen2.5-32B-Instruct",
              "--tensor-parallel-size", "2"]
```

1번 인스턴스는 GPU 0,1번, 2번 인스턴스는 GPU 2,3번을 사용한다. 각 인스턴스는 Tensor Parallel로 2장씩 사용.

### nginx 로드밸런서

```nginx
upstream vllm_servers {
    server vllm-openai-1:8000;
    server vllm-openai-2:8000;
}

server {
    listen 80;
    location /v1 {
        proxy_pass http://vllm_servers;
        proxy_read_timeout 300s;
    }
}
```

---

## Least Connection 대신 Round-Robin을 선택한 이유

처음에는 Least Connection 방식을 고려했다. 하지만 LLM 추론의 특성상 Round-Robin이 더 안정적이다:

LLM 응답은 0.5초에 바로 오는 게 아니라 30초 ~ 150초씩 걸리는 구조다.

- Least Connection: 1번 서버 0개, 2번 서버 50개 처리 중 → 1번에 몰아넣음 → 2번 빠지면 1번 50개, 2번 0개 → 또 2번에 몰아넣음 → 반복
- Round-Robin: 토큰 길이가 평균적으로 일정하다면(이게 중요한 가정), 라운드로빈으로 해도 95% 안정적

**결론:** 평균 토큰 길이가 일정하다는 가정 하에 Round-Robin이 더 균등하다.

---

## 테스트 결과

| 구성 | 처리량 |
|------|-------|
| H100 4장 (최적화 X) | 기준 |
| H100 2장 (최적화 X) | 기준의 절반 |
| H100 4장 (최적화 O) | 기준 대비 향상 |
| H100 2장 (최적화 O) | 개선됨 |
| **H100 2장 × 2인스턴스 + nginx** | 최고 |

인스턴스를 분리하고 nginx로 로드밸런싱하는 게 단일 4장 Tensor Parallel보다 처리량이 더 높게 나왔다.

---

## 교훈

GPU 여러 장으로 단일 모델을 돌릴 때 Tensor Parallelism은 메모리가 부족할 때 쓰는 것이다. VRAM이 충분하면 인스턴스를 여러 개 띄워서 수평 확장하는 게 처리량 면에서 더 유리하다.
