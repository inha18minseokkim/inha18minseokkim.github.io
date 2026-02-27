---
title: "MSA workflow에 cronjob을 올리려면…(20240928)"
date: 2024-09-28
tags:
  - 개발
  - 아키텍처
category:
  - 기술
---
현재 케이뱅크 MSA 파이프라인에서 argo-workflow 부분
뭐 대충 짜잘한 세팅하고
  - project 최상단에 있는 argo-workflow.yaml 파일을 /kbksw/swdpt/…/프로젝트명/argo-workflow.yaml 파일로 mv 한다. 
이게 다임

그리고 Jflow(케이뱅크 통합 작업 관제 시스템) 에서 날리는 스크립트 파일이 있는데 해당 파일에는(runJobParam.sh)
대충 짜잘한 세팅있고
  - argo submit /kbksw/swdpt/…/대충경로/argo-workflow.yaml 
이렇게 되어있음


### 아 결국은 cronjob을 argo submit 으로 못함.

workflow submit 용 스크립트(현재 runJobParam.sh)와
cronWorkflow create 용 스크립트가 둘 다 있어야 함.

