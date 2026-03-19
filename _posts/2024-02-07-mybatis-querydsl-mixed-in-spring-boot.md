---
title: Mybatis QueryDSL 혼용 in Spring boot
date: 2024-02-07
tags:
  - QueryDSL
  - MyBatis
  - Java
category:
  - 실무경험
  - MSA표준
---

```java
public interface BaseProductReader {
    List<FindBaseProductWithFilterOutDto> findBaseProductWithFilter(FindBaseProductWithFilterInDto in);
}
```

Reader 인터페이스 선언

QueryDSLImpl(@Primary, 기본값으로 이거 씀)

```java
@Repository
@Primary
@RequiredArgsConstructor
public class BaseProductReaderImpl implements BaseProductReader {
    private final EntityManager em;
    private final BaseProductRepositoryMapper mapper;
    @Override
    public List<FindBaseProductWithFilterOutDto> findBaseProductWithFilter(FindBaseProductWithFilterInDto in) {
        JPAQueryFactory query = new JPAQueryFactory(em);
        QBaseProduct baseProduct = QBaseProduct.baseProduct;

        BooleanBuilder booleanBuilder = new BooleanBuilder();
        if(in.getCategoryCode() != null) booleanBuilder.and(baseProduct.categoryCode.eq(in.getCategoryCode()));
        if(in.getItemCode() != null) booleanBuilder.and(baseProduct.itemCode.eq(in.getItemCode()));

        List<BaseProduct> results = query.selectFrom(baseProduct)
                .where(
                        booleanBuilder
                ).fetch();
        return results.stream().map(element -> mapper.from(element)).collect(Collectors.toList());
    }
}
```


MybatisImpl

```java
@Mapper
@Repository
public interface BaseProductReaderMyBatisImpl extends BaseProductReader {
    @Override
    List<FindBaseProductWithFilterOutDto> findBaseProductWithFilter(FindBaseProductWithFilterInDto in);
}
```


인터페이스를 구현한 구현체를 둘중 하나만 구현하면 됨.(둘 다 구현한 이유는 그냥 샘플) 

Mybatis를 위한 매핑 정보

```yaml
mybatis:
  mapper-locations:
    - classpath:sqlmap/mappers/*.xml
```

Mybatis 실제 구현부

```yaml
<?xml version="1.0" encoding="UTF-8" ?>

<!DOCTYPE mapper PUBLIC "-//mybatis.org//DTO Mapper 3.0//EN" "http://mybatis.org/dtd/mybatis-3-mapper.dtd">

<mapper namespace="com.example.fdppoc.infrastructure.impl.BaseProductReaderMyBatisImpl">
    <select id="findBaseProductWithFilter" resultType="com.example.fdppoc.infrastructure.dto.FindBaseProductWithFilterOutDto">
        select
            id
             ,category_code
             ,item_code
             ,kind_code
             ,class_code
             ,grade_code
             ,unit_name
             ,unit_value
             ,is_available
             ,category_name
             ,item_name
             ,kind_name
             ,grade_name
             ,inner_product_id
        from base_product
        where 1 = 1
        <if test="categoryCode != null and categoryCode != 'all' ">
            and category_code = #{categoryCode}
        </if>
        <if test="itemCode != null and itemCode != 'all' ">
            and item_code = #{itemCode}
        </if>
    </select>
</mapper>
```

Jackson이 알아서 snake_case ⇒ camelCase 해줌
실제 같은지 대조 테스트

```java
@SpringBootTest
@Slf4j
class BaseProductReaderMyBatisImplTest {
    @Autowired
    BaseProductReaderMyBatisImpl myBatisImpl;
    @Autowired
    BaseProductReaderImpl jpaImpl;
    @Test
    void 입출력테스트() {

        List<FindBaseProductWithFilterOutDto> results = myBatisImpl.findBaseProductWithFilter(FindBaseProductWithFilterInDto
                .builder()
                        .categoryCode("100")
                .build());
        log.info("결과 : {}" ,results);
        Assertions.assertThat(results.stream().map(element->element.getCategoryCode()).toList())
                .doesNotContain("200");
    }
    @Test
    void 비교테스트() {
        List<FindBaseProductWithFilterOutDto> myBatisResults = myBatisImpl.findBaseProductWithFilter(FindBaseProductWithFilterInDto
                .builder()
                .categoryCode("100")
                .build());
        List<FindBaseProductWithFilterOutDto> jpaResults = jpaImpl.findBaseProductWithFilter(FindBaseProductWithFilterInDto
                .builder()
                .categoryCode("100")
                .build());
        Assertions.assertThat(myBatisResults).isEqualTo(jpaResults);

    }

}
```

서비스에서 Reader를 Impl이 아닌 Interface를 주입받아 사용하면 됨.

예시용으로 두 코드를 작성했지만, 실제로 Impl은 하나만 있으면 된다(선택사항)

![](/assets/images/Pasted%20image%2020260228171244_2bc2535d.png)
