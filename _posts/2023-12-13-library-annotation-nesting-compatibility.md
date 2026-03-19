---
title: 자주 쓰는 라이브러리 어노테이션 중첩이 가능한가?
date: 2023-12-13
tags:
  - Java
  - Spring
category:
  - 기술
---

[https://stackoverflow.com/questions/52148496/is-it-possible-to-create-a-custom-annotation-with-a-group-of-annotations-in-java](https://stackoverflow.com/questions/52148496/is-it-possible-to-create-a-custom-annotation-with-a-group-of-annotations-in-java)


```java
@Entity(name = "AnnounceFreeIssue")
@AllArgsConstructor
@NoArgsConstructor
@Builder
@Getter
public class AnnounceFreeIssue implements EssentialReport {
```

이걸

```java
@Retention(RUNTIME)
@Entity(name = "AnnounceFreeIssue")
@AllArgsConstructor
@NoArgsConstructor
@Builder
@Getter
public interface@ CustomAnnotation {
    ...
}
```

이런식으로 되나?

결론: 안된다
어노테이션 여러개 상속하는건 가능하지만 어노테이션 프로세스가 각각 동작하는 방식이 상이하므로 될 수도 있고 안될수도 있으니깐 안된다
일단 롬복이 안되므로 ㅈㅈ

