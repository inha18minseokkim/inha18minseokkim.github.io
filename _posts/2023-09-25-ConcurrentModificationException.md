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

---

### 왜 예외가 발생하는가 - modCount

`ArrayList`(및 `AbstractList` 계열) 내부에는 `modCount`라는 int 필드가 있음. 컬렉션에 **구조적 변경**(add, remove 등 크기 변화)이 일어날 때마다 1씩 증가함.

`iterator()`를 호출하면 Iterator 객체가 생성되는데, 이때 현재 `modCount` 값을 `expectedModCount`로 복사해 기억해둠.

이후 `next()`를 호출할 때마다 내부적으로 `checkForComodification()`을 실행:

```java
// ArrayList.Itr 내부 (OpenJDK 구현)
final void checkForComodification() {
    if (modCount != expectedModCount)
        throw new ConcurrentModificationException();
}
```

`integerList.remove(e)`를 직접 호출하면 `modCount`가 증가하지만 Iterator의 `expectedModCount`는 그대로이므로 불일치 → 예외.
반면 `iterator.remove()`는 삭제 후 `expectedModCount = modCount`로 동기화해주기 때문에 안전함.

이름에 "Concurrent"가 붙어있지만 싱글 스레드에서도 발생하는 이유가 이것. 멀티스레드 상황에서는 더 쉽게 발생하지만 근본 원인은 `modCount` 불일치.

---

### fail-fast

이런 식으로 변경이 감지되는 즉시 예외를 던지는 방식을 **fail-fast** 라고 함. 나중에 예측 불가능한 동작을 하느니 즉시 터뜨리는 게 낫다는 설계 철학.

참고로 `Collections.synchronizedList()`로 감싸거나 `CopyOnWriteArrayList` 같은 컬렉션은 **fail-safe** 방식으로 동작함. 순회 중 수정이 생겨도 예외 대신 복사본을 사용하거나 다른 방식으로 처리.

---

### 해결 방법 정리

**1. iterator.remove() 사용** (위 예제)

**2. removeIf() — Java 8 이상 권장**

```java
integerList.removeIf(e -> e == 2);
```

내부적으로 안전하게 처리해줌. 가장 간결.

**3. 별도 리스트에 모아서 나중에 제거**

```java
List<Integer> toRemove = new ArrayList<>();
for (Integer e : integerList) {
    if (e == 2) toRemove.add(e);
}
integerList.removeAll(toRemove);
```

**4. 멀티스레드 환경이라면 CopyOnWriteArrayList**

```java
List<Integer> list = new CopyOnWriteArrayList<>(integerList);
for (Integer e : list) {
    if (e == 2) list.remove(e); // 수정 시 내부적으로 배열 복사 → 예외 없음
}
```

쓰기마다 배열을 복사하므로 읽기가 훨씬 많은 경우에 적합. 쓰기가 잦으면 성능 부담.

