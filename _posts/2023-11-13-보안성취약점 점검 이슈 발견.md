---
title: 보안성취약점 점검 이슈 발견
date: 2023-11-13
tags:
  - Java
  - 이슈정리
  - 케이뱅크
category:
  - 실무경험
  - BXM
---
정보성 아닌 내용 단순 랜덤 선택하는 로직 짜던 중 그냥 이거 씀

```javascript
Integer randomIndex = ((int)Math.random()*1000)) % pushContentList.size();
```

해당 코드 랜덤 안정성 문제 있다고 해서 바꾸라고 함
다음과 같이 바꿈

```javascript
Random rand = SecureRandom.getInstanceStrong();
Integer randomIndex = rand.nextInt(1000) % pushContentList.size();
```

똑같은 에러남(?!)
다시 바꿈

```javascript
Integer randomIndex = SecureRandom.getInstanceStrong().nextInt(1000) % pushContentList.size();
```

근데 됨(?)

문의 결과
보안성취약점 점검 간에 랜덤 관련 오탐이 발생해서 예외처리를 해놓았는데 
예외처리 빼고 해결하는 과정에서 또 오탐이 발생한 듯 함.
언젠간 고쳐줄듯함.. 아무튼 소스코드 문제는 아니었던걸로



### 번외) 시드값의 안정성

[https://stackoverflow.com/questions/11051205/difference-between-java-util-random-and-java-security-securerandom](https://stackoverflow.com/questions/11051205/difference-between-java-util-random-and-java-security-securerandom)
요약
1. 시드값을 랜덤으로 지정한다고 해서 랜덤 알고리즘이 안전해지는것은 아니다
2. 기존 랜덤 값은 LCG(선형 합동 생성기)를 통해 만들어진다
3. 근데 이건 쉽게 뚫린다 함. 심지어 합동 사이클 다 몰라도 탄착군 좁히듯이 좁혀지는듯
  - [https://ko.wikipedia.org/wiki/선형_합동_생성기](https://ko.wikipedia.org/wiki/%EC%84%A0%ED%98%95_%ED%95%A9%EB%8F%99_%EC%83%9D%EC%84%B1%EA%B8%B0)

```c++
#include <stdint.h>

uint32_t lcg_rand(uint32_t a)
{
    return ((uint64_t)a * 279470273) % 4294967291;
}
```

4. 저런 느낌의 함수에서 시드값 기준을 클럭에서 뽑아와서 쉽게 재현이 가능하다 함
5. [https://resources.infosecinstitute.com/topics/application-security/random-number-generation-java/](https://resources.infosecinstitute.com/topics/application-security/random-number-generation-java/)
6. seureRandom 쓰면 하드웨어 단에서 제공하는 시드값에서 엔트로피를 획득한 후 유사 난수 생성
