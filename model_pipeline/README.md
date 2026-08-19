\# Flight Delay Prediction Using CatBoost



Machine learning system for predicting whether a commercial flight

will be delayed by more than 15 minutes.



\## Project Pipeline



Raw Flight Data

&#x20;       ↓

Data Cleaning

&#x20;       ↓

Airport ID → IATA Mapping

&#x20;       ↓

V4.1 Feature Engineering

&#x20;       ↓

64 Features

&#x20;       ↓

V4.2 Aircraft Propagation Enhancement

&#x20;       ↓

68 Features

&#x20;       ↓

CatBoost Baseline

&#x20;       ↓

Hyperparameter Optimization

&#x20;       ↓

V4.2 Baseline Retained

&#x20;       ↓

Threshold Optimization

&#x20;       ↓

Final Threshold = 0.66

&#x20;       ↓

Real-Flight Prediction Testing



\## Final Model



Model: CatBoost Classifier



Feature version: V4.2



Number of features: 68



\## Final Test Results



| Metric | Score |

|---|---:|

| Accuracy | 87.46% |

| Precision | 72.07% |

| Recall | 46.69% |

| F1 Score | 56.67% |

| ROC-AUC | 80.40% |

| PR-AUC | 63.33% |



\## Threshold



The classification threshold was selected using the validation

set and then frozen before evaluating the test set.



Final threshold:



0.66



\## Important



The original flight datasets are not included in this repository

because of their size.



The trained CatBoost model is also excluded from the normal Git

repository because of its file size.



See the project documentation for dataset and model setup.

