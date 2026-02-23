---
title: "Exception"
date: 2023-09-05
tags: [미지정]
---

## Checked  

RuntimeException 하위 예외는 아니면서 Exception의 하위, try/catch or throws 선언하여 핸들링 필요

## unChecked

RuntimeException, 실행 중에 발생할 수 있는 예외. 핸들링이 강제는 아님

모든 예외는 똑같지만 컴파일러에서 체크 유무로 나뉨(잡아서 던지는건 같다)

### Unchecked를 사용해야 하는 이유(try-catch를 쓰는것이 강제도 아니고 throws를 선언해야 하지도 않는데 써야 하는 이유)

Client 또는 말단에서 해당 로직을 호출했을 때 의도치 않은 동작을 수행했으니 뭔가를 다시 시도하라는 느낌으로 명시적으로 알려줄 수 있음.
너무 많은 Exception 처리는 코드 가독성을 해칠 수 있기 때문에 보통 Checked만 처리하는것이 국룰이라고 함.


### 기본적으로 런타임 예외를 던진다

체크 예외는 잘 안쓰는게 트렌드라 함
비즈니스 로직 상 의도적으로 던지는 경우 쓴다함
ex) 계좌이체 실패 시 던져서 캐치하고 복구하는 로직구현
실수로 예외를 놓치면 안된다고 판단, 컴파일러 단에서 잡아줄 수 있음
그렇다고 꼭 체크예외 쓰라는건아니다

### 체크예외 문제점 - 예외 전파에 의한 의존

SQLException, ConnectException 같은 중대한 결함이 있는 경우 체크 예외 사용
그렇다고 해서 이런 문제들은 대부분 어플리케이션 로직에서 실행할 수 있는것도 아님. 시스템단에서 오는 DB 연결 네트워크 연결 같은게 문제가 생기면 웹어플리케이션 단에서 처리할 수가 없다 대체로.. 그냥 문제가 생겼어요 웹페이지 정도 보여주는게 다일듯
ex) Repository에서 던지는 SQLException → 서비스 비즈니스 메서드에서 throws 선언 → 컨트롤러에서도 throws 
이런식으로 되면 저 throws ?Exception에 로직들이 의존하게 됨. → 나중에 뜯어고쳐야 할 수도(SQLException → JPAException 으로 바꿔야 한다면)
웹어플리케이션이면 ControllerAdvice를 해서 예외 공통 처리할것
사용자들은 여러 종류의 예외를 봐도 뭐 어쩌라고 라고 하거나 정보유출 되는 정도일 것.

### Exception을 그냥 던진다면

일단 의존성 문제는 해결이 된다
하지만 모든 예외를 다 던져 구체적인 예외 던지기를 못한다.. 의도대로 동작 안함
이런식으로 변환가능(stackTrace 물고가서 던질 때 담아서 던져야함)

```java
static class Repository {
  public void call() {
      try {
          runSQL();
      } catch (SQLException e) {
          throw new RuntimeSQLException(e);
      }
  }

  public void runSQL () throws SQLException {
      throw new SQLException("ex");
  }
}
```
