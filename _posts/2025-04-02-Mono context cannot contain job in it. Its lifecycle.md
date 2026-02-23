---
title: "Mono context cannot contain job in it. Its lifecycle"
date: 2025-04-02
tags: [미지정]
---

```kotlin
Flux.merge(
		listOf(listedStocks,overseasStocks,etfs)
			.map{
			it.asMono(coroutineContext)
				.flatMapAny{
						Flux.fromIterable(it)
			}
		}
	)
```

3개의 List를 반환받아서,, 개별의 리스트가 큰데 3개를 한번에 리턴하기에는 메모리가 뻑나는 경우가 있음.
그래서 Flux로 뿌려주는 방향을 검토한다고 샘플코드를 짰음.


## Mono context cannot contain job in it. Its lifecycle

응답은 200으로 잘 떨어졌는데, mediator 파드에서 위 에러가 떨어졌다.

자세히 찾아보니 다음과 같이 바꾸면 됨.

```kotlin
Flux.merge(
		listOf(listedStocks,overseasStocks,etfs)
			.map{
			it.asMono(Dispatcher.IO)
				.flatMapAny{
						Flux.fromIterable(it)
			}
		}
	)
```

또는

```kotlin
Flux.merge(
		listOf(listedStocks,overseasStocks,etfs)
			.map{
			it.asMono(EmptyCoroutineContext)
				.flatMapAny{
						Flux.fromIterable(it)
			}
		}
	)
```


사유를 찾아보니 Mono, Flux는 자바 리액티브 스트림인데 여기서 코루틴 컨텍스트를 포함해서 생긴 일이었다.
asMono() 를 호출하면 코틀린 Deferred , Job 객체를 Mono로 바꾸어줌.
Dispatcher와 Job은 코루틴 컨텍스트


### Mono와 Flux는 EmptyCoroutineContext와 함께 사용할 때 문제없음

EmptyCoroutineContext가 추가적인 생명 주기 관리를 하지 않기 때문.
코루틴 단순히 실행할때 컨텍스트 지정하지 않으니 리액티브 스트림 스레드 관리 방식과 충돌X
즉 EmptyCoroutineContext = 디스패쳐가 지정되지 않아 리액티브 스트림 생명주기를 다루지 않아 충돌 안하는것

### Dispatcher

코루틴 실행될 스레드 관리하는 역할.
[Dispatchers.IO](http://Dispatchers.IO) : I/O 작업용 스레드 풀
Dispatchers.Default: CPU 작업용 스레드 풀
리액티브 스트림에서 Dispatcher 사용 가능. 
Dispatcher는 코루틴이 어디에서 실행될지를 관리하지 리액티브 스트림의 스케줄링, 데이터 흐름을 방해하지 않기 때문.
코루틴 내에서 사용되는 디스패처는 실행되는 스레드 관리만 함. 리액티브 스트림 비동기 데이터 흐름과는 독립적으로 동작



## CoroutineCotext를 asMono()에 넣으면 오류나는 이유?


### ChatGPT의 말:


### ❓ **현재 ****`coroutineContext`****를 ****`asMono()`****에 넣으면 오류가 나는 이유?**

오류 메시지:
> "Mono context cannot contain job in it. Its lifecycle is managed externally"
이 오류가 발생하는 이유는 **코루틴 컨텍스트 (****`coroutineContext`****)에 포함된 ****`Job`****이 ****`Mono`****의 생명주기와 충돌하기 때문**입니다.

---


### ✅ **1. ****`coroutineContext`****에는 ****`Job`****이 포함됨**

코루틴이 실행될 때 `coroutineContext`는 기본적으로 **코루틴의 실행 컨텍스트를 포함**합니다.
이 컨텍스트에는 **현재 실행 중인 `Job`**이 포함되어 있습니다.
예를 들어, 코루틴 내에서 `coroutineContext`를 출력해 보면:

```kotlin
import kotlinx.coroutines.*

fun main() = runBlocking {
    println(coroutineContext)
}


```

출력 예시:

```
[BlockingCoroutine{Active}@6b884d57, JobImpl{Active}@1d44bcfa]
```

여기서 **`JobImpl{Active}`**가 포함된 것을 볼 수 있습니다.
🚨 **문제점**:
`asMono(coroutineContext)`를 호출하면, **현재 코루틴의 ****`Job`****이 포함된 컨텍스트**를 `Mono`에 넘기려고 합니다.
하지만 **`Mono`****는 자체적인 생명주기를 관리**하므로, **코루틴의 ****`Job`****을 포함하면 충돌이 발생**합니다.
따라서 `Mono`에서는 `"Mono context cannot contain job in it"` 오류가 발생합니다.
