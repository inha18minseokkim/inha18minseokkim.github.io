---
title: "회사에서 Surface Pro X (ARM+LTE) 개발환경 구성기"
date: 2024-01-01
tags: [ARM, Windows, 개발환경, Surface, WSL, 삽질]
category:
  - 기술
---

회사에 맥북/노트북 반입이 금지되어 있어서 ARM 기반 LTE 모델인 Surface Pro X를 업무용으로 쓰기 시작했다. 세팅하면서 겪은 것들 정리.

## 왜 Surface Pro X인가

1. 회사 내 맥북/노트북 반입 금지
2. 태블릿 정도는 허용 (갤탭, 아이패드 급) → 서피스가 되는지 물어봤더니 뭐라 안해서 그냥 반입
3. 개인 맥북은 USB 유선 테더링으로 쓸 수 있지만, 그래도 회사 정책이 있으니까
4. 인텔 서피스는 발열 심하고 LTE 없어서 ARM 모델인 SPX 선택

## SP9 5G vs SPX SQ2 비교

| 항목 | SP9 5G 16GB | SPX SQ2 16GB |
|------|------------|--------------|
| SoC | Snapdragon SQ3 | Snapdragon SQ2 |
| 연결 | 5G + LTE | LTE |
| 가격 | 200만원 (중고 120만원↑) | 중고 65만원 |
| 긱벤치 | 2배 | 0.5배 |
![이미지](/assets/images/Pasted%20image%2020260219224502.png)
![이미지](/assets/images/Pasted%20image%2020260219224519.png)

![이미지](/assets/images/Pasted%20image%2020260219224527.png)

웹개발 목적으로 200만원짜리 SQ3는 너무 비싸다. SQ3든 SQ2든 x64 에뮬레이션 성능은 쉽지 않으므로 Native 앱 위주로 쓴다고 생각하면 65만원 중고 SPX로도 충분하다.

결론: 갤럭시탭 S7(LTE)를 동생 주고 Surface Pro X(SQ2 16GB)를 65만원에 구입. 알뜰요금제(Liiv M, 월 13,000원) 데이터쉐어링 유심 연결.

---

## 개발 환경 세팅

### 잘 되는 것들

- **IntelliJ / PyCharm / DataGrip**: UWP Native 지원. 완벽하게 잘 됨
- **OpenJDK ARM64 + Python ARM64**: Native 지원
- **WSL2**: Native 지원 → Ubuntu 20 LTS 정상 동작
- **Docker**: WSL2 위에서 가능 (Docker Buildx로 멀티아키 빌드)
  - minikube 대신 K3s 사용 (가벼움)
  - Redis는 Docker로 올림
- **카카오톡**: 32비트 에뮬레이션으로 크게 문제없음(UWP 내부적으로 어느정도 구현되어있는듯, 예전에 윈8 시절에 UWP 카카오톡 있었던것같은데 마소스토어에서 어느순간 사라짐 ㅜㅜ)
- **반디집**: ARM Native 지원
- **MS Office**: 당연히 됨 (MS 제품이니까)

### 브라우저 문제

- **Chrome**: ARM Native 미지원 (2024년 1월 기준)
  - 크롬은 생태계 정치 이슈로 ARM 지원을 미루고 있었음
	  - ([https://www.theverge.com/2024/1/26/24051485/google-chrome-windows-arm-support-canary-channel-test](https://www.theverge.com/2024/1/26/24051485/google-chrome-windows-arm-support-canary-channel-test))
  - → 2024년 1월 Canary 버전에서 ARM 지원 시작
	  - ![이미지](/assets/images/Pasted%20image%2020260219225421.png)
  - → **2024년 5월** 크롬 정식 ARM 버전 출시! 파폭 탈출
- 그전까지는 Firefox 또는 Whale 사용
- Edge는 자꾸 "부모님 허락받고 컨텐츠 보라"고 해서 안씀

구매 결정 후 서피스 프로 x 관련해서 훌륭한 포스팅을 하나 찾음.
[https://megayuchi.com/2019/12/07/프로그래머-관점에서의-surface-pro-x-벤치마크/](https://megayuchi.com/2019/12/07/%ED%94%84%EB%A1%9C%EA%B7%B8%EB%9E%98%EB%A8%B8-%EA%B4%80%EC%A0%90%EC%97%90%EC%84%9C%EC%9D%98-surface-pro-x-%EB%B2%A4%EC%B9%98%EB%A7%88%ED%81%AC/)

[https://armrepo.ver.lt/](https://armrepo.ver.lt/)
여기에 호환 프로그램 목록 있음

### 기타 툴

- **Postman**: 무거운 x64라 안됨 → IntelliJ 플러그인 또는 Postman Canary 사용
	- 24년 말부터 Postman For Windows AArch 출시 이야기 솔솔 나오는 중
		그 전까지는 VSCode 플러그인 사용
		[https://github.com/postmanlabs/postman-app-support/issues/6583#issuecomment-2710743241](https://github.com/postmanlabs/postman-app-support/issues/6583#issuecomment-2710743241)
	- ![이미지](/assets/images/Pasted%20image%2020260219225614.png)
  - 2025년 12월부터 Postman Windows ARM 공식 지원 시작
- **Git**: 공식 ARM 지원은 아니지만 arm64 미러링 프로젝트 사용 가능
	- https://github.com/git-for-windows/git-sdk-64
	- 하지만 2026년 현재는 공식사이트에 win aarch git이 있음
- **한컴오피스**: 당연히 안됨 쓸 필요도 딱히..

---

## 퍼포먼스

웹개발용으로는 충분히 쾌적하다. JDK가 그렇게 무겁지 않아서 IntelliJ 빌드/실행 무리없음.

절전 모드와 발열은 맥보다는 못하지만, 인텔 윈도우보다 훨씬 좋다.
![이미지](/assets/images/Pasted%20image%2020260219224715.png)
이 정도 퍼포먼스 보여준다.


---

## 겪은 이슈들

### WSL Hanging 문제

ARM 환경에서 WSL이 hang되는 버그가 있었다:
- GitHub Issue #10667, #9454
- → 24H2 빌드 이후 해결
![이미지](/assets/images/Pasted%20image%2020260219224731.png)


---
### Windows 11 24H2(ARM) 변경점

![이미지](/assets/images/Pasted%20image%2020260219225702.png)

업데이트 하려 하니 더 이상 32bit ARM은 지원하지않음

---


### MS Office SSO 문제

회사 MS Office SSO가 윈도우 디바이스를 막아놓아서 (모바일 기기만 허용):

**해결책**: WSA(Windows Subsystem for Android)에 Teams, Outlook 앱 설치. 안드로이드 앱으로 인식되어 SSO 통과.

Figma도 같은 방식으로 해결: HTTP 기본 앱을 WSA 내 크롬으로 설정해두면, Figma SSO 클릭 시 안드로이드 크롬으로 열려서 모바일 디바이스로 인식된다.

Teams, Figma, Outlook, Office365 모두 정상 동작.

---

## 2024년 업데이트

- **2024년 5월**: 드디어 Chrome 정식 ARM 버전 출시
- **2024년 말**: Windows 11 24H2 ARM에서 32bit ARM 앱 지원 종료
- **2025년 12월**: Postman Windows ARM 공식 지원 시작
