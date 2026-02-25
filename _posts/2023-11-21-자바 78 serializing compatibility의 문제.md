---
title: 자바 7/8 serializing compatibility의 문제?
date: 2023-11-21
tags:
  - Java
  - Spring
  - 이슈정리
  - BXM
  - 케이뱅크
---
결론 : 없음, java 7과 8에서 언어가 지원하는 것들이 대폭 커지기는 했는데 바이트코드 스펙이 달라지진 않음. 애초에 그러니깐 8환경에서 7이 돌아가는건가?
[https://stackoverflow.com/questions/46322740/serialization-compatibility-java-7-8](https://stackoverflow.com/questions/46322740/serialization-compatibility-java-7-8)
그리고 저번에 bxm서버에서 런타임으로 java 8 문법이 들어간 클래스 로딩이 가능했음
결국은.. 라이브러리에서 버전 올라올 때 문제인데

aspectj 버전 - 1.6.11
asm 버전 - 3.3.1 

처방 : spring 버전을 업그레이드..

저 파일들만 업그레이드 못하는지 알아봐야할듯
