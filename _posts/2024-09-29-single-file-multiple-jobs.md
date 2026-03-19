---
title: "1파일 n 잡"
date: 2024-09-29
tags:
  - argo
  - workflow
  - CI/CD
  - 인프라
  - job
  - MSA
category:
  - 실무경험
  - MSA표준
---

```javascript
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  generateName: hello-world-
  labels:
    workflows.argoproj.io/archive-strategy: "false"
  annotations:
    workflows.argoproj.io/description: |
      This is a simple hello world example.
spec:
  entrypoint: hello-world
  templates:
    - name: hello-world
      container:
        image: busybox
        command: [echo]
        args: ["hello world"]
---
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  generateName: hell-world-
  labels:
    workflows.argoproj.io/archive-strategy: "false"
  annotations:
    workflows.argoproj.io/description: |
      This is a simple hell world example.
spec:
  entrypoint: hell-world
  templates:
    - name: hell-world
      container:
        image: busybox
        command: [echo]
        args: ["hell world"]
```

코드 실행 부분

```javascript
home@homeui-Macmini workflow % argo submit -n argo multiple-cron-twice.yaml 
Name:                hello-world-zr5nk
Namespace:           argo
ServiceAccount:      unset (will run with the default ServiceAccount)
Status:              Pending
Created:             Sun Sep 29 13:01:17 +0900 (now)
Progress:            
Name:                hell-world-5zbwd
Namespace:           argo
ServiceAccount:      unset (will run with the default ServiceAccount)
Status:              Pending
Created:             Sun Sep 29 13:01:17 +0900 (now)
Progress:            

```


![](/assets/images/Pasted%20image%2020260228171326_028e5bbe.png)

두 작업 동시에 올라감