#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Process all blog posts with 미지정 tags.
Assigns proper tags/categories and adds intro summaries.
"""

import os
import re
import sys

posts_dir = r'C:\Users\Surface\Documents\minseokkim\_posts'

# Collect all files with 미지정
untagged = []
for f in sorted(os.listdir(posts_dir), reverse=True):
    if not f.endswith('.md'):
        continue
    path = os.path.join(posts_dir, f)
    with open(path, encoding='utf-8') as fp:
        content = fp.read()
    if '미지정' in content:
        untagged.append((f, path))

print(f"Total files to process: {len(untagged)}", file=sys.stderr)

def classify(filename, content):
    """Return (tags_list, categories_list, intro_sentence)"""
    f = filename.lower()
    c = content.lower()
    title_match = re.search(r'title:\s*["\']?(.*?)["\']?\s*\n', content)
    title = title_match.group(1) if title_match else filename

    # AWS re:Invent 2025 English posts
    aws_reinvent_posts = [
        'mastering fluent-bit', 'lambda managed instances', 'building the future trading',
        'building resilient deployment pipelines', 'building on aws resilience',
        'advanced data modeling for amazon elasticache', 'vibe data modeling',
        'low-cost logging and observability', 'inference on aws trainium',
        'developing unit cost metrics', 'telemetry forencics', 'supercharge lambda',
        'optimizing agentic', 'evaluating architectural trade-offs', 'behind the scenes how aws',
        'aws reinvent'
    ]
    for kw in aws_reinvent_posts:
        if kw in f or kw in c[:200]:
            return (['AWS', '기술'], ['기술'], 'AWS re:Invent 2025 세션 노트 정리.')

    # Spring Batch posts
    if 'spring batch' in f or 'spring batch' in c[:300] or 'springbatch' in f:
        tags = ['Spring Batch', '개발', 'Java']
        return (tags, ['기술'], 'Spring Batch 관련 개발 내용 정리.')

    # Kafka posts
    if 'kafka' in f:
        if 'keda' in f or 'keda' in c[:300]:
            return (['Kafka', 'KEDA', '인프라'], ['기술'], 'Kafka와 KEDA를 활용한 인프라 구성 정리.')
        if 'kbank' in f or '케이뱅크' in c[:300] or 'kbank' in c[:300]:
            return (['Kafka', '개발', '주식서비스'], ['실무경험'], 'Kafka를 활용한 주식 서비스 MSA 개발 경험 정리.')
        if 'avro' in f or 'avro' in c[:300]:
            return (['Kafka', '개발', '인프라'], ['실무경험'], 'Kafka Avro를 활용한 메시지 직렬화 구현 정리.')
        if 'failing offset' in f or 'failing offset' in c[:300]:
            return (['Kafka', '개발', '이슈정리'], ['실무경험'], 'Kafka failing offset 이슈 해결 경험 정리.')
        if 'cdc' in f or 'debezium' in f or 'cdc' in c[:300]:
            return (['Kafka', '개발', '인프라'], ['기술'], 'PostgreSQL CDC + Debezium + Kafka를 활용한 EDA 구현 정리.')
        return (['Kafka', '개발'], ['실무경험'], 'Kafka 관련 개발 내용 정리.')

    # KEDA posts
    if 'keda' in f:
        if 'kafka' in f or 'kafka' in c[:300]:
            return (['KEDA', 'Kafka', 'Kubernetes'], ['기술'], 'KEDA ScaledJob과 Kafka를 연동한 Kubernetes 스케일링 정리.')
        return (['KEDA', 'Kubernetes', '인프라'], ['기술'], 'KEDA를 활용한 Kubernetes 오토스케일링 구현 정리.')

    # Kubernetes posts
    if 'kubernetes' in f or 'eks' in f or 'k8s' in f:
        if 'kafka' in f or 'kafka' in c[:300]:
            return (['Kubernetes', 'Kafka', '인프라'], ['기술'], 'EKS와 Kafka를 연동한 인프라 구성 정리.')
        if 'keda' in f or 'keda' in c[:300]:
            return (['Kubernetes', 'KEDA', '인프라'], ['기술'], 'Kubernetes KEDA를 활용한 스케일링 구현 정리.')
        if 'pod' in f or 'pod' in c[:300]:
            return (['Kubernetes', '인프라', '이슈정리'], ['기술'], 'EKS Pod 관련 이슈 해결 내용 정리.')
        return (['Kubernetes', '인프라'], ['기술'], 'Kubernetes/EKS 관련 인프라 구성 정리.')

    # CI/CD posts
    if 'gitlab' in f or 'sonarqube' in f or 'sonar' in f or 'gradle' in f or 'ci)' in f or 'ci -' in f or 'ci_' in f:
        if 'gradle' in f and ('settings' in f or 'build' in f):
            return (['CI/CD', '개발', 'Java'], ['기술'], 'Gradle 설정 관련 개발 환경 구성 정리.')
        if 'gitlab' in f and 'saml' in f:
            return (['Git', 'CI/CD', '개발'], ['실무경험'], 'GitLab SAML 환경에서 clone 설정 정리.')
        if 'python' in f or 'python' in c[:300]:
            return (['CI/CD', 'Python', '개발'], ['기술'], 'CI 파이프라인에서 Python Sonarqube 연동 구성 정리.')
        return (['CI/CD', '개발'], ['기술'], 'CI/CD 파이프라인 구성 및 최적화 정리.')

    # Git posts
    if 'gitlab' in f and not ('ci' in f or 'sonar' in f):
        return (['Git', '개발'], ['실무경험'], 'GitLab 관련 개발 환경 설정 정리.')
    if 'gradle' in f:
        if 'multi module' in f or 'submodule' in f:
            return (['Git', 'CI/CD', '개발'], ['기술'], 'Gradle Multi Module과 GitLab Submodule 구성 정리.')
        return (['CI/CD', '개발', 'Java'], ['기술'], 'Gradle 빌드 설정 구성 정리.')

    # Argo / jflow / workflow posts
    if 'argo' in f or 'jflow' in f:
        if 'argo-cd' in f or 'argo cd' in f:
            return (['인프라', 'CI/CD'], ['기술'], 'ArgoCD를 활용한 배포 파이프라인 구성 정리.')
        if 'python' in f or 'python' in c[:300]:
            return (['Python', '인프라', '개발'], ['기술'], 'Python과 Argo Workflow(jflow)를 활용한 파이프라인 구성 정리.')
        return (['인프라', '개발'], ['기술'], 'Argo Workflow(jflow)를 활용한 워크플로우 구성 정리.')

    # Python posts
    if 'python' in f:
        if 'istio' in f or 'sidecar' in f or 'istio' in c[:300]:
            return (['Python', 'Kubernetes', '인프라'], ['기술'], 'Python 서비스의 ISTIO 사이드카 관련 이슈 해결 정리.')
        if 'langchain' in f or 'mcp' in f or 'langchain' in c[:300]:
            return (['Python', 'AI/ML', '기술'], ['기술'], 'Langchain Tool과 MCP를 활용한 AI 에이전트 구현 정리.')
        if 'keda' in f or 'keda' in c[:300]:
            return (['Python', 'KEDA', 'Kubernetes'], ['기술'], 'Python + KEDA ScaledJob 구성 정리.')
        return (['Python', '개발'], ['기술'], 'Python 개발 관련 내용 정리.')

    # AI/ML posts
    if 'rag' in f or 'langraph' in f or 'langchain' in f or 'llm' in f or 'copilot' in f or 'ai facilitator' in f:
        if '공시' in f or '주식' in f or '재무' in f:
            return (['AI/ML', '주식서비스', '기술'], ['기술'], 'AI/ML을 활용한 금융 데이터 처리 및 RAG 구현 정리.')
        if 'm365' in f or 'confluence' in f:
            return (['AI/ML', '기술'], ['기술'], 'M365 Confluence 데이터를 활용한 RAG 시스템 구현 정리.')
        return (['AI/ML', '기술'], ['기술'], 'AI/ML 관련 기술 탐구 및 구현 정리.')

    # Mediation pattern posts
    if 'mediation' in f or 'mediaion' in f:
        if 'reactor' in f or 'webflux' in f or 'non-blocking' in f:
            return (['개발', '아키텍처', 'Java'], ['실무경험'], 'Mediation 패턴 구현 시 Reactor/WebFlux 기반 논블로킹 처리 정리.')
        if 'feign' in f or 'webclient' in f:
            return (['개발', '아키텍처', 'Java'], ['실무경험'], 'Mediation 패턴 구현 시 FeignClient vs WebClient 비교 정리.')
        if 'virtual thread' in f or 'java21' in f:
            return (['개발', '아키텍처', 'Java'], ['실무경험'], 'Mediation 패턴 구현에서 Virtual Thread(Java 21) 적용 정리.')
        if 'kotlin' in f or 'coroutine' in f:
            return (['개발', '아키텍처', 'Java'], ['실무경험'], 'Mediation 패턴에 Kotlin 코루틴을 적용한 구현 정리.')
        if 'interceptor' in f or 'threadlocal' in f:
            return (['개발', '아키텍처', 'Java'], ['실무경험'], 'Mediation 패턴에서 Interceptor, ThreadLocal, ServletContext 활용 정리.')
        if 'recycle_facades' in f:
            return (['개발', '아키텍처', 'Java'], ['실무경험'], 'Mediation 패턴의 RECYCLE_FACADES 설정 관련 정리.')
        if 'microservice' in f or '마이크로서비스' in c[:300] or 'webflux' in c[:300]:
            return (['개발', '아키텍처', 'Java'], ['실무경험'], 'Mediation 패턴 구현 과정에서 마이크로서비스 아키텍처 관련 정리.')
        return (['개발', '아키텍처', 'Java'], ['실무경험'], 'Mediation 패턴 구현 과정 정리.')

    # Redis / Cache posts
    if 'redis' in f or 'elasticache' in f or 'cache' in f or '캐시' in f:
        if 'pubsub' in f or 'pub/sub' in f or 'pub_sub' in f:
            return (['캐싱', '개발', '인프라'], ['실무경험'], 'Redis pub/sub을 활용한 로컬 캐시 동기화 구현 정리.')
        if 'elasticache' in f:
            return (['AWS', '인프라', '캐싱'], ['실무경험'], 'Elasticache 관련 인프라 이슈 분석 및 해결 정리.')
        if 'r2dbc' in f or 'reactive' in f:
            return (['캐싱', '개발', 'Java'], ['기술'], 'Spring Reactive Redis 환경 구성 및 구현 정리.')
        return (['캐싱', '개발'], ['기술'], '캐시 관련 개발 및 설정 정리.')

    # DB posts
    if 'db sync' in f or 'edb' in f or 'jpa' in f or 'mybatis' in f or 'querydsl' in f or 'r2dbc' in f:
        if 'jpa oom' in f or 'oom' in f:
            return (['DB', '개발', '이슈정리'], ['실무경험'], 'JPA OOM 이슈 분석 및 해결 정리.')
        if 'jpa' in f:
            return (['DB', '개발', 'Java'], ['기술'], 'JPA 관련 개발 내용 정리.')
        if 'mybatis' in f or 'querydsl' in f:
            return (['DB', '개발', 'Java'], ['기술'], 'Mybatis와 QueryDSL 혼용 관련 개발 정리.')
        return (['DB', '개발'], ['기술'], 'DB 관련 개발 내용 정리.')

    # Stock service posts
    if '주식' in title or '공모주' in title or '비상장' in title or 'ipo' in f or 'ipo' in c[:300]:
        if '비상장' in title or '비상장' in c[:300]:
            return (['주식서비스', '개발'], ['비상장주식알림서비스'], '비상장주식 관련 서비스 개발 내용 정리.')
        if '공모주' in title or '공모주' in c[:300]:
            return (['주식서비스', '개발', 'DB'], ['실무경험'], '공모주 서비스 관련 개발 및 쿼리 최적화 정리.')
        return (['주식서비스', '개발'], ['실무경험'], '주식 서비스 관련 개발 내용 정리.')

    # Finance/Investment posts
    if '재무' in title or '투자온도' in title or '투자' in title or 'k-ifrs' in f or '재무' in c[:200]:
        return (['재무', '주식서비스'], ['재테크'], '재무 데이터 분석 및 투자 관련 내용 정리.')

    # Meeting notes / scrum
    if 'scrum' in f or '회의' in f or '회의록' in f or 'ot' in f.split('-')[-1].lower() or '요건확정' in f:
        return (['기획', '개발'], ['실무경험'], '스크럼/회의 내용 및 요건 정리.')

    # Spring/Java posts
    if 'spring' in f or 'java' in f or 'jpa' in f or 'layer' in f or 'query based' in f:
        if 'reactive' in f or 'r2dbc' in f:
            return (['개발', 'Java', 'DB'], ['기술'], 'Spring Reactive 환경 구성 및 구현 정리.')
        return (['개발', 'Java'], ['기술'], 'Spring/Java 관련 개발 내용 정리.')

    # BFF post
    if 'bff' in f or 'backend-for-frontend' in f:
        return (['개발', '아키텍처'], ['기술'], 'BFF(Backend-For-Frontend) 패턴 관련 아키텍처 정리.')

    # API gateway / netty
    if 'api-gateway' in f or 'api gateway' in f or 'netty' in f:
        return (['개발', '인프라', '아키텍처'], ['실무경험'], 'API Gateway 관련 설정 및 이슈 해결 정리.')

    # MSA / Architecture posts
    if 'msa' in f or 'mci' in f or 'arch' in f:
        return (['개발', '아키텍처'], ['기술'], 'MSA 아키텍처 관련 설계 및 개발 정리.')

    # Tracelog
    if 'tracelog' in f or 'trace' in f:
        return (['인프라', '개발'], ['실무경험'], '분산 추적 로그(Tracelog) 관련 구현 정리.')

    # S3 / logback
    if 's3' in f or 'logback' in f:
        return (['AWS', '개발', '인프라'], ['기술'], 'S3와 Logback을 활용한 로그 저장 구현 정리.')

    # Interview / 면접
    if '면접' in f or 'interview' in f:
        return (['개발', '기술'], ['실무경험'], '기술 면접 관련 내용 정리.')

    # Seminar notes
    if '세미나' in f or 'seminar' in f or '컨퍼런스' in f:
        if 'aws' in f or 'aws' in c[:300]:
            return (['AWS', '기술'], ['기술'], 'AWS 세미나 내용 정리.')
        return (['기술'], ['기술'], '세미나 내용 정리.')

    # POC / 회의록
    if 'poc' in f or '회의록' in f:
        return (['기획', '개발'], ['실무경험'], 'POC 또는 회의 내용 정리.')

    # Keycloak / security
    if 'keycloak' in f or '키클로크' in f:
        return (['인프라', '개발'], ['기술'], 'Keycloak 인증/인가 시스템 구성 정리.')

    # 동호회 / 활동
    if '실내합니다' in f or '동호회' in f or '전시' in f or 'ot' in f.lower().split('-')[-1][:5]:
        return (['기획'], ['실무경험'], '동호회 활동 및 모임 기록.')

    # Maplestory / game related
    if '마이키즈' in f or '마이키즈' in title:
        return (['개발', '기획'], ['실무경험'], '마이키즈 서비스 관련 개발 및 기획 논의 정리.')

    # 주간 투자왕 / game service
    if '집계' in f or '게임' in f or 'mgm' in f.lower() or '배치' in f.lower() or 'batch' in f.lower():
        if 'spring batch' in c[:500] or 'springbatch' in c[:500]:
            return (['Spring Batch', '개발', 'Java'], ['기술'], 'Spring Batch 관련 개발 내용 정리.')
        return (['개발', '기획', '주식서비스'], ['실무경험'], '주식 게임 서비스 개발 및 기획 논의 정리.')

    # 채널 연동
    if '채널' in f:
        return (['개발', '기획', '주식서비스'], ['실무경험'], '채널 연동 관련 개발 논의 정리.')

    # OpenDart
    if 'opendart' in f or 'dart' in f:
        return (['개발', '주식서비스'], ['비상장주식알림서비스'], 'OpenDart API를 활용한 공시 데이터 수집 정리.')

    # 다중 데이터소스 / DB
    if 'datasource' in f or 'multiple' in f:
        return (['DB', '개발', 'Spring Batch'], ['기술'], '다중 DataSource 구성 관련 개발 정리.')

    # Charset / encoding
    if 'charset' in f or 'encoding' in f:
        return (['개발', '이슈정리'], ['실무경험'], '문자 인코딩 이슈 해결 내용 정리.')

    # Layered architecture
    if 'layer' in f or '레이어' in f:
        return (['개발', '아키텍처', 'Java'], ['기술'], '레이어드 아키텍처 관련 설계 정리.')

    # Hardcoding vs Enum vs separation
    if '하드코딩' in f or 'enum' in f or '분리' in f:
        return (['개발', '아키텍처', 'Java'], ['기술'], '하드코딩 vs Enum vs 코드 분리 전략 정리.')

    # ERD
    if 'erd' in f:
        return (['DB', '기획'], ['실무경험'], '데이터베이스 ERD 설계 내용 정리.')

    # Query OOP
    if 'query based' in f or 'oop' in f:
        return (['개발', '아키텍처', 'Java'], ['기술'], 'Query 기반에서 OOP 전환 관련 설계 정리.')

    # STK / 상품
    if 'stk' in f or '상품' in f or 'public' in f.lower():
        return (['주식서비스', '개발'], ['실무경험'], '주식 서비스 상품 관련 개발 내용 정리.')

    # 상속 / 패턴
    if '상속' in f or '패턴' in f or 'recursive' in f:
        return (['개발', '아키텍처', 'Java'], ['기술'], '상속 구조 및 재귀 패턴 관련 설계 정리.')

    # 업그레이드 / migration
    if '업그레이드' in f or 'upgrade' in f or 'migration' in f or '마이그레이션' in f:
        return (['개발', '인프라'], ['실무경험'], '서비스 업그레이드 및 마이그레이션 내용 정리.')

    # 분산트랜잭션 / saga
    if '분산' in f or 'saga' in f or 'transaction' in f:
        return (['개발', '아키텍처'], ['기술'], '분산 트랜잭션 및 Saga 패턴 관련 정리.')

    # 일일정리 / review
    if '일일정리' in f or '회고' in f or '현황' in f:
        return (['개발', '기획'], ['실무경험'], '개발 현황 및 일일 정리 노트.')

    # 환경구성 / 임시설정
    if '환경' in f or '임시' in f or '설정' in f:
        return (['개발', '인프라'], ['기술'], '개발 환경 구성 및 임시 설정 관련 정리.')

    # Associate / 미니프로젝트
    if 'associate' in f or '미니 프로젝트' in f or '어소시에이트' in c[:200]:
        return (['개발', '기획'], ['실무경험'], '어소시에이트 미니 프로젝트 제출 관련 내용 정리.')

    # 도식화 / 아키텍처 도면
    if '도식화' in f or '아키텍처' in f:
        return (['아키텍처', '개발'], ['기술'], '서비스 아키텍처 도식화 관련 정리.')

    # 재무데이터 / 요약
    if '재무' in f or 'financial' in f:
        return (['재무', '주식서비스'], ['재테크'], '재무 데이터 분석 및 정리.')

    # 미팅 / 기획 관련
    if '논의' in f or '끄적' in f or '정리' in f:
        return (['기획', '개발'], ['실무경험'], '개발 논의 및 기획 내용 정리.')

    # api spec
    if 'api' in f or 'api-spec' in f:
        return (['개발', '기획'], ['실무경험'], 'API 명세 및 설계 관련 정리.')

    # Generic tech
    return (['개발', '기술'], ['실무경험'], '개발 관련 내용 정리.')


def has_intro(body):
    """Check if post body already has a meaningful intro sentence."""
    lines = [l.strip() for l in body.split('\n') if l.strip()]
    if not lines:
        return False
    first = lines[0]
    # If it starts with #, image, or link it's not an intro
    if first.startswith('#') or first.startswith('!') or first.startswith('[') or first.startswith('```') or first.startswith('-') or first.startswith('|'):
        return False
    # If it's a meaningful sentence (20+ chars)
    if len(first) >= 20:
        return True
    return False


def fix_informal(text):
    """Light cleanup of informal language patterns."""
    # Fix common informal endings in sentence positions
    # ㄱㄱ, ㅎㅎ, ㅋㅋ
    text = re.sub(r'ㄱㄱ', '진행합니다', text)
    text = re.sub(r'ㅎㅎ', '', text)
    text = re.sub(r'ㅋㅋ+', '', text)
    text = re.sub(r'ㅠㅠ+', '', text)
    # Remove trailing empty parentheses from cleanup
    text = re.sub(r'\(\s*\)', '', text)
    return text


def process_front_matter(content, tags, categories):
    """Replace tags and category in front matter."""
    # Replace tags: [미지정] or tags:\n  - 미지정
    tags_yaml = 'tags:\n' + ''.join(f'  - {t}\n' for t in tags)
    cat_yaml = 'category:\n' + ''.join(f'  - {c}\n' for c in categories)

    # Replace tags line
    content = re.sub(r'tags:\s*\[미지정\]', tags_yaml.rstrip(), content)
    content = re.sub(r'tags:\n(\s*-\s*미지정\s*\n?)+', tags_yaml, content)

    # Replace category: 기타 with proper category
    content = re.sub(r'category:\n(\s*-\s*기타\s*\n?)+', cat_yaml, content)
    # Also replace if category has 미지정
    content = re.sub(r'category:\n(\s*-\s*미지정\s*\n?)+', cat_yaml, content)

    return content


def add_intro(content, intro):
    """Add intro sentence after front matter if missing."""
    # Find end of front matter
    parts = content.split('---', 2)
    if len(parts) < 3:
        return content
    front = parts[1]
    body = parts[2]

    if has_intro(body):
        return content

    # Add intro after front matter
    new_body = '\n' + intro + '\n' + body.lstrip('\n')
    return '---' + front + '---' + new_body


# Process all files
for i, (filename, path) in enumerate(untagged, 1):
    with open(path, encoding='utf-8') as fp:
        content = fp.read()

    tags, categories, intro = classify(filename, content)

    # Process front matter
    new_content = process_front_matter(content, tags, categories)

    # Light informal cleanup
    new_content = fix_informal(new_content)

    # Add intro if needed
    new_content = add_intro(new_content, intro)

    # Write back
    with open(path, 'w', encoding='utf-8') as fp:
        fp.write(new_content)

    print(f"[{i:3d}/155] Processed: {filename[:60]}", file=sys.stderr)
    print(f"  Tags: {tags}, Category: {categories}", file=sys.stderr)

print("All done!", file=sys.stderr)
