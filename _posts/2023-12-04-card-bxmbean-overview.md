---
title: 카드계 BxmBean에 대하여
date: 2023-12-04
tags:
  - Java
  - Spring
  - BXM
  - 삽질
  - 이슈정리
  - 케이뱅크
category:
  - 실무경험
  - BXM
---
이거 대체 뭔지 모르겠음
기존 개발 방식 말고 다른 방식으로 개발하다가
생성자주입 → 못해. 생성자주입을 하려 했는데 대상클래스.class 를 KbankApplicationContext.getBean(대상클래스.class) 하려고 하니 NoSuchBeanDef가 뜸. 있는데.. 
set 주입 → spring bean이 아니라 bxm bean임. 여기는 NoSuchBeanDef는 안뜨는데 ClassCastException이 뜸.

일단 ClassCastException이 떴다는것 (pkg.Class 타입을 com.sun.proxy 로 변환할 수 없다) 이런것은 jdk dynamic proxy를 사용했을 때 나타나는 문제인 것으로 암


김영한 아저씨의 Aspectj 강의를 듣고나서 확실히 이해가 가긴 했다.
