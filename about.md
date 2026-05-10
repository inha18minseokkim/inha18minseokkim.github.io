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
        <h2 class="about-section-title">Experience</h2>
        <div class="about-exp-item">
          <div class="about-exp-header">
            <span class="about-exp-company">케이뱅크 혁신 서비스 백엔드 개발</span>
            <span class="about-exp-period">2023.01 ~ 현재</span>
          </div>
          <span class="about-exp-role">Backend Developer</span>
          <div class="about-proj-list">

            <div class="about-proj-item">
              <p class="about-proj-title">초기 서비스 개발 및 MSA 전환 <span class="about-exp-period">(2023.01 ~ 2024.01)</span></p>
              <ul class="about-exp-desc">
                <li><strong>신규 서비스 런칭:</strong> 공모주 메이트, 식품물가 알림, 돈나무 키우기 등의 백엔드 서비스와 계정계/카드계 포털 관리자 화면 및 푸시 배치 기능 개발</li>
                <li><strong>MSA 추진 TF 활동:</strong> 레거시 시스템을 Spring Boot 3, PostgreSQL 환경으로 마이그레이션하는 작업에 참여</li>
                <li><strong>MSA 배치 구동 아키텍처 개선:</strong> 사내 정기 작업 관제 시스템(jflow)과 Argo-Workflow를 연동하여 MSA 환경에 배치 어플리케이션을 구동시키는 표준 수립</li>
              </ul>
            </div>

            <div class="about-proj-item">
              <p class="about-proj-title">비상장 주식 서비스 구축 및 레거시-MSA 연동 아키텍처 개선 <span class="about-exp-period">(2024.03 ~ 2024.04)</span></p>
              <p class="about-exp-tech">Java/Kotlin, Spring Boot, Spring Cloud Gateway, JPA</p>
              <ul class="about-exp-desc">
                <li><strong>EKS 간 대외 연동 구조 확립:</strong> IDC 대외계와 EKS 환경을 연결하기 위해 EAI-OpenAPI 릴레이 구조 도입</li>
                <li><strong>API 게이트웨이 라우팅 한계 극복:</strong> 레거시 MCI 어댑터의 URI 매핑 한계를 Spring Cloud Gateway 라우팅 로직 개선으로 해결</li>
                <li><strong>오버엔지니어링 식별 및 최적화:</strong> Spring Cloud Gateway와 Redis 간 불필요한 연동을 선제적으로 파악, 제거하여 장애 시 가용성 확보</li>
                <li><strong>공통 데이터 변경 표준화:</strong> JPA Audit 기능을 활용하여 표준 공통 컬럼(GUID 등) 적재 자동화</li>
                <li><strong>프로젝트 매니지먼트:</strong> 백엔드 핵심 설계 및 유관 부서 간 일정/비즈니스 요건 조율 주도</li>
              </ul>
            </div>

            <div class="about-proj-item">
              <p class="about-proj-title">투자홈/투자캘린더 서비스 개발, 고도화 <span class="about-exp-period">(2024.04 ~ 2025.07)</span></p>
              <p class="about-exp-tech">Kotlin suspend, Kafka, KEDA, Redis</p>
              <ul class="about-exp-desc">
                <li><strong>대외기관 API 병목 현상 해결:</strong> 폐쇄망 제약(10 TPS)을 극복하기 위해 Kafka 기반 OpenAPI 수신 파이프라인 구축, KEDA 도입으로 EKS 자원 효율화</li>
                <li><strong>MSA 하위 도메인 디커플링:</strong> 주식 도메인 내 하위 업무(공모주, 비상장 등) 간 복잡도를 낮추기 위해 BFF 패턴 설계 및 적용</li>
                <li><strong>조회 성능 개선:</strong> 논블로킹 아키텍처와 Redis Lua Script 도입으로 준실시간 국내 주식 데이터 조회 성능 대폭 개선</li>
              </ul>
            </div>

            <div class="about-proj-item">
              <p class="about-proj-title">주간 투자왕 서비스 개발 <span class="about-exp-period">(2025.06 ~ 2025.12)</span></p>
              <p class="about-exp-tech">Kotlin, Spring WebFlux, R2DBC, Kafka</p>
              <ul class="about-exp-desc">
                <li><strong>Full Reactive 스택:</strong> 대량 트래픽 처리를 위해 Spring WebFlux와 R2DBC 도입, 논블로킹 I/O 기반으로 DB 병목 제거</li>
                <li><strong>Hexagonal Architecture 도입:</strong> 도메인 로직과 인프라 간 결합을 끊어 비즈니스 변화에 민첩하게 대응할 수 있는 구조 구축</li>
                <li><strong>이벤트 기반 아키텍처(EDA) 적용:</strong> 계정계 입출금 연동을 위해 Kafka 활용, 서비스 간 결합도를 낮추고 응답 지연 최소화</li>
              </ul>
            </div>

            <div class="about-proj-item">
              <p class="about-proj-title">게임 센터 서비스 개발 <span class="about-exp-period">(2026.04 ~ 진행 중)</span></p>
              <p class="about-exp-tech">Java 21, Spring Boot, Spring Data JDBC, Debezium(CDC), Kafka</p>
              <ul class="about-exp-desc">
                <li><strong>Virtual Thread 및 Spring Data JDBC 도입:</strong> JDK 21의 Virtual Thread와 헥사고날 아키텍처에 적합한 Spring Data JDBC로 기술 스택 전환</li>
                <li><strong>CDC 기반 EDA 입출금 아키텍처:</strong> Debezium CDC 도입, 데이터 정합성이 최우선인 입출금 로직을 Outbox 패턴으로 구현</li>
                <li><strong>도메인 중심 아키텍처 및 로직 통합:</strong> 헥사고날 아키텍처 적용으로 기존 주간 투자왕 서비스에 파편화되어 있던 입출금 처리 로직 통합 성공</li>
              </ul>
            </div>

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
              <span class="stack-tag">Spring Data JPA</span>
              <span class="stack-tag">Kotlin Coroutines</span>
            </div>
          </div>
          <div class="about-stack-group">
            <span class="stack-label">Infra / Etc</span>
            <div class="stack-tags">
              <span class="stack-tag">MSA</span>
              <span class="stack-tag">Kafka</span>
              <span class="stack-tag">Redis</span>
              <span class="stack-tag">Kubernetes</span>
              <span class="stack-tag">CI/CD</span>
              <span class="stack-tag">PostgreSQL</span>
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
        </div>
      </div>

      <div class="about-section-block">
        <h2 class="about-section-title">Certifications</h2>
        <ul class="about-cert-list">
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
          <li><a href="/2024/11/26/mediation-pattern-introduction/">mediation 패턴 도입기 — BFF 설계 전체 흐름 정리</a></li>
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
