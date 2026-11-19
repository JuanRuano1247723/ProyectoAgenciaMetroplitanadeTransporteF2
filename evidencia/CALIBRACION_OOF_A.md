# Calibración de las probabilidades de abandono del corte A

El barrido original de umbrales se construyó con las predicciones fuera de muestra (OOF) del HistGradientBoosting regularizado en A. Cada tarjeta fue predicha por un modelo entrenado en los otros cuatro folds. Se usaron cinco folds estratificados con semilla 42, 77,062 tarjetas y 11,100 abandonos observados.

## Curva y ECE a partir del barrido archivado

![Curva de calibración del corte A con rangos de la probabilidad media y conteos](p2_calibracion_oof_a_acotada.png)

El [CSV del barrido](p2_2_2_curva_ganancia.csv) conserva los verdaderos positivos y el total de tarjetas con puntaje mayor o igual a cada umbral. Restando los acumulados de dos umbrales consecutivos se recuperan los conteos dentro de cada intervalo. Los agregamos en diez intervalos de igual ancho entre 0 y 1, cerrados a izquierda y abiertos a derecha. El último incluye 1.

Para cada intervalo, la tasa observada es la proporción de tarjetas que abandonaron. Podemos acotar la probabilidad media ponderando los extremos de cada tramo fino del barrido por sus conteos. La gráfica muestra esas cotas con barras horizontales y usa el punto medio como estimación de la probabilidad media. Son límites por la resolución del barrido. El grupo con puntajes de 80% a 90% tiene una sola tarjeta y el siguiente está vacío.

El ECE es la suma de las diferencias absolutas entre tasas observadas y probabilidades medias, ponderadas por la fracción de tarjetas de cada intervalo. Aplicamos la definición de [Guo et al.](https://proceedings.mlr.press/v70/guo17a.html) a la probabilidad de la clase positiva. El **ECE estimado es 0.002503** (0.250 puntos porcentuales). El rango compatible con estos conteos va de **0.00052250 a 0.00680037** (aproximadamente 0.052 a 0.680 puntos porcentuales). El [JSON de evidencia](p2_calibracion_oof_a_acotada.json) incluye tasas, poblaciones, medias estimadas y límites por intervalo.

Las frecuencias observadas están cerca de las probabilidades estimadas en los intervalos con más tarjetas de A. El diagnóstico es descriptivo y usa la misma validación con la que se eligió el modelo. Para obtener el ECE directo se necesitan los puntajes OOF individuales. El barrido archivado registra conteos, sin almacenar esos puntajes.

## Reproducción

Con las dependencias del repositorio instaladas se reproduce esta evidencia desde los archivos versionados.

```bash
python -m modelos.calibracion --desde-conteos
```

Para obtener el ECE directo con el warehouse original, configura `LAKE_DIR` para que apunte a la carpeta que contiene `warehouse.duckdb`. El comando lee solo A, reconstruye las predicciones OOF con el modelo y los folds originales, y verifica los conteos de todo el barrido y la PR-AUC OOF antes de emitir resultados.

```bash
python -m modelos.calibracion
```

Si ya tienes el OOF original, puedes pasar un CSV con `etiqueta,puntaje` y precisión completa.

```bash
python -m modelos.calibracion --oof /ruta/al/oof_de_A.csv
```

El resultado directo se escribe en `evidencia/p2_calibracion_oof_a.json` y `evidencia/p2_calibracion_oof_a.png`. El comando hace un diagnóstico de A y no evalúa B ni ajusta el modelo entregado o el umbral.
