---
title: Weak Memory Model
date: 2023-09-24
tags:
  - Java
---
[https://preshing.com/20120930/weak-vs-strong-memory-models/](https://preshing.com/20120930/weak-vs-strong-memory-models/)


![[Pasted image 20260224113138.png]]

Memory Reordering 하는 매커니즘이 머신마다 다를 수 있음. 그리고 이제는 대체로 다 멀티코어이므로 중요함

Weak - 메모리 순서 리오더링 가능. 하드웨어 스펙상으로 가능하기 때문에(컴파일러 단에서) 구현이나 JVM에서 리오더링을 제한하는 로직이 필요할 수 있음
x86/64는 strongly ordered 함
ARM은 alpha 만큼 weak함
캐싱하지 않고 memory dependent하게 volatile 키워드를 사용하도록 하자.

---

### Memory Reordering의 종류

CPU가 허용하는 reordering은 4가지가 있음

| 유형 | 설명 |
|---|---|
| Load-Load | 앞의 read가 뒤의 read보다 나중에 보일 수 있음 |
| Load-Store | 앞의 read가 뒤의 write보다 나중에 보일 수 있음 |
| Store-Store | 앞의 write가 뒤의 write보다 나중에 다른 코어에 전파될 수 있음 |
| Store-Load | 앞의 write가 뒤의 read보다 나중에 전파되어 read가 stale 값을 읽을 수 있음 (가장 흔한 문제) |

x86은 Store-Load 하나만 허용됨. ARM은 네 가지 다 허용.

---

### 왜 reordering이 생기는가 - Store Buffer와 Invalidation Queue

단순히 "CPU가 순서를 바꾼다"가 아니라 하드웨어 구조 때문에 자연스럽게 생기는 현상임

**Store Buffer (Write reordering 원인)**

코어가 write를 할 때 다른 코어에 invalidate 신호를 보내고 acknowledge를 기다리는 동안 멈추면 너무 느리기 때문에, write를 Store Buffer에 쌓아두고 다음 연산을 계속 진행함. 나중에 acknowledge 받으면 그때 캐시에 반영.
→ 다른 코어 입장에서는 write가 늦게 보임. Store-Load reordering 발생.

**Invalidation Queue (Read reordering 원인)**

다른 코어의 invalidate 신호를 받아도 즉시 처리하지 않고 큐에 쌓아둠. 로컬 코어는 큐를 보지 않고 자기 캐시를 그냥 읽음.
→ 이미 무효화됐어야 할 stale 값을 읽게 됨. Load-Store reordering 발생.

---

### Java Memory Model (JMM)

JVM은 x86에서도 돌고 ARM에서도 돌기 때문에 하드웨어 차이를 추상화해야 함. 그게 JMM.
JMM의 핵심은 **happens-before** 관계임.

A happens-before B = A의 결과가 B에게 반드시 보임을 보장

주요 happens-before 규칙:
- 같은 스레드 내 코드 순서
- volatile 변수 write → 이후 같은 변수 read
- `synchronized` 블록 unlock → 이후 같은 모니터 lock
- `Thread.start()` 호출 → 그 스레드 내 모든 작업
- `Thread.join()` 반환 → 조인한 스레드의 모든 작업

happens-before 관계가 없는 상태에서 두 스레드가 같은 메모리를 읽고 쓰면 **Data Race**로 간주함.

---

### volatile이 Reordering을 막는 원리

volatile read/write 시점에 JVM이 **Memory Fence(Barrier)** 명령을 삽입함

- **volatile write 전**: Release Barrier → 이전 연산들이 write 이후로 밀려나지 않게 함 + Store Buffer flush
- **volatile read 후**: Acquire Barrier → 이후 연산들이 read 이전으로 당겨지지 않게 함 + Invalidation Queue flush

즉 volatile은 단순히 "캐시 안 씀"이 아니라 메모리 배리어를 통해 Store Buffer / Invalidation Queue를 강제로 비우는 것.

---

### synchronized, volatile, Atomic 비교

| | synchronized | volatile | AtomicXxx |
|---|---|---|---|
| 가시성 | O | O | O |
| 상호배제 | O | X | X |
| 원자성 | O | X | O (CAS) |
| 성능 | 느림 (blocking) | 빠름 | 빠름 (lock-free) |

volatile `count++`는 원자적이지 않음. read → modify → write 세 단계가 분리되어 있어 interleave 가능.
이 경우엔 `AtomicInteger.incrementAndGet()` 써야 함. CAS(Compare-And-Swap)로 lock 없이 원자적으로 처리.
