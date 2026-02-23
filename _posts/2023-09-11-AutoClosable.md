---
title: "AutoClosable"
date: 2023-09-11
tags: [미지정]
---
자원 회수 프로세스(try-with-resource)를 명시하지 않았을 때 생길 수 있는 일을 정의해놓을 수 있음

```javascript
class HeavyStatefulClass implements AutoCloseable{
    private BufferedReader bufferedReader;
    public HeavyStatefulClass(String path) {
        //이런식으로 자원 풀을 잡아먹거나 leak될 수 있는 무언가 하다가
        try {
            this.bufferedReader = new BufferedReader(new FileReader(path));
        }catch(FileNotFoundException e){
            
        }
    }
    @Override
    public void close() throws IOException {
        //끝났을 때 자원회수하는 프로세스
        bufferedReader.close();
    }
}
```


close는 멱등적인것이 좋음. 한번만 호출된다는 보장이 있으면 좋지만.. 그렇지 않을 수도 있기에
AutoClosable은 IOException 던짐, Closable은 Exception 던짐

ex) BufferedReader는 Closable을 구현한 Readable을 상속한다. 그러므로 try-with-resource 쓰면 자동으로 close() 호출 해서 정리해줌
[try-with-resources]({% post_url 2023-09-12-try-with-resources %})