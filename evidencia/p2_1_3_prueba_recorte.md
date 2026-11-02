# Prueba de recorte (1.3)

Generado: 2026-11-01T19:09:11

Corte A (2026-07-01), features con datos completos vs datos recortados al 30 de junio (ts_local < 2026-07-01).

- Filas comparadas (unidades del corte A): 77,062 (completo: 77,062; recortado: 77,062)
- Filas que solo existen en una de las dos tablas: 0
- Diferencias (celdas distintas en las 15 features): 0
- **Número de diferencias: 0**  (las dos tablas son idénticas)
- Features que fallaron: ninguna

| feature | filas distintas |
|---|---:|
| viajes_28d | 0 |
| viajes_7d | 0 |
| viajes_14d | 0 |
| viajes_14d_previos | 0 |
| tendencia_14d | 0 |
| dias_activos_28d | 0 |
| dias_desde_ultimo_viaje | 0 |
| gasto_28d | 0 |
| tarifa_media_28d | 0 |
| estaciones_distintas_28d | 0 |
| zonas_distintas_28d | 0 |
| transbordos_28d | 0 |
| prop_fin_de_semana_28d | 0 |
| prop_hora_pico_28d | 0 |
| persona_operadores_28d | 0 |

## Control negativo
Una feature deliberadamente con fuga (total de viajes de la unidad con todos los datos, sin cortar en el corte) difiere en 68,205 de las 77,062 filas del corte A, así que esta misma prueba la habría detectado.

## Cómo repetirla
```bash
python -m flows.prueba_recorte
```
