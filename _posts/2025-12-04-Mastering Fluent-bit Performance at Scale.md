---
title: "Mastering Fluent-bit: Performance at Scale"
date: 2025-12-04
tags:
  - AWS
  - 기술
category:
  - 기술
---
fluentbit는 사이드카로 ecs컨테이너 환경에서 워크샵 진행

![](attachment:94dc0f74-64cd-4d85-bba1-893ed496a7fa:image.png)

[**View Application Logs**](https://catalog.workshops.aws/event/dashboard/en-US/workshop/lab0-getting-started/step2-environment-review#view-application-logs)
Let's check recent logs from the Catalog service:
`aws logs tail /aws/fluentbit-workshop/lab0/catalog-logs --follow --since 1d --format json`
✨ As you browse the catalog, you can see "GET" request logs appear in CloudWatch, almost instantly!
Press `Ctrl+C` to stop tailing the logs.
🔎 Notice that the log events are enriched with metadata like the ECS task ARN, and container name - Can you figure out how?
**Hint**
Use the AWS CLI to inspect the ECS task definition and look for a FirelensConfiguration setting:
`aws ecs describe-task-definition --task-definition fluentbit-lab0-ui --no-cli-pager`
**Answer**
The task definition's `log-router` container includes the following FirelensConfiguration option:
`1
2
3
4
5
6
"firelensConfiguration": {
  "type": "fluentbit",
  "options": {
    "enable-ecs-log-metadata": "true"
  }
}`
The `enable-ecs-log-metadata: "true"` setting tells Fluent Bit to automatically enrich logs with ECS task metadata such as task ARN, container name, cluster name, and task definition information.
[**View Fluent Bit Logs**](https://catalog.workshops.aws/event/dashboard/en-US/workshop/lab0-getting-started/step2-environment-review#view-fluent-bit-logs)
Fluent Bit's logs are sent to CloudWatch using the awslogs driver and not Fluent Bit itself. This is to ensure that we do not create a cyclic dependency and have Fluent Bit's logs available through an alternate mechanism, for debugging issues with the logging setup.
Lets inspect the Fluent Bit logs from the UI service:
`aws logs tail /aws/fluentbit-workshop/lab0/ui-fluent-bit-logs --follow --since 1d`
This gives you a glimpse into Fluent Bit's internal operations. We can see that Fluent Bit is reading the application's stdout/stderr logs using the `forward` input plugin, and routing them to a newly created CloudWatch log stream using the `cloudwatch_logs` output plugin.
Press `Ctrl+C` to stop tailing the logs.


보시다시피, 로그에 fluent-bit가 입력 플러그인을 자주 일시 중지해야 한다는 경고가 몇 개 있습니다. 이는 "전방" 입력 플러그인에 구성된 출력 플러그인(이 경우 cloudwatch_logs 출력 플러그인)으로 로그를 플러시하기 전에 메모리 내 버퍼에 로그가 채워지고 있음을 의미합니다. 이 버퍼가 채워지면 전방 입력은 새 로그 수신을 일시 중지해야 하며, 이는 애플리케이션에 따라 [백프레셔를 발생시키거나 ](https://docs.fluentbit.io/manual/administration/backpressure)IO를 플러싱하거나 단순히 로그를 삭제할 수도 있습니다.
Docker → Fluent Bit 순방향 입력 설정에서 입력 버퍼가 한계에 도달하면 Fluent Bit가 입력을 일시 중지하여 Docker 로깅 드라이버에 백프레셔(backpressure)를 발생시킵니다. 이로 인해 로그 쓰기가 완료될 때까지 애플리케이션 속도가 느려지거나 Docker 자체 버퍼의 메모리 사용량이 증가할 수 있습니다. 백프레셔는 프로덕션 환경에서는 피해야 할 요소입니다.

**예상 출력**
- `-- fluent-bit.step2.conf	2025-10-28 12:46:40
+++ fluent-bit.step3.conf	2025-10-28 13:06:07
@@ -10,7 +10,7 @@ Name forward unix_path /var/run/fluent.sock # Defines a limit on how much input data to accept before pausing
- Mem_Buf_Limit 5MB
+ Mem_Buf_Limit 40MB # Run the input in it's own thread threaded true`
Mem_Buf_Limit은 fluent-bit의 출력 플러그인에서 아직 플러시되지 않은 로그를 보관하기 위해 각 *입력* 플러그인이 얼마나 많은 메모리를 할당할지를 결정하는 fluent-bit 구성 매개변수입니다 .
이 매개변수를 설정하면 fluent-bit가 과도한 메모리를 점유하여 OOM-kill되는 것을 방지할 수 있으므로 권장되지만, 워크로드에 비해 너무 낮게 설정하면 심각한 백프레셔가 발생할 수 있습니다. 또한 이 매개변수는 작동 중인 메모리 한도를 인식하지 못하므로 너무 높게 설정해도 OOM-kill이 발생할 수 있습니다.
"mem buf overlimit" 경고가 표시되므로 백프레셔가 발생하고 있다고 추정할 수 있습니다. Mem_Buf_Limit 값을 높여서 오버리밋 경고가 해결되는지 확인해 보겠습니다. 또한, Lua 필터의 메트릭을 사용하여 처리량 변화를 모니터링할 수 있습니다.
Let's look again at the **"Log Throughput By Task"** graph in your dashboard. We should now see a new line appearing for our new task with its higher mem_buf_limit. We should also see that its throughput is noticeably higher than the previous task, since our input plugin is no longer needing to pause and is no longer applying backpressure on our application.


- `-- fluent-bit.step3.conf	2025-11-10 22:54:08
+++ fluent-bit.step4.conf	2025-11-10 22:53:52
@@ -5,12 +5,15 @@ Flush 1 # Gives Fluent Bit time to send pending data after SIGTERM Grace 30
+ storage.path /var/log/flb-storage/
+ # Limit the filesystem storage that each output can use
+ storage.total_limit_size 2G [INPUT] Name forward unix_path /var/run/fluent.sock
- # Defines a limit on how much input data to accept before pausing
- Mem_Buf_Limit 40MB
+ # Filesystem storage does not use Mem_Buf_Limit
+ storage.type filesystem # Run the input in it's own thread threaded true`
위에서 볼 수 있듯이, 이제 Mem_Buf_Limit을 완전히 제거하고 파일 시스템 저장소를 활용하고 있습니다. Mem_Buf_Limit을 높이는 것이 대부분의 사용자에게는 충분한 해결책이 될 수 있지만, 로깅이 증가함에 따라 어느 시점에 새로운 제한에 도달하여 다시 백프레셔를 경험하게 될 위험이 있습니다.
메모리에만 버퍼링하는 대신, fluent-bit는 파일 시스템 버퍼링 기능도 제공합니다. 파일 시스템 버퍼링의 장점은 영구적이며 메모리 버퍼링보다 더 큰 버퍼를 저장할 수 있다는 것입니다. 하지만 디스크 I/O가 증가하고 fluent-bit의 CPU 사용량이 약간 증가한다는 단점이 있습니다.
우리의 사용 사례에서 파일 시스템 버퍼링이 우리의 작업 부하를 처리할 수 있는지 살펴보겠습니다.
다음 단계에서는 파일 시스템 버퍼링을 구성에 추가하고 이것이 처리량, 메모리, CPU 및 IO 메트릭에 어떻게 영향을 미치는지 살펴보겠습니다.

**메모리 사용량**
메모리 사용량이 다소 감소한 것은 사실이지만, "파일 시스템 저장소"라는 용어가 모든 로그가 메모리가 아닌 파일 시스템에 버퍼링된다는 것을 의미하기 때문에 일부 사람들이 예상했던 것만큼 극적이지는 않을 수 있습니다.
하지만 현실은 좀 더 복잡합니다. 파일 시스템 저장소를 사용하는 경우, 플루언트 비트 엔진은 **콘텐츠를 메모리에 저장 하고 **[mmap을](https://man7.org/linux/man-pages/man2/mmap.2.html) 통해 디스크에 복사본을 매핑합니다.[ ](https://man7.org/linux/man-pages/man2/mmap.2.html)새로 생성된 청크는 메모리에서 활성화되고, 디스크에 백업되며, "up"이라고 불리는데, 이는 청크 내용이 메모리에 있다는 것을 의미합니다.
따라서 청크가 대부분 "사용 중"이고 파일 시스템과 메모리에 모두 저장되기 때문에 메모리 이득은 크지 않습니다.

**예상 출력**
- `-- fluent-bit.step4.conf	2025-10-28 13:32:38
+++ fluent-bit.step5.conf	2025-10-28 13:59:04
@@ -6,6 +6,8 @@ # Gives Fluent Bit time to send pending data after SIGTERM Grace 30 storage.path /var/log/flb-storage/
+ # Conservatively each chunk can use 4-5MB so 8 chunks = ~32-40MB of memory
+ storage.max_chunks_up 8 # Limit the filesystem storage that each output can use storage.total_limit_size 2G`
이제 매개변수를 추가하고 있는 것을 볼 수 있습니다 `storage.max_chunks_up`. 이 매개변수는 파일 시스템 저장 옵션이 메모리에 얼마나 많은 메모리를 저장할지 제어합니다.
파일 시스템 저장소를 사용하는데 왜 메모리를 사용하는지 궁금하실 겁니다. 파일 시스템 저장소를 사용하는데 왜 OOM-kill 오류가 발생하는 걸까요?
답은 파일 시스템 저장소를 사용하는 경우 Fluent-bit 엔진이 **메모리에 콘텐츠를 저장 하고 **[mmap을](https://man7.org/linux/man-pages/man2/mmap.2.html) 통해 디스크에 복사본을 매핑한다는 것입니다.[ ](https://man7.org/linux/man-pages/man2/mmap.2.html)새로 생성된 청크는 메모리에서 활성화되고, 디스크에 백업되며, "up"이라고 불리는데, 이는 청크 내용이 메모리에 있다는 것을 의미합니다.
[storage.max_chunks_up](https://docs.fluentbit.io/manual/administration/buffering-and-storage#service-section-configuration) 이라는 구성 매개변수가 있습니다.[ ](https://docs.fluentbit.io/manual/administration/buffering-and-storage#service-section-configuration) 파일 시스템 저장소를 사용할 때 메모리에 "업"될 수 있는 청크 수를 제어하며, 기본값은 128입니다. 각 청크는 *최소* 2MB(출력 플러그인을 위해 각 청크를 JSON으로 언마샬링해야 하는 경우가 많기 때문에 더 큰 경우도 많음)를 사용하므로 상당한 양의 메모리를 사용할 수 있습니다. 보수적으로 계산하면 각 청크는 4~5MB의 메모리를 사용할 것으로 예상할 수 있습니다.
log_router 컨테이너의 메모리가 52MB에 불과하므로 메모리 범위 내에 있도록 max_chunks_up을 줄여야 합니다.

랩 1에서는 Lua 스크립트를 사용하여 애플리케이션 처리량을 측정하고 Fluent Bit 입력의 병목 현상을 파악했습니다. 




l2
애플리케이션 처리량 문제 해결에 따라 AnyCompany Media Group은 K팝 스트리밍 서비스를 전 세계로 확장했습니다. 그러나 이러한 확장은 다음과 같은 새로운 과제를 야기했습니다.
- 지역 스트리밍 노드와 중앙 로깅 시스템 간에 간헐적인 네트워크 연결 문제가 발생합니다.
- 다양한 시간대의 최대 시청 시간 동안 네트워크 혼잡이 발생합니다.
- 로그 전달 실패로 인해 분석 및 규정 준수 데이터에 차이가 발생합니다.
- 네트워크 중단 시 비즈니스 통찰력과 감사 로그에 영향을 미치는 잠재적인 데이터 손실이 발생합니다.

첫 번째 최적화 방식부터 시작해 보겠습니다. 이 최적화에는 두 가지 측면이 있습니다.
1. 재시도 제한 증가:
기본적으로 대상 위치로 로그를 플러시하는 데 실패하면 Fluent Bit는 한 번 재시도합니다. `retry_limit 15`아래 출력 구성의 는 Fluent Bit 엔진에 애플리케이션 로그 전송을 최소 1회에서 최대 15회까지 재시도하도록 요청합니다. 또한 는 `scheduler.base 1`각 `scheduler.cap 10`재시도 간격을 1초에서 10초 사이로 정의합니다.
1. 멀티스레딩:
애플리케이션 로그 입력에 를 사용하면 `threaded true`입력 플러그인이 Fluent Bit의 메인 이벤트 루프와 별도로 자체 전용 스레드에서 실행됩니다. 또한 를 사용하면 `workers 2`애플리케이션 로그 출력 플러그인에 두 개의 스레드가 생성되어 로그를 Cloudwatch에 병렬로 플러시합니다.
2단계의 기준 구성과 비교 **한 차이점을 확인하세요 .**
`diff --color --unified fluentbit-baseline.conf fluentbit-retries-workers.conf`
- `-- fluentbit-baseline.conf
+++ fluentbit-retries-workers.conf
@@ -7,6 +7,8 @@ HTTP_Server On HTTP_Listen 0.0.0.0 HTTP_PORT 2020
+ # Minimum backoff between retries
+ scheduler.base 1
+ # Maximum backoff between retries
+ scheduler.cap 10 # Capture App's stdout logs [INPUT]
@@ -14,6 +16,7 @@ Alias app-logs-input Tag app-logs-input unix_path /var/run/fluent.sock
+ threaded true # Capture Fluent Bit's metrics [INPUT]
@@ -33,6 +36,8 @@ region ${AWS_REGION} log_group_name /aws/fluentbit-workshop/lab2/app-logs log_stream_name ${ECS_TASK_ID}
+ workers 2
+ retry_limit 15 # Send Fluent Bit's metrics to CloudWatch Logs [OUTPUT]`
**Review**
In this lab you:
- Configured Fluent Bit's built-in metrics using Prometheus scraping and CloudWatch EMF output (Step 3).
- Injected network faults to simulate real-world connectivity issues and observed baseline behavior (Step 3).
- Identified dropped records as evidence of output bottlenecks under network stress (Step 3).
- Optimized with increased retry limits and worker threads to reduce data loss (Step 4.1).
- Implemented filesystem buffering with extended grace periods for maximum resilience (Step 4.2).
- Compared resource usage (CPU, memory) across different optimization approaches (Steps 4.1 & 4.2).

l3
**예상 출력**
- `-- fluent-bit.step3.conf 2025-M-D 00:11:48.677900789 +0000
+++ fluent-bit.step3-optimized.conf 2025-M-D 00:19:23.256734142 +0000
@@ -27,6 +27,11 @@ refresh_interval 10 rotate_wait 30 storage.type filesystem
+ # Skip long log lines instead of skipping the entire file
+ skip_long_lines On
+ # Buffer settings
+ buffer_chunk_size 1MB
+ buffer_max_size 10MB # Capture Fluent Bit's metrics [INPUT]
@@ -49,6 +54,7 @@ log_stream_name ${ECS_TASK_ID} workers 2 retry_limit 3 storage.total_limit_size 1G # Send Fluent Bit's metrics to CloudWatch Logs`
- `skip_long_linesbuffer_max_size`
  - 로그 줄이 기본 설정을 초과하면 파일을 건너뜁니다. 이 설정을 "켜짐"으로 설정하면 로그 줄을 건너뛰고 파일을 계속 모니터링합니다.
- `buffer_chunk_sizebuffer_chunk_sizebuffer_max_size`
  - 모니터링되는 파일당 할당할 초기 버퍼 크기입니다. 로그 줄이 버퍼를 초과하면 해당 버퍼를 초과할 때까지
    - 계속 할당됩니다.
- `buffer_max_size`
  - 모니터링되는 파일당 최대 버퍼 크기




l4
- PII를 제거하기 위해 user_email 필드를 해시하여 `content_modifierhash`
  - 프로세서를 사용했습니다 (2단계).
- 프로세서를 사용하여 데이터 볼륨을 최적화함으로써 CloudWatch Logs 비용을 월 $6,492에서 $19.48로 절감했습니다(3단계):
  - 프로세서를 사용하여 `sql`필요한 필드만 선택했습니다.
  - 프로세서를 사용하여 이벤트 `grepvideo_view_final`만 필터링했습니다.
  - 처리량이 ~5000KB/s에서 ~15KB/s로 감소했습니다.
- fluent-bit의 핫 리로드 기능을 활용하여 프로세스를 다시 시작하지 않고도 구성 변경 사항을 반복적으로 테스트했습니다(2단계 및 3단계).
- 필터에 비해 더 나은 성능을 위해 프로세서가 입력 단계에서 어떻게 실행되는지 알아보았습니다(2단계).