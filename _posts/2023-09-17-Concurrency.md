---
title: Concurrency
date: 2023-09-17
tags:
  - Java
  - 동시성
  - 개발
category:
  - 기술
---

```java
private int hashCode;
@Override
public int hashCode() {
	int result = hashcode;
	if(result == 0) {
		result = Short.hashCode(areaCode);
		result = 31 * result + Short.hashCode(prefix);
		result = 31 * result + Short.hashCode(lineNum);
		hashCode = result;
	}
	return result;
}
```


Race condition 문제
여러 스레드가 동시에 위 함수에 접근해버린다면..? ex) result = Short.hashCode(areaCode)를 어떤 스레드1이 실행한 후 2스레드가 막 if문에 진입한다면
⇒ 의도하지 않은 동작 가능

synchronized를 쓴다면?

```java
@Override
public synchronized int hashCode() {
	int result = hashcode;
	if(result == 0) {
		result = Short.hashCode(areaCode);
		result = 31 * result + Short.hashCode(prefix);
		result = 31 * result + Short.hashCode(lineNum);
		hashCode = result;
	}
	return result;
}
```

잘 동작 하지만 클래스에서 해당 메서드를 통으로 선언해버리면 병목현상 일어날 수도
그나마 나은 방법은

```java
private int hashCode;	
@Override
public int hashCode() {
	int result = hashcode;
	synchronized(this) {
		if(result == 0) {
			result = Short.hashCode(areaCode);
			result = 31 * result + Short.hashCode(prefix);
			result = 31 * result + Short.hashCode(lineNum);
			hashCode = result;
		}
		return result;
	}
}
```

이런 식으로 특정 스코프에서만 thread safe 하도록 함
또는 이런식으로

```java
private volatile int hashCode;
```

cpu 캐시가 아니라 메모리의 값 그대로를 참조하여 race condition 문제 해결 가능

+) 자동으로 Thread Safe를 보장하고 싶다면 HashMap이 아닌 HashTable을 사용하기
