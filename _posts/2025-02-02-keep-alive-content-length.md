---
title: "Keep Alive + Content Length를 잘못 세팅하면 벌어지는 일"
date: 2025-02-02
tags: [HTTP, 백엔드, 삽질, MSA, Spring]
---

갑자기 생각나서 글 써봄 (20250202)

3달 전쯤에 mediation 파드를 만들 때 Header Propagation을 하려고 하던 중, 가끔(아니 자주) 요청들이 5번 이상 와바박 호출되는 현상이 발생했었다.

구현한 방식은 이랬다:

1. 클라이언트로부터 온 헤더를 K,V 쌍으로 모두 forEach 돌린다
2. 현재 ThreadLocal 객체 변수에다가 "모두" 다 집어넣는다
3. 다른 파드로 호출 시 requestInterceptor에서 ThreadLocal 변수에 있던 값들을 헤더에 적재해서 호출한다

이렇게 하니 갑자기 어떤 호출의 경우 한 번 호출했는데 말단 파드로 여러 번 연속해서 호출하는 경우가 나왔다.

생각해보니 클라이언트에서 가져왔던 헤더를 모두 다 넘겨주는데, **넘겨주면 안 되는 정보들**이 있었다.

그 중 하나가 `Content-Length`.

`Content-Length`의 경우 body 길이를 호출할 때 계산해서 헤더에 적재하는데, 내가 Propagation을 통해 이전 요청의 Content-Length를 그대로 넘겨버리면 실제 body size와 내가 임의로 적어서 제출한 Content-Length가 달라진다.

**Keep-Alive를 사용하는 경우 정확한 Content-Length를 사용해야 한다.**

Keep-Alive 커넥션에서는 다음 요청이 같은 커넥션을 재사용하는데, 이때 Content-Length를 기준으로 body의 끝을 판단한다. Content-Length가 실제 body보다 작으면 다음 요청의 일부를 현재 응답 body로 착각하고, 커넥션이 이상하게 동작하게 된다.

아마 이것 때문에 Content-Length 만큼 body가 들어오지 않아 커넥션이 닫히지 않은 상태에서 뭔가 잘못 작동해서 호출이 여러 번 나간 듯 하다.

---

**결론**: Header Propagation 구현 시 아래 헤더들은 전파하면 안 된다.

- `Content-Length` — body 길이는 각 요청마다 다르게 계산되어야 함
- `Transfer-Encoding` — chunked 인코딩 정보
- `Host` — 대상 서버 주소
- `Connection` — keep-alive 설정

상위 레이어에서 내려온 헤더를 무분별하게 Propagation하지 말고, 필요한 헤더만 허용 리스트(allowlist) 방식으로 골라서 넘기는 게 안전하다.
