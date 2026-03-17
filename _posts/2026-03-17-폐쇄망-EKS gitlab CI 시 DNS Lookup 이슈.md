---
title: 폐쇄망 EKS GitLab CI 시 DNS Lookup 이슈
date: 2026-03-17
tags:
  - CI/CD
  - Gradle
  - 네트워크
category:
  - 실무경험
---

## 현상

2달 전에 운영 배포하고 한 번도 건드리지 않았던 코프링 프로젝트가, 운영 CI 이미지 빌드 과정에서 **무한 대기 상태**에 빠짐.

## 의심한 것들

1. GitLab Repo 주소를 바꿈
2. 최근 GitLab CI Runner 인스턴스를 **IDC → EKS로 교체**
3. 외부에서 반입한 프로젝트라 내가 모르는 스크립트 어딘가에 외부 URL을 참조하는 로직이 있을 수 있음

## 원인

GitLab CI Runner를 IDC에서 EKS로 바꾸면서 기존에 드러나지 않던 문제가 터진 것.

`build.gradle` 파일에 레포 구성이 아래처럼 되어 있었다.

```groovy
repositories {
    mavenCentral()
}
allprojects {
    repositories {
        maven {
            url '대충 사내망 nexus repo'
        }
    }
}
```

| 환경 | mavenCentral() lookup 결과 | 동작 |
|---|---|---|
| 사내망 PC / IDC GitLab Runner | DNS 응답 없음 → lookup 실패 | 자동으로 Nexus로 fallback |
| EKS (폐쇄망 VPC 내) | **coreDNS가 IP 반환** | Gradle이 해당 IP로 연결 시도 → 연결 불가 → 타임아웃 |

EKS 환경에서는 coreDNS가 `mavenCentral()`의 IP를 반환해버린다. 아마 너무 잘 알려진 도메인이라 coreDNS 기본 설정에 포함된 게 아닐까 싶다. IP는 반환하지만 실제로는 폐쇄망이라 연결이 안 되고, Gradle은 계속 연결을 시도하다가 타임아웃이 나버린다.

## 배운 점

- **VPC 내 EKS도 외부 도메인 nslookup이 될 수 있다.** 뚫려 있지 않으면 연결은 안 되지만, DNS 응답 자체는 온다. 근데 대체 왜그런진 좀 알아봐야할듯
- **`build.gradle`의 repository 선언 순서가 의미가 없지 않다.** 상단에 선언된 레포부터 순서대로 시도하기 때문에, 폐쇄망 환경에서는 외부 레포를 앞에 두면 안 된다. 그것도 그런데 처음에 프로젝트 반입할 때 mavenCentral()을 안지워서 이런 일이 일어났다.

