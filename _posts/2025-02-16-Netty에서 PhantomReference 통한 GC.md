---
title: Netty에서 PhantomReference 통한 GC
date: 2025-02-16
tags:
  - Webflux
  - Java
category:
  - 기술
---


### Java 객체의 참조를 간접적으로 유지, GC 받을때는 Notify 가능

즉, ReferenceCount는 올라가지 않되 연결고리는 있음.

```java
class LargeObject {
    private final byte[] data = new byte[1024 * 1024 * 100]; // 100MB 크기의 배열
}
```

큰 클래스 하나 만들어

```java
class PhantomReferenceExample {
    public static void main(String[] args) throws InterruptedException {
        System.out.println("startTime = " + LocalDateTime.now());
        // 큰 메모리를 가진 Object 생성
        LargeObject largeObject = new LargeObject();

        // ReferenceQueue 생성
        ReferenceQueue<LargeObject> referenceQueue = new ReferenceQueue<>();

        // PhantomReference 생성
        PhantomReference<LargeObject> phantomReference = 
									        new PhantomReference<>(largeObject, referenceQueue);

        // largeObject 참조 해제
        largeObject = null;

        // 가비지 컬렉션 수행
        System.gc();
        //GC 되기전에 프로세스가 종료될 수도 있으므로 넣음
        Thread.sleep(1000L);
        // ReferenceQueue에서 PhantomReference를 가져와서 처리
        Reference<? extends LargeObject> referenceFromQueue;
        while ((referenceFromQueue = referenceQueue.poll()) != null) {
            if (referenceFromQueue == phantomReference) {
                // 여기에서 해당 객체의 리소스를 해제하거나, 반납하는 작업을 수행
                System.out.println("LargeObject 객체가 가비지 컬렉션 되었습니다.");
                System.out.println("collectedTime = " + LocalDateTime.now());
            }
        }
    }
}

```


Heap 내 다른 객체에 의한 참조
Java 스택에서 참조하는 것
JNI를 통한 Native Stack에서 참조하는 것

![이미지](/assets/images/Pasted%20image%2020260225082254.png)


strongly reachable : root set으로부터 시작해서 어떤 reference object도 중간에 끼지 않은 상태로 참조 가능한 객체, 다시 말해, 객체까지 도달하는 여러 참조 사슬 중 reference object가 없는 사슬이 하나라도 있는 객체
softly reachable : strongly reachable 객체가 아닌 객체 중에서 weak reference, phantom reference 없이 soft reference만 통과하는 참조 사슬이 하나라도 있는 객체
메모리 크기와 객체 사용 빈도에 따라 GC 여부 결정
(Weakly Reachable과는 달리) GC때마다 회수안됨.
자주 사용할수록 오래 삶
weakly reachable : strongly reachable 객체도 softly reachable 객체도 아닌 객체 중에서, phantom reference 없이 weak reference만 통과하는 참조 사슬이 하나라도 있는 객체
GC 수행되면 바로 죽음
phantomly reachable : strongly reachable 객체, softly reachable 객체, weakly reachable 객체 모두 해당되지 않는 객체. 이 객체는 파이널라이즈(finalize)되었지만 아직 메모리가 회수되지 않은 상태이다.
***Soft Reference, Weak Reference와 다르게, 사용하기 위함 보다는 올바르게 삭제하고 삭제 이후 작업을 조작하기 위함이다.***
unreachable : root set으로부터 시작되는 참조 사슬로 참조되지 않는 객체
(정석) GC에 의한 척결 대상

![[Pasted image 20260301004026.png]]


### ***Phantomly Reference - 사용하기 위함 보다는 올바르게 삭제하고 삭제 이후 작업을 조작하기 위함이다.***

이걸 키포인트로 하고, Native Memory를 어케 삭제하냐면..


![이미지](/assets/images/Pasted%20image%2020260225082303.png)

ByteBuffer의 cleaner라는 객체는 PhantomReference를 상속함.

```java
public class Cleaner extends PhantomReference<Object> {

    private static final ReferenceQueue<Object> dummyQueue = new ReferenceQueue<>();

    ...

    private final Runnable thunk;

    private Cleaner(Object referent, Runnable thunk) {
        super(referent, dummyQueue);
        this.thunk = thunk;
    }

    // DirectByteBuffer 생성자에서 Cleaner.create(this, new Deallocator(base, size, cap))을 호출한다.
    // 즉, PhantomReference의 referent로 들어가는 객체는 DirectByteBuffer이다.
    // DirectByteBuffer 객체가 PhantomReference로만 참조되는 순간에 ReferenceQueue에 PhantomRefernce 객체가 enqueue된다.
    // 이때, PhantomRefernce 객체는 Cleaner이며 ReferenceQueue에서 poll하여 후처리를 실행하는 daemon thread에서 clean method를 호출하는 것이다.
    public static Cleaner create(Object ob, Runnable thunk) {
        if (thunk == null)
            return null;
        return add(new Cleaner(ob, thunk));
    }

    /**
     * Runs this cleaner, if it has not been run before.
     */
    public void clean() {
        if (!remove(this))
            return;
        try {
            // thunk는 Deallocator의 객체이므로 thunk.run 호출시 Deallocator의 run method가 호출된다.
            // Deallocator의 run method에서는 native method인 UNSAFE.freeMemory(long)을 호출하여 kernel buffer를 release한다.
            thunk.run();
        } catch (final Throwable x) {
            AccessController.doPrivileged(new PrivilegedAction<>() {
                    public Void run() {
                        if (System.err != null)
                            new Error("Cleaner terminated abnormally", x)
                                .printStackTrace();
                        System.exit(1);
                        return null;
                    }});
        }
    }
}
```

위 Cleaner 클래스에서 

```java
public static Cleaner create(Object ob, Runnable thunk) {
    if (thunk == null)
        return null;
    return add(new Cleaner(ob, thunk));
}
```

독립 스레드에서 실행하는 Runnable 인터페이스를 받는데, Deallocator를 받음
그게 밑에 있는데

```java
private static class Deallocator implements Runnable {

    private long address;
    private long size;
    private int capacity;

    private Deallocator(long address, long size, int capacity) {
        assert (address != 0);
        this.address = address;
        this.size = size;
        this.capacity = capacity;
    }

    // Cleaner의 clean method에서 thunk.run()을 통해 호출된다.
    public void run() {
        if (address == 0) {
            return;
        }
        UNSAFE.freeMemory(address);
        address = 0;
        Bits.unreserveMemory(size, capacity);
    }
}
```

여기 중에 run 메소드

```java
public void run() {
    if (address == 0) {
        return;
    }
    UNSAFE.freeMemory(address);
    address = 0;
    Bits.unreserveMemory(size, capacity);
}
```

실제로 UNSAFE를 통해 메모리를 해제함(JNI 시스템콜 해주는 기능이라고 생각하면됨)

즉, PhantomReference 객체가 참조하는 객체가 GC대상이 된다면
	ex) buffer = null 해서 referenceCount가 0이 되면
PhantomReference 객체는 ReferenceQueue에 Enqueue 되고, 
	근데 여기서 PhantomReference는 Cleaner임. 
		후처리하는 데몬 스레드에서 Cleaner.clean()을 수행함
			근데 Cleaner.clean()은 내부적으로 Deallocator.run()을 실행하는데
				run할 때 JNI 콜(UNSAFE.freeMemory) 하여 DirectByteBuffer를 GC하면서 Kerner Buffer도 정리해버림
요약: PhantomReference는 메모리가 정리될 때 이벤트 리스닝 같은 역할을 해줌. DirectByteBuffer가 정리될 때 Phantomly Reachable 하게 만들어놓고 GC 시점에 메모리 해제하도록 함.


### 그럼 Netty에서 Release 행위는 어디서 함?(즉, buffer=null을 해야 실행될거 아님)

PooledByteBuf에서 함

```java
abstract class PooledByteBuf<T> extends AbstractReferenceCountedByteBuf {
    
    private final Handle<PooledByteBuf<T>> recyclerHandle;

    protected PoolChunk<T> chunk;
    protected long handle;
    // ByteBuffer가 저장된다.
    protected T memory;
    protected int offset;
    protected int length;

    ...
    
    @Override
    protected final void deallocate() {
        if (handle >= 0) {
            final long handle = this.handle;
            this.handle = -1;
            memory = null;
            chunk.decrementPinnedMemory(maxLength);
            chunk.arena.free(chunk, tmpNioBuf, handle, maxLength, cache);
            tmpNioBuf = null;
            chunk = null;
            cache = null;
            recycle();
        }
    }
}
```

      memory = null; 이거임
다만 이건 referenceCount가 0이 되었을 때 호출되니깐 release 잘 안해주면 deallocate 호출되지 않는다.

```java
public abstract class AbstractReferenceCountedByteBuf extends AbstractByteBuf {
    ...
    
    @Override
    public boolean release() {
        return handleRelease(updater.release(this));
    }

    @Override
    public boolean release(int decrement) {
        return handleRelease(updater.release(this, decrement));
    }

    private boolean handleRelease(boolean result) {
        if (result) {
            deallocate();
        }
        return result;
    }

    /**
     * Called once {@link #refCnt()} is equals 0.
     */
    protected abstract void deallocate(); // PooledByteBuf에서 구현하고 있다.
}

```

여기서 release > referenceCount 가 decrement만큼 줄어듬 > handleRelease에서 result가 true 면 deallocate 실행 이런식으로 됨.