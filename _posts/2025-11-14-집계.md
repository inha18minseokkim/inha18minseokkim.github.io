---
title: "집계"
date: 2025-11-14
tags:
  - 개발
  - 기획
  - 주식서비스
category:
  - 실무경험
---
주식 게임 서비스 개발 및 기획 논의 정리.
### 주중

1. 집계 전 gameId, gameBaseDate 기준으로 모든 랭킹 테이블 데이터 날림(평소에는 당연히 0건만 날림)
2. 주식 뽑은 개수가 0명이면 집계 제외
  1. 수익률 계산 시 뽑은 날짜 계산방법
    1. 뽑은 gameDate 보다 작거나 같은 날짜 중 가장 최근 개장일
    2. min(processDate, gameEndDate) 보다 작거나 같은 날짜 중 가장 최근 개장일
  2. 만약 날짜가 i > ii 면 해당 수익 제외 
    1. 해당 케이스는 수동으로 과거의 랭킹을 집계하는 경우 해당 됨(미래에 뽑은 주식 제외해야 하기 때문)
3. sql partition 활용해서 랭킹 데이터 생성
  1. processDate 의 랭킹이란? processDate 전일 종가 기준 수익률

### 주말

1. 집계 전 현재 진행중인 유효한 게임의 상태를 OPEN > COUNTING으로 바꿈 (shutdown)
2. 주중 집계 배치 실행
  1. game의 최종 집계 기준일자는 gameEndDate, 즉 금요일
3. 리워드 생성 작업 실행
4. gameId에 해당하는 game의 processDate 랭킹을 가져옴
  1. gameEndDateTime이 아니라 processDate를 사용하는 이유는 혹시 gameEndDate 사이에 무슨 일이 있어서 조기샤따운 하려면 processDate를 지정해서 수요일 기준으로 랭킹을 매겨서 리워드를 지급하던가 해야함
5. (beforeStep) 해당 랭킹에서 1등인 사람만 골라서 총 명수를 구함
  1. 인원수가 0명 이하면 throw
6. 총상금 / 명수를 해서 1인당 리워드 금액을 구하여 jobExecution에 넣음
7. chunk로 gameId 의 게임에 gameBaseDt 가 processDate이며 1등에 해당하는 사람들을 가져옴 
8. rgstDt에 processDate를 넣고 아까 만든 1인당 리워드 금액을 넣고 batch Write 함
9. (afterStep) gameId, gameBaseDate에 해당하는 리워드들의 sum을 가져와서 총 상금 금액보다 작거나 같으면 delete 하고 ExitStatus.FAILED
10. 성공했으면 이대로 game status를 COUNTING 상태로 두다가 월요일 아침 10시에 COUNTING> OPEN 하면서 다음 게임 시작
