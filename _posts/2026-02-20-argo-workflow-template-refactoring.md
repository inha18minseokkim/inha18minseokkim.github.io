---
title: argo workflow template refactoring
date: 2026-02-19
tags:
  - argo
  - workflow
  - job
  - MSA
category:
  - 기술
---
# Argo Workflow 중복 제거: WorkflowTemplate으로 공통화하기

## 문제: 복붙의 늪에 빠진 Workflow 정의

ETF 데이터 적재를 위해 3개의 Argo Workflow를 운영하고 있었다.

| Workflow | 역할 |
|----------|------|
| `etf-load-job` | ETF 기본 정보 적재 |
| `etf-price-load-job` | ETF 시세 적재 |
| `etf-price-realtime-load-job` | ETF 실시간 시세 적재 (반복 실행) |

문제는 세 파일의 YAML이 **거의 동일하다**는 것이다.

### 반복되는 영역

```yaml
# 이 블록이 3개 파일에 전부 복붙되어 있다
spec:
  hostAliases:
    - ip: "172.16.21.140"
      hostnames:
        - "inter-apiwas00.k-bank.com"
  ttlStrategy:
    secondsAfterCompletion: 86400
  # ...
  templates:
    - name: job
      container:
        image: 815039643166.dkr.ecr.ap-northeast-2.amazonaws.com/kbank/convenience/stock/deepsearch-dataload-job:CHA2402-003961
        command: ["/bin/sh", "-c"]
        args: ["python -m src.job.{{workflow.parameters.JOB_NAME}}"]
        env:
          # 공통 파라미터
          - name: JOB_NAME
            value: "{{workflow.parameters.JOB_NAME}}"
          - name: URL
            value: "{{workflow.parameters.URL}}"
          - name: PORT
            value: "{{workflow.parameters.PORT}}"
          - name: TZ
            value: Asia/Seoul
          # Secret 8개 (DB 5개 + Redis + DeepSearch 2개)
          - name: DB_HOST
            valueFrom:
              secretKeyRef:
                name: stock-secret
                key: DB_HOST
          - name: DB_PORT
            valueFrom:
              secretKeyRef:
                name: stock-secret
                key: DB_PORT
          # ... DB_NAME, DB_USERNAME, DB_PASSWORD,
          #     REDIS_ENDPOINT, DEEPSEARCH_ID, DEEPSEARCH_PW
```

각 파일이 80~120줄인데, **이 중 60줄 이상이 완전히 동일한 코드**다.

### 이게 왜 문제인가

- **Secret 추가 시 3곳 수정**: 새로운 Secret이 추가되면 3개 파일을 모두 찾아서 동일하게 수정해야 한다.
- **이미지 태그 변경 시 3곳 수정**: 배포할 때마다 Docker 이미지 태그를 3곳에서 바꿔야 한다.
- **hostAliases 변경 시 3곳 수정**: IP가 바뀌면 역시 3곳.
- **실수 가능성**: 한 곳만 빠뜨려도 장애로 이어진다.

세 파일의 차이점은 실제로 이 정도뿐이다:

| 구분 | etf-load-job | etf-price-load-job | etf-price-realtime-load-job |
|------|-------------|-------------------|---------------------------|
| 고유 파라미터 | (없음) | DATE_FROM, DATE_TO | PROCESS_DATE, SLEEP_SECOND, TARGET_NATION_CODES |
| 실행 구조 | 단순 1회 | 단순 1회 | withSequence 루프 + continueOn |
| 기타 | - | - | CSI Volume |

---

## 해결: WorkflowTemplate + workflowTemplateRef

Argo Workflows에서 제공하는 `WorkflowTemplate` 리소스를 활용해 공통 부분을 추출한다.

### templateRef vs workflowTemplateRef

Argo에서 WorkflowTemplate을 참조하는 방법은 두 가지다.

#### 1. `templateRef` — 개별 template만 참조

```yaml
# Workflow 안에서 특정 template을 가져다 쓴다
templates:
  - name: job
    steps:
      - - name: run
          templateRef:
            name: my-workflow-template    # WorkflowTemplate 이름
            template: load-job            # 그 안의 template 이름
```

이 방식은 WorkflowTemplate에 정의된 **개별 container/script template만** 가져온다.
`hostAliases`, `ttlStrategy` 같은 **Workflow-level 설정은 상속되지 않는다**.

#### 2. `workflowTemplateRef` — Workflow 전체 설정 상속

```yaml
# Workflow가 WorkflowTemplate을 "기반 클래스"처럼 사용한다
spec:
  workflowTemplateRef:
    name: my-workflow-template
  arguments:
    parameters:
      - name: JOB_NAME
        value: "etf_load"
```

이 방식은 WorkflowTemplate의 **모든 spec-level 설정을 상속**받는다:
- `hostAliases` ✅
- `ttlStrategy` ✅
- `entrypoint` ✅ (오버라이드 가능)
- `templates` ✅
- `arguments` 기본값 ✅

**우리의 목표에는 `workflowTemplateRef`가 적합하다.**

---

## 구현

### 1. 공통 WorkflowTemplate

모든 Workflow가 공유하는 설정을 하나의 WorkflowTemplate에 정의한다.

```yaml
# deepsearch-dataload-job-default-template.yaml
apiVersion: argoproj.io/v1alpha1
kind: WorkflowTemplate
metadata:
  name: deepsearch-dataload-job-default-template
  namespace: convenience
spec:
  # ✅ Workflow-level 공통 설정
  hostAliases:
    - ip: "172.16.21.140"
      hostnames:
        - "inter-apiwas00.k-bank.com"
  ttlStrategy:
    secondsAfterCompletion: 86400 # 1일

  # ✅ 기본 엔트리포인트
  entrypoint: job

  # ✅ 가능한 모든 파라미터를 default로 선언
  arguments:
    parameters:
      - name: JOB_NAME
      - name: URL
      - name: PORT
      - name: PAGE_SIZE
        default: ""
      - name: DATE_FROM
        default: ""
      - name: DATE_TO
        default: ""
      - name: PROCESS_DATE
        default: ""
      - name: SLEEP_SECOND
        default: ""
      - name: TARGET_NATION_CODES
        default: ""
      - name: MAX_ITERATION
        default: "1"

  templates:
    # ✅ 컨테이너 템플릿 (핵심 공통 부분)
    - name: load-job
      inputs:
        parameters:
          - name: JOB_NAME
          - name: URL
          - name: PORT
          - name: PAGE_SIZE
            default: ""
          - name: DATE_FROM
            default: ""
          - name: DATE_TO
            default: ""
          - name: PROCESS_DATE
            default: ""
          - name: SLEEP_SECOND
            default: ""
          - name: TARGET_NATION_CODES
            default: ""
      container:
        image: 815039643166.dkr.ecr.ap-northeast-2.amazonaws.com/kbank/convenience/stock/deepsearch-dataload-job:CHA2402-003961
        command: ["/bin/sh", "-c"]
        args: ["python -m src.job.{{inputs.parameters.JOB_NAME}}"]
        env:
          - name: JOB_NAME
            value: "{{inputs.parameters.JOB_NAME}}"
          - name: URL
            value: "{{inputs.parameters.URL}}"
          - name: PORT
            value: "{{inputs.parameters.PORT}}"
          - name: PAGE_SIZE
            value: "{{inputs.parameters.PAGE_SIZE}}"
          - name: DATE_FROM
            value: "{{inputs.parameters.DATE_FROM}}"
          - name: DATE_TO
            value: "{{inputs.parameters.DATE_TO}}"
          - name: PROCESS_DATE
            value: "{{inputs.parameters.PROCESS_DATE}}"
          - name: SLEEP_SECOND
            value: "{{inputs.parameters.SLEEP_SECOND}}"
          - name: TARGET_NATION_CODES
            value: "{{inputs.parameters.TARGET_NATION_CODES}}"
          - name: TZ
            value: Asia/Seoul
          # Secret 환경변수 (8개) — 한 곳에서만 관리
          - name: DB_HOST
            valueFrom:
              secretKeyRef:
                name: stock-secret
                key: DB_HOST
          - name: DB_PORT
            valueFrom:
              secretKeyRef:
                name: stock-secret
                key: DB_PORT
          - name: DB_NAME
            valueFrom:
              secretKeyRef:
                name: stock-secret
                key: DB_NAME
          - name: DB_USERNAME
            valueFrom:
              secretKeyRef:
                name: stock-secret
                key: DB_USERNAME
          - name: DB_PASSWORD
            valueFrom:
              secretKeyRef:
                name: stock-secret
                key: DB_PASSWORD
          - name: REDIS_ENDPOINT
            valueFrom:
              secretKeyRef:
                name: stock-secret
                key: REDIS_ENDPOINT
          - name: DEEPSEARCH_ID
            valueFrom:
              secretKeyRef:
                name: stock-secret
                key: DEEPSEARCH_ID
          - name: DEEPSEARCH_PW
            valueFrom:
              secretKeyRef:
                name: stock-secret
                key: DEEPSEARCH_PW
          - name: SERVICE_NAME
            valueFrom:
              fieldRef:
                fieldPath: metadata.labels['app.kubernetes.io/name']

    # ✅ 기본 엔트리포인트 (단순 1회 실행)
    - name: job
      steps:
        - - name: run
            template: load-job
            arguments:
              parameters:
                - name: JOB_NAME
                  value: "{{workflow.parameters.JOB_NAME}}"
                - name: URL
                  value: "{{workflow.parameters.URL}}"
                - name: PORT
                  value: "{{workflow.parameters.PORT}}"
                - name: PAGE_SIZE
                  value: "{{workflow.parameters.PAGE_SIZE}}"
                - name: DATE_FROM
                  value: "{{workflow.parameters.DATE_FROM}}"
                - name: DATE_TO
                  value: "{{workflow.parameters.DATE_TO}}"
                - name: PROCESS_DATE
                  value: "{{workflow.parameters.PROCESS_DATE}}"
                - name: SLEEP_SECOND
                  value: "{{workflow.parameters.SLEEP_SECOND}}"
                - name: TARGET_NATION_CODES
                  value: "{{workflow.parameters.TARGET_NATION_CODES}}"
```

포인트:
- `arguments.parameters`에 모든 파라미터를 `default: ""`로 선언한다. 각 Workflow는 필요한 파라미터만 오버라이드하면 된다.
- `load-job` 템플릿은 `inputs.parameters`로 값을 받는다. `workflow.parameters`를 직접 참조하지 않아 재사용성이 높다.
- `job` 엔트리포인트가 `workflow.parameters`를 `load-job`의 `inputs.parameters`로 전달하는 브릿지 역할을 한다.

### 2. 단순 실행 Workflow (etf-load-job, etf-price-load-job)

기본 `job` 엔트리포인트를 그대로 사용하므로 metadata와 arguments만 선언하면 된다.

```yaml
# etf-load-job-v2.yaml
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  generateName: etf-load-job-v2-workflow-
  labels:
    app.kubernetes.io/component: workflow
    app.kubernetes.io/instance: convenience
    app.kubernetes.io/name: etf-load-job
  namespace: convenience
spec:
  workflowTemplateRef:
    name: deepsearch-dataload-job-default-template
  arguments:
    parameters:
      - name: JOB_NAME
      - name: URL
      - name: PORT
      - name: PAGE_SIZE
```

```yaml
# etf-price-load-job-v2.yaml
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  generateName: etf-price-load-job-v2-workflow-
  labels:
    app.kubernetes.io/component: workflow
    app.kubernetes.io/instance: convenience
    app.kubernetes.io/name: etf-price-load-job
  namespace: convenience
spec:
  workflowTemplateRef:
    name: deepsearch-dataload-job-default-template
  arguments:
    parameters:
      - name: JOB_NAME
      - name: URL
      - name: PORT
      - name: DATE_FROM
      - name: DATE_TO
      - name: PAGE_SIZE
```

**84줄, 88줄 → 각각 14줄, 16줄로 축소.**

### 3. 반복 실행 Workflow (etf-price-realtime-load-job)

이 Workflow는 `withSequence`로 반복 실행하는 고유한 구조가 있다.
`entrypoint`를 오버라이드하고, 반복 구조만 로컬 template으로 정의한다.
컨테이너 실행(`load-job`)은 WorkflowTemplate에서 상속받은 template을 그대로 사용한다.

```yaml
# etf-price-realtime-load-job-v2.yaml
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  generateName: etf-price-realtime-load-job-v2-workflow-
  labels:
    app.kubernetes.io/component: workflow
    app.kubernetes.io/instance: convenience
    app.kubernetes.io/name: etf-price-realtime-load-job
  namespace: convenience
spec:
  workflowTemplateRef:
    name: deepsearch-dataload-job-default-template
  entrypoint: realtime-job    # ← 기본 entrypoint(job)를 오버라이드
  arguments:
    parameters:
      - name: PROCESS_DATE
      - name: JOB_NAME
      - name: URL
      - name: PORT
      - name: MAX_ITERATION
      - name: PAGE_SIZE
      - name: SLEEP_SECOND
      - name: TARGET_NATION_CODES
  volumes:                      # ← 이 Workflow에만 필요한 CSI Volume
    - name: stock-aws-secrets-inline
      csi:
        driver: secrets-store.csi.k8s.io
        readOnly: true
        volumeAttributes:
          secretProviderClass: stock-aws-secrets-v2
  templates:
    # 로컬 template: 반복 실행 구조만 정의
    - name: realtime-job
      parallelism: 1
      steps:
        - - name: execute-step
            template: realtime-main-step
            continueOn:
              failed: true
              error: true
            withSequence:
              start: 1
              end: "{{=asInt(workflow.parameters.MAX_ITERATION)}}"
    - name: realtime-main-step
      steps:
        - - name: step1
            template: load-job   # ← WorkflowTemplate의 load-job을 참조
            continueOn:
              failed: true
              error: true
            arguments:
              parameters:
                - name: JOB_NAME
                  value: "{{workflow.parameters.JOB_NAME}}"
                - name: URL
                  value: "{{workflow.parameters.URL}}"
                - name: PORT
                  value: "{{workflow.parameters.PORT}}"
                - name: PROCESS_DATE
                  value: "{{workflow.parameters.PROCESS_DATE}}"
                - name: PAGE_SIZE
                  value: "{{workflow.parameters.PAGE_SIZE}}"
                - name: SLEEP_SECOND
                  value: "{{workflow.parameters.SLEEP_SECOND}}"
                - name: TARGET_NATION_CODES
                  value: "{{workflow.parameters.TARGET_NATION_CODES}}"
```

핵심: `template: load-job`이 로컬에 없으면 Argo가 `workflowTemplateRef`의 WorkflowTemplate에서 찾는다.
반복/에러 핸들링 같은 **오케스트레이션 로직**만 로컬에 두고, **컨테이너 실행**은 공통 template을 재사용한다.

---

## Before / After 비교

### 수정 포인트별 비교

| 변경 상황 | Before | After |
|-----------|--------|-------|
| Secret 추가 | 3개 파일 수정 | WorkflowTemplate 1곳 |
| Docker 이미지 태그 변경 | 3개 파일 수정 | WorkflowTemplate 1곳 |
| hostAliases IP 변경 | 3개 파일 수정 | WorkflowTemplate 1곳 |
| ttlStrategy 변경 | 3개 파일 수정 | WorkflowTemplate 1곳 |
| 새 Job 추가 | 기존 파일 복붙 후 수정 | 10~15줄 Workflow 작성 |

### 코드량 비교

| 파일 | Before | After |
|------|--------|-------|
| WorkflowTemplate | - | 117줄 |
| etf-load-job | 84줄 | 14줄 |
| etf-price-load-job | 88줄 | 16줄 |
| etf-price-realtime-load-job | 118줄 | 52줄 |
| **합계** | **290줄** | **199줄** |

줄 수 자체도 줄었지만, 더 중요한 것은 **동일 코드의 반복이 0이 되었다**는 점이다.
Job이 늘어날수록 효과는 더 커진다. 4번째 Job부터는 10~15줄만 추가하면 된다.

---

## 정리

- 여러 Argo Workflow가 같은 컨테이너 이미지, Secret, 인프라 설정을 공유한다면 `WorkflowTemplate`으로 추출하자.
- `templateRef`는 개별 template만 참조하고, `workflowTemplateRef`는 `hostAliases`, `ttlStrategy` 등 Workflow-level 설정까지 상속한다.
- 고유한 실행 구조(반복, 병렬 등)가 필요한 Workflow는 `entrypoint`를 오버라이드하고 로컬 template을 정의하되, 컨테이너 template은 WorkflowTemplate에서 가져다 쓴다.
- 파라미터는 WorkflowTemplate의 `arguments`에 `default: ""`로 전부 선언하고, 각 Workflow는 필요한 것만 오버라이드한다.
