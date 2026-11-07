# Prueba de invariancia (simulada) · 2.4

**Qué exige el PDF:** el día de la calificación recibirán los mismos datos con 30 días más; correrán el flujo y `predecir.py` con corte 30 de agosto, y las predicciones deben ser idénticas a las entregadas. Si cambian, el pipeline usa datos posteriores al corte.

**Qué se pudo probar hoy:** no tenemos esos 30 días extra, así que se hizo lo inverso, con el corte B (2026-07-31). Se recortaron los **datos crudos** a eventos anteriores al corte (`flows/recortar_datos.py`), se reconstruyó todo desde cero en un lake aparte (Bronze, Silver, dbt, features) y se comparó con la corrida con los datos completos. Es la misma prueba, pero quitando días en vez de agregarlos.

| | Datos recortados | Datos completos |
|---|---:|---:|
| Filas de origen (Transmetro / Transurbano / Aerómetro / MetroRiel / CDC) | 469,284 / 1,083,158 / 256,271 / 390,134 / 52,320 | 713,786 / 1,635,788 / 387,053 / 590,844 / 77,636 |
| Unidades en el corte B | 76,096 | 76,096 |
| Unidades a contactar (puntaje ≥ 0.32) | 9,344 | 9,344 |
| SHA-256 del CSV de predicciones | `674a04a04beeed5d478839be6bbfa02579426d58c9fbfc5c31424840dd84426d` | `674a04a04beeed5d478839be6bbfa02579426d58c9fbfc5c31424840dd84426d` |

**Resultado:** archivos idénticos. 0 diferencias en `unidad_id`, `tarjetas`, `puntaje` y `contactar` en las 76,096 filas.

## Por qué debería cumplirse con datos reales extendidos
- Las features solo usan eventos en `[corte − 28 días, corte)` y la población solo mira abordajes anteriores al corte y bajas del CDC con `commit_ts` anterior al corte (prueba de recorte de 1.3, 0 diferencias).
- La regla de Silver `fecha_futura` compara contra la **fecha de ingesta**, no contra el último día de los datos, así que agregar días no cambia qué eventos se aceptan antes del corte.
- La unidad se identifica con `operador:llave`, que no depende del secreto de seudonimización: el CSV es igual en cualquier máquina.
- `predecir.py` solo carga el modelo guardado; no entrena.

## Límites
- No se probó con los 30 días reales: eso solo se verá en la defensa. Si los datos nuevos cambian formatos o reglas de calidad, podría aparecer una diferencia que esta simulación no ve.
- Al recortar se descartan las filas con fecha ilegible, que de todos modos Silver rechaza.

## Cómo repetirla
```bash
python -m flows.recortar_datos datos_red datos_recortados 2026-07-31T00:00:00
LAKE_DIR=lake_recortado python predecir.py --datos datos_recortados --fecha-corte 2026-07-31 --salida pred_recortado.csv
python predecir.py --datos datos_red --fecha-corte 2026-07-31 --salida pred_completo.csv
shasum -a 256 pred_recortado.csv pred_completo.csv
```
