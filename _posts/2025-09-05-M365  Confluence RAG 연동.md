---
title: "M365 <> Confluence RAG 연동"
date: 2025-09-05
tags: [미지정]
category: 기타
---
Confluence 문서 RAG 사용을 위해 M365와 Confluence api간 3LO 인증수행해야하는데 절차 정리함


![](attachment:1dee3b5e-e221-4279-8b3a-2c6f63e521f6:image.png)

M365 Admin 에서 Conectores > ConfluenceCloud Connection 추가 

![](attachment:db371901-1322-4882-a66b-0794171c74d3:image.png)

3LO 인증 수행 해야하는데 여기서 Atlassian 에서 M365 콜백 url을 등록해줘야함

[https://developer.atlassian.com/console](https://developer.atlassian.com/console)
에서 Myapp 가서 앱 아무거나 하나 만들어

![](attachment:64949287-69ca-4d1e-8005-acb4025360ad:image.png)

3LO로 인증할 수 있도록 셋팅

![](attachment:c527a7a1-6787-4ce7-b06f-47d75aee1e76:image.png)

Authorization 가서 Callback URL 에
[https://gcs.office.com/v1.0/admin/oauth/callback](https://gcs.office.com/v1.0/admin/oauth/callback)
입력 후 밑에 Granular Confluence API authorization URL로 인증을 수행하던가
M365 Confluence 설정 화면(oauth 로그인 하는곳) 에 가서 로그인하면 됨

![](attachment:74c92e90-95ad-4a00-a32e-cd664c64e691:image.png)

이렇게 Ready 상태가 되어야 함

![](attachment:3ce5b2be-76cf-44fd-bc19-86274316eb6a:image.png)

knowledge 에 컨플루언스를 등록해주면 됨
