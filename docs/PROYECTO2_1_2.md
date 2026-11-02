# Proyecto 2 · 1.2 Etiqueta, población y unidad

Modelo: `dbt_metro/models/features/poblacion_etiqueta.sql`. Consultas: `sql/entregables_p2_1_2.sql`. Resultados: `evidencia/p2_1_2_resultados.txt`.

## Definición de la etiqueta

La etiqueta es 1 si la unidad no tiene ningún abordaje válido, en ningún operador, en los 30 días que empiezan en la fecha de corte (00:00 hora local), y 0 si tiene al menos uno.

"Abordaje válido" es una fila de `silver_evento_unificado` (lo que Silver rechazó está en `silver_cuarentena` y no cuenta). Dejar de viajar no es lo mismo que la baja del CDC: un DELETE del padrón no se usa como etiqueta.

## Unidad elegida: la tarjeta

La unidad es la tarjeta, es decir, cada (operador, llave) de Silver (`usuario_sk`). Justificación:

- En el Proyecto 1 `usuario_sk` es la capa de certeza: cada (operador, llave) existe y nunca se pierde. `persona_id` es una hipótesis (misma parte numérica en Transmetro, Transurbano y MetroRiel) que `diagnostico_identidad.sql` no logró demostrar.
- Aerómetro usa un hash opaco que no se puede enlazar con ningún otro operador; con la tarjeta como unidad entra completo, sin inventar enlaces.
- Con la persona, un error de la hipótesis mezclaría usuarios distintos dentro de una fila y movería la etiqueta sin que se note.
- El costo de esta elección se puede medir con los datos: un usuario que cambia de operador sin dejar la red aparece como abandono (ver abajo).
- Los DELETE del CDC solo existen para tarjetas de Transmetro, que es exactamente la unidad.

## Población

Entran a un corte las unidades con al menos 2 abordajes válidos en los 28 días anteriores y sin un DELETE del CDC vigente en el corte. El 28 es la ventana de features; el corte C se construye con el mismo código, pero no tiene etiqueta (sus 30 días no están en los datos).

| Corte | Fecha | Población | Positivos | Tasa positiva |
|---|---|---:|---:|---|
| A | 2026-07-01 | 77,062 | 11,100 | 11,100 / 77,062 = 0.1440 |
| B | 2026-07-31 | 76,096 | 10,249 | 10,249 / 76,096 = 0.1347 |

Verificación independiente (consulta aparte, sin el modelo): sin excluir los DELETE la población A sería 77,385 y los positivos 11,423. Las 323 unidades excluidas son tarjetas dadas de baja antes del corte y todas son positivas.

## Costo de la unidad

Positivos cuya persona (`persona_id`, hipótesis del Proyecto 1) siguió viajando en el horizonte con otra tarjeta, es decir, abandonos aparentes que no lo son:

| Corte | Positivos | Siguen con otra tarjeta | Proporción |
|---|---:|---:|---|
| A | 11,100 | 2,404 | 2,404 de 11,100 = 0.2166 |
| B | 10,249 | 2,400 | 2,400 de 10,249 = 0.2342 |

Cómo se contó: para cada unidad positiva se cuentan los abordajes de su `persona_id` en los 30 días del horizonte y se restan los de la propia tarjeta; si queda algo, viajó con otra tarjeta.

Límite: este número depende de la hipótesis de identidad, y solo cubre Transmetro, Transurbano y MetroRiel. Las tarjetas de Aerómetro (1,460 positivas en A, 0.1315 de los positivos; 1,360 en B, 0.1327) no se pueden enlazar, así que su costo real es desconocido y el número es un mínimo.
