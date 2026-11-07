# Proyecto 2 · 2.1 Ensemble y sesgo-varianza · 2.3 Segmentación con KMeans y PCA

Código: `modelos/ensemble.py` y `modelos/segmentos.py`. Evidencia en `evidencia/p2_2_1_*` y `evidencia/p2_2_3_*`. Unidad: la tarjeta. Solo se usa el corte A; el corte B no se carga en ningún paso.

## 2.1 Ensemble

Los modelos se comparan con los mismos 5 folds estratificados del corte A que en 1.4 (`modelos/comun.py`, semilla 42) y con la misma métrica, PR-AUC (justificada en `docs/PROYECTO2_1_3_1_4.md`). Se entrenaron dos ensembles, Random Forest e HistGradientBoosting, cada uno en una versión flexible y una regularizada. Cada logística usa el C elegido en 1.4.

### Tabla de modelos (entrenamiento y validación)

| modelo | PR-AUC entrenamiento | PR-AUC validación (media) | desv. est. | brecha | ROC-AUC entren. | ROC-AUC valid. | seg. entren. |
|---|---:|---:|---:|---:|---:|---:|---:|
| Baseline 1: tasa positiva de A para todos | 0.1440 | 0.1440 | 0.0000 | 0.0000 | 0.5000 | 0.5000 | 0.0 |
| Baseline 2: puntaje = −viajes_28d | 0.2731 | 0.2731 | 0.0024 | 0.0000 | 0.7301 | 0.7301 | 0.0 |
| Logística L2 (Ridge), C=0.003162 | 0.4158 | 0.4158 | 0.0111 | 0.0000 | 0.8062 | 0.8059 | 0.9 |
| Logística L1 (Lasso), C=0.01 | 0.4158 | 0.4158 | 0.0109 | 0.0000 | 0.8059 | 0.8057 | 1.2 |
| Logística Elastic Net (l1_ratio 0.5), C=0.01 | 0.4159 | 0.4159 | 0.0109 | 0.0000 | 0.8061 | 0.8058 | 1.9 |
| Random Forest flexible (árboles sin límite de profundidad) | 0.9675 | 0.3565 | 0.0048 | +0.6110 | 0.9944 | 0.7677 | 5.9 |
| Random Forest regularizado (hojas de al menos 100 filas) | 0.4499 | 0.4327 | 0.0080 | +0.0173 | 0.8318 | 0.8182 | 4.5 |
| HistGradientBoosting flexible (lr 0.1, 63 hojas, 300 iter.) | 0.6775 | 0.4248 | 0.0052 | +0.2526 | 0.9228 | 0.8098 | 40.0 |
| HistGradientBoosting regularizado (lr 0.05, prof. 3, 200 iter.) | 0.4469 | 0.4377 | 0.0072 | +0.0092 | 0.8250 | 0.8199 | 3.4 |

La brecha es PR-AUC de entrenamiento menos PR-AUC de validación. Los baselines no se entrenan, así que su brecha es 0. Los segundos son el tiempo total de entrenar los 5 folds.

### Sesgo-varianza

| Modelo | Diagnóstico | Por qué |
|---|---|---|
| Baselines | Sesgo alto | No aprenden nada de los datos; el baseline 1 solo reproduce la tasa. |
| Logística (L2, L1, Elastic Net) | Sesgo relativamente alto, varianza baja | Entrenamiento y validación coinciden (brecha 0.0000), pero los ensembles regularizados llegan a 0.43, así que a la recta le falta capacidad para las relaciones no lineales. |
| Random Forest flexible | Varianza alta (sobreajuste) | Entrena a 0.9675 y valida a 0.3565: memoriza el entrenamiento y rinde peor en validación que la logística. |
| Random Forest regularizado | Equilibrado | Brecha de 0.0173 y validación 0.4327, mejor que la logística. |
| HistGradientBoosting flexible | Varianza alta | Brecha de 0.2526 (0.6775 contra 0.4248): demasiadas hojas y demasiadas iteraciones. |
| HistGradientBoosting regularizado | Equilibrado | Brecha de 0.0092 y la mejor validación (0.4377). Limitar la profundidad a 3 y la tasa de aprendizaje a 0.05 quitó casi toda la varianza sin perder precisión. |

### Importancia por permutación (en validación, no en entrenamiento)

Modelo: HistGradientBoosting regularizado. Caída de PR-AUC al permutar cada feature en los folds de validación (5 repeticiones por fold). Gráfica: `evidencia/p2_2_1_importancias.png`.

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

`dias_desde_ultimo_viaje` domina (0.184, unas cinco veces la importancia de la segunda), igual que en la logística de 1.4. `persona_operadores_28d` es la segunda: quien usa más de un operador abandona menos, coherente con el costo de la unidad de 1.2.

### Decisión

Va a producción el HistGradientBoosting regularizado. Mejora a la logística en 0.022 de PR-AUC (0.4377 contra 0.4158) y en 0.014 de ROC-AUC (0.8199 contra 0.8059). La mejora es modesta, pero es mayor que la desviación estándar entre folds (0.007 a 0.011) y se repite en las dos métricas y en los dos ensembles regularizados. Su costo de complejidad es bajo: entrena en 3.4 s los 5 folds contra 0.9 s de la logística, y su falta de interpretabilidad se compensa con la importancia por permutación. Los modelos flexibles se descartan por sobreajuste. Limitación: las cuatro configuraciones de ensemble se eligieron a mano, no con una búsqueda; elegir el mejor entre ellas con la validación da una cifra algo optimista, que el test único del corte B (2.2) confirmará o corregirá.

## 2.3 Segmentación con KMeans y PCA

Se aplica KMeans a las 15 features numéricas del corte A (77,062 unidades), escaladas con `StandardScaler` (media 0, desviación 1). No se usa la etiqueta para formar los segmentos (solo para describirlos después), no se usa el corte B, y el segmento no se usa como feature de ningún clasificador, así que no hace falta ajustar KMeans dentro de la validación cruzada.

### Elección de k

Gráficas en `evidencia/p2_2_3_k.png`:

| k | inercia | silueta |
|---:|---:|---:|
| 2 | 854,460 | 0.483 |
| 3 | 744,636 | 0.270 |
| 4 | 684,260 | 0.158 |
| 5 | 635,310 | 0.159 |
| 6 | 596,385 | 0.153 |
| 7 | 560,811 | 0.155 |
| 8 | 535,231 | 0.156 |

Se eligió k = 3. La silueta cae de 0.270 con k = 3 a 0.158 con k = 4 y después queda plana, y la curva del codo pierde pendiente a partir de k = 3. Se descartó k = 2 aunque tenga la silueta más alta: solo separa a los viajeros intensos (11%) del resto y no permite acciones distintas. La silueta se calculó con una muestra fija de 10,000 filas por costo.

### Gráfico PCA

`evidencia/p2_2_3_pca.png`: los segmentos en los dos primeros componentes (muestra de 12,000 puntos). La varianza explicada es 44.4% + 10.4% = 54.7%. El componente 1 es casi un eje de nivel de actividad: los segmentos se ordenan de izquierda a derecha de menos a más actividad. Cuidado al leerlo: con solo el 54.7% de la varianza en dos ejes, la separación visual es aproximada.

### Tabla de segmentos

Tasa de abandono global del corte A: 0.1440. La tasa por segmento es descriptiva: no prueba que el segmento cause el abandono.

| Segmento | Nombre | Tamaño | % | Tasa de abandono | Mediana de viajes en 28 días | Mediana de días activos | Mediana de días desde el último viaje | Mediana de gasto (Q) | Mediana de operadores (persona) |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | Ocasionales en riesgo | 57,857 | 75.1% | 0.1823 | 5 | 4 | 5 | 7.0 | 2 |
| 1 | Regulares | 17,175 | 22.3% | 0.0300 | 23 | 14 | 1 | 32.5 | 1 |
| 2 | Intensivos | 2,030 | 2.6% | 0.0187 | 74 | 23 | 1 | 96.2 | 1 |

Cada segmento tiene nombre: los *ocasionales en riesgo* viajan unas 5 veces al mes y llevan 5 días sin abordar (concentran 10,546 de los 11,100 positivos, el 95%); los *regulares* viajan unos 14 días de 28 y casi nunca se van; los *intensivos* son pocos y se quedan.

### Acciones de retención

1. Ocasionales en riesgo: son los únicos candidatos a la campaña. Un mensaje con recarga de cortesía, priorizado por la probabilidad del modelo (2.2), porque el presupuesto no alcanza para los 57,857.
2. Regulares: no se les da incentivo, porque abandonan en el 3% y regalarles recarga cuesta más de lo que retiene. Un recordatorio sin costo solo a quienes bajan su ritmo (`tendencia_14d` negativa) para detectar el enfriamiento a tiempo.
3. Intensivos: ninguna acción de retención (abandonan en el 1.9%). Se pueden usar para otras iniciativas, como programas de fidelidad o de referidos.

Límite: el 75% de la población cae en un solo segmento, así que la segmentación por sí sola no basta para decidir a quién contactar; esa decisión viene del modelo y del umbral de costo en 2.2.
