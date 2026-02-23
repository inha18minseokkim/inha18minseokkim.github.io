---
title: Finalizer 주의점
date: 2023-09-11
tags:
  - Java
  - 개발
---

```javascript
class Muyaho  {
    private int id;
    public Muyaho(int id){
        if(id == 0){
            throw new IllegalArgumentException("id는 0이 될 수 없음");
        }
        this.id = id;
    }
    public void muyaho() {
        System.out.println("Muyaho!");
    }
}
```

id가 0인 경우 인스턴스 생성 및 메서드 호출 금지
but 이런식으로 finalize를 오버라이딩함

```javascript
class Yamuho extends Muyaho {

    public Yamuho(int id) {
        super(id);
    }

    @Override
    protected void finalize() {
        this.muyaho();
    }
}
```


gc를 이용하여 간접호출 가능

```javascript
@SpringBootApplication
public class TestApplication {

    public static void main(String[] args) throws InterruptedException {
        try {
            Yamuho yamuho = new Yamuho(0);
        }catch(IllegalArgumentException e){
            System.out.println(e.getMessage());
        }
        Thread.sleep(1000);
        System.gc();
    }
}
```

> Task :TestApplication.main()
> id는 0이 될 수 없음
> Muyaho!

그러므로 
모 클래스를 final로 생성(상속막음)
또는 모 클래스의 finalize() 메서드를 finalize로 오버라이딩

```javascript
class Muyaho  {
    private int id;
    public Muyaho(int id){
        if(id == 0){
            throw new IllegalArgumentException("id는 0이 될 수 없음");
        }
        this.id = id;
    }
    public void muyaho() {
        System.out.println("Muyaho!");
    }
    @Override
    protected final void finalize() {
        
    }
}
```

