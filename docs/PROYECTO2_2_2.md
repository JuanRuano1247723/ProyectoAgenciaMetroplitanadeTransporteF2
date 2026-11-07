# Proyecto 2 · 2.2 Umbral según costo y test único

Código: `modelos/umbral.py`. Evidencia en `evidencia/p2_2_2_*`. Modelo: HistGradientBoosting regularizado (elegido en 2.1 antes de abrir el corte B). Unidad: la tarjeta.

## Ganancia

Escenario de la Agencia (valores simulados, iguales para todos los grupos): contactar a un usuario cuesta **Q5**; si el usuario se iba a ir, la campaña lo retiene en el **25%** de los casos; un usuario retenido vale **Q60**.

Un usuario que se iba a ir y es contactado deja, en promedio, 0.25 × Q60 = **Q15**. Cada contacto cuesta Q5, se iba a ir o no. Para un grupo contactado con TP usuarios que se iban a ir y FP que no:

```
G = 0.25 × 60 × TP − 5 × (TP + FP)
  = 15·TP − 5·TP − 5·FP
  = 10·TP − 5·FP        (en quetzales)
```

Por usuario con probabilidad p de irse, la ganancia esperada de contactarlo es g(p) = 15·p − 5, que es positiva si **p > 5/15 = 1/3**. Ese es el umbral teórico si las probabilidades están calibradas; el umbral real se deriva de los datos.

Cuenta completa en el corte A (validación cruzada, 77,062 unidades, 11,100 positivos), con el umbral elegido 0.32: 4,476 TP y 5,430 FP, así que G = 10 × 4,476 − 5 × 5,430 = 44,760 − 27,150 = **Q17,610**.

## Elección del umbral (solo con el corte A)

Se usaron las predicciones de validación cruzada del corte A (cada unidad la predice un modelo que no la vio, con los mismos 5 folds de 1.4 y 2.1). Se calculó la ganancia para umbrales de 0.02 a 0.98 en pasos de 0.005 y se eligió el máximo. Curva: `evidencia/p2_2_2_curva_ganancia.png`, datos en `p2_2_2_curva_ganancia.csv`.

| Umbral | Contactados | TP | FP | Precisión | Recall | Ganancia (Q) |
|---:|---:|---:|---:|---:|---:|---:|
| 0.10 | 36,733 | 9,707 | 27,026 | 0.264 | 0.875 | −38,060 |
| 0.20 | 21,671 | 7,513 | 14,158 | 0.347 | 0.677 | 4,340 |
| 0.25 | 16,478 | 6,359 | 10,119 | 0.386 | 0.573 | 12,995 |
| 0.30 | 11,642 | 5,033 | 6,609 | 0.432 | 0.453 | 17,285 |
| **0.32** | **9,906** | **4,476** | **5,430** | **0.452** | **0.403** | **17,610** |
| 0.35 | 7,812 | 3,752 | 4,060 | 0.480 | 0.338 | 17,220 |
| 0.40 | 5,589 | 2,950 | 2,639 | 0.528 | 0.266 | 16,305 |
| 0.50 | 2,547 | 1,581 | 966 | 0.621 | 0.142 | 10,980 |

- **Umbral elegido: 0.320.** El teórico (1/3) da Q17,600, casi lo mismo: la curva es plana entre 0.30 y 0.35, así que el umbral es estable.
- Contactar a todos en A daría −Q218,810: sin modelo la campaña pierde dinero.
- El umbral quedó guardado en `evidencia/p2_2_2_umbral.json` **antes** de leer el corte B.

## Test B (una sola evaluación)

Con el umbral congelado, se entrenó el modelo final con **todo el corte A** y se evaluó en el corte B (76,096 unidades, 10,249 positivos, tasa 0.1347) una sola vez. Detalle en `evidencia/p2_2_2_test_b.json`; el script se niega a repetir la evaluación.

- **Fecha:** 2026-11-06 17:47.
- **Commit:** la corrida partía del commit base `c211dd2` (rama `fase-2`), con `modelos/umbral.py` todavía sin versionar. El código y esta evidencia se subieron en el commit `091f1ed` (ver `docs/BITACORA_P2.md`).
- **Métrica:** PR-AUC 0.3916 (ROC-AUC 0.8148), junto a sus baselines.

| Modelo (umbral 0.32) | Contactados | TP | FP | FN | TN | Precisión | Recall | Ganancia (Q) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **HistGradientBoosting regularizado** | 9,344 | 3,896 | 5,448 | 6,353 | 60,399 | 0.417 | 0.380 | **11,720** |
| Baseline 1: probabilidad de A para todos (0.144, no supera 1/3) | 0 | 0 | 0 | 10,249 | 65,847 | 0.000 | 0.000 | 0 |
| Baseline 2: mismos 9,344 contactos, los de menos viajes | 9,344 | 3,038 | 6,306 | 7,211 | 59,541 | 0.325 | 0.296 | −1,150 |
| Contactar a todos | 76,096 | 10,249 | 65,847 | 0 | 0 | 0.135 | 1.000 | −226,745 |

Cuenta de la ganancia del modelo: G = 10 × 3,896 − 5 × 5,448 = 38,960 − 27,240 = **Q11,720**.

PR-AUC en B: modelo 0.3916, baseline 1 (tasa de B) 0.1347, baseline 2 (−viajes_28d) 0.2644.

### Resultado peor que en validación: explicación (sin volver a ajustar nada)

Contra validación del corte A (PR-AUC 0.4370 con las predicciones cruzadas; ganancia Q17,610), en B bajaron la PR-AUC (0.3916), la precisión (0.452 a 0.417), el recall (0.403 a 0.380) y la ganancia (Q17,610 a Q11,720, −33%). El modelo sigue ganando dinero y supera a todos sus baselines. Qué se observa:

1. **Se pierden verdaderos positivos, no se ganan falsos:** TP bajó de 4,476 a 3,896 (−13%) y FP casi no cambió (5,430 a 5,448). Como cada FP cuesta Q5 y cada TP deja Q10 netos, perder TP es lo que baja la ganancia.
2. **B tiene menos positivos:** la tasa positiva es 0.1347 en B contra 0.1440 en A (−6.5%). La PR-AUC depende de la tasa; el ranking del modelo casi no cambió (ROC-AUC 0.8148 contra 0.8199 en validación). Medida contra su baseline, la mejora es parecida: PR-AUC/tasa = 2.91 en B y 3.04 en A.
3. **Las features no cambiaron mucho:** sin usar la etiqueta, la mediana de días desde el último viaje es 4 en A y 3 en B; la fracción con 7 o más días sin viajar es 31.9% en A y 32.7% en B. Hay algo más de unidades "en riesgo" aparente en B y menos abandonos reales, así que se acierta menos.
4. **Optimismo de la validación:** la configuración del ensemble se eligió entre cuatro con la misma validación cruzada (2.1) y el umbral se eligió con esas mismas predicciones; ambas cosas inflan un poco la cifra de A. Parte de la diferencia es esa selección, y por eso existe un test que no se tocó.

No se sabe separar con certeza cuánto se debe a cada causa sin volver a mirar B, y eso está prohibido. No se cambió el umbral, el modelo ni la configuración después de ver B.
