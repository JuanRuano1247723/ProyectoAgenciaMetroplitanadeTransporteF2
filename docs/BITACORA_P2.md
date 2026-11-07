# Bitácora del Proyecto 2

Registro de las decisiones y evaluaciones que no se pueden repetir. El corte B solo se evalúa **una vez**.

## Test único en el corte B (2.2)

| Campo | Valor |
|---|---|
| Fecha y hora | 2026-11-06 17:47 (hora local) |
| Rama y commit base | `fase-2`, `c211dd2` (el código de `modelos/umbral.py` y la evidencia de 2.2 aún no estaban versionados) |
| Commit que contiene el código y la evidencia | `091f1ed` (rama `fase-2`, subido por Ruano; la evidencia quedó movida a `evidencia/` en un commit posterior) |
| Modelo | HistGradientBoosting regularizado (lr 0.05, profundidad 3, 200 iteraciones), entrenado con todo el corte A. Elegido en 2.1 antes de abrir B |
| Umbral | 0.32, elegido con las predicciones de validación cruzada del corte A y guardado en `evidencia/p2_2_2_umbral.json` antes de leer B |
| Comando | `python -m modelos.umbral evaluar-b` (se niega a repetirse si existe `evidencia/p2_2_2_test_b.json`) |
| Resultado | PR-AUC 0.3916; precisión 0.417; recall 0.380; ganancia Q11,720 (TP 3,896, FP 5,448) |
| Contra validación | PR-AUC 0.4370 y ganancia Q17,610 en A: peor en B; explicación en `docs/PROYECTO2_2_2.md`, sin reajustar |
| Después de ver B | No se cambió ni el modelo, ni el umbral, ni la configuración |

Nota técnica: el campo `arbol_con_cambios_sin_commit` del JSON dice `false` porque en esa corrida el chequeo ignoraba archivos nuevos sin versionar (lo corregí después en el código; no afecta ningún resultado). En realidad `modelos/umbral.py` estaba sin versionar.
