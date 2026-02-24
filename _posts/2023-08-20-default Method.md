---
title: "default Method"
date: 2023-08-20
tags: [미지정]
---
인터페이스에서 구현된 함수의 대안


### 인터페이스에 메서드를 추가하면?

바이너리 호환성은 유지됨. 새로 추가된 메서드를 호출하지만 않으면 새로운 메서드 구현 없이도 기존 클래스 파일은 잘 동작.


### 디폴트 메서드


```java
public interface sized {
	int size();
	default boolean isEmpty() {
		return size() == 0;
	}
}
```

소스 호환성도 유지된다.
기존 
- 신규 메서드 추가 → 그럼 그걸 implements한 클래스들은 수동으로 다 구현해줘야함
- 그게 현실적으로 안됨 → 상속받는 클래스에서 빈 구현체를 구현해야만 함 → ?? 
- 그럼 추상 클래스로 만들자 → 추상 클래스와 자바8 인터페이스 엄밀히 다름
디폴트 메서드가 있으면
- 호환성 유지 가능
- 기본 구현 제공 하여 구현하는 클래스에서 빈 구현 추가 안해도 됨

```java
interface Iterator<T> {
	boolean hasNext();
	T next();
	default void remove() {
		throw new UnsupportedOperationException();
	}//이런식으로 기본구현해놓음
} 
```

- 구현부가 있지만 클래스가 아니라 인터페이스이기 때문에 여전히 다중 상속 가능(클래스는 단일상속만 가능)

다중상속 시 인터페이스 & 클래스 동일 시그니처 메서 우선순위
1. 클래스가 항상 이김
2. 클래스가 없으면 더 자식인 인터페이스가 이김(더 구체적인 인터페이스)
3. 그럼에도 안되면 명시적으로 디폴트 메서드 오버라이드 후 호출

인터페이스에서는 toString, hashCode, equals default로 정의 불가능
왜?
Object의 것과 implement 하는 인터페이스의 것중 뭐가 우선순위인지 몰라
애초에 인터페이스에는 멤버가 없을텐데 선언해놓는 의미가 없음
다중 인터페이스 구현하는 경우에 뭐가 우선?
[ConcurrentModificationException]({% post_url 2023-09-25-ConcurrentModificationException %})
