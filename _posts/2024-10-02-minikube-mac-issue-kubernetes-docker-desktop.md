---
title: Minikube + Mac 안되는 이유, Kubernetes with Docker desktop
date: 2024-10-02
tags:
  - Docker
  - MacOS
category:
  - 기술
---
[minikube service 외부 접속 안되는 이유](https://mythpoy.tistory.com/50)
도커 드라이버 덕분에 Minikube tunnel, service 등 이상한 로직을 발라야 해서 안되는데
언제부턴가 Docker desktop에 쿠버네티스 지원 기능이 들어감

그래서 이제 minikube 이런거 말고 개발용으로는 Docker desktop의 kubernetes 쓰면
포트포워딩같은것도 알아서 잘 해줌 굳
service에서 LoadBalancer나 NodePort 사용하면 바로 맥에서 뚫림 ㄷㄷ
