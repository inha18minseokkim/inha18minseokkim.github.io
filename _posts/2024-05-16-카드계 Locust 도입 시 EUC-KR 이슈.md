---
title: 카드계 Locust 도입 시 EUC-KR 이슈
date: 2024-05-16
tags:
  - Java
  - BXM
  - 케이뱅크
category: 실무경험
---

### 문제상황

MSA 환경에 올라가는 서비스 테스트시 사용하는 Locust를 카드계에서도 사용해보자
문제점은 MCI → 카드계 어댑터는 Body에 json이 아닌 fixedLength 방식으로 데이터를 보낸다.
즉, MCI(fixedLength) → Crdap (fixedLength → Json, 따지고보면 여기가 컨트롤러) → Bxm Service(Json) 으로 되는 구조
FixedLength를 사용하기 때문에 MCI → CrdAp로 POST 요청 시 헤더에 tlgrLen과 MCIIntfId 등을 보냄. tlgrLen → 뒤에 따라오는 POST Body(통문자열) 길이, MCIIntfId → 전문 스펙에 대한 정보
그래서 Crdap에서 MCIIntfId 보고 전문 메타정보 가져와서 길이에 맞게 잘라 json으로 변환함

BC카드 발급하는 프로세스 부하 테스트가 필요하다고 하는데 할 줄 아는사람이 나밖에 없어서 무슨일인가 알아보고 있었는데, 자꾸 Crdap 공통부문에서 길이가 안맞다고 함;;

### 원인

BXM omm(DTO) 파일의 길이 산정방식과 파이썬에서 사용하는 길이 산정방식이 다르기 때문.
BXM omm 파일에서 필드를 선언할 때 길이를 100으로 한다는것 → 100바이트로 한다는 것
Bxm은 오라클 기준으로 길이를 통일시켜놓은듯.
그래서 오라클 기준 영어숫자특수문자 → 1바이트, 한글 → 3바이트로 길이를 친다.
하지만 파이썬은 그런거 없이 len 사용하면 모두 1
tlgrLen(뒤따르는 총 전문 길이) 를 Locust에서 보낼 때 단순 len(line_data)를 하여서 파이썬에서는 모두 평등하게 1로 보냄
하지만 Crdap에서 봤을 때 한글을 3바이트로 자르니 정확하게 한글 숫자 * 2 의 길이 만큼 안맞다고 뜸.

### 해결방법

일단은 한글 개수 * 2 를 더하면 맞기 때문에 파이썬 정규표현식을 사용하여 리퀘스트를 보내기 전에 전문 길이를 약간 조작해주는 식으로 변경
ASIS

```java
header_raw['tlgrLen'] = str(sum(self.sizes) + len(line_data) 
- self.sizes[0]).zfill(self.sizes[0])
```

TOBE

```java
header_raw['tlgrLen'] = str(sum(self.sizes) + len(line_data) 
- self.sizes[0] + len(re.findall("[ㄱ-ㅎㅏ-ㅣ가-힣",line_data)*2).zfill(self.sizes[0])
```


인스턴스가 늘어나면 regex compile 하는 부분 공통으로 뺄 예정
