---
title: "Gradle 초기화 시점(settings.gradle → build.gradle,202407)"
date: 2025-01-27
tags: [미지정]
category:
  - 기타
---

현시점 최선(202407)
[Gitlab SAML 환경에서 clone (1)]({% post_url 2025-01-27-Gitlab SAML 환경에서 clone (1) %})
1. gitlab-ci 스크립트 뜯어봤는데 현재 submodule clone 하는 스크립트가 구성되어있지않음
2. 그래서 임시로 dockerfile 내부에서 clone 후 gradle build 하는 방식을 사용
3. SAML SSO를 사용하고 프로젝트가 private이기 때문에 docker 내부에서 kbank git으로 찌르는건 가능하지만 SSO id pw 인증 불가
4. 
[build.gradle Settings.gradle (1)]({% post_url 2025-01-27-build.gradle Settings.gradle (1) %})
[https://docs.gradle.org/current/userguide/userguide.html](https://docs.gradle.org/current/userguide/userguide.html)

settings.gradle에 git clone 스크립트 추가

```groovy
pluginManagement {
	var commonModule = new File(rootDir,"./listed-stock-common/build.gradle")
	if(!commonModule.exists()) {
			exec {
				commandLine 'sh', './init-modules.sh'
			}
	}
}
...
```


```shell
git config --global credential.helper store
echo "https://아이디:토큰@git.kbankwithu.com" > ~/.git-credentials
git config --global --add safe.directory /home/gradle
git config --global user.name 20160860
git submodule init
git submodule update --remote --recursive
```

이렇게 셋팅해놓으면 docker build 이미지에서 bootrun > gradle task가 돌기 전에 git 서브모듈repo를 땡겨오고 compileJava 부터 시작
  - 처음에는 settings.gradle에 해당 스크립트 적지 않고 Dockerfile에서 실행하려 했음. 
    - 이미지 배포 까지는 성공하지만 추후에 들어가는 sonarQube 파이프라인에서는 도커이미지 내에서 실행하는것이 아니라 그냥 gradle sonar 커맨드를 실행해버려서 또 프로젝트를 땡기지못함(다시말하지만 이 시점에서 sre가 ci 스크립트를 못 바꿔줌)
    - gradle sonar를 실행하면 compileJava부터 실행되는데 해당 시점에 서브모듈들이 체크아웃되지 않은 상황이라 실패

처음에는 settings.gradle에 해당 스크립트 적지 않고 Dockerfile에서 실행하려 했음. 
  - 이미지 배포 까지는 성공하지만 추후에 들어가는 sonarQube 파이프라인에서는 도커이미지 내에서 실행하는것이 아니라 그냥 gradle sonar 커맨드를 실행해버려서 또 프로젝트를 땡기지못함(다시말하지만 이 시점에서 sre가 ci 스크립트를 못 바꿔줌)
  - gradle sonar를 실행하면 compileJava부터 실행되는데 해당 시점에 서브모듈들이 체크아웃되지 않은 상황이라 실패

이미지 배포 까지는 성공하지만 추후에 들어가는 sonarQube 파이프라인에서는 도커이미지 내에서 실행하는것이 아니라 그냥 gradle sonar 커맨드를 실행해버려서 또 프로젝트를 땡기지못함(다시말하지만 이 시점에서 sre가 ci 스크립트를 못 바꿔줌)
gradle sonar를 실행하면 compileJava부터 실행되는데 해당 시점에 서브모듈들이 체크아웃되지 않은 상황이라 실패

그리고 IDE상에서 편의를 위해 버튼 딸깍으로 gitlab 모듈 업데이트 하는 스크립트 하나 짬

```shell
task cloneSubmodule {
	exec {
		commandLine 'git','submodule','update','--remote','--init','--recursive'
	}
}
```



### 그럼 그냥 위 task를 compileJava에 dependOn을 걸면 안되나?

안됨.
compileJava 하는 시점에 compileClassPath나 소스코드 메타정보를 다 긁어가서 include 서브모듈 하는 시점에 소스코드를 넣어야함!! 우리가  빌드 버튼 누르고 바로 파일을 추가해도 안되는것처럼
[Build Lifecycle](https://docs.gradle.org/current/userguide/build_lifecycle.html)

![](https://prod-files-secure.s3.us-west-2.amazonaws.com/c38aebd7-2834-4fac-b2fc-a2f0c17ce81d/384419d4-38e6-482c-ab83-958174ced619/Untitled.png)



### 앞으로 할일

SRE 선생님과 함께  서브모듈 기능을 gitlab ci에 추가하는것 협의 보고  위 코드는 없애도록 할 것.
안되는게 많다보니 이상한코드가 점점 늘어나는 것 같다.