---
title: Class Loader
date: 2023-11-15
tags:
  - Java
  - 이슈정리
---
회사에서 java 8 런타임 환경에서 java 8 문법이 실행되지 않는 이슈때문에 여기까지 왔다. BXM 프레임워크에서 새로운 객체를 생성하다가 오류가 났는데, 로그 트레이싱 하는 과정에서 bxm 라이브러리가 나오고, objectweb.asm 이라는 외부 라이브러리가 나옴.(당연히 new 쓰면 자바 네이티브가 나와야하는것 아니냐?)

말 그대로 클래스를 로딩하는 모듈
  - .class 파일을 jvm 머신 메모리에 올려

![이미지](/assets/images/Pasted%20image%2020260225090445.png)

Loading
  - .class 파일을 읽고 적절한 바이너리 데이터 만들고 메소드 영역에 저장
    - .class파일이 JVM 스펙에 맞는지 확인, 자바 버전 확인
Linking
  - Verifying
    - 바이너리 검증
  - Preparing
    - 메모리 공간 준비
  - Resolution
    - Constant Pool’s Symbolic Reference → Direct Reference, 실제 메모리 주솟값으로 변환
Initializing
  - 메모리 영역에 static 값 할당, SuperClass 초기화 및 해당 Class 초기화

## 계층구조 클래스로더

Bootstrap ClassLoader 
  - - jre/lib/rt.jar 로드
    - Native C
Extension ClassLoader 
  - - jre/lib/ext 로드
    - sun.misc.Launcher에 있음. URLClassLoader 상속
Application ClassLoader ⇒ 여기를 바꿔놓은듯
  - - classpath 로드함
    - sun.misc.Launcher에 있음. URLClassLoader 상속

아마 BXM은 Application ClassLoader를 바꿔놓았거나 Bxm.container에 있는 ClassLoader를 통해서 호출하도록 로직을 바꿔놓은듯 함
아! 다시 찾아보니 정확하게는 디폴트로 현재 클래스를 호출했던 클래스로더를(어떻게 보면 어플리케이션 컨텍스트에 있는 클래스로더?) 사용하기 때문에 그런것 같음
그러니깐 
  1. BXM 어플리케이션을 서버에서 실행함(어떻게 실행하는지는 좀 뜯어봤는데 자체 classLoader 올리고 Application이라는걸 기동하고… 자체 uuid 박고 그런 특수한 작업을 함. spring boot 실행할 때 의존주입하고 그런거 함 아무튼)
  2. new Class(); 했을 때 실험으로 했던 환경이 이미 Bxm Context가 실행된 환경에서 new를 실행해서 bxm에서 제공하는 classloader를 타고
  3. 그런데 bxm에서 제공하는 classloader는 로깅같은거 하는 프록시를 주입하는데
  4. 해당 프록시는 CGLIB라고 인터페이스 유무에 상관없이 바이트코드 조작으로 클래스를 조작하는건데 
  5. 여기서 asm,aspectj의 버전이 자바 8 문법을 지원하지 않아 
  6. .class 파일은 있음에도 바이트코드 호환이 되지 않아 클래스 로딩을 하지 못하는 문제가 생겨 NoSuchBeanDef 예외가 뜨거나 ClassNotFound 예외가 뜬것

그럼 객체 생성(new)는 대체 어떻게 bxm에 의존성을 가질 수 있는가를 생각해보니…
  - 다음과 같은 내용을 찾을 수 있었다
> Java will always use the classloader that loaded the code that is executing.
[https://stackoverflow.com/questions/42297568/how-to-use-custom-classloader-to-new-object-in-java](https://stackoverflow.com/questions/42297568/how-to-use-custom-classloader-to-new-object-in-java)
그러니깐 현재 실행되고 있는 객체를 로딩한 클래스로더를 디폴트로 물고 새로운 Class를 생성하니(new) 객체를 생성하는 new 키워드를 호출할 때 bxm 디펜던시가 생기는것.
  - 왜? 테스트를 할 때 BxmService 를 호출한 걸로 실행했기 때문에!! 애초에 서버는 올라가있는 상황이니깐 BxmService 빈을 올리고 롤링배포 후에 EAI 콜 통해서 서비스를 호출하니깐 자동으로 해당 BxmBean을 만드는 클래스로더는 Bxm에서 제공하는 클래스로더. 그러니깐 new를 호출할 때 Bxm 클래스로더가 호출됨. 그러니깐 바이트코드 에러가 남
정리 끝 땅땅


[https://hbase.tistory.com/174](https://hbase.tistory.com/174)
