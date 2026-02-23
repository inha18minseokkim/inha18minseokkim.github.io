---
title: "Combinator"
date: 2023-08-19
tags: [미지정]
---

```java
static <A,B,C> Function<A,C> compose(Function<B,C> g, Function<A,B> f) {
	return x-> g.apply(f.apply(x));
}

```

따지고보면 f*g(x) = f(g(x)) ⇒ h(x) 로 변환한 느낌
함수 자체를 객체(Function<I,O>)로 만들어서 중첩형식으로 사용하는 것.

```java
static <A> Function<A,A> repeat(int n, Function<A,A> f) {
	return n == 0 ? x -> x : compose(f,repeat(n-1,f));
}

repeat(3,(Integer x) -> 2 * x);
//이런식으로 x^2^2^2 구현 가능
```

