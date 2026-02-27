---
title: EAI 전문 조립 관련
date: 2023-12-26
tags:
  - HTTP
  - 개발
category:
  - 실무경험
  - Network
---

외부 API 연동 시 EAI를 경유하는 구조에서 발생한 제약사항과 해결 방식 정리.

---

### 불가능한 것

**1. 행내 메타 기준 임의 변경**
- 외부(오픈API)에서 수신한 컬럼 값을 행내 시스템에서 바로 사용하려면, 어딘가에서 행내 메타 표준 Entity로 매핑해주는 로직이 필요하다.
- 이 매핑 작업 없이 오픈API 원문 컬럼명을 그대로 사용하는 것은 사실상 불가.

**2. DDL 자동화**
- 테이블을 직접 DDL로 선언한 뒤 메타 신청을 거쳐야 하므로, 자동화 적용 불가.

**3. EAI를 경유하지 않고 외부와 직접 통신**
- 망분리 규제로 인해 외부 통신은 반드시 EAI를 경유해야 한다.
- EAI 대외 담당자가 보안성 심의 통과 및 방화벽 예외 신청을 진행해야 한다.
- EKS에 연결된 VPC 내부에서도 동일하게 적용:
  - ❌ `Egress → Remote` (직접 통신 불가)
  - ✅ `Egress → Kbank IOC → EAI → Remote → EAI → Ingress`

---

### 가능한 것

**JSON → JSON 릴레이 (EAI openApi 솔루션 경유)**

행내 통신 표준이 fixedLength 전문 규격이므로, EAI 담당자에게 전문 스펙을 전달하여 변환 처리를 위임한다.

**AS-IS (fixedLength 방식):**
1. 업무 앱 → EAI: fixedLength로 전송
2. EAI openApi 솔루션: fixedLength를 JSON으로 매핑 → 외부에 JSON으로 전송
3. 외부 → EAI: JSON 수신 → fixedLength로 매핑 → 업무 앱에 전달
4. 업무 앱: fixedLength를 DTO로 매핑

**TO-BE (JSON 방식, 개발 완료):**
- EAI openApi 솔루션의 JSON to JSON 기능을 활용.
- EAI 호출 시 HTTP Body를 JSON 원문 String 그대로 수신.
- 업무 애플리케이션에서 Jackson으로 직접 매핑 처리.
- 방화벽 신청 등 보안 절차는 기존과 동일하게 필요.

---

### 개발 완료 후 추가 발견된 문제

**EAI OOM 이슈 (응답 바디 1MB 초과 시)**

JSON 방식으로 전환 후, EAI에서 **1MB 이상의 바디 전문을 수신하면 OOM이 발생**하는 문제가 확인됐다.

**사용 가능 조건:**
1. 페이징 처리를 통해 응답 바디를 **1MB 미만**으로 유지할 수 있는 경우
2. 호출 빈도가 낮은 경우 (**10 TPS 이상 요청 시 중간 유실 발생**)

두 조건을 모두 충족하는 경우에만 JSON Body 방식 사용을 권장.
