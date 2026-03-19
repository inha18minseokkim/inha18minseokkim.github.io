---
title: "집계 후 푸시 발송"
date: 2025-11-14
tags:
  - 개발
  - 기획
  - 주식서비스
category:
  - 실무경험
---
주식 게임 서비스 개발 및 기획 논의 정리.
### 집계대상이란?

집계 테이블에 하나라도 존재하면 집계 대상이라고 하자
그렇다면 현재로서는 a(gameEndDt에 존재하는 모든 고객들)을 대상이라고 보면 된다
a + 푸시 동의한 고객 join
  - gameEndDt를 직접 쓰지 말고 processDate가 월요일이니깐 processDate.minusDays(1L)을 사용하자
  - 왜냐하면 또 gameEndDt 보다 더 빨리 게임이 끝날 수도 있으니깐
