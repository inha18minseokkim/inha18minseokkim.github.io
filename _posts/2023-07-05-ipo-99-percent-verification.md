---
title: "공모주 크롤링 99.99% 검증완료 + 로직 개선"
date: 2023-07-05
tags: [삽질, 공모주, 크롤링, Python, OpenDart, 케이뱅크]
category:
  - 재테크
---

일단 가지고 있는 대략 천건의 파일 중 이슈가 있는 세 건(공시자료가 최신버전이라 과거 공시자료를 찾아야 하지만 기업 이름이 달라 못찾음, 실제로 최초로 받는 건은 과거공시자료일 것이므로 문제없음)

과 2019년 이전(파일데이터를 찾을 수 없음, 금감원이 5년 초과 데이터는 xml로 안줌) 건들 빼고는 모두 파싱이 완료된 상태이다.

<details>
<summary>길어</summary>

```
/Users/kimminseok/PycharmProjects/openDartDocumentParser/venv/bin/python /Users/kimminseok/PycharmProjects/openDartDocumentParser/main.py
1079
2023-10-28 23:09:48.463 | INFO     | __main__:<module>:18 - 케이비제22호스팩 탐색 시작
2023-10-28 23:09:48.505 | INFO     | __main__:<module>:21 - 20220908000411.xml  /케이비제22호기업인수목적/케이비제22호스팩
2023-10-28 23:09:48.558 | INFO     | __main__:<module>:24 - ['증권발행조건확정            ']
2023-10-28 23:09:48.559 | ERROR    | __main__:<module>:26 - 현재 최신 공시자료에서 찾을 수 없음. 과거 공시파일 로딩중
2023-10-28 23:09:48.796 | DEBUG    | parser.pastReport:loadPastReportReceptNumber:10 - 케이비제22호스팩 의 기업코드 : 01672053
2023-10-28 23:09:48.805 | DEBUG    | parser.pastReport:loadPastReportReceptNumber:14 - 해당 기업의 수요예측시작일자 - 1년 전일 기준으로 리포트 목록 조회 시작 : 20210905 ~ 20231028
2023-10-28 23:09:48.919 | DEBUG    | parser.pastReport:loadPastReportReceptNumber:24 - {'status': '000', 'message': '정상', 'group': [{'title': '일반사항', 'list': [{'rcept_no': '20220805000213', 'corp_cls': 'K', 'corp_code': '01672053', 'corp_name': '케이비제22호스팩', 'sbd': '2022년 09월 13일 ~ 2022년 09월 14일', 'pymd': '2022년 09월 16일', 'sband': '2022년 09월 13일', 'asand': '2022년 09월 16일', 'asstd': '-', 'exstk': '-', 'exprc': '-', 'expd': '-', 'rpt_rcpn': '-'}]}, {'title': '증권의종류', 'list': [{'rcept_no': '20220805000213', 'corp_cls': 'K', 'corp_code': '01672053', 'corp_name': '케이비제22호스팩', 'stksen': '기명식보통주', 'stkcnt': '5,000,000', 'fv': '100', 'slprc': '2,000', 'slta': '10,000,000,000', 'slmthn': '일반공모'}]}, {'title': '인수인정보', 'list': [{'rcept_no': '20220805000213', 'corp_cls': 'K', 'corp_code': '01672053', 'corp_name': '케이비제22호스팩', 'stksen': '기명식보통주', 'actsen': '대표', 'actnmn': '케이비증권', 'udtcnt': '5,000,000', 'udtamt': '10,000,000,000', 'udtprc': '350,000,000', 'udtmth': '총액인수'}]}, {'title': '자금의사용목적', 'list': [{'rcept_no': '20220805000213', 'corp_cls': 'K', 'corp_code': '01672053', 'corp_name': '케이비제22호스팩', 'se': '공모예치자금', 'amt': '10,000,000,000'}, {'rcept_no': '20220805000213', 'corp_cls': 'K', 'corp_code': '01672053', 'corp_name': '케이비제22호스팩', 'se': '발행제비용', 'amt': '-'}]}]}
```

</details>
