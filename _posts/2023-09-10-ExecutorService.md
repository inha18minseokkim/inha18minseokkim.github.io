---
title: ExecutorService
date: 2023-09-10
tags:
  - Java
  - 개발
---

## 스레드풀 없는 환경


```java
class Muyaho implements Runnable {

    @Override
    public void run() {
        try {
            Thread.sleep(200L);
        } catch (InterruptedException e) {
            throw new RuntimeException(e);
        }
        System.out.println(Thread.currentThread() + "ASDF");
    }
}
@SpringBootApplication
public class TestApplication {

    public static void main(String[] args)  {
        for(int i = 0; i < 100; i++){
            Thread thread = new Thread(new Muyaho());
            thread.start();
        }
    }
}
```

스레드 거의 100개 생성되었을듯.. 그러므로 스레드풀로 관리해야함


```java
class Muyaho implements Runnable {

    @Override
    public void run() {
        try {
            Thread.sleep(200L);
        } catch (InterruptedException e) {
            throw new RuntimeException(e);
        }
        System.out.println(Thread.currentThread() + "ASDF");
    }
}
@SpringBootApplication
public class TestApplication {

    public static void main(String[] args)  {
        ExecutorService executorService = Executors.newFixedThreadPool(1);
        for(int i = 0; i < 100; i++){
            Muyaho muyaho = new Muyaho();
            executorService.submit(muyaho::run);
        }
        executorService.shutdown();
    }
}
```

이런식으로 스레드풀 관리 가능
스레드풀에 스레드 몇개 써야하는지는 음.. IO bound에 따라 다를듯(성능튜닝의 문제)

```java
@SpringBootApplication
public class TestApplication {

    public static void main(String[] args)  {
        int cpuLength = Runtime.getRuntime().availableProcessors();
        System.out.println(cpuLength);
        ExecutorService executorService = Executors.newFixedThreadPool(cpuLength);
        for(int i = 0; i < 100; i++){
            Muyaho muyaho = new Muyaho();
            executorService.submit(muyaho::run);
        }
        executorService.shutdown();
    }
}
```

이런식으로 cpu 코어에 맞게도 설정 가능하지만 네트워크를 많이 탄다면 더 늘려서 context 스위칭을 하더라도 보내놓고 다른 작업을 시키는것도 좋은 선택지가 될 수 있을듯