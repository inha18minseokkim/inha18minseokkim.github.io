---
title: 상위 인터페이스에서 하위 클래스 변수 접근
date: 2023-09-28
tags:
  - Java
  - 뻘짓
category:
  - 기술
---
못함
[https://stackoverflow.com/questions/46521203/how-to-access-childs-field-from-the-interface-in-java](https://stackoverflow.com/questions/46521203/how-to-access-childs-field-from-the-interface-in-java)
이글 보고 못한다고 생각했는데 reflection으로 구현하면 가능할 것 같아서 시도해봄
다만 reflection을 비즈니스 구현할 때 써도되는지는 잘..모르겠음 - 나중에 알아보는걸로

예제

```java
interface A {
    public default void a() throws IllegalAccessException {
        for(Field field: this.getClass().getDeclaredFields()){
            System.out.println(field.getName() + " : " + field.getClass() + " : " + field.get(this).toString());
        }
    }
}
class AA implements A {
    private Integer a;
    private Integer b;
    public AA(int a, int b){
        this.a = a;
        this.b = b;
    }
}
@SpringBootApplication
public class TestApplication {
    public static void main(String[] args) throws InterruptedException, IllegalAccessException {
        AA aa = new AA(1,2);
        aa.a();
    }
}
```

기대했던 output은 나오지 않고 다음과 같이 뜸.

```java
Exception in thread "main" java.lang.IllegalAccessException: interface com.example.test.A cannot access a member of class
```


해결방법
인터페이스 일일이 구현해주기

```java
interface A {
    public void a() throws IllegalAccessException;
}
class AA implements A {
    private Integer a;
    private Integer b;
    public AA(int a, int b){
        this.a = a;
        this.b = b;
    }

    @Override
    public void a() throws IllegalAccessException {
        for(Field field: this.getClass().getDeclaredFields()){
            System.out.println(field.getName() + " : " + field.getClass() + " : " + field.get(this).toString());
        }
    }
}
```

장점(내생각) : 인터페이스는 타입과 스펙만 명세하게 하여 코드가 깔끔하고 책임한계가 명확
단점(내생각) : 구현부 오버라이딩하는것을 일일이 다 해줘야함(코드 중복 심각)
추상클래스로 만들기

```java
abstract class  A {
    public void a() throws IllegalAccessException {
        for(Field field: this.getClass().getDeclaredFields()){
            field.setAccessible(true);
            System.out.println(field.getName() + " : " + field.getClass() + " : " + field.get(this).toString());
        }
    }
}
class AA extends A {
    private Integer a;
    private Integer b;
    public AA(int a, int b){
        this.a = a;
        this.b = b;
    }
    @Override
    public void a() throws IllegalAccessException {
        super.a();
    }
}
@SpringBootApplication
public class TestApplication {
    public static void main(String[] args) throws InterruptedException, IllegalAccessException {
        AA aa = new AA(1,2);
        aa.a();
    }
}
```

장점(내생각) : 코드 중복이 없음.
단점(내생각) : 타입 명세 외에 다른 로직이 들어가버림. 사실 그건 ~~default 메서드도 마찬가지긴 함~~

그래서 그냥

```java
interface A {
    public default void a() throws IllegalAccessException {
        for(Field field: this.getClass().getDeclaredFields()){
            field.setAccessible(true);
            System.out.println(field.getName() + " : " + field.getClass() + " : " + field.get(this).toString());
        }
    }
}
class AA implements A {
    private Integer a;
    private Integer b;
    public AA(int a, int b){
        this.a = a;
        this.b = b;
    }
}
```

이런식으로 구현하기로 함

왜냐하면

```java
public interface EssentialResponseElement {
    public default EssentialResponseElement validateAndPass(EssentialResponseElement element) throws IllegalAccessException {
        for(Field field : this.getClass().getDeclaredFields()) {
            if(field.getType().equals(String.class)){
                field.setAccessible(true);
                String o = (String)field.get(this);
                field.set(this,o.replace("-","")
                        .replace(",",""));
            }
        }
        return this;
    }
}
```

이런식으로 구현할 예정임. 데이터 받은 후 위 디폴트 메서드를 한번 파이프라인에서 거쳐서 데이터를 가공할 예정

```java
[{rcept_no=20190221000921, corp_cls=K, corp_code=00378363, corp_name=3S, nstk_ostk_cnt=376,265, nstk_estk_cnt=-, fv_ps=500, bfic_tisstk_ostk=44,395,878, bfic_tisstk_estk=-, fdpp_fclt=-, fdpp_bsninh=-, fdpp_op=783,393,850, fdpp_dtrp=-, fdpp_ocsa=-, fdpp_etc=3,000,000, ic_mthn=제3자배정증자, ssl_at=-, ssl_bgd=-, ssl_edd=-}]
AnnouncePaidIncreaseElement(rcept_no=20190221000921, corp_cls=K, corp_code=00378363, corp_name=3S, nstk_ostk_cnt=376,265, nstk_estk_cnt=-, fv_ps=500, bfic_tisstk_ostk=44,395,878, bfic_tisstk_estk=-, fdpp_fclt=-, fdpp_bsninh=-, fdpp_op=783,393,850, fdpp_dtrp=-, fdpp_ocsa=-, fdpp_etc=3,000,000, ic_mthn=제3자배정증자, ssl_at=-, ssl_bgd=-, ssl_edd=-)
```

이렇게 되어 있는 데이터들(대략 api 20종. 포맷이 살짝씩 다르지만 같은 종류 데이터)
엔티티와 매퍼 20개씩은 어쩔 수 없이 만들어야겠지만 api 받는 부분, 데이터 정제하는 부분, repository 저장하는 부분 같은걸 각각 구현하여 20세트 만들면 정신이 나가기 때문에 reflector를 사용해서 구현할 예정

결론 : 그냥 interface에서 default 메서드 사용하되 field의 setAccessible을 사용하는것으로 합의
