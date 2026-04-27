---
title: 하네스 엔지니어링 까지는 아니고 목줄 엔지니어링
date: 2026-04-26
tags:
  - AI/ML
  - 개발환경
category:
  - 실무경험
---

팀 프로젝트에서 Claude Code를 써서 실제 서비스를 개발해봤는데, 그냥 "AI한테 코드 짜달라고 했다"가 아니라 나름의 워크플로우를 갖춰서 진행했던 과정을 정리해봄.

---

## 배경

금융 사내망(RND망) 환경이라 Docker도 못 쓰고, `googleapis` SSL 오류 때문에 Claude Code 일반 설치도 안 됨. 이런 제약 속에서 팀 3인이 게임 서비스를 AI 보조로 개발해야 했음. 그래서 그냥 아예 외부에서 개발함

---

## 전체 워크플로우

```
요구사항 정의 (자연어)
   ↓
rnd-wiki에 스펙 문서 작성
(requirements.md → domain-spec.md / erd-spec.md / api-spec.md)
   ↓
CLAUDE.md 작성 (AI 컨텍스트 주입)
   ↓
GitHub Issue 생성 (milestone + label 필수)
   ↓
Claude Code에게 Issue 번호 기반으로 구현 지시
   ↓
PR (Closes #N) → 머지
```

---

## 핵심 파트별

### rnd-wiki — 스펙의 단일 진실 공급원

별도 레포(`rnd-wiki`)를 스펙 문서 전용으로 운영했음.

- `requirements.md`: 기획자가 자연어로 작성한 날것의 요구사항
- 이걸 구조화해서 `domain-spec.md` / `erd-spec.md` / `api-spec.md` 세 문서로 분리
- `arcade-service`에는 `sync-docs.sh`로 복사본만 두고, 수정은 무조건 rnd-wiki에서만

requirements.md 원문은 이런 식임.

> "사용자의 닉네임 정보 필요, 가입할 때 받는건 아니고 내부 계정계를 호출해서 닉네임을 가져옴. 이걸 가입할 때 적재할것"

이걸 AI한테 그냥 던지면 안 되고, 구조화된 스펙 문서로 변환해서 넘겨야 함. GitHub Actions로 README 목차 자동 갱신도 걸어뒀음.

---

### CLAUDE.md — AI에게 건네는 사원증 + 사규

**CLAUDE.md가 없으면 Claude Code는 빈손으로 작업하는 거랑 같음.** 이 프로젝트에서 CLAUDE.md에 담은 내용:

| 항목           | 내용                                                                     |
| ------------ | ---------------------------------------------------------------------- |
| 스펙 문서 위치     | `../rnd-wiki/spec/*.md`가 원본, `docs/`는 사본                               |
| 기술 스택        | JDK 21 / Kotlin 2.1 / Spring Boot 4.0 / **JPA 금지** (Spring Data JDBC만) |
| 패키지 구조       | `api/` / `domain/` / `infrastructure/` 레이어별 명세                         |
| 레이어 규칙       | `domain/`에 Spring import 절대 금지, `data class` 금지                        |
| 컬럼 네이밍       | `arcd_` prefix vs `alco_` prefix 구분, 구버전 약어 사용 금지 목록                   |
| GitHub 워크플로우 | Issue 먼저 생성 → 브랜치 → PR (Closes #N) 순서 강제                               |
| 보안 원칙        | HMAC timing-safe compare, secret 하드코딩 금지                               |
| 미결 사항        | 임의 결정 금지 항목 명시 ("반드시 사용자에게 물어볼 것")                                     |

**AI가 "알아서 판단"하면 안 되는 경계를 명시적으로 선언한 것이 핵심**이었음. 특히 미결 사항 섹션 — 여기 적혀있는 항목은 Claude가 절대 임의로 결정 못 하고 반드시 물어보도록 강제함.

---

### GitHub Issue 템플릿 — 티켓의 구조화

두 가지 템플릿을 만들어서 씀.

**feature 이슈** — 구현 작업용

```
목적 / 작업 범위 (체크리스트) / 기술 결정 사항 / 참고 문서 / 완료 조건(DoD)
```

**blocked 이슈** — 외부 의사결정 대기용

```
미결 사항 요약 / 배경 / 선택지 Trade-off 표 / 결정권자 / 결정 기한 / 영향받는 이슈
```

PR 템플릿도 `개요 / 기술 결정 및 근거 / Trade-off / 미결 사항 / Closes #N` 구조로 통일.

**`blocked` 이슈 타입을 따로 만든 게 의외로 효과적**이었음. "지금 결정 안 된 것"을 가시화해서 AI가 미결 상태에서 임의로 코드 짜는 걸 막는 장치 역할을 함.

---

### 아키텍처 — 헥사고날로 경계 강제

```
api/            ← Controller + Service + DTO
domain/         ← 순수 POJO (Spring/JDBC import 금지)
infrastructure/ ← JDBC Entity / Mapper / Repository / HTTP Client
```

`domain/`을 순수하게 유지하는 건 AI가 코드 짤 때 가장 자주 어기는 규칙 중 하나임. 방심하면 `@Component`나 `@Repository` 같은 거 도메인 클래스에 붙여버림.

CLAUDE.md에 **"data class 금지, 명시적 생성자 호출"** 규칙을 명시해두고, Claude Code memory에도 따로 기록해서 대화가 끊겨도 계속 적용되도록 했음.

---

### 사내망 환경 제약 극복

설치부터가 문제였는데, `rnd-wiki/guides/claude-code-setup.md`에 팀 공유용 가이드 작성해둠.

- Claude Code 바이너리 직접 다운로드 → `~/.local/bin/`에 배치
- `NODE_TLS_REJECT_UNAUTHORIZED=0` 환경변수로 사내 SSL 우회
- Gradle도 `-Djavax.net.ssl.trustStoreType=WINDOWS-ROOT`로 해결

---

## 실제 구현 도메인

6개 핵심 도메인을 Issue 단위로 쪼개서 구현함.

| 도메인 | 역할 |
|---|---|
| User | 가입·탈퇴·닉네임 (soft delete) |
| Game Content | 제휴사·게임·이벤트 기준정보 CRUD |
| Event Reception | Blomics S2S 포스트백 수신 + HMAC 검증 + 멱등성 |
| Campaign | 리워드 한도 체크 + Outbox 패턴으로 Kafka 발행 |
| Ranking | 캠페인 단위 랭킹, 제휴사 API 연동 |
| Invitation | 친구 초대 관계 등록 |

---

## 마무리

해보면서 느낀 것들:

- **CLAUDE.md를 잘 쓰는 것 자체가 팀 아키텍처 결정을 문서화하는 행위임.** AI한테 설명하려고 쓰는 건데, 결국 팀 전체의 개발 기준서가 됨
- **"임의 결정 금지" 항목을 명시하는 게 중요함.** AI가 판단할 영역과 못 할 영역을 분리해야 함. 안 그러면 AI가 알아서 채워버리는데 나중에 발견하면 골치 아픔
- **스펙 문서와 코드 레포를 분리해야 함.** 스펙이 코드에 섞이면 AI가 참조할 원본이 불명확해짐
- **blocked 이슈로 불확실성을 가시화하면 좋음.** 미결 상태로 코드 짜는 것 자체를 프로세스로 막을 수 있음
- **사내망 같은 제약 환경에서도 AI 도구 도입은 가능함.** 설치 가이드 문서화가 핵심