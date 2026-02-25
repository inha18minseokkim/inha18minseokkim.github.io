---
title: H100 4장 + Qwen-32b-Instruct 부하테스트 - GPU 4장을 제대로 쓰는 방법
date: 2025-10-20
tags:
  - LLM
  - GPU
  - nginx
  - Docker
  - AI
category: 기술
---

부하테스트 좀 봐주다가 재미있는 문제가 생겨서 한번 가지고와봄

### 6-3. Docker Compose 예제 1 :: 백엔드 + DB + 모델(vllm)

- Dockerfile
    
    ```docker
    # 가볍고 최적화된 Python 베이스 이미지 사용
    FROM python:3.10.12-slim
    
    # Python이 pyc 파일을 생성하지 않고, 출력 버퍼링 없이 실행되도록 설정
    ENV PYTHONDONTWRITEBYTECODE=1
    ENV PYTHONUNBUFFERED=1
    
    # 시스템 패키지 업데이트 및 필수 패키지 설치 (빌드에 필요한 경우)
    RUN apt-get update && apt-get install -y --no-install-recommends \\
        build-essential \\
        && rm -rf /var/lib/apt/lists/*
    
    # 작업 디렉토리 설정 
    # command(CMD) 명령어의 실행 위치가 됨
    WORKDIR /home/jskim/data_js/sapie_project_2025 
    
    # 의존성 파일을 먼저 복사하여 캐시 활용(사실 requirements.txt 는 프로젝트 루트에 있어야 중복 copy 방지 가능)
    COPY ./sapie_project_2025/dev_container/docker/requirements.txt ./dev_container/docker/requirements.txt  
    
    # pip 업그레이드 후 의존성 설치
    RUN pip install --upgrade pip \\
        && pip install --no-cache-dir -r ./dev_container/docker/requirements.txt
    
    # 나머지 백엔드 소스코드 복사(운영 환경에서만 필요)
    # COPY . /home/jskim/data_js
    
    # 컨테이너 시작 시 main.py를 실행하여 FastAPI 서버를 구동(docker-compose 에 실행 명령어 정의 안 하고 직접 docker run 할 거면 지정)
    # CMD ["python3", "main.py"]
    
    ```
    
- docker-compose.yml
    
    ```yaml
    version: '3.8'
    services:
      sapie-backend:
        container_name: sapie-backend
        build:
          context: "/home/jskim/data_js"  # 도커 컨테이너가 접근 가능한 위치이자 COPY, RUN 등 도커파일 내 명령어의 실행 위치
          dockerfile: "./sapie_project_2025/dev_container/docker/Dockerfile"  # 백엔드 전용 Dockerfile (GPU 미포함)
        ports:
          - "5409:5406"  # 백엔드 서비스 포트 (예: uvicorn 실행 시)
        volumes:
          - /home/jskim/data_js:/home/jskim/data_js
        command: ["python3", "./main.py"]
        networks:
          - compose_test
    
      vllm-compose-test:
        image: vllm/vllm-openai:latest  # GPU 지원이 포함된 vllm 이미지 사용
        container_name: vllm-compose-test
        deploy:
          resources:
            reservations:
              devices:
                - driver: nvidia
                  count: all
                  capabilities: [gpu]
        ports:
          - "8000:8000"
        volumes:
          - /home/jskim/data_js/vllm/code/models:/models
        command: ["--model", "/models/Qwen2.5-14B-Instruct-AWQ", "--host", "0.0.0.0", "--port", "8000"]
        networks:
          - compose_test
          
      mongodb:
        image: mongo:latest
        container_name: mongodb
        ports:
          - "27017:27017"
        volumes:
          - /home/jskim/data_js/data/db:/home/jskim/data_js/data/db
        networks:
          - compose_test
    
    networks:
      compose_test:
        external: true
    #    driver: bridge
    ```
    

# 문제점

아무리 제한된 환경이라지만(prod 환경 h100 4장, 마치 케이뱅크 네트워크 인프라 환경을 보는 느낌) 최대한 속도를 내라고 하니.. 주어진 환경 내에서 최대한 짜낼 수 있는 환경을 만들어보기로 함.

### 왜 4장을 꼭 다 쓸까?

그쪽회사 팀장 아저씨가 구성해놓은 환경을 보고 H100(한장에 VRAM 92기가) 4장인데 추론 서버가 하나였음. 32b 정도니깐 vram 368기가 전체를 단 하나의 인스턴스로 올리고 있다는 소리. 해봤자 30기가 정도인데 나머지 320기가 정도는 놀리고 있다는 소리. 물론 컨트롤 패널 보면 4개의 vram 메모리 점유율이 100%로 찍히지만 그건 그냥 점유만 하고 있는거지 실제로 쓰는건 아닐 수 있다는 생각이 들었음.

그래서 인스턴스 4개를 띄워서 nginx 붙여보기로 함.

### 6-4. Docker Compose 예제 2 :: 추론 속도 최적화에 활용

- nginx.conf
    
    ```toml
    worker_processes auto;  # Nginx가 사용할 worker 프로세스 수를 자동으로 설정 (서버의 cpu 코어 수에 따라 적절히 할당)
    events {
        worker_connections 1024;  # 각 worker 프로세스당 최대 동시 연결 수 
    }
    
    http {
        upstream vllm_servers {  # 백엔드 서버들의 그룹 정의
            # least_conn;  # 가장 적게 연결된 서버로 분배
            server vllm-openai-32-32768-1:8000;
            server vllm-openai-32-32768-2:8000;
        }
    
        server {
            listen 8000;
    
            location /v1 {  # 클라이언트가 /v1 경로로 요청하면 이 블록의 설정을 적용
                proxy_pass http://vllm_servers;  # 들어온 요청을 앞서 정의한 vllm_servers 그룹 중 하나로 프록시
                proxy_set_header Host $host;  # 원래 요청의 Host 헤더를 그대로 백엔드 서버로 전달
                proxy_set_header X-Real-IP $remote_addr; # 클라이언트의 실제 IP를 X-Real-IP 헤더로 전달 (백엔드에서 클라이언트 IP 확인 가능)
                proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;  # 클라이언트 IP 체인을 X-Forwarded-For에 누적 (로깅 및 분석 등에 활용)
            }
        }
    }
    ```
    
- docker-compose.yml
    
    ```yaml
    version: '3.8'
    
    services:
      vllm-openai-1:
        image: vllm/vllm-openai:latest
        container_name: vllm-openai-32-32768-1
        networks:
          - new-sapie-backend-dev
        ports:
          - "8001:8000"
        deploy:
          resources:
            reservations:
              devices:
                - driver: nvidia
                  device_ids: ["0", "1"]
                  capabilities: [gpu]
        volumes:
          - /data/axolotl/models:/models
        command: >
          --model /models/Qwen2.5-32B-Instruct
          --host 0.0.0.0
          --port 8000
          --tensor-parallel-size 2
          --dtype bfloat16
          --max-num-seqs 32
          --enable-chunked-prefill
          --max-num-batched-tokens 32768
    
      vllm-openai-2:
        image: vllm/vllm-openai:latest
        container_name: vllm-openai-32-32768-2
        networks:
          - new-sapie-backend-dev
        ports:
          - "8002:8000"
        deploy:
          resources:
            reservations:
              devices:
                - driver: nvidia
                  device_ids: ["2", "3"]  
                  capabilities: [gpu]
        volumes:
          - /data/axolotl/models:/models
        command: >
          --model /models/Qwen2.5-32B-Instruct
          --host 0.0.0.0
          --port 8000
          --tensor-parallel-size 2
          --dtype bfloat16
          --max-num-seqs 32
          --enable-chunked-prefill
          --max-num-batched-tokens 32768
    
      nginx:
        image: nginx:latest
        container_name: nginx-load-balancer
        depends_on:
          - vllm-openai-1
          - vllm-openai-2
        networks:
          - new-sapie-backend-dev
        ports:
          - "8000:8000"
        volumes:
          - ./nginx.conf:/etc/nginx/nginx.conf:ro
    
    networks:
      new-sapie-backend-dev:
        external: true
    ```
    
    이런식으로 1번, 2번 gpu는 인스턴스 1번, 3번 4번 gpu는 인스턴스 2번으로 세팅한다는 내용
    
    그리고 1번 2번 인스턴스는 nginx로 묶어서 로드밸런싱 한다
    
- `Docker Compose + Nginx` 활용 이유
    
    - H100 NVLink Bridge
        
        ![이미지](/assets/images/Pasted%20image%2020260223115955.png)
        
    
    ### **1. 문제 정의: GPU 간 통신 병목과 비효율적 부하 분산**
    
    - NVIDIA H100 GPU를 활용하여 대규모 모델을 서빙할 때, **GPU 간 데이터 전송과 부하 분산 최적화**는 성능을 결정하는 중요한 요소
    - 초기에는 단순히 **2장, 4장 등의 GPU 개수만 고려하여 배포**했지만, **최적의 GPU 연결 방식(NVLink + PCIe 구조)을 고려하지 않으면 성능이 저하됨**을 발견
        - 위에서 보듯이 NVLink를 사용하면 1,2 // 3,4번 이렇게 연결이 되는데 4개를 한 인스턴스로 묶으면 2~3 // 1~4 이렇게 컨텍스트 스위칭이 발생하면 병목이 발생하지 않을까 라는 생각이 들었다.
    
    ### **2. 해결책 탐색: NVLink + PCIe 토폴로지를 고려한 최적 배치**
    
    - **H100 GPU는 NVLink로 2장씩 강하게 연결**되어 있음 (`nvidia-smi topo -m` 으로 확인)
        
        ![이미지](/assets/images/Pasted%20image%2020260223120002.png)
        
    - **단순히 GPU 개수를 늘리는 것보다, NVLink로 연결된 GPU를 하나의 논리적 그룹으로 배포하는 것이 효율적**일 가능성이 높음
        
    - 즉, `2장 단위`로 배포하는 것이 성능 최적화에 기여할 수 있을 것이라 가설을 세움
        
    
    ### **3. 실험 설계: Docker Compose + Nginx를 활용한 부하 분산 최적화**
    
    - 여러 개의 vLLM 인스턴스를 배포하여 **다양한 GPU 사용 방식(2장, 4장, 1장)에서 성능을 측정**
    - **Docker Compose**를 활용하여 GPU 2장 단위로 컨테이너를 배포하고,
    - **Nginx를 로드 밸런서로 사용**하여 최적의 요청 분배 방식을 실험함
        - Round Robin
        - Least Connection
        - NVLink 그룹별 요청 분배
    
    ### **4. 결과 분석: 2장씩 묶어 4장을 활용할 때 성능이 가장 우수**
    
    - 단순히 GPU 개수만 늘리는 방식보다, **NVLink 기반으로 2장씩 묶어서 4장 단위로 배포했을 때 추론 속도가 가장 빠름**
    - 이유:
        1. **NVLink로 직접 연결된 GPU 간 통신 속도가 빠름 → 내부적인 batch 처리 최적화**
        2. **PCIe를 통한 CPU-GPU 데이터 전송이 병목이 되지 않도록 부하를 균형 있게 분산**
        3. **Nginx + Docker Compose를 활용하여 요청을 효율적으로 라우팅**함으로써 **워크로드를 최적화**
        4. **8장 풀로드보다 4장 단위로 적절히 분산하는 것이 모델 응답 속도에 유리**
    
    ### **5. 결론 및 최적 배포 전략**
    
    - **"더 많은 GPU를 사용한다고 성능이 항상 좋아지는 것은 아니다."**
        
    - **NVLink 기반의 최적 토폴로지를 고려하여 배포 전략을 수립하는 것이 성능 최적화의 핵심**
        
    - `Docker Compose + Nginx` 를 활용하여 **각 NVLink 그룹 단위로 부하를 분산하는 방식이 가장 효과적**
        
    - 추론 속도 비교
        
        ### First Token 반환까지 걸린 시간
        
        :: 30명, 10분, 최대 부하(응답 완료 후 바로 다음 요청) 기준
        
        - H100 4장 (속도 최적화 X)
            
            ![이미지](/assets/images/Pasted%20image%2020260223120020.png)
            
        - H100 2장 (속도 최적화 X)
            
            ![이미지](/assets/images/Pasted%20image%2020260223120024.png)
            
        - H100 4장 (속도 최적화 O)
            
            ![이미지](/assets/images/Pasted%20image%2020260223120030.png)
            
        - H100 2장 (속도 최적화 O)
            
            ![이미지](/assets/images/Pasted%20image%2020260223120034.png)
            
        - H100 2장 x 2 (속도 최적화 O + nginx 활용)
            
            ![이미지](/assets/images/Pasted%20image%2020260223120038.png)
            

### 그냥 Round-Robin 사용한 이유

Least Connection - 데이터가 0.5s 이런식으로 즉발 리턴하는게 아니라 30초 ~ 150초 ~ 이런식으로 응답이 상당히 길기 때문에 호출이 쌓이는 구조,

즉 1번 0개 , 2번 50개 >>> 이러니깐 nginx 는 1번에 호출 다 밀어넣을거고

2번 호출이 다 빠지면 1번 50개, 2번 0개 >> 이러면 또 2번에 호출 다 밀어넣고 이런 상황이 있을 수 있으므로

평균적인 토큰의 길이가 일정하다면 >>>> 이거 중요한 가정

그냥 라운드로빈으로 하는게 거의 95% 안정적이다라는 결론을 내림.

---

## 교훈

GPU 여러 장으로 단일 모델을 돌릴 때 Tensor Parallelism은 메모리가 부족할 때 쓰는 것이다. VRAM이 충분하면 인스턴스를 여러 개 띄워서 수평 확장하는 게 처리량 면에서 더 유리하다.
