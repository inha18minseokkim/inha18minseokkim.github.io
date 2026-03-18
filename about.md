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
            <span class="about-exp-company">케이뱅크</span>
            <span class="about-exp-period">재직 중</span>
          </div>
          <span class="about-exp-role">Backend Developer</span>
          <ul class="about-exp-desc">
            <li>주식 서비스 <strong>BFF(Backend-For-Frontend) 레이어 설계 및 구현</strong> — Mediation 패턴 도입</li>
            <li>기존 Java + OpenFeign + CompletableFuture 구조에서 <strong>Spring WebFlux(Reactor) 기반 논블로킹</strong> 아키텍처로 전환</li>
            <li>Java → <strong>Kotlin 마이그레이션</strong>. Kotlin 코루틴(<code>suspend</code> + <code>async/await</code>)으로 복수 API 병렬 조합 구현, 가독성과 동시성 제어 동시에 개선</li>
            <li>WebClient 커스텀 구현 — Reactor Context를 통한 <strong>사내 표준 헤더 전파(Header Propagation)</strong></li>
            <li>Reactor Non-blocking vs Virtual Thread(Java 21) 성능 비교 실험 및 기술 선택 근거 정리</li>
          </ul>
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
        <h2 class="about-section-title">Featured Posts</h2>
        <ul class="about-posts-list">
          <li><a href="/2024/11/26/mediation-패턴-도입기/">mediation 패턴 도입기 — BFF 설계 전체 흐름 정리</a></li>
          <li><a href="/2024/10/11/mediation-패턴-도입기-feignClient-vs-webClient-non-blocking(20240915)/">feignClient vs WebClient Non-blocking 비교</a></li>
          <li><a href="/2024/12/04/mediation-패턴-도입기-Reactor-Non-blocking-vs-Multi-Thread(virtual)-실험/">Reactor Non-blocking vs Virtual Thread 실험</a></li>
          <li><a href="/2025/02/06/mediation-패턴-도입기-하지만-100-코틀린이라면/">Java Reactor에서 Kotlin 코루틴으로 — 왜 코틀린인가</a></li>
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
  .about-header { flex-direction: column; align-items: flex-start; }
  .about-contact { align-items: flex-start; }
  .about-stack-group { flex-direction: column; gap: 0.4rem; }
  .stack-label { min-width: unset; }
}
</style>
