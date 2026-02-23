---
title: "ConcurrentModificationException"
date: 2023-09-25
tags: [미지정]
---


## default 메서드 문제점

바뀌면 안되는데 바뀌어버리는것 - 인터페이스 변경을 통해 기존에 상속받고 있던 하위 클래스에 강제로 메서드 주입 가능. 하위 클래스 개발자가 의도하지 않은 동작 할 수 있음. 해당 default 메서드를 오버라이딩 해서 의도한 동작을 하도록 해야 함
그럼 디폴트 메서드가 있어야 하는 이유가 없음
sync 된 환경에서 동작하는 하위 클래스인데 상위 클래스에서 sync를 고려하지 않은 디폴트 메서드를 호출 시 ConcurrentModificationException

싱글 스레드 상황

```java
public static void main(String[] args) throws InterruptedException {
        List<Integer> integerList = new ArrayList<>();
        integerList.add(0);
        integerList.add(1);
        integerList.add(2);
        integerList.add(3);
        integerList.add(4);
        for(Integer e : integerList){
            if(e == 2) integerList.remove(e);
        }
        System.out.println(integerList);
    }
```

for문 내부에 iterator가 integerList를 사용하는 경우에 iterator가 모르는 컬렉션에서 수정을 하면 문제 발생
iterator에서 지우면 괜찮음

```java
public static void main(String[] args) throws InterruptedException {
        List<Integer> integerList = new ArrayList<>();
        integerList.add(0);
        integerList.add(1);
        integerList.add(2);
        integerList.add(3);
        integerList.add(4);
        Iterator<Integer> iterator = integerList.iterator();
        while(iterator.hasNext()){
            if(iterator.next() == 2){
                iterator.remove();
            }
        }
        System.out.println(integerList);
    }
```

