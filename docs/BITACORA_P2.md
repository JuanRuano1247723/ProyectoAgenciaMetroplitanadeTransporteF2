# Bitácora del Proyecto 2

Registro de las decisiones y evaluaciones que no se pueden repetir. El corte B solo se evalúa una vez.

## Integrantes y cuentas de Git

Esta revisión del 17 de noviembre de 2026 completa los responsables a partir de los commits de implementación y de la evidencia guardada. José García confirmó la identidad de su cuenta Yipieight. El responsable de una decisión puede ser distinto de quien presenta ese tema en el video.

| Integrante | Cuenta que firma el trabajo en Git |
|---|---|
| José García | `Yipieight` |
| Daniel Xiquin | `danielxiquin` |
| Daniel Ruano | `JuanRuano1247723` |

## Decisiones, responsables y cifras de respaldo

| ID | Qué se decidió y por qué | Responsable | Cifra que respalda la decisión | Commit y evidencia |
|---|---|---|---|---|
| P2-01 | Usar tarjeta y operador como unidad, con una fila por corte. Incluir al menos dos abordajes válidos en 28 días y excluir las bajas vigentes. Etiquetar como abandono la ausencia de abordajes válidos en los 30 días siguientes. | Daniel Xiquin | A, 11,100 / 77,062 = 0.1440. B, 10,249 / 76,096 = 0.1347. El costo de usar tarjeta se observa en 2,404 positivos de A y 2,400 de B que siguieron usando otra tarjeta, aproximadamente 21.7% y 23.4%. | [8a1130b](https://github.com/JuanRuano1247723/ProyectoAgenciaMetroplitanadeTransporteF2/commit/8a1130bb8eccd78f6cec5f3ba7ac50e0c52fde54), implementación de población y etiqueta. [Definición y resultados](PROYECTO2_1_2.md). |
| P2-02 | Construir las variables desde Silver con historia anterior al corte, limitada a 28 días. Auditar la fuga comparando el resultado con y sin datos futuros. | José García | Quince variables, 77,062 filas de A y cero diferencias en el recorte. El control negativo con fuga deliberada difiere en 68,205 filas. Ninguna variable falló en la primera prueba. | [e5bed86](https://github.com/JuanRuano1247723/ProyectoAgenciaMetroplitanadeTransporteF2/commit/e5bed865cbee400980f204d6b4657d42849c11ac). [Auditoría de fuga](../evidencia/p2_1_3_prueba_recorte.md). |
| P2-03 | Usar PR-AUC como métrica principal de ordenamiento y ROC-AUC como complemento. Comparar baselines y regresión logística con los mismos cinco folds estratificados de A, semilla 42. | José García | Tasa positiva de A, 0.1440. Baseline por frecuencia, PR-AUC 0.2731. Logística L2, 0.4158. Elastic Net, 0.4159. B queda fuera de la selección. | [f48bfa8](https://github.com/JuanRuano1247723/ProyectoAgenciaMetroplitanadeTransporteF2/commit/f48bfa85eeddd2dc4e6bdcbbf3513313cc9bdd19) y documentación de [1.3 y 1.4](PROYECTO2_1_3_1_4.md). |
| P2-04 | Elegir HistGradientBoosting regularizado para controlar la complejidad y sostener el resultado de validación. Configuración de profundidad 3, aprendizaje 0.05, 200 iteraciones, mínimo 100 filas por hoja y L2 = 1. | Daniel Xiquin | PR-AUC media en A, 0.4377 ± 0.0072; ROC-AUC, 0.8199. Brecha de PR-AUC, 0.0092. Random Forest flexible pasa de 0.9675 a 0.3565; Random Forest regularizado valida en 0.4327. La diferencia pequeña entre los dos regularizados se reporta con su incertidumbre. | [a034aec](https://github.com/JuanRuano1247723/ProyectoAgenciaMetroplitanadeTransporteF2/commit/a034aec5e653c378bf03a2b891b6f0049d4da2cc), decisión documentada en [c211dd2](https://github.com/JuanRuano1247723/ProyectoAgenciaMetroplitanadeTransporteF2/commit/c211dd2dd0adb08125621b17ca9445b7cf49468d). [Tabla 2.1](PROYECTO2_2_1_2_3.md). |
| P2-05 | Explicar el modelo con importancia por permutación calculada sobre validación. Interpretar las asociaciones con el límite de que la importancia predictiva no acredita causalidad. | Daniel Xiquin | Permutar días desde el último viaje reduce PR-AUC en 0.1837; permutar el número de operadores, en 0.0364. | [a034aec](https://github.com/JuanRuano1247723/ProyectoAgenciaMetroplitanadeTransporteF2/commit/a034aec5e653c378bf03a2b891b6f0049d4da2cc). [Importancias](../evidencia/p2_2_1_importancias.md). |
| P2-06 | Derivar la ganancia del escenario y elegir el umbral con las predicciones fuera de muestra de A. Congelarlo antes de evaluar B. | Daniel Ruano | Contacto Q5, retención supuesta 25% y valor Q60. G = 10·TP − 5·FP. Umbral 0.32. En A, TP 4,476, FP 5,430 y ganancia Q17,610. | [091f1ed](https://github.com/JuanRuano1247723/ProyectoAgenciaMetroplitanadeTransporteF2/commit/091f1edbc24227d17ca3939404f698a1da0b57cc). [Derivación](PROYECTO2_2_2.md) y [umbral conservado](../evidencia/p2_2_2_umbral.json). |
| P2-07 | Realizar una única evaluación en B y conservar el modelo y el umbral después de verla. Documentar la caída respecto de A y los commits reales de la ejecución. | Daniel Ruano | B, 76,096 unidades, PR-AUC 0.3916, TP 3,896, FP 5,448 y ganancia Q11,720. Contactar a todos produce −Q226,745. Corrida del 6 de noviembre a las 17:47. | Base de la corrida [c211dd2](https://github.com/JuanRuano1247723/ProyectoAgenciaMetroplitanadeTransporteF2/commit/c211dd2dd0adb08125621b17ca9445b7cf49468d); implementación y registro en [091f1ed](https://github.com/JuanRuano1247723/ProyectoAgenciaMetroplitanadeTransporteF2/commit/091f1edbc24227d17ca3939404f698a1da0b57cc). [JSON original](../evidencia/p2_2_2_test_b.json). |
| P2-08 | Formar tres segmentos con KMeans sobre las variables estandarizadas de A. Usar la etiqueta después para describir sus tasas. Proponer acciones por actividad y priorizar la campaña con el modelo. | Daniel Xiquin | k = 3, silueta 0.270, frente a 0.158 con k = 4. Ocasionales, 57,857 y 18.23% de abandono, contacto priorizado. Regulares, 17,175 y 3.00%, seguimiento de bajo costo. Intensivos, 2,030 y 1.87%, sin incentivo general. PCA, 54.7% de varianza en dos componentes. | [6d62c13](https://github.com/JuanRuano1247723/ProyectoAgenciaMetroplitanadeTransporteF2/commit/6d62c13907abbf43f02afa665c0fbba0cfcca03e) y [c211dd2](https://github.com/JuanRuano1247723/ProyectoAgenciaMetroplitanadeTransporteF2/commit/c211dd2dd0adb08125621b17ca9445b7cf49468d). [Segmentos y acciones](PROYECTO2_2_1_2_3.md). |
| P2-09 | Serializar el pipeline y ejecutar inferencia con dependencias fijadas, cargando el modelo y el umbral guardados. Generar el CSV de C sin volver a seleccionar el modelo. | José García | Modelo 1.0.0, umbral 0.32 y semilla 42. Corte C del 30 de agosto, 76,127 filas y 9,768 contactos. | [c7ba2ec](https://github.com/JuanRuano1247723/ProyectoAgenciaMetroplitanadeTransporteF2/commit/c7ba2ecd9381d19d1a75d3ecb2d74abb2173ec2e), [6fc5d63](https://github.com/JuanRuano1247723/ProyectoAgenciaMetroplitanadeTransporteF2/commit/6fc5d63245df190a099d3a641db903e8f6ffa9b8) y [eb79640](https://github.com/JuanRuano1247723/ProyectoAgenciaMetroplitanadeTransporteF2/commit/eb79640832ef130f801ce9040947629d318aa1a5). [Ficha](FICHA_MODELO.md). |
| P2-10 | Verificar la invariancia de predicciones al añadir datos posteriores al corte y registrar la procedencia de los archivos usados en la defensa. | José García | La comprobación original de B dio CSV idénticos. En la preparación del 17 de noviembre, las salidas C de 90 y 120 días coinciden con la entrega; las salidas B de 60 y 90 días también coinciden. | [c162dee](https://github.com/JuanRuano1247723/ProyectoAgenciaMetroplitanadeTransporteF2/commit/c162dee755e81876ab78d62cd1c1f7ed5de4f593), [prueba original](../evidencia/p2_2_4_prueba_invariancia.md) y [registro de la defensa](../evidencia/defensa_2026_11_17/README.md). |

Las acciones por segmento son propuestas del ejercicio. El responsable de la implementación y documentación de 2.3 es Daniel Xiquin, aunque Daniel Ruano presenta las acciones en el video.

## Correspondencia con la explicación cruzada

| Persona que explica | Decisión de otra persona | Responsable registrado |
|---|---|---|
| José García | Elección y regularización del modelo, P2-04 | Daniel Xiquin |
| Daniel Xiquin | Ganancia y elección del umbral, P2-06 | Daniel Ruano |
| Daniel Ruano | Filtro temporal y prueba de recorte, P2-02 | José García |

## Test único en el corte B (2.2)

| Campo | Valor |
|---|---|
| Fecha y hora | 2026-11-06 17:47 (hora local) |
| Responsable | Daniel Ruano (`JuanRuano1247723`) |
| Rama y commit base | `fase-2`, `c211dd2` (el código de `modelos/umbral.py` y la evidencia de 2.2 aún no estaban versionados) |
| Commit que contiene el código y la evidencia | `091f1ed` (rama `fase-2`, subido por Ruano; la evidencia quedó movida a `evidencia/` en un commit posterior) |
| Modelo | HistGradientBoosting regularizado (lr 0.05, profundidad 3, 200 iteraciones), entrenado con todo el corte A. Elegido en 2.1 antes de abrir B |
| Umbral | 0.32, elegido con las predicciones de validación cruzada del corte A y guardado en `evidencia/p2_2_2_umbral.json` antes de leer B |
| Comando | `python -m modelos.umbral evaluar-b` (se niega a repetirse si existe `evidencia/p2_2_2_test_b.json`) |
| Resultado | PR-AUC 0.3916; precisión 0.417; recall 0.380; ganancia Q11,720 (TP 3,896, FP 5,448) |
| Contra validación | PR-AUC 0.4370 en las predicciones OOF concatenadas de A y ganancia Q17,610. La tabla 2.1 reporta la media de PR-AUC por fold, 0.4377 ± 0.0072. B queda por debajo de ambas referencias; explicación en `docs/PROYECTO2_2_2.md` |
| Después de ver B | No se cambió ni el modelo, ni el umbral, ni la configuración |

Nota técnica: el campo `arbol_con_cambios_sin_commit` del JSON dice `false` porque en esa corrida el chequeo ignoraba archivos nuevos sin versionar (lo corregí después en el código; no afecta ningún resultado). En realidad `modelos/umbral.py` estaba sin versionar.

## Congelación para la defensa

La versión anterior se conserva como `entrega-final-anterior-ee29390`, sobre el commit `ee29390f02e5bac158c3d1d25b02503f72fbca16`. Esta revisión documental se identifica como `entrega-final-v2` y como el tag requerido `entrega-final`, ambos sobre el commit que contiene esta bitácora completa. La captura de MLOps de entrega debe mostrar ese commit mediante `git log -1` y su coincidencia con `entrega-final`.

El CSV C entregado conserva SHA-256 `43c73f333c2a557b8306278e514d82ab2fc1776f5b796cbdaea10148f148561d`. Los identificadores del código de inferencia y del modelo se incluyen en el [registro de integridad](../evidencia/defensa_2026_11_17/integridad.json). La prueba estadística de B permanece registrada en la corrida original del 6 de noviembre.
