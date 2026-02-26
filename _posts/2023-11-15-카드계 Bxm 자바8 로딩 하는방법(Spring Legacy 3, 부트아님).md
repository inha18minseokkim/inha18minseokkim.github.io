---
title: 카드계 Bxm 자바8 로딩 하는방법(Spring Legacy 3, 부트아님)
date: 2023-11-15
tags:
  - Java
  - Spring
  - 이슈정리
  - 뻘짓
  - BXM
  - 케이뱅크
category:
  - 실무경험
---

### 경과

1. 해당 자바파일이 java8 모듈로 컴파일되어 .class 파일이 떨어지는 것 까지는 서버 bin경로에서 확인완료
2. 그런데 Bxm에서 해당 서비스 빈을 호출하는 순간 NoSuchBeanDef Exception 발생
3. 김영한 아저씨 강의(스프링 핵심원리 기초)를 듣다가 스프링 AOP에서 바이트코드를 조작한다는 내용을 들음(파이썬 하다가 갑자기 취업해서 스프링 잘 모르는 상태)
4. 그러면 해당 스프링 컨텍스트에서 .class 파일을 AOP Proxy로 변환하다가 문제가 생긴게 아닐까? 하는 상당히 합리적인 의심이 들었음. (덕분에 밤 10시에 강의듣다가 출근할뻔 한것 여자친구가 말림. 갔다가 막차끊기면 못와서)
5. 그러면 getBean이나 해당 서비스 빈을 호출하는 것이 아닌 Test t = new Test() 이런식으로 호출을 하면 어떻게 될까?

### new 생성자 호출 결과(자바 기본 객체 생성방법)

다행히 밤에 출근하려는거 여자친구가 말려서 그다음날 아침 출근해서 확인해봄
1. new를 사용하여 생성했는데 new를 호출하는 부분에서 예외를 던지면서 bxm.loader.classloader.internal.AbstractAppplicationClassLoader.loadClass라는 메서드로 떨어지면서 ArrayIndexOutOfBoundsException 예외가 났다
2. 마지막 stack trace에서는 org.objectweb.asm.ClassReader.readClass(Unknown Source)에서 에러가 났다고 함
3. objectweb이라는 모듈은 무슨 솔루션인것같았음
4. 확실한 것은 java 8과 상관없는 bxm의 무언가를 호출하여서 객체를 생성하는것

### Reflection으로 객체 생성하는 방법 시도 → .class로 getConstructor 하기


```c++
Class<?> tmpClass = Class.forName("풀패키지 경로");
Object a = tmpClass.getConstructor().newInstance();
```

이런식으로 했는데도 똑같은 오류가 남.
.class 호출도 bxm으로 빠짐

### ClassLoader를 직접 사용하기


```c++
public class FileClassLoader extends ClassLoader {
   
   private String root;
   
   /**
    * @param rootDir 클래스를 읽어올 루트 디렉토리
    */간
   public FileClassLoader(String rootDir) throws FileNotFoundException {
      super(FileClassLoader.class.getClassLoader() );
      
      File f = new File(rootDir);
      if (f.isDirectory())
         root = rootDir;
      else
         throw new FileNotFoundException(rootDir+" isn't a directory");
   }
   
   /**
    * @param name 검색할 클래스 이름
    */
   public Class findClass(String name) throws ClassNotFoundException {
      try {
         String path = root + File.separatorChar + 
                       name.replace('.', File.separatorChar) + ".class";
         
         FileInputStream file = new FileInputStream(path);
         byte[] classByte = new byte[file.available()];
         file.read(classByte);
         
         return defineClass(name, classByte, 0, classByte.length);
      } catch(IOException ex) {
         throw new ClassNotFoundException();
      }
   }
```

블로그 뒤져서 이런 글을 참고해서 .class 파일을 직접 로드하는 클래스를 직접 배포하고(이 객체는 기존 bxm의 classloader를 사용해서 객체화 함) 해당 .class 파일을 직접 땡겨봄

```c++
//현재 클래스 파일의 위치를 읽어온다. 일단 테스트용으로 현재 문제되는 .class 파일이 같은 경로에 있음
final File f = new File(BGamCmtnHistMgmt.class.getProtectionDomain().getCodeSource().getLocation().getPath());
FileClassLoader fileClassLoader = new FileClassLoader(f.getPath());
//해당 문제의 클래스 파일 로딩
Class<?> a = fileClassLoader.findClass("kbank.cd.gam.business.Test");
//타입 생성자를 가져와 호출
Object aaa = a.getConstructor().newInstance();
//메서드 정보 가져옴
Method[] methods = aaa.getClass().getMethods();
//해당 메서드 호출
methods[0].invoke(aaa,aList);
```

이런식으로 하면 람다식이 포함되어 컴파일된 클래스를 로딩할 수 있고 호출 할 수 있다
할 수는 있다는것이지 프레임워크 AOP를 빼고 해당 로직이 실행되는것이니 그냥 재미로만 보자..

### 결론

1. 카드계 java 실행환경은 java 1.8이 맞다. Function같은 인터페이스 사용가능함
2. 근데 컴파일러는 javac 1.7이었다(이건 발견 후 말씀드리고 8버전으로 올림)
3. 근데 클래스를 로딩하는 부분은 java 7이다(?!) 이건 구멍이 뚫린건지.. 솔루션의 한계인지 알아봐야한다
4. 그래도 결과적으로 os 실행환경이 java 8이고 앱을 실행하는 기저의 자바 환경은 8이기 때문에 다음과 같은 방식으로 로딩 “할 수는” 있다
5. 다만 BXM에서 저런식으로 클래스를 로딩하는 이유가 만약에 서비스 안에서 트랜잭션을 잡거나 하는데 프록시를 사용하기 위한것이었다면 결제 같은 코어한 기능에서는 쓰기 어렵다
  1. 이 부분은 후에 BXM 어노테이션과 클래스로더, 프록시를 한번 뜯어보면서 알아봐야할것같다
6. 근데 만약 그렇다면 대체 작년에 Java 1.8을 왜 올린걸까..?
  1. java 8 라이브러리를 쓰기 위해서 배포 → 나 말고 java 8 라이브러리 및 문법 쓰는사람 없어서 이제 발견한거(;;)
  2. 개선된 자바를 쓰기 위해서 → 아니 클래스 컴파일하고 로드했던 부분은 7이라니깐? 심지어 pp서버에서조차 javac 1.7버전 쓰다가 Function 들어간 클래스 배포하다가 에러남
7. 회사 팀원들에게 공유했더니 플기팀에서 배포할때 까먹은 것 같다고 함
  1. 만약 그게 맞으면 대체 작년에 올리면서 java 바꾸고 어플리케이션 실행한것말고는 한게 없는것 아닌가..
  2. 소 뒷걸음치다가 쥐 잡았다.
