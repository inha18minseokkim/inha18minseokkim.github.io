---
title: Java Memory Model + final 선언 필요성(JLS 17.4)
date: 2023-09-23
tags:
  - Java
category: 기술
---
JLS 17.4 - 프로그램 실행 룰.
요약 : 중간에 실행 순서를 바꿀 수도 있음. - Memory Model이 정해놓은 한도에 따라 다를 수 있음

### 문제상황

[https://docs.oracle.com/javase/specs/jls/se8/html/jls-17.html#jls-17.4.5](https://docs.oracle.com/javase/specs/jls/se8/html/jls-17.html#jls-17.4.5)
> *The semantics of the Java programming language allow compilers and microprocessors to perform optimizations that can interact with incorrectly synchronized code in ways that can produce behaviors that seem paradoxical.*
컴퓨터 구조 시간에 배웠던 내용인듯 하다. 
명령어 실행 처리 할 때 논리적으로 문제 없으면 프로세서가 명령어 실행 순서 바꿈 

| 재배치 전 |  |  | 재배치 후 |  |
| --- | --- | --- | --- | --- |
| Thread 1 | Thread 2 |  | Thread 1 | Thread 2 |
| `r2 = A;` | `r1 = B;` |  | B = 1; | r1 = B; |
| `B = 1;` | `A = 2;` |  | r2 = A; | A = 2; |

A가 공유자원인 경우 의도하지 못한 동작 가능
실행 결과에 논리적으로 문제가 없으면 특정 변수 공간을 재사용 하는 문제도 있음

| 재배치 전 |  |  | 재배치 후 |  |
| --- | --- | --- | --- | --- |
| Thread 1 | Thread 2 |  | Thread 1 | Thread 2 |
| `r1 = p;` | `r6 = p;` |  | r1 = p; | r6 = p; |
| `r2 = r1.x;` | `r6.x = 3;` |  | r2 = r1.x; | r6.x = 3; |
| `r3 = q;` |  |  | r3 = q; |  |
| `r4 = r3.x;` |  |  | r4 = r3.x; |  |
| `r5 = r1.x;` |  |  | r5 = r2; |  |

r5에 넣는 변수가 r1.x에서 해당 값을 이미 갖고있다고 판단하는 r2의 값을 넣음. 만약 해당 변수들이 shared 되었다면 의도치 않은 동작 가능

→ 근데 이게 각각의 실행 흐름에서만 봤을때는 논리적임. 여러 스레드가 동시에 특정 자원을 점유하고 사용하는 경우 문제가 생길 수 있음
> *If a program has no data races, then all executions of the program will appear to be sequentially consistent.*
(스레드가 다른 스레드의 상황을 고려하지 않기 때문, 아니 다른 스레드 상황을 어떻게 알아;;)

# final 

한 번 초기화 되면 다시 다른 값으로 바뀌지 않게 안전한 초기화 가능. 
immutable이 보장되므로 race condition 문제 없음. 싱크 문제 없음. 
레지스터에 final 객체의 값 캐싱 가능.
그래서 가급적이면 메모리에서 다시 로딩 안하고 바로 가져다 씀 
> The detailed semantics of `final` fields are somewhat different from those of normal fields. In particular, compilers have a great deal of freedom to move reads of `final` fields across synchronization barriers and calls to arbitrary or unknown methods. Correspondingly, compilers are allowed to keep the value of a `final` field cached in a register and not reload it from memory in situations where a non-`final` field would have to be reloaded.

final은 스펙 상 인스턴스에서 필드가 초기화된 후에 다른 스레드가 접근 가능하도록 강제함.
> An object is considered to be *completely initialized* when its constructor finishes. A thread that can only see a reference to an object after that object has been **completely initialized is guaranteed to see the correctly initialized values** for that object's `final` fields.
만약 이게 사실이면 반드시 초기화 이후에 쓰여져야 하는 다중 스레드에서 접근이 가능한 공통 객체들은 final로 선언하는것이 안전함.
+) 그렇다 하더라도 이게 문제가 되는 경우는 정말 얼마 없을듯함. 근데 해서 손해보는건 딱히 없으니..
물론 오픈jdk는 final 하나라도 들어있으면 해당 객체가 생성 될 때 까지 freeze될 수 있음(jvm spec). 이건 language spec이므로 일단 참고는 하도록 

```java
class FinalFieldExample { 
    final int x;
    int y; 
    static FinalFieldExample f;

    public FinalFieldExample() {
        x = 3; 
        y = 4; 
    } 

    static void writer() {
        f = new FinalFieldExample();
    } 

    static void reader() {
        if (f != null) {
            int i = f.x;  // 3임이 보장됨(final 선언)
            int j = f.y;  // 3일 수도 있고 0일 수도 있음
        } 
    } 
}
```



### 그러므로, final을 선언하면 final-field-safe한 context 내에서는 thread-safe 하다

그렇다. reflection이나 Serializable, System.*, 즉 시스템 차원에서 바꿔버리는 것을 사용하면 또 보장이 안될 수 있다.
aggressive optimization 예제

```java
class A {
    final int x;
    A() {
        x = 1;
    }

    int f() {
        return d(this,this);
    }

    int d(A a1, A a2) {
        int i = a1.x;
        g(a1);
        int j = a2.x;
        return j - i;
    }

    static void g(A a) {
        // uses reflection to change a.x to 2
    }
}
```

이 짓을 하면 f()의 결과는 -1, 0, 1 셋 중 하나가 나온다. 값 보장이 안된다.
> A `final`-field-safe context has additional protections. If a thread has seen an incorrectly published reference to an object that allows the thread to see the default value of a `final` field, and then, within a `final`-field-safe context, reads a properly published reference to the object, it will be guaranteed to see the correct value of the `final` field. In the formalism, code executed within a `final`-field-safe context is treated as a separate thread (for the purposes of `final` field semantics only).


# Word Tearing

byte array의 경우 각 스레드가 서로 다른 곳을 접근하는 경우에 불일치성이 발생할 수 있음.

```java
public class WordTearing {
    long a = 0L;
    
    void thread1() {
        a = 0x0000FFFF;
    }
    
    void thread2() {
        a = 0xFFFF0000;
    }
}
```

이 짓을 하면 `0x0000FFFF`, `0xFFFF0000`, `0x00000000`, `0xFFFFFFFF` 다 가능(랜덤으로)
이건 스펙마다 다를듯. 프로세서가 64비트 cpu면 별 문제없겠지만.. x86 cpu면 두 연산에 걸쳐 해야하므로 문제있을지도..
> Some processors do not provide the ability to write to a single byte. It would be illegal to implement byte array updates on such a processor by simply reading an entire word, updating the appropriate byte, and then writing the entire word back to memory.

### 그리고 64비트 변수의 경우 신경써야할 것이 있음

> For the purposes of the Java programming language memory model, a single write to a non-volatile `long` or `double` value is treated as two separate writes: one to each 32-bit half. This can result in a situation where a thread sees the first 32 bits of a 64-bit value from one write, and the second 32 bits from another write.
> Writes and reads of **volatile** `long` and `double` values **are always atomic.**
> *Some implementations may find it convenient to divide a single write action on a 64-bit **`long`** or **`double`** value into two write actions on adjacent 32-bit values. For efficiency's sake, this behavior is implementation-specific; an implementation of the Java Virtual Machine is free to perform writes to **`long`** and **`double`** values atomically or in two parts.*
> *Implementations of the Java Virtual Machine are encouraged to avoid splitting 64-bit values where possible. Programmers are encouraged to declare shared 64-bit values as **`volatile`** or synchronize their programs correctly to avoid possible complications.*
혹시..32비트씩 읽을 때 long,double같은 64비트 변수가 쪼개져서 읽어지므로 atomic 하지 않을 수도 있다는 우려(우려하는 사람이 사람인가) 때문에 적어놓은듯
실제로 Word Tearing이 일어날 수 있음. 이런 변수의 경우 volatile로 선언해 줘서 원자성 보장



# Synchronized

원래 알고있던 용도 - mutex lock을 걸어서 다른 변수들이 해당 연산 실행하는 동안 변경 못하게 함
그거 말고 또 synchronized 블록 진입 시 해당 스레드에 있는 변수들이 모두 메모리에 있는 값으로 flush 됨
⇒ 스레드간 통신을 지원한다고 볼 수 있음
+) sout이 시간을 많이 먹어서 실제 구현할 때 쓰지 말라고 하는 이유

```java
public void println(String x) {
    synchronized (this) {
        print(x);
        newLine();
    }
}
```

synchronized 블록으로 감싸져 있기 때문!!

```java
public class StopThread {
    private static boolean stopRequested;

    public static void main(String[] args) throws InterruptedException {
        Thread backgroundThread = new Thread(() -> {
            int i = 0;
            while (!stopRequested) {
                i++;
                System.out.println("STOP ?"); //이거 없으면 무한루프 돔
            }
        });
        backgroundThread.start();

        TimeUnit.SECONDS.sleep(1);
        stopRequested = true;
    }
}
```


[https://cjlee38.github.io/post/language/java/2023-03-06-java-memory-model-explained/](https://cjlee38.github.io/post/language/java/2023-03-06-java-memory-model-explained/)

[Weak Memory Model]({% post_url 2023-09-24-Weak Memory Model %})