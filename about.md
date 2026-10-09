---
layout: default
title: About
permalink: /about
---
<section class="about-section">
  <div class="container about-container">

    <div class="about-header">
      <div class="about-title-block">
        <h1 class="about-name">김민석<span class="dot">.</span></h1>
        <p class="about-role">Backend Developer</p>
        <p class="about-company">케이뱅크</p>
      </div>
      <div class="about-contact">
        <a href="mailto:bjm7701@naver.com" class="contact-link">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="20" height="16" x="2" y="4" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/></svg>
          bjm7701@naver.com
        </a>
        <a href="https://github.com/inha18minseokkim" target="_blank" rel="noopener" class="contact-link">
          <svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.745 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"/></svg>
          GitHub ↗
        </a>
      </div>
    </div>

    <div class="about-body">

      <div class="about-intro">
        <p>Java/Kotlin 백엔드 개발자. 주식 서비스 BFF 레이어 구현을 주도했고, Spring WebFlux와 Kotlin 코루틴을 직접 공부해서 실무에 도입했음. 복잡한 MSA 환경에서 어떻게 하면 더 읽기 쉽고 효율적인 코드를 짤 수 있는지 계속 고민 중.</p>
      </div>

      <div class="about-section-block">
        <h2 class="about-section-title">Core Competencies</h2>
        <ul class="about-exp-desc">
          <li><strong>MSA · EKS 서비스 설계/운영:</strong> IDC 레거시와 EKS 연계, Spring Cloud Gateway, BFF 패턴, 헥사고날 아키텍처</li>
          <li><strong>Kafka 기반 EDA · 데이터 파이프라인:</strong> 폐쇄망 대외 데이터 수신 파이프라인, 계정계 입출금 비동기화, Transactional Outbox</li>
          <li><strong>배치 · CI/CD 표준화:</strong> 정기작업 솔루션과 Argo Workflow/Kubernetes 잡 연동 표준, KEDA, Helm</li>
          <li><strong>모니터링 · 로깅 표준:</strong> 데브옵스와 Spring Boot 로깅 표준 합의, traceId 전파, 커넥션 풀·idle-timeout 장애 분석</li>
        </ul>
      </div>

      <div class="about-section-block">
        <h2 class="about-section-title">Experience</h2>
        <div class="about-exp-item">
          <div class="about-exp-header">
            <span class="about-exp-company">케이뱅크 혁신 서비스 백엔드 개발</span>
            <span class="about-exp-period">2023.01 ~ 현재</span>
          </div>
          <span class="about-exp-role">Backend Developer</span>
          <div class="about-proj-list">

            <div class="about-proj-item">
              <p class="about-proj-title">eBPF 기반 Spring Boot 애플리케이션 로깅 표준 수립 <span class="about-exp-period">(2026.08 ~ 진행 중)</span></p>
              <p class="about-proj-role">역할: 개발 측 표준 협의 (데브옵스와 공동 수립)</p>
              <p class="about-exp-tech">Spring Boot, Spring WebFlux, Kotlin Coroutines, Spring Cloud Gateway</p>
              <ul class="about-exp-desc">
                <li>데브옵스와 Spring Boot 로깅 표준 합의 (<strong>행내 EKS 애플리케이션 전체</strong> 대상)</li>
                <li>eBPF 수집 전환에 맞춰 OTel 에이전트 제거, traceId 전파를 MDC·CoroutineContext·SCG에서 직접 구현</li>
              </ul>
              <p class="about-proj-link">관련 글: <a href="/2026/08/26/stock-mediation-499-part5/">Reactor에서 MDC가 안 찍히는 이유 (traceId 전파 시리즈)</a></p>
            </div>

            <div class="about-proj-item">
              <p class="about-proj-title">주간 투자왕 서비스 리뉴얼 <span class="about-exp-period">(2026.08 ~ 진행 중)</span></p>
              <p class="about-proj-role">역할: 백엔드 단독 개발</p>
              <ul class="about-exp-desc">
                <li>기존 주간 투자왕 서비스에 한국 시장 리그 추가</li>
              </ul>
            </div>

            <div class="about-proj-item">
              <p class="about-proj-title">게임 라운지 서비스 개발 <span class="about-exp-period">(2026.04 ~ 2026.07)</span></p>
              <p class="about-proj-role">역할: 설계 주도</p>
              <p class="about-exp-tech">Java 21, Spring Boot, Spring Data JDBC, Kafka, Aurora PostgreSQL</p>
              <ul class="about-exp-desc">
                <li><strong>배경:</strong> 주간 투자왕에 입출금 처리 로직이 흩어져 있었고, 서비스 DB 저장과 Kafka 발행이 별개로 동작해 한쪽만 성공하면 리워드가 누락될 수 있었음. <strong>순간 TPS 400</strong> 수준을 버티는 것을 목표로 설계</li>
                <li>JDK 21 Virtual Thread와 헥사고날 아키텍처에 맞는 Spring Data JDBC로 기술 스택 전환</li>
                <li>Transactional Outbox 적용. Aurora wal_level 제약으로 CDC 대신 크론잡 기반 Polling 방식 채택</li>
                <li>헥사고날 아키텍처로 주간 투자왕에 흩어져 있던 입출금 처리 로직을 하나로 통합</li>
                <li><strong>성과:</strong> 계정계 순단 시에도 게임 서비스들이 정상 동작하도록 구조 변경</li>
              </ul>
              <p class="about-proj-link">관련 글: <a href="/2026/05/15/aurora-debezium-cdc-to-polling/">Aurora에서 Debezium CDC 포기하고 Polling으로 간 이야기</a></p>
            </div>

            <div class="about-proj-item">
              <p class="about-proj-title">주식 서비스 DDD 리팩토링 <span class="about-exp-period">(2025.12 ~ 2026.03)</span></p>
              <p class="about-proj-role">역할: 주식 서비스 주담당자로서 구조 개선</p>
              <p class="about-exp-tech">Kotlin, Spring Boot</p>
              <ul class="about-exp-desc">
                <li>공모주 메이트, 해외주식/ETF 서비스를 MDD + MVC 구조에서 DDD + 헥사고날 구조로 리팩토링</li>
                <li>stock-customer-service RESTful 리팩토링 및 도메인 통합 테스트 작성</li>
                <li>폐쇄망 환경에서 사내 AI 모델로 테스트 코드 작성과 리팩토링 공수 절감</li>
              </ul>
            </div>

            <div class="about-proj-item">
              <p class="about-proj-title">주간 투자왕 서비스 개발 <span class="about-exp-period">(2025.06 ~ 2025.12)</span></p>
              <p class="about-proj-role">역할: 설계 참여</p>
              <p class="about-exp-tech">Kotlin, Spring WebFlux, R2DBC, Kafka</p>
              <ul class="about-exp-desc">
                <li><strong>배경:</strong> 계정계 동기 호출 구조라 계정계 지연 시 EAI 적체로 행 전체에 영향</li>
                <li>대량 트래픽 처리를 위해 Spring WebFlux와 R2DBC 도입, 논블로킹 I/O 기반으로 DB 병목 제거</li>
                <li>Kafka 기반으로 계정계 입출금 연동을 비동기화해 계정계 호출 부하 분산</li>
                <li>고객 ID를 파티션 키로 사용해 고객별 순서 보장, 중복 처리 방지</li>
                <li>헥사고날 아키텍처 도입으로 도메인 로직과 인프라 간 결합 해제</li>
              </ul>
            </div>

            <div class="about-proj-item">
              <p class="about-proj-title">투자홈/투자캘린더 서비스 개발, 고도화 <span class="about-exp-period">(2024.04 ~ 2025.07)</span></p>
              <p class="about-proj-role">역할: BFF 설계 및 구현 주도</p>
              <p class="about-exp-tech">Kotlin Coroutines, Spring WebFlux, Kafka, KEDA</p>
              <ul class="about-exp-desc">
                <li>폐쇄망 대외기관 API 제약(<strong>10 TPS</strong>)을 극복하기 위해 Kafka 기반 OpenAPI 수신 파이프라인 구축</li>
                <li>데이터 수신 Pod에 KEDA를 적용해 EKS 자원 효율화</li>
                <li>주식 도메인 하위 업무(공모주, 비상장 등) 간 복잡도를 낮추기 위해 BFF 패턴 설계·적용</li>
                <li>FeignClient/WebClient, Reactor/Virtual Thread 비교 실험 후 Kotlin 코루틴 + WebFlux 채택</li>
              </ul>
              <p class="about-proj-link">관련 글: <a href="/2024/10/10/mediation-pattern-where-is-the-common-handler/">mediation 패턴 도입기 시리즈</a></p>
            </div>

            <div class="about-proj-item">
              <p class="about-proj-title">MSA 배치 실행 표준화 (정기작업 솔루션 ↔ Kubernetes 잡 연동 개선) <span class="about-exp-period">(2024.09 ~ 2025.02)</span></p>
              <p class="about-proj-role">역할: 표준 수립 주도</p>
              <p class="about-exp-tech">Spring Boot, Spring Batch, Argo Workflow, Kubernetes, KEDA, Helm, GitLab CI</p>
              <ul class="about-exp-desc">
                <li><strong>배경:</strong> 2023년 최초 연동 시 배치 하나당 프로젝트 하나를 만드는 구조로 구성되어, 1년 만에 서브도메인별 배치 프로젝트가 5개, 많게는 30개까지 늘어남. 행내 배치 표준이 jar 기동 방식이라 IDC 정기작업 솔루션에서 EKS를 트리거하려면 점프호스트 쉘 호출만 가능했음</li>
                <li>맥미니 홈서버에 구축해 둔 Minikube에서 Argo Workflow 연동 구조를 먼저 POC한 뒤 내부망 서버에 반영</li>
                <li>@ConditionalOnProperty에 파라미터를 전달해 특정 잡 빈만 기동하는 JobLauncher 표준을 만들어 한 프로젝트에서 다수의 잡을 관리, 가이드 문서화</li>
                <li>데브옵스 엔지니어와 협의해 CI 스크립트가 폴더 단위로 N개의 workflow yaml을 배포하도록 개선, KEDA ScaledObject 배포용 Helm Chart 구성</li>
                <li>점프호스트 스크립트용 CI 파이프라인 신설, 데브옵스·개발팀 역할 분리</li>
                <li><strong>성과:</strong> 서브도메인별 배치 프로젝트 5~30개 → 1~2개로 통합, 현재 다른 팀에서도 사용 중</li>
              </ul>
              <p class="about-proj-link">관련 글: <a href="/2024/10/20/first-complete-version/">@ConditionalOnProperty 기반 잡 실행 표준 + Argo Workflow 템플릿</a> · <a href="/2024/08/19/regrets-and-apologies/">배치 1:1 구조의 문제와 개선 방향</a></p>
            </div>

            <div class="about-proj-item">
              <p class="about-proj-title">비상장 주식 서비스 구축 및 레거시-MSA 연동 아키텍처 개선 <span class="about-exp-period">(2024.03 ~ 2024.04)</span></p>
              <p class="about-proj-role">역할: 백엔드 핵심 설계 및 일정 조율 주도</p>
              <p class="about-exp-tech">Java/Kotlin, Spring Boot, Spring Cloud Gateway, JPA</p>
              <ul class="about-exp-desc">
                <li>IDC 대외계와 EKS 환경 연결을 위해 EAI-OpenAPI 릴레이 구조 도입</li>
                <li>Spring Cloud Gateway와 Redis 간 불필요한 연동을 파악·제거해 장애 시 가용성 확보</li>
              </ul>
            </div>

            <div class="about-proj-item">
              <p class="about-proj-title">초기 서비스 개발 및 MSA 전환 <span class="about-exp-period">(2023.01 ~ 2024.01)</span></p>
              <p class="about-proj-role">역할: 개발 참여</p>
              <p class="about-exp-tech">Java 17, Spring Boot 3, PostgreSQL, Docker, Kubernetes, Kafka</p>
              <ul class="about-exp-desc">
                <li>공모주 메이트, 식품물가 알림, 돈나무 키우기 등 신규 서비스 백엔드 개발</li>
                <li>계정계/카드계 포털 관리자 화면 및 푸시 배치 기능 개발</li>
                <li>MSA 추진 TF에서 레거시 시스템을 Spring Boot 3, PostgreSQL 환경으로 마이그레이션</li>
              </ul>
            </div>

          </div>
        </div>
      </div>

      <div class="about-section-block">
        <h2 class="about-section-title">Troubleshooting</h2>
        <div class="about-proj-list">
          <div class="about-proj-item">
            <p class="about-proj-title">주식 BFF 간헐적 499 원인 분석 <span class="about-exp-period">(2026.06 ~ 2026.08)</span></p>
            <p class="about-proj-role">역할: 원인 분석 및 조치</p>
            <ul class="about-exp-desc">
              <li>원인: SCG의 <strong>idle-timeout 1초 설정</strong>으로 커넥션이 먼저 끊김 → 제거 후 구간별 idle-timeout 정합, SCG 재시도 추가</li>
              <li>분석 중 발견한 커넥션 풀 고갈도 함께 해결</li>
              <li>남은 499는 실제 에러가 아닌 eBPF 트레이싱 노이즈임을 확인</li>
            </ul>
            <p class="about-proj-link">관련 글: <a href="/2026/08/17/stock-mediation-499-part1/">stock-mediation 499 트레이싱 삽질 (1~4부)</a></p>
          </div>
        </div>
      </div>

      <div class="about-section-block">
        <h2 class="about-section-title">Tech Stack</h2>
        <div class="about-stack-grid">
          <div class="about-stack-group">
            <span class="stack-label">Language</span>
            <div class="stack-tags">
              <span class="stack-tag main">Kotlin</span>
              <span class="stack-tag main">Java</span>
            </div>
          </div>
          <div class="about-stack-group">
            <span class="stack-label">Framework</span>
            <div class="stack-tags">
              <span class="stack-tag main">Spring Boot</span>
              <span class="stack-tag main">Spring WebFlux</span>
              <span class="stack-tag">Kotlin Coroutines</span>
              <span class="stack-tag">Spring Cloud Gateway</span>
              <span class="stack-tag">Spring Data JPA / JDBC</span>
              <span class="stack-tag">R2DBC</span>
              <span class="stack-tag">Spring Batch</span>
            </div>
          </div>
          <div class="about-stack-group">
            <span class="stack-label">Messaging / Data</span>
            <div class="stack-tags">
              <span class="stack-tag main">Kafka</span>
              <span class="stack-tag">Debezium(CDC)</span>
              <span class="stack-tag">Redis</span>
              <span class="stack-tag">PostgreSQL(Aurora)</span>
            </div>
          </div>
          <div class="about-stack-group">
            <span class="stack-label">Infra / CI·CD</span>
            <div class="stack-tags">
              <span class="stack-tag">AWS EKS</span>
              <span class="stack-tag">Kubernetes</span>
              <span class="stack-tag">Argo Workflow</span>
              <span class="stack-tag">KEDA</span>
              <span class="stack-tag">Helm</span>
              <span class="stack-tag">GitLab CI</span>
            </div>
          </div>
        </div>
      </div>

      <div class="about-section-block">
        <h2 class="about-section-title">Education</h2>
        <div class="about-exp-item">
          <div class="about-exp-header">
            <span class="about-exp-company">인하대학교</span>
            <span class="about-exp-period">18학번</span>
          </div>
          <ul class="about-exp-desc">
            <li><strong>주전공:</strong> 컴퓨터공학과</li>
            <li><strong>복수전공:</strong> 글로벌금융학과 (금융공학, 재무회계)</li>
          </ul>
        </div>
      </div>

      <div class="about-section-block">
        <h2 class="about-section-title">Awards &amp; Activities</h2>
        <ul class="about-exp-desc">
          <li><strong>사내 AI 공모전 금상</strong> (2025 상반기) — 주식 서비스 프로젝트를 사내 AI 모델에 녹여 폐쇄망 환경에서 테스트 코드 작성, 리팩토링, 바이브 코딩 적용</li>
          <li><strong>AWS re:Invent 2025</strong> 참가 (AI 공모전 포상) — ElastiCache 세션 내용을 Redis Pub/Sub 기반 로컬 캐시 동기화에 적용</li>
          <li><strong>사내 세션 발표</strong> (2025.10) — <a href="/2025/10/31/letter-to-business-managers-eda/">BM들에게 보내는 편지 - EDA</a>: 기획·사업 담당자 대상 EDA 도입 필요성 발표</li>
        </ul>
      </div>

      <div class="about-section-block">
        <h2 class="about-section-title">Certifications</h2>
        <ul class="about-cert-list">
          <li><span class="cert-name">신용분석사</span><span class="cert-meta">한국금융연수원, 2026.06</span></li>
          <li><span class="cert-name">재경관리사</span><span class="cert-meta">삼일회계법인, 2025.10</span></li>
          <li><span class="cert-name">회계관리</span><span class="cert-meta">삼일회계법인, 2025.01</span></li>
          <li><span class="cert-name">재무위험관리사 (국내FRM)</span><span class="cert-meta">금융투자협회, 2024.08</span></li>
          <li><span class="cert-name">투자자산운용사</span><span class="cert-meta">금융투자협회, 2024.03</span></li>
          <li><span class="cert-name">자산관리사 (FP)</span><span class="cert-meta">한국금융연수원, 2023.08</span></li>
          <li><span class="cert-name">증권투자권유대행인</span><span class="cert-meta">금융투자협회, 2021.04</span></li>
          <li><span class="cert-name">전산회계</span><span class="cert-meta">한국세무사회, 2020.12</span></li>
        </ul>
      </div>

      <div class="about-section-block">
        <h2 class="about-section-title">Featured Posts</h2>
        <ul class="about-posts-list">
          <li><a href="/2024/10/10/mediation-pattern-where-is-the-common-handler/">mediation 패턴 도입기 — 짬통은 어디에?</a></li>
          <li><a href="/2024/10/11/mediation-feign-client-vs-webclient-nonblocking/">feignClient vs WebClient Non-blocking 비교</a></li>
          <li><a href="/2024/12/04/mediation-reactor-nonblocking-vs-virtual-thread/">Reactor Non-blocking vs Virtual Thread 실험</a></li>
          <li><a href="/2025/02/06/mediation-what-if-100-percent-kotlin/">Java Reactor에서 Kotlin 코루틴으로 — 왜 코틀린인가</a></li>
          <li><a href="/2025/10/31/letter-to-business-managers-eda/">BM들에게 보내는 편지 - EDA</a></li>
        </ul>
      </div>

    </div>
  </div>
</section>

<style>
.about-section { padding: 3rem 0 5rem; }
.about-container { max-width: 720px; }

.about-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  margin-bottom: 3rem;
  padding-bottom: 2rem;
  border-bottom: 1px solid var(--border);
  flex-wrap: wrap;
  gap: 1.5rem;
}
.about-name {
  font-size: 2.4rem;
  font-weight: 700;
  margin: 0 0 0.3rem;
  letter-spacing: -0.5px;
}
.about-role {
  font-size: 1rem;
  color: var(--text-muted, #888);
  margin: 0;
}
.about-company {
  font-size: 0.9rem;
  color: var(--accent, #58a6ff);
  margin: 0.2rem 0 0;
  font-weight: 500;
}
.about-contact {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  align-items: flex-end;
}
.contact-link {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.9rem;
  color: var(--text-muted, #888);
  text-decoration: none;
  transition: color 0.15s;
}
.contact-link:hover { color: var(--accent, #58a6ff); }
.contact-link svg { width: 15px; height: 15px; flex-shrink: 0; }

.about-intro {
  margin-bottom: 2.5rem;
  line-height: 1.8;
  font-size: 1rem;
  color: var(--text, #e6edf3);
}

.about-section-block { margin-bottom: 2.8rem; }
.about-section-title {
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1.5px;
  color: var(--text-muted, #888);
  margin: 0 0 1.2rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid var(--border);
}

.about-exp-owns {
  font-size: 0.88rem;
  color: var(--text-muted, #888);
  margin: 0 0 1rem;
}
.about-proj-list { display: flex; flex-direction: column; gap: 1.2rem; }
.about-proj-item { padding-left: 0.8rem; border-left: 2px solid var(--border); }
.about-proj-title {
  font-size: 0.92rem;
  font-weight: 600;
  color: var(--text, #e6edf3);
  margin: 0 0 0.4rem;
}
.about-proj-role {
  font-size: 0.82rem;
  color: var(--accent, #58a6ff);
  margin: 0 0 0.3rem;
}
.about-proj-link {
  font-size: 0.82rem;
  color: var(--text-muted, #888);
  margin: 0.4rem 0 0;
}
.about-proj-link a { color: var(--accent, #58a6ff); text-decoration: none; }
.about-proj-link a:hover { text-decoration: underline; }
.about-exp-desc a { color: var(--accent, #58a6ff); text-decoration: none; }
.about-exp-tech {
  font-size: 0.82rem;
  color: var(--text-muted, #888);
  margin: 0 0 0.5rem;
  font-style: italic;
}

.about-exp-item { margin-bottom: 1.2rem; }
.about-exp-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 0.2rem;
}
.about-exp-company { font-weight: 600; font-size: 1rem; }
.about-exp-period { font-size: 0.85rem; color: var(--text-muted, #888); }
.about-exp-role { font-size: 0.9rem; color: var(--accent, #58a6ff); display: block; margin-bottom: 0.8rem; }
.about-exp-desc {
  margin: 0;
  padding-left: 1.2rem;
  line-height: 1.85;
  font-size: 0.92rem;
  color: var(--text, #e6edf3);
}
.about-exp-desc li { margin-bottom: 0.35rem; }
.about-exp-desc code {
  background: var(--code-bg, #161b22);
  padding: 0.1rem 0.4rem;
  border-radius: 4px;
  font-size: 0.85em;
}

.about-stack-grid { display: flex; flex-direction: column; gap: 0.9rem; }
.about-stack-group { display: flex; gap: 1rem; align-items: flex-start; }
.stack-label {
  font-size: 0.82rem;
  color: var(--text-muted, #888);
  min-width: 90px;
  padding-top: 0.2rem;
  flex-shrink: 0;
}
.stack-tags { display: flex; flex-wrap: wrap; gap: 0.4rem; }
.stack-tag {
  font-size: 0.82rem;
  padding: 0.2rem 0.65rem;
  border-radius: 4px;
  background: var(--tag-bg, #21262d);
  color: var(--text-muted, #aaa);
  border: 1px solid var(--border);
}
.stack-tag.main {
  color: var(--accent, #58a6ff);
  border-color: var(--accent, #58a6ff);
  background: transparent;
}

.about-cert-list {
  margin: 0;
  padding: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 0.55rem;
}
.about-cert-list li {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  font-size: 0.92rem;
  gap: 0.5rem;
  flex-wrap: wrap;
}
.cert-name { color: var(--text, #e6edf3); }
.cert-meta { font-size: 0.82rem; color: var(--text-muted, #888); }

.about-posts-list {
  margin: 0;
  padding-left: 1.2rem;
  line-height: 2;
}
.about-posts-list li { font-size: 0.92rem; }
.about-posts-list a {
  color: var(--text, #e6edf3);
  text-decoration: none;
  border-bottom: 1px solid transparent;
  transition: border-color 0.15s, color 0.15s;
}
.about-posts-list a:hover {
  color: var(--accent, #58a6ff);
  border-bottom-color: var(--accent, #58a6ff);
}

@media (max-width: 600px) {
  .about-section { padding: 2rem 0 3.5rem; }
  .about-name { font-size: 1.9rem; }
  .about-header { flex-direction: column; align-items: flex-start; gap: 1rem; margin-bottom: 2rem; }
  .about-contact { align-items: flex-start; }
  .about-intro { font-size: 0.95rem; margin-bottom: 2rem; }
  .about-section-block { margin-bottom: 2rem; }
  .about-stack-group { flex-direction: column; gap: 0.4rem; }
  .stack-label { min-width: unset; }
  .about-proj-item { padding-left: 0.6rem; }
  .about-cert-list li { flex-direction: column; gap: 0.1rem; }
  .cert-meta { font-size: 0.78rem; }
  .about-posts-list { padding-left: 1rem; }
}
</style>
