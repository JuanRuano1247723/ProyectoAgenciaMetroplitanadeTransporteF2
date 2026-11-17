# Verificación de la entrega para la defensa

Registro documental del 17 de noviembre de 2026, preparado por José García (`Yipieight`). Los resultados corresponden a las ejecuciones conservadas durante la preparación de la defensa. Los archivos `integridad.json` y `datos_90_procedencia.json` permiten contrastar los artefactos y la entrada utilizada.

## Entrada de 90 días

La carpeta de 90 días se reconstruyó desde el conjunto extendido del ingeniero, conservando los bytes de los registros del periodo de generación del 1 de junio al 29 de agosto de 2026. El ZIP original de 90 días no estaba disponible en la carpeta de trabajo. Los nueve conteos resultantes coinciden con `docs/conteos_esperados_p2.csv` y los hashes están en [datos_90_procedencia.json](datos_90_procedencia.json).

Transurbano contiene 1,645 registros conservados con un error de fecha desplazada 400 días. Se usó la fecha de generación para seleccionar su pertenencia al periodo y se conservó la fecha errónea en el archivo de entrada, de modo que Silver aplique la regla original de rechazo.

## Comprobaciones de predicciones

| Comprobación | Resultado |
|---|---|
| Corte C con 90 días frente al CSV entregado | Archivos idénticos, 76,127 filas y 9,768 contactos |
| Corte C con 120 días frente al CSV entregado | Archivos idénticos |
| Corte B con 60 días frente a 90 días | Archivos idénticos, 76,096 filas y 9,344 contactos |

SHA-256 de C, `43c73f333c2a557b8306278e514d82ab2fc1776f5b796cbdaea10148f148561d`.

SHA-256 de B, `674a04a04beeed5d478839be6bbfa02579426d58c9fbfc5c31424840dd84426d`.

La comparación de B comprueba invariancia de la inferencia del modelo guardado. La única evaluación estadística de B, incluida la elección previa del umbral en A, sigue siendo la corrida del 6 de noviembre documentada en [BITACORA_P2.md](../../docs/BITACORA_P2.md).

## Demostración y versión evaluada

La entrega documental completa se congela con `entrega-final` y `entrega-final-v2` sobre el mismo commit. El commit anterior queda accesible como `entrega-final-anterior-ee29390`. La demostración de pantalla debe grabarse después de esta actualización, en una toma continua con este orden.

1. Mostrar `git log -1` y comprobar que HEAD coincide con el commit de `entrega-final`.
2. Ejecutar `python predecir.py --datos <carpeta_de_90_dias> --fecha-corte 2026-08-30`.
3. Mostrar los hashes de la salida y del CSV versionado, más la comparación byte a byte.
4. Abrir `docs/FICHA_MODELO.md` y señalar las fugas revisadas y las limitaciones.

El ensayo de ingesta completa construyó el warehouse mediante Kafka y dbt. La captura de inferencia puede reutilizarlo cuando la comprobación de huellas confirma que corresponde a esos mismos nueve archivos. La consola informa esa reutilización y debe explicarse en la voz del video.

La ficha del commit anterior conserva una nota de invariancia pendiente. Las verificaciones adicionales de esta preparación quedan registradas aquí. También existe una diferencia documental entre su frase sobre calibración pendiente y el mensaje del commit `ee29390`; el video debe evitar convertir esa frase antigua en una conclusión actual sin su evidencia específica.
