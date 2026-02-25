---
title: "Reflection 활용 가능"
date: 2023-11-07
tags: [미지정]
category: 기타
---
FlatFileItemReader 구현 중 연합인포맥스에서 파일 데이터 수신 시 | 로 구분된 데이터 가져올 때 Column 정보를 제공해 주는 상황에서 문제생김
static String Array를 사용하여 제공해줬지만 코드 가독성이 좋지 못함

개선사항
ReflectionUtil을 추가하여 Class 타입을 넣으면 Field의 이름을 ArrayList로 반환하는 함수 만들어서 배포하기로 함(Reflection 써도 된다고 함)

런타임 오류가 날 수 있는 여지가 다분하지만, 간단하게 필드 리스트 긁어오는정도는 오케이 라고 하심
기존 BXM에서는 상상하지 못했던 기능이라 신기해서 적어봄.

```java
import java.lang.reflect.Field;
import java.util.ArrayList;
import java.util.List;

public class ReflectionUtils {

    public static List<String> getMemberValueNames(Class<?> clazz) {
        List<String> memberValueNames = new ArrayList<>();

        Field[] fields = clazz.getDeclaredFields();
        for (Field field : fields) {
            memberValueNames.add(field.getName());
        }

        return memberValueNames;
    }
}
```

