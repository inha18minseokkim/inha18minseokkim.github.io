---
title: stratify + Clustering
date: 2025-07-16
tags:
  - AI/ML
---

```python
kmeans = KMeans(n_clusters=8,random_state=2)
kmeans.fit(scaled_data)
군집예측 = kmeans.predict(scaled_data)
print(pd.Series(군집예측).value_counts(normalize=True).round(2))
train_data, test_data, train_target, test_target = train_test_split(housing.data, housing.target ,test_size=0.25,shuffle=True,random_state=2,stratify=군집예측)
print(train_data.shape,test_data.shape)
```

train test split 시 stratify 지정해줘야 분포가 고르게 분할된다. 다만 분포를 어떻게 찾을것인지에 대한 알고리즘 3가지 있음.

### KMeans


### AgglomerativeClustering

병합군집 - 군집을 형성한다음 옆 인근 군집 땅따먹기로 병합하면서 합침 거리구하는방식은 euclidean 

```java
병합군집 = AgglomerativeClustering(n_clusters=4, linkage='ward',metric='euclidean')z`
```


### DBSCAN

밀도기반군집 - 클러스터 자동 탐지(클러스터수 쓰지 않는 것이 핵심)

![[Pasted image 20260225103932.png]]

이렇게 될 수도 있음 noise 없애는게 좋음
