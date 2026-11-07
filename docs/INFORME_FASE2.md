# Informe de la Fase 2 · ¿Quién deja de usar la red?

Proyecto 2, Ciencia de Datos, Universidad Rafael Landívar. **Los datos son simulados.** Repositorio con la etiqueta `fase-2`.

## 1. El problema y las decisiones de base

Se predice si una tarjeta deja de usar la red en los 30 días siguientes a una fecha de corte. Todo lo que ve el modelo es anterior al corte.

| Decisión | Elección | Por qué | Detalle |
|---|---|---|---|
| Etiqueta | 1 si no hay ningún abordaje válido, en ningún operador, en los 30 días desde el corte | Dejar de viajar no es lo mismo que la baja del CDC | `docs/PROYECTO2_1_2.md` |
| Unidad | La tarjeta (operador, llave) | `usuario_sk` es la capa de certeza del Proyecto 1; `persona_id` es solo una hipótesis y Aerómetro no se puede enlazar | `docs/PROYECTO2_1_2.md` |
| Población | ≥ 2 abordajes válidos en 28 días y sin DELETE del CDC vigente | Hay historia para predecir; las bajas ya están decididas | `docs/PROYECTO2_1_2.md` |
| Cortes | A 1-jul (entrenar), B 31-jul (test único), C 30-ago (predicciones) | Diseño del enunciado | |
| Métrica | PR-AUC, con ROC-AUC secundaria | Clase minoritaria (14.4%) y se contacta a una lista ordenada | `docs/PROYECTO2_1_3_1_4.md` |

| Corte | Población | Positivos | Tasa |
|---|---:|---:|---:|
| A | 77,062 | 11,100 | 0.1440 |
| B | 76,096 | 10,249 | 0.1347 |
| C | 76,127 | oculta | |

Costo de la unidad: 21.7% (A) y 23.4% (B) de los positivos siguieron viajando con otra tarjeta. Es un mínimo, porque Aerómetro no se puede enlazar.

## 2. Datos desde cero (1.1)

Un comando, `python -m flows.correr_todo`, vacía el lake, carga por lotes y CDC, pasa por Kafka y construye Silver y Gold con dbt. Los 9 archivos cuadran con los conteos esperados (diferencia 0). Tiempo total 77.8 s (`evidencia/p2_1_1_*`).

## 3. Features y fuga (1.3)

15 features de los 28 días anteriores al corte, más el operador. La prueba de recorte (datos completos contra datos cortados al corte) dio **0 diferencias en 77,062 filas**; una feature con fuga puesta adrede sí falló (68,205 filas), por lo que la prueba detecta fugas. Diccionario en `docs/DICCIONARIO_FEATURES_P2.md`.

## 4. Modelos (1.4 y 2.1)

Todos con los mismos 5 folds estratificados del corte A (semilla 42). El corte B no se toca.

| Modelo | PR-AUC validación | desv. est. | brecha entren.–valid. |
|---|---:|---:|---:|
| Baseline 1: tasa de A | 0.1440 | 0.0000 | 0 |
| Baseline 2: −viajes_28d | 0.2731 | 0.0024 | 0 |
| Logística L2 / L1 / Elastic Net | 0.4158 | 0.011 | 0.000 |
| Random Forest flexible | 0.3565 | 0.0048 | +0.611 |
| Random Forest regularizado | 0.4327 | 0.0080 | +0.017 |
| HistGradientBoosting flexible | 0.4248 | 0.0052 | +0.253 |
| **HistGradientBoosting regularizado** | **0.4377** | 0.0072 | +0.009 |

- Las tres penalizaciones de la logística empatan (diferencia 0.0001, contra una desviación de 0.011): con 15 features y 77 mil filas, regularizar casi no cambia nada.
- Los ensembles flexibles sobreajustan (varianza alta); los regularizados quedan equilibrados.
- Se eligió el HGB regularizado: +0.022 de PR-AUC sobre la logística, mayor que la desviación entre folds, a costa de 3.4 s en vez de 0.9 s de entrenamiento. Las cuatro configuraciones se eligieron a mano y con la misma validación, por lo que 0.4377 es algo optimista.
- Importancia por permutación en validación: `dias_desde_ultimo_viaje` (caída 0.184) domina; la segunda, `persona_operadores_28d`, cae 0.036.

Detalle: `docs/PROYECTO2_1_3_1_4.md`, `docs/PROYECTO2_2_1_2_3.md`.

## 5. Umbral y test único (2.2)

Escenario simulado: contactar Q5, retención 25%, usuario retenido Q60. Ganancia **G = 10·TP − 5·FP**; umbral teórico 5/15 = 0.333. Con las predicciones de validación cruzada de A se barrió el umbral y se eligió **0.32** (Q17,610 en A; la curva es plana entre 0.30 y 0.35). Quedó guardado en `evidencia/p2_2_2_umbral.json` antes de leer B.

Test B, una sola vez (2026-11-06 17:47, código y evidencia en el commit `091f1ed`):

| Modelo (umbral 0.32) | Contactados | TP | FP | Precisión | Recall | Ganancia |
|---|---:|---:|---:|---:|---:|---:|
| HGB regularizado | 9,344 | 3,896 | 5,448 | 0.417 | 0.380 | **Q11,720** |
| Baseline 1 | 0 | 0 | 0 | 0 | 0 | Q0 |
| Baseline 2 (mismos contactos, menos viajes) | 9,344 | 3,038 | 6,306 | 0.325 | 0.296 | −Q1,150 |
| Contactar a todos | 76,096 | 10,249 | 65,847 | 0.135 | 1.000 | −Q226,745 |

PR-AUC en B: modelo 0.3916, baselines 0.1347 y 0.2644. **B salió peor que la validación** (PR-AUC 0.4377 → 0.3916; ganancia Q17,610 → Q11,720). Se pierden verdaderos positivos (4,476 → 3,896) y los falsos casi no cambian; B tiene menos positivos (0.1347 contra 0.1440); y hay algo de optimismo por haber elegido configuración y umbral con la misma validación. No se ajustó nada después de ver B (`docs/BITACORA_P2.md`). Detalle: `docs/PROYECTO2_2_2.md`.

## 6. Segmentación (2.3)

KMeans con las 15 features escaladas del corte A, sin etiqueta ni corte B. k = 3 (silueta 0.270, que cae a 0.158 con k = 4; k = 2 se descartó porque solo separa al 11% más intenso). PCA con 54.7% de varianza en dos ejes.

| Segmento | % | Tasa de abandono | Acción |
|---|---:|---:|---|
| Ocasionales en riesgo | 75.1% | 0.182 | Campaña priorizada por el puntaje del modelo |
| Regulares | 22.3% | 0.030 | Solo recordatorio sin costo a quien baja su ritmo |
| Intensivos | 2.6% | 0.019 | Sin retención; fidelidad o referidos |

El 95% de los positivos está en el primer segmento: la segmentación sola no decide a quién contactar, lo hace el modelo con el umbral.

## 7. MLOps (2.4)

- `python predecir.py --datos <carpeta> --fecha-corte 2026-08-30` produce `unidad_id, tarjetas, puntaje, contactar`; carga `modelos_guardados/modelo_abandono_v1.0.0.joblib` (pipeline completo) y no reentrena.
- Versiones fijas en `requirements.txt`, semilla 42, README para otra máquina.
- Predicciones de C: `predicciones/predicciones_corte_C.csv`, 76,127 filas, 9,768 con `contactar = 1`. Se verificó que `predecir.py` las reproduce idénticas (misma huella SHA-1).
- Ficha del modelo: `docs/FICHA_MODELO.md`.

## 8. Fuga y rendimiento

| Prueba | Resultado |
|---|---|
| Recorte de features (1.3) | 0 diferencias en 77,062 filas |
| Invariancia simulada (datos recortados al 31-jul contra completos) | Predicciones idénticas (`evidencia/p2_2_4_prueba_invariancia.md`) |
| Invariancia real con 30 días más | Se hace en la calificación |
| Test B | Usado una vez, modelo y umbral congelados |
| Pruebas automáticas | 87 de 87 pasan |

| Rendimiento | Tiempo |
|---|---:|
| Carga desde cero | 78 s |
| Features (dbt) | 5 s |
| Entrenamiento del modelo final | 0.65 s |
| Predicción de 76,127 unidades | 0.4 s |

## 9. Limitaciones

Datos simulados. La tarjeta como unidad cuenta como abandono a quien cambia de tarjeta. Solo 28 días de historia y sin variables demográficas. No se verificó la calibración de las probabilidades, de la que depende que el umbral 0.32 sea el mejor. La ganancia depende de un escenario de costos simulado. La mejora del ensemble sobre la logística es modesta.
