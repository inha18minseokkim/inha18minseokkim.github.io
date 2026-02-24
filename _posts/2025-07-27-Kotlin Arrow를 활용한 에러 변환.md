---
title: Kotlin Arrow를 활용한 에러 변환
date: 2025-07-27
tags:
  - Kotlin
  - arrow
---
[[Optics/Lens] 내 멋대로 Optics 이해하기 Feat) arrow-kt](https://see-ro-e.tistory.com/333)
함수형 프로그래밍 공부중인데 코틀린에서 변환을 좀 자동화해주는


### isomorphism


![[Pasted image 20260225083420.png]]

둘은 대수적으로 같음
**동형**은 "A 구조의 데이터를 B 구조로, 그리고 그 반대로 완전히 변환할 수 있다"는 관계
즉, A의 모든 정보가 B에 모두 들어 있으며, B로부터 다시 A를 완전히 복원할 수 있음
**`Pair<String, String>`**과 **`SampleClass(fieldA: String, fieldB: String)`**은 필드 개수, 타입이 같다 보니 서로 변환이 자유롭고, 되돌릴 수도 있음

```kotlin
@optics data class AnimeCharacter(val name: String, val career: String) {
    companion object
}

val conan = AnimeCharacter("코난", "탐정")
val conanTuple = ("코난" to "탐정")

val iso: Iso<AnimeCharacter, Pair<String, String>> = AnimeCharacter.iso

iso.get(conan) // Pair("코난", "탐정")
iso.reverseGet(conanTuple) // AnimeCharacter("코난", "탐정")
```


## 왜 이게 중요한가?

FP(함수형 프로그래밍) 스타일에서는 "구조가 완전히 동일한 두 타입 간에는 자유롭게 전환 가능하다"는 특성을 활용
복잡한 구조의 데이터도, 더 단순한 표현(튜플, 리스트 등)으로 바꿨다 다시 원래 구조로 되돌릴 수 있어, 데이터 변환 및 가공 로직이 깔끔.


### 그러므로 오류 처리를 한번 해보자


```kotlin
Either<UserError, User>
```

Either는 코틀린 Arrow에서 제공해주는 라이브러리
Left > 실패, Right > 성공으로 타입 구분해줌

```kotlin
import arrow.core.Either
import arrow.core.left
import arrow.core.right

data class User(val id: Int, val name: String, val age: Int)
sealed class UserError {
    object NotFound : UserError()
    object InvalidAge : UserError()
}

// 예외 대신 값으로 에러를 반환
fun findUser(id: Int): Either<UserError, User> =
    if (id == 42) User(42, "Alice", 27).right()
    else UserError.NotFound.left()

fun validateAge(user: User): Either<UserError, User> =
    if (user.age >= 0) user.right()
    else UserError.InvalidAge.left()

// 함수형 스타일로 에러/성공 체이닝
val result: Either<UserError, User> =
    findUser(10).flatMap { user -> validateAge(user) }

when (result) {
    is Either.Right -> println("사용자 정보 OK: ${result.value}")
    is Either.Left -> when (result.value) {
        UserError.NotFound -> println("사용자를 찾을 수 없습니다.")
        UserError.InvalidAge -> println("나이 정보가 유효하지 않습니다.")
    }
}
```

try catch와 비교

```kotlin
fun findUser(id: Int): User {
    if (id == 42) return User(42, "Alice", 27)
    throw UserNotFoundException()
}

fun validateAge(user: User): Boolean {
    if (user.age >= 0) return true
    throw IllegalArgumentException("Invalid age!")
}

// 에러가 반드시 try-catch로 예외처리 강제됨
try {
    val user = findUser(10)
    validateAge(user)
    println("사용자 정보 OK")
} catch (e: Exception) {
    println("에러: ${e.message}")
}

```


## 코틀린 Arrow의 함수형 에러 핸들링과의 차이점 및 이점(GPT)

**Arrow의 Either, Validated**를 활용한 에러 핸들링은 자바의 전통적 방식에 비해 다음과 같은 장점이 있습니다.
**런타임 예외가 아닌 타입 기반(컴파일 타임) 에러 처리**
Arrow의 **`Either`**는 함수 반환값에 에러를 **명시적으로 타입**으로 선언하므로, 호출 시 항상 성공/실패를 고려한 분기 처리가 강제됩니다.
자바/Spring의 예외(Exception)는 생략되거나, 예외 누락이 발생할 위험이 있습니다.
**체이닝 및 조합의 편리함**
Arrow의 **`map`**, **`flatMap`**, **`fold`** 등 함수형 연산자(모나딕 체이닝)를 통해 여러 비즈니스 로직을 우아하게 연결할 수 있습니다.
자바에서는 try-catch 블록이 중첩되거나, 반복적으로 사용되어 복잡도가 증가할 수 있습니다.
**여러 에러 축적 (Validated)**
Arrow의 **`Validated`**는 폼 검증처럼 여러 필드의 에러를 **모아 한 번에 보고**할 수 있습니다.
자바에서는 에러 리스트를 직접 관리해야 하고, 불변성을 보장하기 어렵습니다.
**가독성·유지보수성 향상**
함수형 스타일은 비즈니스 로직과 에러 처리를 분리해 **가독성**이 좋아지며, 에러 흐름이 명확하게 드러납니다.
자바는 try-catch의 난립·깊은 중첩, 예외 전파 등으로 가독성이 떨어질 수 있습니다.
**테스트 용이성**
Arrow 기반 함수는 결과가 데이터로 반환되어 자동화 테스트가 쉽고, 예외 상황 확인이 직관적입니다.


### 굳이 Try Catch를 쓰지말고 저런식으로 해야하는 이유?


| **try-catch 문제점** | **에러값 반환의 장점** |
| --- | --- |
| 예외가 어디서 터질지 예측하기 어렵다 | 호출부에서 에러처리를 강제한다 |
| 여러 비즈니스 흐름에 중첩된 try-catch | 간단한 체인(map/flatMap)으로 연결 가능 |
| 성능상 비용 발생 (예외 처리는 비쌈) | 값 처리이므로 성능 부담 줄어듦 |
| 예외 타입 관리가 어려움 | 에러 타입을 명확하게 설계 가능 |
| 예외 누락으로 런타임 에러 가능 | 컴파일에서 빠진 에러 처리 잡아냄 |

결론 - 작은 프로젝트나 영향도가 적은곳에서는 그냥 try catch 사용하자. 다만 현재 내가 맡고있는 다양한 Datasource로의 호출이 있고 처리가 있다면 이렇게 하는것도 나쁘지 않을듯?