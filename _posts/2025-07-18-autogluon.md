---
title: "autogluon"
date: 2025-07-18
tags: [AI/ML]
category: 기타
---
[Forecasting Time Series - Evaluation Metrics](https://auto.gluon.ai/stable/tutorials/timeseries/forecasting-metrics.html)
Probabilitic Forecast - 확률에 기반한 예측, WQL
Point Forecast - 정확한 예측, MASE


### 장점

좋은모델 많음. 좋은모델 다 때려넣고 추상화시켜서 

### 단점

무겁다. 많은 모델이 다 있어서
딥러닝 모델은 제로샷으로 되어있어 훈련되진 않음
  - 그래도 딥러닝 모델 중 ChronosFineTuned 이건 amazon에서 파인튜닝 시켜줌


```python
predictor = TimeSeriesPredictor(
    prediction_length=48, #예측할 시계열 길이
    target = 'target', #시계열 예측의 대상
    eval_metric='MASE', #평가 지표
    path = 'autogluon/m4-hourly' #저장 경로
)
predictor.fit(train_data,presets='medium_quality',time_limit=600)
```



```python
Warning: path already exists! This predictor may overwrite an existing predictor! path="autogluon/m4-hourly"
Beginning AutoGluon training... Time limit = 600s
AutoGluon will save models to '/home/me/autogluon/m4-hourly'
=================== System Info ===================
AutoGluon Version:  1.3.1
Python Version:     3.10.18
Operating System:   Linux
Platform Machine:   x86_64
Platform Version:   #1 SMP Tue Nov 5 00:21:55 UTC 2024
CPU Count:          12
GPU Count:          1
Memory Avail:       14.07 GB / 15.57 GB (90.4%)
Disk Space Avail:   896.79 GB / 1006.85 GB (89.1%)
===================================================
Setting presets to: medium_quality

Fitting with arguments:
{'enable_ensemble': True,
 'eval_metric': MASE,
 'hyperparameters': 'light',
 'known_covariates_names': [],
 'num_val_windows': 1,
 'prediction_length': 48,
 'quantile_levels': [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9],
 'random_seed': 123,
 'refit_every_n_windows': 1,
 'refit_full': False,
 'skip_model_selection': False,
 'target': 'target',
 'time_limit': 600,
 'verbosity': 2}

Inferred time series frequency: 'h'
Provided train_data has 148060 rows, 200 time series. Median time series length is 700 (min=700, max=960). 

Provided data contains following columns:
	target: 'target'

AutoGluon will gauge predictive performance using evaluation metric: 'MASE'
	This metric's sign has been flipped to adhere to being higher_is_better. The metric score can be multiplied by -1 to get the metric value.
===================================================

Starting training. Start time is 2025-07-18 01:34:43
Models that will be trained: ['Naive', 'SeasonalNaive', 'RecursiveTabular', 'DirectTabular', 'ETS', 'Theta', 'Chronos[bolt_small]', 'TemporalFusionTransformer']
Training timeseries model Naive. Training for up to 66.4s of the 597.6s of remaining time.
	-6.6629       = Validation score (-MASE)
	0.18    s     = Training runtime
	3.57    s     = Validation (prediction) runtime
Training timeseries model SeasonalNaive. Training for up to 74.2s of the 593.8s of remaining time.
	-1.2169       = Validation score (-MASE)
	0.16    s     = Training runtime
	0.17    s     = Validation (prediction) runtime
Training timeseries model RecursiveTabular. Training for up to 84.8s of the 593.5s of remaining time.
	-0.9339       = Validation score (-MASE)
	9.67    s     = Training runtime
	0.84    s     = Validation (prediction) runtime
Training timeseries model DirectTabular. Training for up to 97.2s of the 582.9s of remaining time.
	-1.2921       = Validation score (-MASE)
	8.24    s     = Training runtime
	0.43    s     = Validation (prediction) runtime
Training timeseries model ETS. Training for up to 114.9s of the 574.3s of remaining time.
	-1.9661       = Validation score (-MASE)
	0.16    s     = Training runtime
	17.95   s     = Validation (prediction) runtime
Training timeseries model Theta. Training for up to 139.0s of the 556.2s of remaining time.
	-2.1426       = Validation score (-MASE)
	0.16    s     = Training runtime
	1.05    s     = Validation (prediction) runtime
Training timeseries model Chronos[bolt_small]. Training for up to 185.0s of the 554.9s of remaining time.
/home/me/.conda/envs/amazon/lib/python3.10/site-packages/requests/__init__.py:86: RequestsDependencyWarning: Unable to find acceptable character detection dependency (chardet or charset_normalizer).
  warnings.warn(
	Warning: Exception caused Chronos[bolt_small] to fail during training... Skipping this model.
	module 'pyarrow' has no attribute 'PyExtensionType'
Training timeseries model TemporalFusionTransformer. Training for up to 274.7s of the 549.4s of remaining time.
	-2.2672       = Validation score (-MASE)
	83.16   s     = Training runtime
	0.25    s     = Validation (prediction) runtime
Fitting simple weighted ensemble.
	Ensemble weights: {'DirectTabular': 0.07, 'ETS': 0.05, 'RecursiveTabular': 0.85, 'SeasonalNaive': 0.02, 'TemporalFusionTransformer': 0.01}
	-0.9122       = Validation score (-MASE)
	0.81    s     = Training runtime
	19.64   s     = Validation (prediction) runtime
Training complete. Models trained: ['Naive', 'SeasonalNaive', 'RecursiveTabular', 'DirectTabular', 'ETS', 'Theta', 'TemporalFusionTransformer', 'WeightedEnsemble']
Total runtime: 134.38 s
Best model: WeightedEnsemble
Best model score: -0.9122
```

![이미지](/assets/images/Pasted%20image%2020260225104920.png)
