Modelo: HistGradientBoosting regularizado (lr 0.05, prof. 3, 200 iter.). Caída de PR-AUC al permutar cada feature en los folds de validación (5 repeticiones por fold).

| # | feature | caída de PR-AUC | desv. est. entre folds |
|---:|---|---:|---:|
| 1 | dias_desde_ultimo_viaje | 0.1837 | 0.0109 |
| 2 | persona_operadores_28d | 0.0364 | 0.0022 |
| 3 | gasto_28d | 0.0083 | 0.0006 |
| 4 | viajes_7d | 0.0080 | 0.0015 |
| 5 | viajes_14d | 0.0078 | 0.0039 |
| 6 | tendencia_14d | 0.0056 | 0.0021 |
| 7 | viajes_28d | 0.0040 | 0.0006 |
| 8 | tarifa_media_28d | 0.0029 | 0.0008 |
| 9 | dias_activos_28d | 0.0022 | 0.0014 |
| 10 | op_TM | 0.0022 | 0.0012 |
