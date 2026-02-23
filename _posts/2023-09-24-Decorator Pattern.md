---
title: "Decorator Pattern"
date: 2023-09-24
tags: [미지정]
---
상속 단점으로 인해 Wrapper Class를 만들고 본 기능은 위임해서 쓰는 패턴

![](https://prod-files-secure.s3.us-west-2.amazonaws.com/c38aebd7-2834-4fac-b2fc-a2f0c17ce81d/5978a99f-230b-41a1-83aa-779fa015982a/Untitled.png)


내부 구현을 신경쓰지 않아도 됨 - 실제로 상속으로 구현하는 경우 내부 구현을 신경쓸 수 밖에 없는 경우가 있지만 Composition의 경우 진짜로 브릿지만 제공하고 추가기능을 얹는 식으로 개발하기 때문에 신경안써도됨

```java
// 코드 18-1 잘못된 예 - 상속을 잘못 사용했다! (114쪽)
public class InstrumentedHashSet<E> extends HashSet<E> {
    // 추가된 원소의 수
    private int addCount = 0;

    public InstrumentedHashSet() {
    }

    public InstrumentedHashSet(int initCap, float loadFactor) {
        super(initCap, loadFactor);
    }

    @Override public boolean add(E e) {
        addCount++;
        return super.add(e);
    }

    @Override public boolean addAll(Collection<? extends E> c) {
        addCount += c.size();
        return super.addAll(c);
    }

    public int getAddCount() {
        return addCount;
    }

    public static void main(String[] args) {
        InstrumentedHashSet<String> s = new InstrumentedHashSet<>();
        s.addAll(List.of("틱", "탁탁", "펑"));
        System.out.println(s.getAddCount());
    }
}
```

내부구현에 의존하고 영향을 받는 코드

```java
// 코드 18-2 래퍼 클래스 - 상속 대신 컴포지션을 사용했다. (117-118쪽)
public class InstrumentedSet<E> extends ForwardingSet<E> {
    private int addCount = 0;

    public InstrumentedSet(Set<E> s) {
        super(s);
    }

    @Override public boolean add(E e) {
        addCount++;
        return super.add(e);
    }
    @Override public boolean addAll(Collection<? extends E> c) {
        addCount += c.size();
        return super.addAll(c);
    }
    public int getAddCount() {
        return addCount;
    }

    public static void main(String[] args) {
        InstrumentedSet<String> s = new InstrumentedSet<>(new HashSet<>());
        s.addAll(List.of("틱", "탁탁", "펑"));
        System.out.println(s.getAddCount());
    }
}
```


```java
// 코드 18-3 재사용할 수 있는 전달 클래스 (118쪽)
public class ForwardingSet<E> implements Set<E> {
    private final Set<E> s;
    public ForwardingSet(Set<E> s) { this.s = s; }

    public void clear()               { s.clear();            }
    public boolean contains(Object o) { return s.contains(o); }
    public boolean isEmpty()          { return s.isEmpty();   }
    public int size()                 { return s.size();      }
    public Iterator<E> iterator()     { return s.iterator();  }
    public boolean add(E e)           { return s.add(e);      }
    public boolean remove(Object o)   { return s.remove(o);   }
    public boolean containsAll(Collection<?> c)
                                   { return s.containsAll(c); }
    public boolean addAll(Collection<? extends E> c)
                                   { return s.addAll(c);      }
    public boolean removeAll(Collection<?> c)
                                   { return s.removeAll(c);   }
    public boolean retainAll(Collection<?> c)
                                   { return s.retainAll(c);   }
    public Object[] toArray()          { return s.toArray();  }
    public <T> T[] toArray(T[] a)      { return s.toArray(a); }
    @Override public boolean equals(Object o)
                                       { return s.equals(o);  }
    @Override public int hashCode()    { return s.hashCode(); }
    @Override public String toString() { return s.toString(); }
}
```


문제점 - 콜백 프레임워크와 셀프

```java
class BobFunction implements FunctionToCall {

    private final Service service;

    public BobFunction(Service service) {
        this.service = service;
    }

    @Override
    public void call() {
        System.out.println("밥을 먹을까..");
    }

    @Override
    public void run() {
        this.service.run(this);
    }
}
```


```java
public class BobFunctionWrapper implements FunctionToCall {

    private final BobFunction bobFunction;

    public BobFunctionWrapper(BobFunction bobFunction) {
        this.bobFunction = bobFunction;
    }

    @Override
    public void call() {
        this.bobFunction.call();
        System.out.println("커피도 마실까...");
    }

    @Override
    public void run() {
        this.bobFunction.run();
    }
}
```


```java
public class Service {

    public void run(FunctionToCall functionToCall) {
        System.out.println("뭐 좀 하다가...");
        functionToCall.call();
    }

    public static void main(String[] args) {
        Service service = new Service();
        BobFunction bobFunction = new BobFunction(service);
        BobFunctionWrapper bobFunctionWrapper = new BobFunctionWrapper(bobFunction);
        bobFunctionWrapper.run();
    }
}
```


결국 여기서 Wrapper든 아니든 FunctionToCall을 호출했음. 다만 wrapper 에서

```java
    @Override
    public void run() {
        this.bobFunction.run();
    }
```

self를 호출하면서 wrapper의 call은 실행되지 않음(예제가 적절한지는 잘 모르겠음)
해결책으로는 총 세가지가 떠오름

처음부터 그럼 run에 

```java
    @Override
    public void run() {
        this.bobFunction.call();
        System.out.println("커피도 마실까...");
    }
```

이렇게 적었어야 할듯. 다만 이러면 클래스 본연의 의도대로 작성이 안되긴 할듯.
왜 FunctionToCall을 Wrapper도 implement한지 모르겠다(아마 같은 프레임워크를 돌기 때문이라고 추측, 만약에 그렇지 않으면 캐스팅에서 문제가 생길테니..)
Wrapped된 class의 레퍼런스 제공

```java
public class BobFunctionWrapper {

    private final BobFunction bobFunction;

    public BobFunctionWrapper(BobFunction bobFunction) {
        this.bobFunction = bobFunction;
    }
		public BobFunction getInstance() {
				return this.bobFunction;
		}

    public void run() {
				this.bobFunction.call();
        System.out.println("커피도 마실까...");
        this.bobFunction.run();
    }
}
```

이 예제에서는 적절한 예제는 아닌것같음(타입이 달라져버림).. 아무튼 이런식으로 다룰 수 있는 케이스도 있다고 생각함.
그냥 Wrapped 된 클래스에서 Wrapper의 존재를 알도록 하자
이건 그냥 말도 안되는 소리인것같음(LSP 위배)
