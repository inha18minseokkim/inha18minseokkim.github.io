---
title: "**Low-cost logging and observability with Amazon OpenSearch Service**"
date: 2025-12-02
tags: [미지정]
category:
  - 기타
---

Reduce storage to optimize costs
Compression
Index Rollups - 오래된 데이터는 aggregate 해버림
Optimized Instance
Selective Ingestion

규모 커지면
integrate 하고 S3에 메타데이터 인덱스 넣어서 인덱스 스킵 가능하도록 하고 opensearch index에 미리 원하는 방식대로 인덱싱 해놓음(materialized view) 

Storage tiering
Hot(Data Nodes) - Warm(Ultrawarm nodes) - Cold(Cold Storage)

[Optimize storage costs in Amazon OpenSearch Service using Zstandard compression | Amazon Web Services](https://aws.amazon.com/jp/blogs/big-data/optimize-storage-costs-in-amazon-opensearch-service-using-zstandard-compression/)

직접 쿼리를 사용하면 수집 파이프라인을 구축하거나 OpenSearch에 데이터를 인덱싱하지 않고도 Amazon CloudWatch Logs, Amazon S3, Amazon Security Lake에 있는 데이터를 쿼리할 수 있습니다. 직접 쿼리는 수집 파이프라인을 구축할 필요성을 없애고 클러스터 내 스토리지 필요성을 크게 줄입니다. 이는 종종 [제로 ETL 통합 으로 언급됩니다. ](https://aws.amazon.com/what-is/zero-etl/).
[이 모듈에서는 S3에 직접 쿼리를](https://docs.aws.amazon.com/opensearch-service/latest/developerguide/direct-query-s3-overview.html) 설정합니다.[ ](https://docs.aws.amazon.com/opensearch-service/latest/developerguide/direct-query-s3-overview.html)S3 버킷에 저장된 VPC 흐름 로그를 쿼리합니다. Amazon S3에 저장된 로그를 분석하는 방법을 배우게 됩니다. 이 접근 방식은 다음과 같은 방식으로 로그 분석을 간소화합니다.
- 복잡한 ETL 프로세스 제거
- 데이터 복제와 관련된 비용 절감
- 최신 로그 데이터에 대한 실시간에 가까운 액세스 제공
- 빠르게 증가하는 로그 볼륨을 처리하기 위해 쉽게 확장 가능
다음은 OpenSearch 서비스와 S3 직접 쿼리 통합의 아키텍처 다이어그램입니다.

![](https://static.us-east-1.prod.workshops.aws/731c0e51-84cf-46c9-aba3-016fdf810d9f/static/zETL/zero-etl-vpc-flow.png?Key-Pair-Id=K36Q2WVO3JP7QD&Policy=eyJTdGF0ZW1lbnQiOlt7IlJlc291cmNlIjoiaHR0cHM6Ly9zdGF0aWMudXMtZWFzdC0xLnByb2Qud29ya3Nob3BzLmF3cy83MzFjMGU1MS04NGNmLTQ2YzktYWJhMy0wMTZmZGY4MTBkOWYvKiIsIkNvbmRpdGlvbiI6eyJEYXRlTGVzc1RoYW4iOnsiQVdTOkVwb2NoVGltZSI6MTc2NTMyMjM5OX19fV19&Signature=H6FS7AvgZBAV5ODVyx5QuqbbfXCbtnRm6cz8zEuy8%7EKy3PZEwJGlEpFTqXKyEcoUvgX3%7EnU6IHud%7EoycADOOQPZX0%7EOOM96LzgZyDoxFNy28%7EWug0VFYX6E2H%7Ec2pTlIQ6VcRUakLYpYynx2ke1GMEDP6wfCX1L9Eq17jIIdFmoZRnO12e44T-Vrk6dE1iNoQVIB-pqFD1UQzhC5nSnWPuBSwgkUYbS8TgYvhP1wlJEWfyYvo6DealFh1dRSyKLvZB7GVYmwrZZcOZrz6Si0PZfjHGhMVQZr5aJgt%7E1t5oiWlOhmA3CTeHtgdUfY%7EW1wHRG9bNAw1xg8vHodXy%7EV8Q__)

OpenSearch 서비스는 세 가지 유형의 [가속을 제공합니다. ](https://docs.opensearch.org/latest/dashboards/management/accelerate-external-data/)다양한 인덱스를 생성하여 S3에서 쿼리 성능을 향상하는 방법을 알아봅니다. 이 모듈에서는 OpenSearch에서 사용 가능한 각 유형의 가속을 살펴보겠습니다.
- [설정](https://catalog.workshops.aws/event/dashboard/en-US/workshop/module-2-direct-query/setup)
- [직접 쿼리](https://catalog.workshops.aws/event/dashboard/en-US/workshop/module-2-direct-query/directquery)
- [가속 쿼리](https://catalog.workshops.aws/event/dashboard/en-US/workshop/module-2-direct-query/acceleratedqueries)
- [심상](https://catalog.workshops.aws/event/dashboard/en-US/workshop/module-2-direct-query/visualisation)
- [데이터 레이크 모범 사례](https://catalog.workshops.aws/event/dashboard/en-US/workshop/module-2-direct-query/datalakeoptimization)