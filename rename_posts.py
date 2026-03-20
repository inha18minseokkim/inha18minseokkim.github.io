import os
import re

POSTS_DIR = r"C:\Users\Surface\Documents\minseokkim\_posts"

MAPPING = {
    "2023-03-27-Batch의 Transaction 시점, Context에 관해": "2023-03-27-batch-transaction-timing-and-context",
    "2023-05-25-운영리스크 관련 이슈": "2023-05-25-operational-risk-issues",
    "2023-06-07-내부상품대분류관련": "2023-06-07-internal-product-category",
    "2023-06-27-POC회의록(20230627)": "2023-06-27-poc-meeting-notes-20230627",
    "2023-08-08-카드계 BXM 스테이징 javac&spring 버전 이슈": "2023-08-08-card-bxm-staging-javac-spring-version-issue",
    "2023-08-11-[세미나] 거시 금융시장의 주요 이슈": "2023-08-11-seminar-macro-financial-market-issues",
    "2023-08-19-참조 투명성 예제": "2023-08-19-referential-transparency-example",
    "2023-08-19-함수형 프로그래밍": "2023-08-19-functional-programming",
    "2023-08-31-플라이웨이트 패턴": "2023-08-31-flyweight-pattern",
    "2023-09-04-회의록(야놀자 사례)": "2023-09-04-meeting-notes-yanolja-case",
    "2023-09-05-싱글톤 패턴": "2023-09-05-singleton-pattern",
    "2023-09-08-의존 객체 주입": "2023-09-08-dependency-injection",
    "2023-09-09-불필요한 객체생성 피하기": "2023-09-09-avoid-unnecessary-object-creation",
    "2023-09-10-개인적인 생각 with Facade(20230910)": "2023-09-10-personal-thoughts-on-facade-pattern",
    "2023-09-11-Finalizer 주의점": "2023-09-11-finalizer-cautions",
    "2023-09-23-Java Memory Model + final 선언 필요성(JLS 17.4)": "2023-09-23-java-memory-model-final-declaration-jls-17-4",
    "2023-09-28-상위 인터페이스에서 하위 클래스 변수 접근": "2023-09-28-accessing-subclass-fields-from-interface",
    "2023-09-30-getBean + 다형성": "2023-09-30-getbean-and-polymorphism",
    "2023-10-01-getBean을 하지마라": "2023-10-01-do-not-use-getbean",
    "2023-10-06-금요일": "2023-10-06-friday",
    "2023-10-10-뻘짓) Spring Batch 5 + Multiple DataSource": "2023-10-10-spring-batch-5-multiple-datasource-trial",
    "2023-10-24-경영계획 아이디어 회의 선발(20231031)": "2023-10-24-business-planning-idea-meeting",
    "2023-10-27-Branch 전략 논의": "2023-10-27-git-branch-strategy-discussion",
    "2023-10-27-Spring Batch + Cursor Based ItemReader 이슈": "2023-10-27-spring-batch-cursor-based-itemreader-issue",
    "2023-11-02-Spring batch 아키텍쳐 논의삽질": "2023-11-02-spring-batch-architecture-discussion",
    "2023-11-13-보안성취약점 점검 이슈 발견": "2023-11-13-security-vulnerability-inspection-issue",
    "2023-11-15-카드계 Bxm 자바8 로딩 하는방법(Spring Legacy 3, 부트아님)": "2023-11-15-card-bxm-java8-loading-spring-legacy",
    "2023-11-21-자바 78 serializing compatibility의 문제": "2023-11-21-java-78-serialization-compatibility-issue",
    "2023-12-04-카드계 BxmBean에 대하여": "2023-12-04-card-bxmbean-overview",
    "2023-12-05-JDK Dynamic Proxy Casting이슈": "2023-12-05-jdk-dynamic-proxy-casting-issue",
    "2023-12-12-발견한 기술 이슈 및 삽질(BXM framework,카드계)": "2023-12-12-bxm-framework-technical-issues",
    "2023-12-13-자주 쓰는 라이브러리 어노테이션 중첩이 가능한가": "2023-12-13-library-annotation-nesting-compatibility",
    "2023-12-18-EAI openApi 데이터 수신 관련": "2023-12-18-eai-openapi-data-reception",
    "2023-12-20-결재 반려 시 gitlab branch delete 이슈": "2023-12-20-gitlab-branch-delete-on-approval-rejection",
    "2023-12-26-EAI 전문 조립관련": "2023-12-26-eai-message-assembly",
    "2023-12-26-JPA 키워드 정리": "2023-12-26-jpa-keywords-summary",
    "2023-12-29-밀리패스(프로젝트 캔슬됨 ㅜ)": "2023-12-29-millipass-cancelled-project",
    "2024-01-08-금융규제 샌드박스": "2024-01-08-financial-regulatory-sandbox",
    "2024-01-08-비대면 실명인증(유권해석 및 사례)": "2024-01-08-non-face-real-name-verification",
    "2024-01-08-오픈api 방식 인증": "2024-01-08-open-api-authentication",
    "2024-01-13-금융규제 샌드박스 매뉴얼 요약": "2024-01-13-financial-regulatory-sandbox-manual-summary",
    "2024-01-14-사례) 실명인증관련 가장 최근 샌드박스": "2024-01-14-recent-sandbox-case-real-name-verification",
    "2024-01-14-준비해야 할 사항(정리중)": "2024-01-14-preparation-checklist",
    "2024-01-17-수신 캐시백 지급프로세스 트랜잭션": "2024-01-17-deposit-cashback-payment-transaction",
    "2024-01-22-국인체(국방인사정보체계 구축 및 운영에 관한 훈령)": "2024-01-22-defense-personnel-information-system-directive",
    "2024-01-26-첫 GO 중 Gitlab 이슈(공모주 메이트)": "2024-01-26-first-go-live-gitlab-issue-ipo-mate",
    "2024-01-29-식품물가 마이그레이션": "2024-01-29-food-price-data-migration",
    "2024-02-01-EDB 성능 봐야함": "2024-02-01-edb-performance-review",
    "2024-02-02-Query based→ OOP 전환 커브": "2024-02-02-query-based-to-oop-transition",
    "2024-02-05-Layer 분리": "2024-02-05-layer-separation",
    "2024-02-07-Mybatis QueryDSL 혼용 in Spring boot": "2024-02-07-mybatis-querydsl-mixed-in-spring-boot",
    "2024-02-07-카드계 개발 젠킨스 문제(~202312현재)java 클래스의 롤링배포 방식 문제": "2024-02-07-card-jenkins-rolling-deploy-issue",
    "2024-02-08-캐싱 전략": "2024-02-08-caching-strategy",
    "2024-02-15-코드성 vs Enum vs 도메인 분리": "2024-02-15-code-value-vs-enum-vs-domain-separation",
    "2024-02-21-비상장 주식 알림 서비스(두나무 제휴, ~ 202404)": "2024-02-21-unlisted-stock-alert-service-dunamu",
    "2024-02-21-종목 단축코드": "2024-02-21-stock-short-code",
    "2024-02-21-화면 명세(회의전 기획안)": "2024-02-21-screen-spec-pre-meeting",
    "2024-02-21-활용 데이터": "2024-02-21-utilized-data",
    "2024-02-22-화면 명세(회의 후)": "2024-02-22-screen-spec-post-meeting",
    "2024-02-29-두나무 문의 내용": "2024-02-29-dunamu-inquiry",
    "2024-03-04-PostgreSQL 시퀀스 + 캐시 주의점": "2024-03-04-postgresql-sequence-cache-caution",
    "2024-03-04-이력성 Column AOP(GUID,JpaAudit)": "2024-03-04-audit-column-aop-guid-jpa-audit",
    "2024-03-11-구조 (202401 ver,Kbank MSA 최초 오픈 시점)": "2024-03-11-kbank-msa-initial-architecture-202401",
    "2024-03-12-MSA→EAI→OpenApi→두나무→OpenApi→EAI→MSA 데이터 수신 개발": "2024-03-12-msa-eai-openapi-dunamu-data-reception",
    "2024-03-21-MCI2api-gateway 개선(spring-cloud) 삽질기": "2024-03-21-mci-api-gateway-spring-cloud-improvement",
    "2024-03-28-LocalDateTime 직역직렬화 관련 이슈": "2024-03-28-localdatetime-serialization-issue",
    "2024-03-31-RouteLocator로 body 열어 같은 path → 다른 target 라우팅 하는법": "2024-03-31-routelocator-same-path-different-target-routing",
    "2024-04-04-RouteLocator로 Path 파싱 후 라우팅": "2024-04-04-routelocator-path-parsing-routing",
    "2024-04-04-새로운 이슈(파일 크기 OOM)": "2024-04-04-file-size-oom-issue",
    "2024-04-15-권리변동에 따른 데이터 보정 필요": "2024-04-15-data-correction-for-rights-change",
    "2024-04-22-메타 긴급반영건(컬럼 길이 변경)": "2024-04-22-emergency-meta-column-length-change",
    "2024-04-29-리팩토링1차(20240430)": "2024-04-29-refactoring-1st-phase-20240430",
    "2024-05-07-Gradle + Spring 멀티 모듈": "2024-05-07-gradle-spring-multi-module",
    "2024-05-16-Proxy를 활용한 테더링 뻘짓": "2024-05-16-proxy-tethering-experiment",
    "2024-05-16-카드계 Locust 도입 시 EUC-KR 이슈": "2024-05-16-card-locust-euckr-encoding-issue",
    "2024-05-18-Spring Cloud Config-Server + Spring Security (Basic Auth) 정리(Bootstrap 사용 안함)": "2024-05-18-spring-cloud-config-server-spring-security-basic-auth",
    "2024-05-26-기획안 질문": "2024-05-26-planning-questions",
    "2024-05-28-주식 단위업무 MSA Arch 개선": "2024-05-28-stock-unit-msa-architecture-improvement",
    "2024-06-05-환율 서비스 일시 장애(20240531)": "2024-06-05-exchange-rate-service-outage-20240531",
    "2024-06-11-상장주식시세": "2024-06-11-listed-stock-price",
    "2024-06-11-투자온도(구 공포탐욕지수)": "2024-06-11-investment-temperature-fear-greed-index",
    "2024-06-14-상장주식시세 기획안 개선 + API 기준 데이터 정리": "2024-06-14-listed-stock-price-plan-improvement-api-data",
    "2024-06-25-EKS-IDCkafka-openApi 수신 구조 잡기": "2024-06-25-eks-idc-kafka-openapi-data-reception-architecture",
    "2024-07-02-20240702 UX 기획안 확정 회의": "2024-07-02-ux-planning-final-meeting-20240702",
    "2024-07-04-Redis Pipeline 조회 ⇒ Lua 조회": "2024-07-04-redis-pipeline-to-lua-query",
    "2024-07-10-케이뱅크 메타 표준 & Spring Data Envers 도입기": "2024-07-10-kbank-meta-standard-spring-data-envers",
    "2024-07-11-Kafka with Kbank MSA + 표준 스케줄러": "2024-07-11-kafka-kbank-msa-standard-scheduler",
    "2024-07-16-Charset 인코딩 문제, 유량제어 문제": "2024-07-16-charset-encoding-and-rate-control-issue",
    "2024-07-19-Gradle Multi Module + Gitlab Submodule 도입기": "2024-07-19-gradle-multi-module-gitlab-submodule",
    "2024-08-13-failing offset 문제와 데이터 수신 및 적재용으로 kafka 구성에 대해": "2024-08-13-kafka-failing-offset-and-data-ingestion",
    "2024-08-19-후회합니다 죄송합니다": "2024-08-19-regrets-and-apologies",
    "2024-08-20-거래량 불일치": "2024-08-20-trading-volume-inconsistency",
    "2024-08-20-해외주식 NASDAQ NYSE test ticker(to Exclude)": "2024-08-20-overseas-stock-nasdaq-nyse-test-tickers",
    "2024-09-04-EKS - IDC kafka - openApi 그대로 구현해보기(절망 프로젝트)": "2024-09-04-eks-idc-kafka-openapi-implementation-attempt",
    "2024-09-09-K-IFRS 관련": "2024-09-09-k-ifrs-overview",
    "2024-09-09-다중 파티션 고도화": "2024-09-09-multi-partition-enhancement",
    "2024-09-09-연결재무제표 작성 대상기업면제기업": "2024-09-09-consolidated-financial-statement-exempt-companies",
    "2024-09-09-재무데이터 노출기준 정하기": "2024-09-09-financial-data-exposure-criteria",
    "2024-09-09-정기 작업이 꼭 배치 형태여야 하는가(20240909)": "2024-09-09-does-scheduled-job-have-to-be-batch",
    "2024-09-09-주권상장법인 사업보고서 제출기한": "2024-09-09-listed-company-business-report-deadline",
    "2024-09-11-검색 기능 고도화 신규 개발(20241001, 비상장주식도 같이)": "2024-09-11-search-feature-enhancement-unlisted-stock",
    "2024-09-11-데이터 수신 pod에 KEDA 적용": "2024-09-11-keda-on-data-reception-pod",
    "2024-09-12-주식수변동에 따른 가격 히스토리 갱신": "2024-09-12-price-history-update-on-share-count-change",
    "2024-09-27-글로벌 시장 코드(NMS,NYQ,,,)": "2024-09-27-global-market-codes-nms-nyq",
    "2024-09-28-MSA workflow에 cronjob을 올리려면…(20240928)": "2024-09-28-msa-workflow-cronjob-deployment",
    "2024-09-28-argo-workflow+ 케이뱅크 jflow": "2024-09-28-argo-workflow-kbank-jflow",
    "2024-09-28-맥미니용 샘플 배포(20240928)": "2024-09-28-mac-mini-sample-deployment",
    "2024-09-28-여러 번 실행(recursive)": "2024-09-28-recursive-execution",
    "2024-09-29-1파일 n 잡": "2024-09-29-single-file-multiple-jobs",
    "2024-10-01-실패해도 계속 실행 잡": "2024-10-01-continue-on-failure-job",
    "2024-10-02-Minikube + Mac 안되는 이유, Kubernetes with Docker desktop": "2024-10-02-minikube-mac-issue-kubernetes-docker-desktop",
    "2024-10-02-실패해도 계속 실행 잡 2(개선버전)": "2024-10-02-continue-on-failure-job-v2",
    "2024-10-10-Public 망에서 작업(희망사항)": "2024-10-10-working-on-public-network-wishlist",
    "2024-10-10-STK업무 장애(DBA의 작업실수)": "2024-10-10-stk-service-outage-dba-mistake",
    "2024-10-10-mediation 패턴 도입기 - 짬통은 어디에": "2024-10-10-mediation-pattern-where-is-the-common-handler",
    "2024-10-10-리팩토링2차(20240910)": "2024-10-10-refactoring-2nd-phase-20240910",
    "2024-10-11-1차 리팩토링 및 로직 개선  (~20241015)": "2024-10-11-first-refactoring-and-logic-improvement",
    "2024-10-11-Kubernetes 노드 DNS 장애(20240920)": "2024-10-11-kubernetes-node-dns-failure-20240920",
    "2024-10-11-mediation 패턴 도입기 - feignClient vs webClient non blocking(20240915)": "2024-10-11-mediation-feign-client-vs-webclient-nonblocking",
    "2024-10-12-MCI  api-gateway - 로깅 삽질기": "2024-10-12-mci-api-gateway-logging-troubleshooting",
    "2024-10-12-경쟁률 계산기의 한계(얼마 넣으면 청약 가능)": "2024-10-12-ipo-competition-rate-calculator-limitations",
    "2024-10-12-공모주 데이터의 지속적인 에러": "2024-10-12-ipo-data-persistent-errors",
    "2024-10-12-스테이징 DB 장애(용량 부족)": "2024-10-12-staging-db-outage-disk-full",
    "2024-10-12-주관사, 공동 주관사 문제": "2024-10-12-ipo-lead-underwriter-joint-underwriter-issue",
    "2024-10-12-파일 수신 시점 문제(대고객 인지 늦음)": "2024-10-12-file-reception-timing-delay-issue",
    "2024-10-19-WebClient.Builder + 싱글톤 시 헤더 설정 주의(중복 정의 가능)": "2024-10-19-webclient-builder-singleton-header-duplicate-warning",
    "2024-10-20-1차 완성본": "2024-10-20-first-complete-version",
    "2024-10-22-JPA 복합 키 + JoinTable 응용": "2024-10-22-jpa-composite-key-jointable",
    "2024-10-28-Kafka - Avro를 활용한 직렬 역직렬화(20241028)": "2024-10-28-kafka-avro-serialization-deserialization",
    "2024-11-02-mediation 패턴 도입기 - reactive feign vs virtual thread(java21)": "2024-11-02-mediation-reactive-feign-vs-virtual-thread-java21",
    "2024-11-04-FindAll~사용시 JPA FetchJoin + 안됨": "2024-11-04-jpa-findall-fetchjoin-issue",
    "2024-11-06-20241208 정기 중단PM간 주식 업무 개선 마이그레이션사항(꽤큼)": "2024-11-06-stock-service-migration-improvement-20241208",
    "2024-11-26-mediation 패턴 도입기 - Interceptor, ThreadLocal, ServletContext + 유실까지": "2024-11-26-mediation-interceptor-threadlocal-servletcontext-data-loss",
    "2024-11-26-mediation 패턴 도입기 - RECYCLE_FACADES": "2024-11-26-mediation-recycle-facades",
    "2024-11-26-mediation 패턴 도입기": "2024-11-26-mediation-pattern-introduction",
    "2024-11-30-mediation 패턴 도입기 - 케이뱅크 내부에서 webflux의 한계(20241130기준)": "2024-11-30-mediation-webflux-limitations-in-kbank",
    "2024-12-02-mediation 도입기 - 높은 부하 상황에서 자원 사용량": "2024-12-02-mediation-resource-usage-under-high-load",
    "2024-12-04-mediation 패턴 도입기 - Reactor Non-blocking vs Multi Thread(virtual) 실험": "2024-12-04-mediation-reactor-nonblocking-vs-virtual-thread",
    "2024-12-09-mediation 패턴 도입기 - Reactor에 대한 오해와 실수": "2024-12-09-mediation-reactor-misconceptions-and-mistakes",
    "2024-12-17-mediaion 패턴 도입기 - webclient + openfeign 사용": "2024-12-17-mediation-webclient-openfeign-usage",
    "2024-12-22-mediation 패턴 도입기 - openfeign + kotlin 코루틴 조합. 꼭 써야할까": "2024-12-22-mediation-openfeign-kotlin-coroutine-combination",
    "2024-12-31-Python + jflow 필요성 + 샘플 프로젝트": "2024-12-31-python-jflow-necessity-and-sample-project",
    "2024-12-31-argo-workflow  jflow 연동 개선건(20241231)": "2024-12-31-argo-workflow-jflow-integration-improvement-20241231",
    "2024-12-31-정기작업에 관하여 삽질(스프링 배치, 파이썬 스크립트 등등)": "2024-12-31-scheduled-job-troubleshooting-spring-batch-python",
    "2025-01-14-Python + Argo Event (결과  원하는대로 안됨)": "2025-01-14-python-argo-event-failed-result",
    "2025-01-20-스프링부트 배치) 공통 메타 DB + Multiple DataSource(20250120)": "2025-01-20-spring-batch-common-meta-db-multiple-datasource",
    "2025-01-21-Netty Native memory 문제": "2025-01-21-netty-native-memory-issue",
    "2025-01-22-202412) 현재 상황에서는 Reactor, 중기적으로는 VThread, 장기적으로는 둘다": "2025-01-22-reactor-now-vthread-mid-term-both-long-term",
    "2025-01-27-Gradle 초기화 시점(settings.gradle → build.gradle,202407)": "2025-01-27-gradle-initialization-timing-settings-build",
    "2025-01-27-멀티 모듈의 공통 함정에 대해 깨달은 점(202501)": "2025-01-27-multi-module-common-pitfalls",
    "2025-01-28-아키텍쳐협의회 회의록(20241219)": "2025-01-28-architecture-council-meeting-notes-20241219",
    "2025-02-02-Keep Alive + Content Length를 잘못세팅하면 벌어지는 일": "2025-02-02-keep-alive-content-length-misconfiguration",
    "2025-02-03-Jpa FetchJoin vs BatchSize , 각각의 장단점 주의점": "2025-02-03-jpa-fetchjoin-vs-batchsize-tradeoffs",
    "2025-02-03-스프링부트 배치) 배치 메타테이블이 필요할까": "2025-02-03-spring-batch-is-meta-table-necessary",
    "2025-02-06-Jpa Upsert 존재하지 않는 이유": "2025-02-06-jpa-upsert-does-not-exist",
    "2025-02-06-mediation 패턴 도입기 - 하지만 100% 코틀린이라면": "2025-02-06-mediation-what-if-100-percent-kotlin",
    "2025-02-11-스프링부트 배치) ResourcelessJobRepository (Spring batch 5.2.0-M2)": "2025-02-11-spring-batch-resourceless-job-repository",
    "2025-02-12-argo-workflow - jflow 연동 개선건 2 (202502)": "2025-02-12-argo-workflow-jflow-integration-improvement-2-202502",
    "2025-02-12-멀티 모듈 구성 개선(안, 202502)": "2025-02-12-multi-module-configuration-improvement",
    "2025-02-13-단일 이미지 빌드 환경에서 멀티모듈 빌드(뻘)": "2025-02-13-single-image-multi-module-build",
    "2025-02-16-Netty에서 PhantomReference 통한 GC": "2025-02-16-netty-phantom-reference-gc",
    "2025-02-17-OpenDart - 전문투자자 대상 선별 방법": "2025-02-17-opendart-professional-investor-selection",
    "2025-02-19-CI - Gradle&Sonar Pipeline 버전 업그레이드": "2025-02-19-ci-gradle-sonar-pipeline-version-upgrade",
    "2025-02-20-Spring Batch Exit 로직 개선(20250220)": "2025-02-20-spring-batch-exit-logic-improvement",
    "2025-02-20-api 분석": "2025-02-20-api-analysis",
    "2025-02-20-무형자산가상자산 계정 분석": "2025-02-20-intangible-virtual-asset-account-analysis",
    "2025-02-20-투자온도 SUNSET 건": "2025-02-20-investment-temperature-sunset",
    "2025-03-05-요건확정회의(20250305)": "2025-03-05-requirements-finalization-meeting-20250305",
    "2025-03-06-ETF Data Categorizing 관련": "2025-03-06-etf-data-categorizing",
    "2025-03-16-Python - ISTIO 사이드카 연동 문제(사이드카보다 파이썬 외부 연결이 더 빨라,20250317)": "2025-03-16-python-istio-sidecar-integration-issue",
    "2025-03-17-CI) Sonarqube + Python 연동 문제 해결  Sonar Scanner Image": "2025-03-17-ci-sonarqube-python-integration-sonar-scanner-image",
    "2025-03-18-Gitlab CI 관련 삽질": "2025-03-18-gitlab-ci-troubleshooting",
    "2025-03-29-Insert On Conflict(Upsert)는 과연 성능저하가 없을까": "2025-03-29-insert-on-conflict-upsert-performance-impact",
    "2025-03-29-스택이 무진장 커진다면 힙은 필요없을까": "2025-03-29-if-stack-grows-huge-is-heap-unnecessary",
    "2025-04-01-RateLimiting을 응용하여 이력 적재 속도를 조절해보자": "2025-04-01-rate-limiting-for-history-ingestion-speed-control",
    "2025-04-29-비선형 처리기(AKA. AI)": "2025-04-29-nonlinear-processor-aka-ai",
    "2025-04-29-주식서비스 LANGRAPH": "2025-04-29-stock-service-langgraph",
    "2025-04-30-주식서비스 RAG 파이프라인 구축": "2025-04-30-stock-service-rag-pipeline",
    "2025-05-07-재무 데이터 처리": "2025-05-07-financial-data-processing",
    "2025-05-25-[Tech Talk] 케이뱅크 주식 MSA 서비스를 활용한 LangChain + MCP": "2025-05-25-tech-talk-kbank-stock-msa-langchain-mcp",
    "2025-05-30-Redis 활용 이력 적재 RateLimit": "2025-05-30-redis-history-ingestion-rate-limit",
    "2025-05-30-개인화정보 캐싱 전략": "2025-05-30-personalized-info-caching-strategy",
    "2025-06-18-AI 공모전 - 2025상반기 (금상, 400만원 + 싱가폴 Fintech week 참가)": "2025-06-18-ai-contest-2025-first-half-gold-prize",
    "2025-06-28-Caffeine Cache를 Static 선언한다면 어떻게 될까": "2025-06-28-caffeine-cache-static-declaration-effects",
    "2025-07-05-AI - PT 콘티": "2025-07-05-ai-presentation-storyboard",
    "2025-07-06-@Transactional(readOnly=True)를 막 쓰지 말자": "2025-07-06-transactional-readonly-careful-usage",
    "2025-07-14-conda 사용하는 이유": "2025-07-14-why-use-conda",
    "2025-07-14-멀티캠퍼스 [금융특화] 파이썬과 오픈소스를 활용한 딥러닝(심화)": "2025-07-14-multicampus-financial-python-deep-learning",
    "2025-07-16-Jflow - Control M AWS 연동": "2025-07-16-jflow-control-m-aws-integration",
    "2025-07-18-채용사이트 홍보물 유튜브 인터뷰": "2025-07-18-recruitment-site-youtube-interview",
    "2025-07-27-Kotlin Arrow를 활용한 에러 변환": "2025-07-27-kotlin-arrow-error-transformation",
    "2025-07-29-DB Sync 개선": "2025-07-29-db-sync-improvement",
    "2025-07-29-S3 + logback 활용안": "2025-07-29-s3-logback-usage-plan",
    "2025-08-12-EKS Pod 배포 및 구동시 38080(server.port) already in use 발생 exec form": "2025-08-12-eks-pod-deploy-port-already-in-use-exec-form",
    "2025-08-19-2025 금융권 공동채용 박람회": "2025-08-19-2025-financial-sector-job-fair",
    "2025-09-05-M365  Confluence RAG 연동": "2025-09-05-m365-confluence-rag-integration",
    "2025-09-08-Cache Validate 주기 및 기준정보 없을 때": "2025-09-08-cache-validation-period-and-missing-reference-data",
    "2025-09-08-Java Committed Memory 부제  메모리가 왜 계속 증가함": "2025-09-08-java-committed-memory-increase-investigation",
    "2025-09-19-주간 투자왕": "2025-09-19-weekly-investment-king",
    "2025-09-26-api명세": "2025-09-26-api-specification",
    "2025-09-29-Postgresql 파티션 PK": "2025-09-29-postgresql-partition-pk",
    "2025-10-16-R2dbc Connection POOL 설정": "2025-10-16-r2dbc-connection-pool-configuration",
    "2025-10-16-Spring Reactive Redis Repo 구현": "2025-10-16-spring-reactive-redis-repo-implementation",
    "2025-10-31-BM들에게 보내는 편지 - EDA": "2025-10-31-letter-to-business-managers-eda",
    "2025-10-31-채널 연동 관련 끄적": "2025-10-31-channel-integration-notes",
    "2025-11-06-25 Associate 미니 프로젝트 제출": "2025-11-06-25-associate-mini-project-submission",
    "2025-11-14-MGM 처리관련 논의": "2025-11-14-mgm-processing-discussion",
    "2025-11-14-게임 초기화": "2025-11-14-game-initialization",
    "2025-11-14-집계 후 푸시 발송": "2025-11-14-push-notification-after-aggregation",
    "2025-11-14-집계": "2025-11-14-aggregation",
    "2025-11-14-현금 리워드 소멸 경고 배치": "2025-11-14-cash-reward-expiry-warning-batch",
    "2025-11-16-왜 서비스가 토스처럼 부드럽지 못할까": "2025-11-16-why-is-our-service-not-as-smooth-as-toss",
    "2025-12-21-Elasticache 네트워크 대역 장애": "2025-12-21-elasticache-network-bandwidth-outage",
    "2025-12-22-Redis pubsub 활용해서 Local Cache 동기화 - kotlin arrow 응용": "2025-12-22-redis-pubsub-local-cache-sync-kotlin-arrow",
    "2025-12-22-마이키즈": "2025-12-22-my-kids",
    "2025-12-22-샤딩 활용 N Parallel workflow  Aggregate": "2025-12-22-sharding-n-parallel-workflow-aggregate",
    "2026-01-02-Postgresql CDC + Debezium + kafka 사용 EDA  transactional outbox 패턴": "2026-01-02-postgresql-cdc-debezium-kafka-eda-transactional-outbox",
    "2026-01-18-신혼여행가서 메이플 일퀘하는데 연결이 안됨": "2026-01-18-maple-daily-quest-connection-issue-on-honeymoon",
    "2026-01-26-Raptor RAG 활용 공시 문서 압축 요약": "2026-01-26-raptor-rag-disclosure-document-summarization",
    "2026-02-12-공모주 메이트 2차 리팩토링": "2026-02-12-ipo-mate-second-refactoring",
    "2026-03-04-테스트코드 짜기는 싫지만 TDD는 하고 싶어": "2026-03-04-dislike-test-code-but-want-tdd",
    "2026-03-08-보금자리론 확약통지 후 추가 대출 신청 및 상담": "2026-03-08-home-loan-commitment-additional-loan-consultation",
    "2026-03-09-Notion 에서 Obsidian으로 옮긴 이유": "2026-03-09-why-i-moved-from-notion-to-obsidian",
    "2026-03-17-폐쇄망-EKS gitlab CI 시 DNS Lookup 이슈": "2026-03-17-closed-network-eks-gitlab-ci-dns-lookup-issue",
}


def main():
    renamed_count = 0
    skipped_count = 0
    not_found_count = 0

    # Step 1: Rename files
    print("=== Step 1: Renaming files ===")
    for old_stem, new_stem in MAPPING.items():
        old_path = os.path.join(POSTS_DIR, old_stem + ".md")
        new_path = os.path.join(POSTS_DIR, new_stem + ".md")

        if os.path.exists(new_path) and not os.path.exists(old_path):
            print(f"  [ALREADY DONE] {new_stem}.md")
            skipped_count += 1
            continue

        if not os.path.exists(old_path):
            print(f"  [NOT FOUND] {old_stem}.md")
            not_found_count += 1
            continue

        if os.path.exists(new_path):
            print(f"  [SKIP - dest exists] {old_stem}.md -> {new_stem}.md")
            skipped_count += 1
            continue

        os.rename(old_path, new_path)
        print(f"  [RENAMED] {old_stem}.md -> {new_stem}.md")
        renamed_count += 1

    print(f"\nRename summary: {renamed_count} renamed, {skipped_count} skipped/already done, {not_found_count} not found")

    # Step 2: Update {% post_url %} references in all .md files
    print("\n=== Step 2: Updating post_url references ===")
    all_md_files = [
        os.path.join(POSTS_DIR, f)
        for f in os.listdir(POSTS_DIR)
        if f.endswith(".md")
    ]

    refs_updated_total = 0
    files_updated = 0

    for md_file in all_md_files:
        try:
            with open(md_file, "r", encoding="utf-8") as f:
                content = f.read()
        except UnicodeDecodeError:
            print(f"  [ENCODING ERROR] {os.path.basename(md_file)}")
            continue

        new_content = content
        file_refs_updated = 0

        for old_stem, new_stem in MAPPING.items():
            # Match {% post_url OLD_STEM %} with possible whitespace variants
            pattern = r'\{%\s*post_url\s+' + re.escape(old_stem) + r'\s*%\}'
            replacement = '{{% post_url {} %}}'.format(new_stem)
            updated, count = re.subn(pattern, replacement, new_content)
            if count > 0:
                new_content = updated
                file_refs_updated += count

        if file_refs_updated > 0:
            with open(md_file, "w", encoding="utf-8") as f:
                f.write(new_content)
            print(f"  [UPDATED] {os.path.basename(md_file)}: {file_refs_updated} reference(s) updated")
            refs_updated_total += file_refs_updated
            files_updated += 1

    print(f"\nReference update summary: {refs_updated_total} reference(s) updated across {files_updated} file(s)")

    print("\n=== Final Summary ===")
    print(f"  Files renamed:            {renamed_count}")
    print(f"  Files skipped/not found:  {skipped_count + not_found_count}")
    print(f"  References updated:       {refs_updated_total} in {files_updated} file(s)")


if __name__ == "__main__":
    main()
