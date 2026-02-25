---
title: "Python + jflow 필요성 + 샘플 프로젝트"
date: 2024-12-31
tags: [미지정]
category: 기술
---

## 개선 사항

1. 가벼운 작업 하나 돌리는데 spring application을 굳이 띄워야하나
  1. 파이썬 스크립트의 경우 파이썬 파일 하나 실행하면 거기에 딸려있는 import를 무는정도지만
  2. spring 의 경우 main 어플리케이션이 기동하면서 dependency에 등록되어있고 작성된 빈이 모두 뜨는 형태임
2. 파이썬 쓰고싶음(json 처리, 문자열 처리 등등..)
3. py 파일을 선택해서 기동하고 싶음

## 제한사항

1. jflow 에서 트리거가 날아와야함
2. 작업이 끝난 후 작업이 어떻게 끝났는지(정상,비정상 종료)를 리턴받아야 함
3. spring 실행과 python 실행을 하나로 묶고싶다(docker 사용)
4. argo-workflow가 중간에 필요하다. 그렇지 않다면 1,2번을 충족시킬 수 있는 방법을 kube job에서 찾아야 한다.

### 데모 개발


![](https://prod-files-secure.s3.us-west-2.amazonaws.com/c38aebd7-2834-4fac-b2fc-a2f0c17ce81d/ba70c4ef-1576-42aa-ab17-7760628bf0ea/image.png)

간단하게 디렉터리를 나눔

### Dockerfile 

파이썬 & 자바 실행환경 단일화 + MSA 환경에서 실행을 위한 도커파일

```java
# 베이스 이미지 설정
FROM python:3.11-slim

RUN apt-get update \
    && apt-get -y install libpq-dev gcc

# 컨테이너 내부 작업 디렉토리 설정
WORKDIR /app

# requirements.txt 복사 및 의존성 설치
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# app 폴더의 모든 파일 복사
COPY app/ ./app/

## 작업 디렉토리를 job 폴더로 변경
#WORKDIR /app/job

ENV PYTHONPATH=/app

# 기본 실행 명령어 (필요 시 수정)
ENTRYPOINT ["python"]
```


### requirements.txt

잡에 들어갈 공통 종속성 정의

```java
kafka-python==2.0.2
orjson==3.10.13
redis==5.2.1
pandas==2.2.3
SQLAlchemy==2.0.36
psycopg2==2.9.10
confluent-kafka==2.7.0
loguru
```


### job 디렉터리

파이썬 소스코드 넣음
소스코드 내부에서 디렉터리를 어떻게 분류할지는 이제 개발자들끼리 논의해야 함

### argo-workflow 디렉터리

jflow-argo workflow 연동을 위해 사용.

```java
#python 파일 인자로 받아서 실행
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  generateName: hello-job
  annotations:
    job-name: "{{workflow.parameters.job-file-name}}"
spec:
  entrypoint: main
  arguments:
    parameters:
      - name: job-file-name #디폴트 없음. 파라미터 입력안하면 무조건 실행하지마

  templates:
    - name: main
      steps:
        - - name: "{{workflow.parameters.job-file-name}}"
            template: hello-job
    - name: hello-job
      container:
        image: muyaho/python-job-sample:latest
        command: [ "/bin/sh", "-c" ]
        args: [ "python /app/job/{{workflow.parameters.job-file-name}}.py" ]
        env:
          - name: JOB_NAME d
            value: "{{workflow.parameters.job-file-name}}"
```

만약 jflow에서 모든것이 다 처리가 가능하면 argo-workflow가 굳이 필요하진 않을 듯 함.

![](https://prod-files-secure.s3.us-west-2.amazonaws.com/c38aebd7-2834-4fac-b2fc-a2f0c17ce81d/778a68f7-157b-4298-9eb7-fcc9b293097a/image.png)

자바 파이썬 모두 같은 실행환경에서 실행 가능.
dockerized 된 환경에서 파이썬 스크립트 실행

![](https://prod-files-secure.s3.us-west-2.amazonaws.com/c38aebd7-2834-4fac-b2fc-a2f0c17ce81d/58b3fda6-34f9-452e-98fd-5249178f26a3/image.png)

윈도우 cmd 스크립트 예시

```java
set PYTHONPATH=C:\Users\Surface\IdeaProjects\python-job-example && python ListedStockPricePubJob.py 2025-01-08 2025-01-08
```

윈도우 파워쉘 스크립트 예시

```java
$env:PYTHONPATH="C:\Users\Surface\IdeaProjects\python-job-example" ; python ListedStockPricePubJob.py 2025-01-08 2025-01-08
```

도커 이미지 실행 예시

```java
docker run muyaho/python-job-example:latest ./app/lisㅠted/stock/job/KafkaSubSelectJob.py
```



### 과연 이것이 최선인가

MSA 환경에서 argo-workflow를 사용하는 경우 도커 이미지를 기동하여 다음과 같은 특징을 가진다고 생각
장점
1. 작업의 환경이 완전 격리됨
2. 격리됨에 따라 다른 로직에 영향도가 사라짐
3. 쿠버네티스에 구성해놓은 config들 사용가능(아마?)
단점
1. 공통 소스 모듈을 구성하지 않는 이상 복붙
2. 이미지가 뜨는데 시간, 자원이 많이 쓰임

온라인 서비스에서는 격리된 환경에서 서비스를 실행하여 다른 서비스로 실시간 장애 전파를 막을 수 있는것이 장점이지만, 정기작업으로 도는 녀석들에게 이러한 장점을 주려고 단점들을 희생하는게 맞을까는 의문
결국 정기작업용 노드가 따로 빠져나오는것으로부터 자유롭지는 못할 것.

