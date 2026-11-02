| modelo | PR-AUC media | PR-AUC desv. est. | ROC-AUC media | ROC-AUC desv. est. |
|---|---:|---:|---:|---:|
| Baseline 1: tasa positiva de A para todos | 0.1440 | 0.0000 | 0.5000 | 0.0000 |
| Baseline 2: puntaje = −viajes_28d | 0.2731 | 0.0024 | 0.7301 | 0.0034 |
| Logística L2 (Ridge), C=0.003162 (λ=316.2) | 0.4158 | 0.0111 | 0.8059 | 0.0027 |
| Logística L1 (Lasso), C=0.01 (λ=100) | 0.4158 | 0.0109 | 0.8057 | 0.0026 |
| Logística Elastic Net (l1_ratio 0.5), C=0.01 (λ=100) | 0.4159 | 0.0109 | 0.8058 | 0.0026 |
