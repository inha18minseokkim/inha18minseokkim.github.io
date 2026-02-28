---
title: Gradle 초기화 시점(settings.gradle → build.gradle)
date: 2025-01-27
tags:
  - Gradle
  - CI/CD
  - Git
  - 케이뱅크
category:
  - 실무경험
  - MSA표준
---

GitLab CI 환경에서 Git Submodule을 사용할 때 발생하는 문제와 Gradle 빌드 라이프사이클을 활용한 해결 방법을 정리한다. (2024년 7월 기준)

---

## 문제 상황

| 항목 | 상황 |
|------|------|
| 환경 | GitLab + SAML SSO + Private Repository |
| 이슈 | gitlab-ci 스크립트에 submodule clone 기능 미구성 |
| 제약 | SRE팀에서 CI 스크립트 수정 불가 (당시 기준) |

**관련 문서:**
- [Gitlab SAML 환경에서 clone (1)]({% post_url 2025-01-27-Gitlab SAML 환경에서 clone (1) %})
- [build.gradle Settings.gradle (1)]({% post_url 2025-01-27-build.gradle Settings.gradle (1) %})
- [Gradle User Guide](https://docs.gradle.org/current/userguide/userguide.html)

---

## 해결 방법: settings.gradle에서 서브모듈 클론

### 핵심 아이디어

`settings.gradle`은 `build.gradle`보다 **먼저 실행**되므로, 이 시점에 서브모듈을 클론하면 빌드 시 소스코드가 준비된 상태가 된다.

### settings.gradle 설정

```groovy
pluginManagement {
    var commonModule = new File(rootDir, "./listed-stock-common/build.gradle")
    if (!commonModule.exists()) {
        exec {
            commandLine 'sh', './init-modules.sh'
        }
    }
}
```

### init-modules.sh 스크립트

```shell
git config --global credential.helper store
echo "https://아이디:토큰@git.kbankwithu.com" > ~/.git-credentials
git config --global --add safe.directory /home/gradle
git config --global user.name 20160860
git submodule init
git submodule update --remote --recursive
```

---

## 왜 Dockerfile이 아닌 settings.gradle인가?

처음에는 Dockerfile에서 서브모듈을 클론하려 했으나 실패했다.

| 방식 | Docker 이미지 빌드 | SonarQube 파이프라인 |
|------|-------------------|---------------------|
| Dockerfile에서 클론 | 성공 | **실패** |
| settings.gradle에서 클론 | 성공 | 성공 |

**실패 원인:**
- SonarQube 파이프라인은 Docker 이미지 내부가 아닌 **호스트에서 직접** `gradle sonar` 실행
- 이 시점에 서브모듈이 체크아웃되지 않아 `compileJava` 실패

---

## FAQ: compileJava에 dependsOn을 걸면 안 되나?

**안 된다.**

Gradle 빌드 라이프사이클상 `compileJava` 실행 시점에는 이미 `compileClasspath`와 소스코드 메타정보가 수집된 상태다.

![Gradle Build Lifecycle](/assets/images/Pasted%20image%2020260228171246_52d065e4.png)

> 빌드 버튼을 누른 직후 파일을 추가해도 반영되지 않는 것과 같은 원리

**참고:** [Gradle Build Lifecycle](https://docs.gradle.org/current/userguide/build_lifecycle.html)

---

## IDE 편의 기능: 서브모듈 업데이트 Task

```groovy
task cloneSubmodule {
    exec {
        commandLine 'git', 'submodule', 'update', '--remote', '--init', '--recursive'
    }
}
```

IDE에서 버튼 클릭으로 서브모듈을 업데이트할 수 있다.

---

## 향후 계획

SRE팀과 협의하여 GitLab CI에 서브모듈 기능을 정식으로 추가하고, 위 임시 코드는 제거할 예정이다.

> 제약이 많다 보니 우회 코드가 늘어나는 상황. 근본적인 해결이 필요하다.