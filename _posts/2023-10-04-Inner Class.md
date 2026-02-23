---
title: "Inner Class"
date: 2023-10-04
tags: [미지정]
---

```java
public class OuterClass {
	private int number = 10;
	
	void printNumber() {
		InnerClass innerClass = new InnerClass();
	}

	private class InnerClass {
		void doSomething() {
			System.out.println(number);
			OuterClass.this.printNumber();
		}
	}

	public static void main(String[] args) {
		InnerClass innerClass = new OuterClass().new InnerClass();
		innerClass.doSomething();
	}
}
```

