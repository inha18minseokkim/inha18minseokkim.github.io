---
title: Reflection
date: 2023-08-31
tags:
  - Java
---
JVM은 클래스 정보를 클래스 로더를 통해 읽어와서 해당 정보를 JVM 메모리에 저장 
클래스 정보를 투영시킨 느낌이라 리플렉션이라는데 솔직히 잘 모르겠고 아무튼 해당 정보를 반영한다고 생각

## 어노테이션(우리가 쓰는 @Component, @Bean 등)

이게 예시임. 어노테이션 자체는 아무런 역할을 하지 않음. 다만 이걸 써놓으면 클래스 로더에서 로딩하고 어떤 어노테이션이 있는지 확인 가능. 어노테이션 붙여놓은것 보고 런타임에 어떤 방식으로 작동시킬거냐..를 스프링이 결정하는 느낌으로 움직이는듯

### 예제 코드


```java
interface HelloService {
    String hello();
    String bye();
}
class ChineseHello implements HelloService{
    public int a;
    public ChineseHello(){
        a = 1;
    }
    @Override
    public String hello(){
        return "Ni Hao";
    }
    @Override
    public String bye(){
        return "Zhai zien";
    }
}
```

해당 클래스의 정보를 가져올 수 있음 - 생성자, 안에 있는 메서드 정보 등을 가져와서 컴파일 타임에 클래스를 몰라도 뭔가 많이 할 수 있음

```java
Public class HelloServiceFactory{
	public static void main(String[] args) {
//첫 번째 방식
		Class<HelloService> xClass = HelloService.class;
//두 번째 방식
		HelloService helloService = new HelloService();
		Class<? extends HelloService> bclass = helloService.getClass();
//세 번째 방식
		Class<?> aClass = Class.forName("me.whiteShip.hello.ChineseHelloService");
//아무튼 이런식으로 로딩됨. 당연히 forName의 대상이 인터페이스면 
	//constructor 없으므로 NoSuchMethodException뜸
		Constructor<?> constructor = aClass.getConstructor();
		Constructor<?> constructor1 = aClass.getDeclaredConstructor();
//두 방법 다 생성자 호출 가능
		HelloService helloService = (HelloService) constructor.newInstance();
		System.out.println(helloService.hello);
	}
}
```

텍스트 만으로 클래스 정보를 로드해서 인스턴스 생성 가능.
극단적으로 생각해보면 컴파일 타임에 아무것도 안하고 텍스트 정보들 만으로 프로그램 만들 수도 있긴 할듯(그러진 않겠지만)
특정 인터페이스의 생태계(생명주기? 프로세스? 특정 인터페이스가 동작하는 일련의 흐름)을 구성해놓고 각기 다른 세부 구현체들을 해당 프로세스에 넣는 방식으로 작동시킬 수 있을 것 같음

```java
Class<ChineseHello> xClass = ChineseHello.class;
Constructor<?> cons = xClass.getConstructor();
HelloService obj = (HelloService) cons.newInstance(); //HelloService로 구현
System.out.println(obj.hello()); //ChineseHello인걸 몰라도 일단 인터페이스 메서드 호출 가능
System.out.println(obj.bye()); //일련의 프로세스를 통일성 있게 탈 수 있음
```


### 필드/메서드 추출


```java
public static void main(String[] args) throws ClassNotFoundException, NoSuchMethodException, InvocationTargetException, InstantiationException, IllegalAccessException {
        Class<?> aClass = Class.forName("com.example.test.ChineseHello");
        Constructor<?> constructor1 = aClass.getDeclaredConstructor();
        HelloService helloService2 = (HelloService) constructor1.newInstance();

        for(Field field : aClass.getDeclaredFields()){
            String fieldInfo = field.getType() + ", " + field.getName() + " = " + field.get(helloService2);
            System.out.println(fieldInfo);
        }
    }//int, a = 1 나온다
```


### 어노테이션 추출

어노테이션 사용 클래스 예제

```java
package com.example.test;

import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import lombok.Data;

@Entity(name="tmpTable")
@Data
public class TestEntity {
    @Id
    private Long id;

}
```


```java
public static void main(String[] args) throws ClassNotFoundException, NoSuchMethodException, InvocationTargetException, InstantiationException, IllegalAccessException {
        Class<?> tmpClass = Class.forName("com.example.test.TestEntity");
        Entity entityAnnotation = tmpClass.getAnnotation(Entity.class);
        String value = entityAnnotation.name();
        System.out.println(value); //tmpTable 나옴
    }
```


## 단점

컴파일 시점에 분석된 클래스를 활용하는게 아님. 런타임임. 느림
실제로 실행하기 전까지 오류인걸 모를 수 있다 ㄷㄷ 컴파일 시점이 아니라 위험
타입 체크를 컴파일 타임에 불가. + 객체의 추상화

## 느낀점

개발자가 쓸 일은 없을 것 같다..프레임워크를 만든다거나 할 때 쓸듯 다만 업무 기본 공통 유틸리티 정리할 때 쓸만할듯(2023 9월 첫주차 MSA 프레임워크 공통업무 정의 시 참조할 것)
