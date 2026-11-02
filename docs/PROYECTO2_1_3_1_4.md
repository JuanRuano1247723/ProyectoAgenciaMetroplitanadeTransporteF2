# Proyecto 2 · 1.3 Features y auditoría de fuga · 1.4 Baselines y regresión logística

Código: `dbt_metro/models/features/features_corte.sql`, `flows/prueba_recorte.py`, `modelos/comun.py`, `modelos/linea_base.py`. Evidencia en `evidencia/p2_1_3_*` y `evidencia/p2_1_4_*`. La unidad es la tarjeta (ver `docs/PROYECTO2_1_2.md`).

## 1.3 Features

- **Tabla de features:** `features.features_corte`, una fila por unidad y corte para A (77,062), B y C, con `unidad_id`, `fecha_corte`, 15 features y `etiqueta` (vacía en C). Una prueba de dbt comprueba una sola fila por (unidad, corte).
- **Diccionario:** `docs/DICCIONARIO_FEATURES_P2.md`. Una fila por feature con qué mide, ventana (ninguna pasa de 28 días) y tabla de Silver.
- **Prueba de recorte:** `python -m flows.prueba_recorte` calcula el corte A con datos completos y con datos recortados al 30 de junio. Resultado en `evidencia/p2_1_3_prueba_recorte.md`: 77,062 filas comparadas, **0 diferencias**, ninguna feature falló. Como control, una feature con fuga adrede (total de viajes sin cortar) difiere en 68,205 filas, así que la prueba sí detecta fugas. No hubo features que corregir: ninguna falló en la primera corrida.

## 1.4 Baselines y regresión logística

Todo se evalúa con la misma validación cruzada estratificada de 5 folds (semilla 42, `modelos/comun.py`) y solo con el corte A: 11,100 positivos de 77,062 = 0.1440. El corte B no se usa.

### Métrica elegida: PR-AUC (average precision)

El 14.4% de las unidades son positivas, y la Agencia no puede contactar a todos: necesita ordenar a los usuarios para llamar primero a los de mayor riesgo y le importa que los contactados sean de verdad quienes se van. La PR-AUC mide justo eso (qué tan pura es la lista de contactados a medida que se amplía) y no se infla por la clase mayoritaria, como pasa con la exactitud, que daría 0.856 con "nadie se va". Su referencia es la tasa positiva (0.144), que es lo que obtiene el baseline 1. Como métrica secundaria se reporta ROC-AUC. Se usa una métrica de ranking porque el umbral se decide después, con costos (2.2).

### Tabla de modelos (5 folds del corte A)

| modelo | PR-AUC media | PR-AUC desv. est. | ROC-AUC media | ROC-AUC desv. est. |
|---|---:|---:|---:|---:|
| Baseline 1: tasa positiva de A para todos | 0.1440 | 0.0000 | 0.5000 | 0.0000 |
| Baseline 2: puntaje = −viajes_28d | 0.2731 | 0.0024 | 0.7301 | 0.0034 |
| Logística L2 (Ridge), C=0.003162 (λ=316.2) | 0.4158 | 0.0111 | 0.8059 | 0.0027 |
| Logística L1 (Lasso), C=0.01 (λ=100) | 0.4158 | 0.0109 | 0.8057 | 0.0026 |
| Logística Elastic Net (l1_ratio 0.5), C=0.01 (λ=100) | 0.4159 | 0.0109 | 0.8058 | 0.0026 |

El baseline 2 usa una sola feature sin entrenar: quien hizo menos viajes en las 4 semanas antes del corte queda con más riesgo, porque la actividad reciente es la señal más directa de que alguien está dejando de usar la red. Mejora al baseline 1, pero la logística lo supera por mucho.

### Gráfica

`evidencia/p2_1_4_curva_lambda.png`: PR-AUC de validación contra λ = 1/C para las tres penalizaciones, con la desviación estándar entre folds. Cada círculo marca el λ elegido (el de mayor PR-AUC media de cada penalización). La curva es plana para λ pequeños y cae cuando el castigo es muy fuerte (la L1 colapsa al baseline con λ = 10,000, porque anula todos los coeficientes).

Límite: las tres penalizaciones empatan, ya que sus diferencias (0.0001) son mucho menores que la desviación estándar entre folds (≈0.011). Con 15 features y 77,062 filas, regularizar casi no cambia el resultado. Además, λ se eligió con los mismos folds con los que se reporta, así que la cifra es un poco optimista; la evaluación honesta es el test único del corte B (2.2).

### Coeficientes (L2, variables estandarizadas, ajustada con todo el corte A solo para interpretar)

Un coeficiente positivo empuja hacia el abandono (etiqueta 1). Se usó la L2 porque la L1 y la Elastic Net anulan varios coeficientes y no alcanzan para listar 5.

| Feature | Coef. | Interpretación |
|---|---:|---|
| `dias_desde_ultimo_viaje` | +0.612 | Tiene sentido: cuantos más días lleva sin abordar, más probable es que ya no vuelva. Es con mucho la señal más fuerte. |
| `estaciones_distintas_28d` | +0.056 | Efecto pequeño. Una vez controlados los viajes, quien usa más estaciones es menos rutinario, y la rutina fija protege contra el abandono. |
| `op_MR` | +0.056 | Efecto pequeño: las tarjetas de MetroRiel tienen un poco más de riesgo que el promedio con el mismo comportamiento. |
| `prop_fin_de_semana_28d` | +0.050 | Tiene sentido: quien viaja sobre todo en fin de semana es un usuario ocasional, no un viajero diario. |
| `viajes_14d_previos` | +0.032 | Efecto casi nulo y su signo depende de las otras variables de conteo (están muy correlacionadas con `viajes_28d` y `viajes_14d`). No se debe leer aislado. |

Del otro lado, protegen contra el abandono `dias_activos_28d` (−0.592) y `viajes_7d` (−0.365): quien viaja más días y más en la última semana se queda. Los coeficientes de las variables de conteo (`viajes_7d`, `viajes_14d`, `viajes_28d`, `dias_activos_28d`) están correlacionados entre sí, así que sus signos individuales no son causales; lo estable es la lectura de conjunto: poca actividad reciente implica más riesgo.
