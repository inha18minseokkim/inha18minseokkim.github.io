---
title: "푸시메세지 조립 - 한국어 종성과 조사 처리"
date: 2023-03-01
tags: [Java, 한국어, 알고리즘, 삽질]
category: 기술
---

푸시 알림 메시지를 조립할 때 한국어 조사 처리가 필요했다. "OO 님이 를/을 구매했습니다" 같은 케이스.

## 한글 유니코드 구조

- 초성: 19자
- 중성: 21자
- 종성: 28자 (종성 없음 포함)

핵심 개념: 진수와 비트마스킹처럼 자릿수를 빼면 초/중/종성을 분리할 수 있다.

```java
char lastName = name.charAt(name.length() - 1);
int index = (lastName - 0xAC00) % 28;
```

`0xAC00`는 유니코드에서 '가'에 해당한다. `(글자 - 0xAC00)`를 28로 나눈 나머지가 종성 인덱스다.

- 나머지가 0이면 받침 없음 (모음 종성)
- 나머지가 1~27이면 자음 받침

---

## 조사 케이스

푸시메시지에서 조합이 필요한 케이스는 3가지다:

### 1. 를/을

- 받침 없으면 → **를**
- 받침 있으면 → **을**

### 2. 로/으로

- 받침 없으면 → **로**
- ㄹ 받침이면 → **로** (예외!)
- 그 외 받침 있으면 → **으로**

### 3. 이/가

- 받침 없으면 → **가**
- 받침 있으면 → **이**

---

## 로/으로 예외 처리

"로/으로"의 경우 국립국어원 기준:

> "조사 '으로'는 'ㄹ'을 제외한 받침 있는 체언 뒤에 붙는 반면 조사 '로'는 받침 없는 체언이나 'ㄹ' 받침으로 끝나는 체언 뒤에 결합합니다."

즉 "서울로", "달로"는 ㄹ 받침이라 "로"를 쓰고, "학교로"처럼 받침 없으면 "로", "집으로"처럼 다른 받침이면 "으로"다.

종성 인덱스에서 ㄹ은 8번이다 (0xAC00 + 8 = '갈'의 받침 인덱스).

---

## 구현 예시

```java
public String getParticle(String word, String withConsonant, String withoutConsonant) {
    char lastChar = word.charAt(word.length() - 1);
    int jongseong = (lastChar - 0xAC00) % 28;
    return jongseong == 0 ? withoutConsonant : withConsonant;
}

// 를/을
String particle = getParticle(itemName, "을", "를");

// 이/가
String particle = getParticle(userName, "이", "가");

// 로/으로 (ㄹ 예외 처리 필요)
public String getRoParticle(String word) {
    char lastChar = word.charAt(word.length() - 1);
    int jongseong = (lastChar - 0xAC00) % 28;
    if (jongseong == 0) return "로";      // 받침 없음
    if (jongseong == 8) return "로";      // ㄹ 받침
    return "으로";                         // 그 외 받침
}
```

---

## 느낀 점

한국어 처리는 영어 기반 라이브러리에서 기본 제공되지 않는 케이스가 많아서 직접 구현해야 하는 경우가 종종 있다. 유니코드 구조를 이해하면 생각보다 간단하게 처리할 수 있다.
