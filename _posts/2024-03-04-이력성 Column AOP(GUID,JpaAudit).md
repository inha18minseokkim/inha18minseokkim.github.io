---
title: 이력성 Column AOP(GUID,JpaAudit)
date: 2024-03-04
tags:
  - 주식서비스
  - 케이뱅크
  - 기획
  - Java
  - Spring
  - 개발
category:
  - 실무경험
---
현재 행내에는 등록id, 등록guid, 등록일시, 수정id,수정guid,수정일시 6가지 컬럼을 이력성으로 남겨둠
사용하지 않는 경우에는.. 그럴일은 없음. 무조건 하라고 함.
bxm 기존에는 rgst_dt,rgst_guid_id,rgst_dttm,amnn…. 6개를 다 get set 해서 넘겨줘야했음. 
MSA 환경 Spring Boot로 넘어오면서 AOP를 자유롭게 사용할 수 있으니 업무 DTO, 업무로직에서 이력로그 getset 부분을 없애봄

# MCI 에서 헤더부분 가져오는 로직


```json
public record CommonContext(
        String userId,
        String createDate
        ) {
    public String createGuid() {
        return userId+createDate;
    }
}
```


```json
public final class CommonContextHolder {
    private static final ThreadLocal<CommonContext> context = new ThreadLocal<>();

    private CommonContextHolder(){

    }
    public static CommonContext getHeader() {
        return context.get();
    }
    public static void setHeader(CommonContext header){
        header.createGuid();
        context.set(header);
    }
    public static void clear() {
        context.remove();
    }
}
```

편의를 위해 필드 두 개만 가져옴 각 스레드마다 가져와서 ThreadLocal static으로 사용하는 로직

```json
@Aspect
@Component
@RequiredArgsConstructor
@Slf4j(topic="PreProcess")
public class PreProcess {
    @Pointcut("@within(org.springframework.web.bind.annotation.RestController)")
    private void preProcess() {

    }
    @Before("preProcess()")
    public void doProcess(JoinPoint joinPoint){
        ServletRequestAttributes requestAttributes = (ServletRequestAttributes) RequestContextHolder.getRequestAttributes();
        //HTTP 리퀘스트가 아닌 경우 그냥 보내, TOBE : GUID 채번 및 생성(서비스단에서 업무가 시작하는 로직이 생기는 경우)
        if(requestAttributes == null) return;

        //헤더에서 가져온 GUID를 Context 객체에 셋팅해줌
        HttpServletRequest request = requestAttributes.getRequest();
        String userId = request.getHeader("userId");
        String createDate = request.getHeader("createDate");
        CommonContextHolder.setHeader(new CommonContext(userId,createDate));
        log.info("@@@@@@@@@@@@@@@@@@@@@@@@@@");
        log.info(CommonContextHolder.getHeader().toString());
    }
}
```

RestController에서 들어올 때 헤더값들 가져오는 로직(대충 필드 두 개만 본따서 짬)


# 1. JpaAudit + Annotation 사용


```json
@MappedSuperclass
@SuperBuilder
@NoArgsConstructor
@EntityListeners({AuditingEntityListener.class, GuidAuditListener.class})
public abstract class TimeStamp {
    @Column(name = "rgst_id")
    @CreatedBy
    private String registerId;
    @Column(name = "rgst_guid_id")
    @CreatedGuid
    private String registerGuidId;
    @Column(name="rgst_dttm")
    @CreatedDate
    private LocalDateTime registerDateTime;
    @Column(name="amnn_id")
    @LastModifiedBy
    private String amendId;
    @Column(name="amnn_guid_id")
    @ModifiedGuid
    private String amendGuidId;
    @Column(name="amnn_dttm")
    @LastModifiedDate
    private LocalDateTime amendDateTime;
}
```


```json
@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.FIELD)
public @interface CreatedGuid {
}

@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.FIELD)
public @interface ModifiedGuid {
}
```

@CreatedBy LastModifiedBy ModifiedDate CreatedDate는 모두 JpaAudit 기본 로직으로 제공함
문제는 GUID의 경우 수동으로 등록해야 함

```json
@Slf4j
public class GuidAuditListener {
			@PrePersist
	    @PreUpdate
	    public void setCustomGuidField(Object t) {
	        if(t instanceof TimeStamp) {
	            TimeStamp target = (TimeStamp) t;
	
	            Arrays.stream(TimeStamp.class.getDeclaredFields())
	                    .filter(field -> field.isAnnotationPresent(ModifiedGuid.class))
	                    .forEach(field -> {
	                        field.setAccessible(true);
	                        CommonContext header = CommonContextHolder.getHeader();
	                        try {
	                            field.set(target, header.createGuid());
	                        } catch (IllegalArgumentException | IllegalAccessException e) {
	                            e.printStackTrace();
	                        }
	                    });
	        }
	        if(t instanceof HistoryTimeStamp){
	            HistoryTimeStamp target = (HistoryTimeStamp) t;
	
	            Arrays.stream(HistoryTimeStamp.class.getDeclaredFields())
	                    .filter(field -> field.isAnnotationPresent(CreatedGuid.class))
	                    .forEach(field -> {
	                        field.setAccessible(true);
	                        CommonContext header = CommonContextHolder.getHeader();
	                        try{
	                            log.info("XXXY  {}",header.createGuid());
	                            if(field.get(target) == null)
	                                field.set(target,header.createGuid());
	                        }catch (IllegalArgumentException | IllegalAccessException e){
	                            e.printStackTrace();
	                        }
	                    });
	        }
	
	    }
}
```

각 instance인 경우, 특정 필드가 어노테이션을 가지고 있는 경우 Persist,Update 전에 ThreadSafe 한 CommonContext 끼워넣는 로직
그럴일은 없지만 넣는 과정에서 예외 발생 시 throw 하지 않고 에러로그만 출력

![이미지](/assets/images/Pasted%20image%2020260226115435.png)
헤더에 값 셋팅하면 이렇게 됨


# JpaAudit를 적극 사용


```json
@MappedSuperclass
@SuperBuilder
@NoArgsConstructor
@EntityListeners({AuditingEntityListener.class, GuidAuditListener.class})
public abstract class TimeStamp {
    @Column(name = "rgst_id")
    @CreatedBy
    private String registerId;
    @Column(name = "rgst_guid_id")
    private String registerGuidId;
    @Column(name="rgst_dttm")
    @CreatedDate
    private LocalDateTime registerDateTime;
    @Column(name="amnn_id")
    @LastModifiedBy
    private String amendId;
    @Column(name="amnn_guid_id")
    @ModifiedGuid
    private String amendGuidId;
    @Column(name="amnn_dttm")
    private LocalDateTime amendDateTime;

    @PrePersist
    public void onCreate(){
        this.registerGuidId = CommonContextHolder.getHeader().createGuid();
        this.amendGuidId = CommonContextHolder.getHeader().createGuid();
    }
    @PreUpdate
    public void onUpdate(){
        this.amendGuidId = CommonContextHolder.getHeader().createGuid();
    }
}
```

이런식으로 PrePersist,PreUpdate 걸어놓고

```json
@Slf4j
public class GuidAuditListener {
    @PrePersist
    public void prePersist(Object entity) {
        if(entity instanceof TimeStamp){
            ((TimeStamp)entity).onCreate();
        }
        if(entity instanceof HistoryTimeStamp){
            ((HistoryTimeStamp)entity).onCreate();
        }
    }
    @PreUpdate
    public void preUpdate(Object entity){
        if(entity instanceof  TimeStamp){
            ((TimeStamp)entity).onUpdate();
        }
    }
}
```

이렇게 각 이벤트에 대하여 걸어놓음

