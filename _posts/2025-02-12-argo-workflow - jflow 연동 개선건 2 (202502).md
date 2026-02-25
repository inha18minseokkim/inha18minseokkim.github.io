---
title: "argo-workflow - jflow 연동 개선건 2 (202502)"
date: 2025-02-12
tags: [미지정]
category: 기타
---

### ASIS

1 Project - 1 Image - 1 argo-workflow 형태였음.
그러다보니 만들어야 하는 작업의 개수가 N개가 되는 경우 프로젝트를 N개 만들어야 하고 ,소스코드의 의미없는 복붙, 프로젝트 수 증가에 따른 문서 처리 개수 증가 등이 생김.
그리고 현재 케이뱅크 MSA 환경에서 멀티모듈 구성은 불가하다(안은 제시했지만 실현되는데 상당히 오래 걸릴 예정)

### TOBE

일단 argo-workflow.yaml 파일을 한 프로젝트에서 여러 개 배포할 수 있도록 gitlab ci 파이프라인 수정
  - argo-workflow.yaml 파일을 cp 하는것에서 argo-workflow 폴더를 cp -r 하도록 수정
jflow에서 기동되는 쉘스크립트 V2가 기존에는 argo-workflow.yaml을 수행하도록 하였지만, 특정 디렉터리 내의 yaml 파일을 argo submit 하는 방식으로 변경

