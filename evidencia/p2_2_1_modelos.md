| modelo | PR-AUC entrenamiento | PR-AUC validación (media) | desv. est. | brecha | ROC-AUC entren. | ROC-AUC valid. | seg. entren. |
|---|---:|---:|---:|---:|---:|---:|---:|
| Baseline 1: tasa positiva de A para todos | 0.1440 | 0.1440 | 0.0000 | -0.0000 | 0.5000 | 0.5000 | 0.0 |
| Baseline 2: puntaje = −viajes_28d | 0.2731 | 0.2731 | 0.0024 | -0.0000 | 0.7301 | 0.7301 | 0.0 |
| Logística L2 (Ridge), C=0.003162 | 0.4158 | 0.4158 | 0.0111 | -0.0000 | 0.8062 | 0.8059 | 0.9 |
| Logística L1 (Lasso), C=0.01 | 0.4158 | 0.4158 | 0.0109 | +0.0000 | 0.8059 | 0.8057 | 1.2 |
| Logística Elastic Net (l1_ratio 0.5), C=0.01 | 0.4159 | 0.4159 | 0.0109 | +0.0000 | 0.8061 | 0.8058 | 1.9 |
| Random Forest flexible (árboles sin límite de profundidad) | 0.9675 | 0.3565 | 0.0048 | +0.6110 | 0.9944 | 0.7677 | 5.9 |
| Random Forest regularizado (hojas de al menos 100 filas) | 0.4499 | 0.4327 | 0.0080 | +0.0173 | 0.8318 | 0.8182 | 4.5 |
| HistGradientBoosting flexible (lr 0.1, 63 hojas, 300 iter.) | 0.6775 | 0.4248 | 0.0052 | +0.2526 | 0.9228 | 0.8098 | 40.0 |
| HistGradientBoosting regularizado (lr 0.05, prof. 3, 200 iter.) | 0.4469 | 0.4377 | 0.0072 | +0.0092 | 0.8250 | 0.8199 | 3.4 |
