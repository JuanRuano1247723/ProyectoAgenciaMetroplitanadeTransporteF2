# Diccionario de features · Proyecto 2 (1.3)

Tabla: `features.features_corte` (modelo `dbt_metro/models/features/features_corte.sql`). Una fila por unidad (tarjeta, `usuario_sk`) y fecha de corte, para los cortes A (2026-07-01), B (2026-07-31) y C (2026-08-30). La etiqueta de C va vacía.

Todas las features salen de **`silver.silver_evento_unificado`** y usan solo eventos en `[corte − 28 días, corte)`, es decir, antes de las 00:00 del corte. Ninguna ventana pasa de 28 días. "Evento" es un abordaje válido (lo rechazado está en `silver_cuarentena` y no entra).

| Feature | Qué mide | Ventana | Tabla de Silver |
|---|---|---|---|
| `viajes_28d` | Abordajes de la tarjeta | 28 días | `silver_evento_unificado` |
| `viajes_7d` | Abordajes de la tarjeta | 7 días | `silver_evento_unificado` |
| `viajes_14d` | Abordajes de la tarjeta | 14 días | `silver_evento_unificado` |
| `viajes_14d_previos` | Abordajes entre 28 y 14 días antes del corte | días 15 a 28 | `silver_evento_unificado` |
| `tendencia_14d` | `viajes_14d − viajes_14d_previos`: negativo si viaja menos que antes | 28 días | `silver_evento_unificado` |
| `dias_activos_28d` | Días distintos con al menos un abordaje | 28 días | `silver_evento_unificado` |
| `dias_desde_ultimo_viaje` | Días entre la fecha del último abordaje y la fecha de corte (1 = viajó ayer) | 28 días | `silver_evento_unificado` |
| `gasto_28d` | Suma de los montos en quetzales | 28 días | `silver_evento_unificado` |
| `tarifa_media_28d` | `gasto_28d / viajes_28d` | 28 días | `silver_evento_unificado` |
| `estaciones_distintas_28d` | Estaciones o paradas distintas donde abordó | 28 días | `silver_evento_unificado` |
| `zonas_distintas_28d` | Zonas distintas (sin contar las no mapeadas, −1) | 28 días | `silver_evento_unificado`, `silver_estacion` |
| `transbordos_28d` | Abordajes marcados como transbordo por el operador (Transmetro) | 28 días | `silver_evento_unificado` |
| `prop_fin_de_semana_28d` | Fracción de abordajes en sábado o domingo | 28 días | `silver_evento_unificado` |
| `prop_hora_pico_28d` | Fracción de abordajes entre las 6 y las 8, o entre las 17 y las 19 (horas locales; regla fija) | 28 días | `silver_evento_unificado` |
| `persona_operadores_28d` | Operadores distintos en que abordó la persona de la tarjeta (hipótesis de identidad del Proyecto 1) | 28 días | `silver_evento_unificado`, `silver_usuario` |

Columnas que no son features: `unidad_id` (seudónimo de la tarjeta), `fecha_corte`, `corte` (A, B o C), `operador_cod` (operador de la tarjeta, TM, TU, AM o MR) y `etiqueta` (1 si no abordó en los 30 días desde el corte; vacía en C).

Notas:
- `persona_operadores_28d` depende de la hipótesis de identidad (la misma parte numérica en Transmetro, Transurbano y MetroRiel es la misma persona). Para las tarjetas de Aerómetro siempre vale 1.
- La prueba de que ninguna feature mira al futuro está en `evidencia/p2_1_3_prueba_recorte.md` (`python -m flows.prueba_recorte`).
