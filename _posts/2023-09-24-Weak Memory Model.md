---
title: "Weak Memory Model"
date: 2023-09-24
tags: [미지정]
---
[https://preshing.com/20120930/weak-vs-strong-memory-models/](https://preshing.com/20120930/weak-vs-strong-memory-models/)


![](https://prod-files-secure.s3.us-west-2.amazonaws.com/c38aebd7-2834-4fac-b2fc-a2f0c17ce81d/c18f2707-30f6-4885-aa85-5bce9ab67717/Untitled.png)


Memory Reordering 하는 매커니즘이 머신마다 다를 수 있음. 그리고 이제는 대체로 다 멀티코어이므로 중요함

Weak - 메모리 순서 리오더링 가능. 하드웨어 스펙상으로 가능하기 때문에(컴파일러 단에서) 구현이나 JVM에서 리오더링을 제한하는 로직이 필요할 수 있음
x86/64는 strongly ordered 함
ARM은 alpha 만큼 weak함
캐싱하지 않고 memory dependent하게 volatile 키워드를 사용하도록 하자.
