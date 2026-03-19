---
title: Insert On Conflict(Upsert)는 과연 성능저하가 없을까?
date: 2025-03-29
tags:
  - DB
category:
  - 기술
  - DB
---

## 현재 사용중인 쿼리


```java
INSERT INTO tb_stk_ovrs_stck_m (
            tckr_id, stck_eng_nm, stck_kor_nm, stck_conc_nm, 
            exch_cd_val, mrkt_cd, lstn_dt, exad_yn, efctv_yn, 
            rgst_id, rgst_guid_id, rgst_dttm, amnn_id, amnn_guid_id, amnn_dttm
        ) VALUES (
            %(tckr_id)s, %(stck_eng_nm)s, %(stck_kor_nm)s, %(stck_conc_nm)s, 
            %(exch_cd_val)s, %(mrkt_cd)s, %(lstn_dt)s, %(exad_yn)s, %(efctv_yn)s, 
            %(rgst_id)s, %(rgst_guid_id)s, %(rgst_dttm)s, %(amnn_id)s, %(amnn_guid_id)s, %(amnn_dttm)s
        ) ON CONFLICT (tckr_id) 
        DO UPDATE SET 
            stck_eng_nm = EXCLUDED.stck_eng_nm,
            stck_kor_nm = EXCLUDED.stck_kor_nm,
            stck_conc_nm = EXCLUDED.stck_conc_nm,
            exch_cd_val = EXCLUDED.exch_cd_val,
            mrkt_cd = EXCLUDED.mrkt_cd,
            lstn_dt = EXCLUDED.lstn_dt,
            exad_yn = EXCLUDED.exad_yn,
            efctv_yn = EXCLUDED.efctv_yn,
            amnn_id = EXCLUDED.amnn_id,
            amnn_guid_id = EXCLUDED.amnn_guid_id,
            amnn_dttm = EXCLUDED.amnn_dttm;
```

Spring jdbc 대신 Python psycopg2를 사용해서 upsert 방식을 사용중인 경우가 있음.

## 왜?

Oracle 을 쓰는 경우에는 Merge를 사용하기 때문에 “되게 위험한 것을 사용하시네요” 라는 답을 들은 적이 있음. 
그래서 
1. 혹시 위험한가 싶어서 
2. 왜 위험하다고 생각했을까?
를 알아보기 위함.


### Upsert 를 사용할 수 밖에 없는 비즈니스적인 이유

어떤 데이터 적재 작업의 경우
1. cursor 생성
2. range에 해당하는 값을 row delete (commit 안함)
3. 다시 값들을 insert
4. commit
을 한다. ex) 삼성전자의 2024년 3월 24일부터 2025년 3월 25일까지 주가정보를 모두 delete 후 재적재

다만 다음과 같은 경우는 좀 제한적임.
1. 기준정보 업데이트만 필요해요
2. row delete 하기에는 좀 껄끄러운 경우
아무튼 도메인의 엔티티 기준정보니깐.. 많아봤자 데이터 만건이라 그냥 upsert 사용함
  - (가격정보 같은 경우는 1만 * M 이고 노출 안되더라도 큰 문제가 없으므로 그냥 row delete)


### 결론적으로..

insert on conflict문의 경우 퍼포먼스에는 큰 문제 없음
왜냐하면 어차피 기존 Insert의 경우에도 데이터를 넣기 전에 pk와 unique index(constraint)를 체크하고 insert를 수행하기 때문.
  - on conflict시 update를 하는 행위는 이미 constraint 체크 행위가 끝나고 한 다음 이니 액세스를 두 번 하는것은 아니다!
  - 업데이트에 대한 추가 연산은 있을지언정, index access를 두 번 하지는 않는다는 느낌


### 엄밀히 위험한 점

📌 PostgreSQL의 MVCC 특성상, 위 `UPDATE` 실행 시 **다음과 같은 일이 발생**합니다.
1. 기존 행이 **"삭제됨" (dead tuple)** 으로 표시됨.
2. 새로운 행이 추가됨.
3. 기존 `UPDATE`가 **모든 인덱스를 수정해야 함!**
4. `VACUUM`을 통해 dead tuple을 정리해야 함.

그러므로 insert + update를 할 때 액세스 하는 비용 자체는 문제가 없다.
다만 업데이트에 대한 추가 연산은 있을지언정 >> 추가 연산을 신경 아예 안 쓸 수는 없다는 것.
Toast Data, 즉 긴 문자열과 JsonB를 포함하는 경우 디스크 낭비가 심각해질 수 있음. 기존행을 삭제하고 새로운 행을 생성한 다음 레퍼런스를 돌리는 방식이니!!
  - +) dead tuple 문제가 있을 수 있음.



### Oracle Merge와 다른 점


```java
MERGE INTO target_table t
USING (SELECT key_col, data_col FROM source_table) s
ON (t.key_col = s.key_col)
WHEN MATCHED THEN
    UPDATE SET t.data_col = s.data_col
WHEN NOT MATCHED THEN
    INSERT (t.key_col, t.data_col) VALUES (s.key_col, s.data_col);
```

Oracle Merge 의 경우 
1. on 절에 index가 걸리지 않으면 액세스 속도가 늦어질 수 있음(index unique scan <<<< 넘사벽 <<<<table full scan)
2. 만약 index range scan, skip scan을 쓴다고 하더라도 처음에 내가 생각했던 요건대로 움직이지 않을 확률 이 있음. 동일한 키 값이 match가 되면 중복 insert가 될 수도 있기 때문(물론 이걸 의도하고 쓸 수도 있지만)

| 기능 | PostgreSQL: `INSERT ON CONFLICT` | Oracle: `MERGE` |
| --- | --- | --- |
| **필수 인덱스** | `UNIQUE INDEX` 또는 `PRIMARY KEY`가 필요 | `ON` 조건에 인덱스 없어도 실행 가능 |
| **충돌 감지** | `UNIQUE INDEX`를 활용하여 빠르게 충돌 확인 | `ON` 조건을 `FULL SCAN`할 수도 있음 |
| **I/O 비용** | `UNIQUE INDEX`가 있어 충돌 감지가 빠름 (낮은 I/O) | `ON` 조건이 효율적이지 않으면 `TABLE SCAN` 발생 (높은 I/O) |
| **업데이트 충돌 방지** | `UNIQUE CONSTRAINT`로 동시성 제어 | `ON` 조건이 불안정하면 `ORA-30926` 오류 가능 |
| **실행 방식** | `INSERT` 시 `CONFLICT`가 있으면 `UPDATE` | `ON` 조건에 따라 `UPDATE` 또는 `INSERT` |

아마 이런 문제를 생각하고 위험한걸 사용하는게 아닌가..라고 하신듯


### PS. 물론 인덱스가 능사는 아니다.

Update를 할 때 무조건 인덱스를 태우는것이 좋지는 않음. 
1. update 대상을 조건절에서 적절한 필터링을 하지 못할 때 
2. 테이블이 작을 때 
3. row 대부분이 대상일때
이런경우는 TBFS를 태우는게 맞음.
