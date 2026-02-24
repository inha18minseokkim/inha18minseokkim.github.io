---
title: try-with-resources
date: 2023-09-12
tags:
  - Java
  - 개발
---

```java
static String firstLineOfFile(String path) throws IOException {
	BufferedReader br = new BufferedReader(new FileReader(path));
	try {
		return br.readLine();
	} finally {
		br.close();
	}
}
```

기존 try  catch finally 문 
try에 예외를 일으킬 수 있는 statement를 집어넣고 성공하든 실패하든 finally는 호출 되므로 finally에 자원 회수 파트를 넣자
문제점

```java
static void copy(String src, String dst) throws IOException {
	InputStream in = new FileInputstream(src);
	try {
		OutputStream out = new FileOutputstream(dst);
		try {
			byte[] buf = new byte[BUFFER_SIZE];
			int n;
			while ((n = in,read(buf)) >= 0 )
				out.write(buf,0,n);
		} finally {
			out.close();
			}
		finally {
			in.close();
		}
}
```

중첩하면 이모양이 나버림
그리고 기존 try는 catch 하는 exception이 하나.. 예를들어 try에서 exception이 발생한 후 finally에서 발생하면 함수를 호출한 client는 finally의 exception만 보임


```java
try(InputStream in = new FileInputStream(src);
		OutputStream out = new FileOutputstream(dst)){
	
```

이런식으로 하면 코드 훨씬 간결해짐. 숨겨진 예외도 Supressed로 나타남.
try-with-resources를 쓰면 첫 번째 코드처럼 바꿔줌(중첩형식으로) + AutoClosable.close()를 호출하면서 단계적으로 자원회수함


```java
try{
	FileOutputStream out = new FileOutputStream(dst);
	try{
		...//try문 계속 중첩
	} catch(Throwable var8) {
		try{
			out.close();
		} catch(Throwable var7) {
				var8.addSuppressed(var7);//먼저 발생한 예외를 추가
			}
			throw var8;
	}
		throw var8;//다 발생된것 던져
	}
	out,close(); //또 호출할 수 있음. 그러므로 AutoClosable.close()는 멱등적인것이 좋다
```

