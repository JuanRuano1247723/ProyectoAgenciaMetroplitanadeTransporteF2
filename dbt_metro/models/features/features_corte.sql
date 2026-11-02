{#
  features_corte  (Proyecto 2, 1.3)
  GRANO: una fila por unidad (tarjeta = usuario_sk) y fecha de corte, para los cortes A, B y C de poblacion_etiqueta.
  Las features salen SOLO de silver_evento_unificado, y solo de eventos con  [corte - 28 d, corte):
  ninguna ventana pasa de 28 días y ningún evento en o después del corte entra al cálculo.
  La etiqueta viene de poblacion_etiqueta (NULL en el corte C). Significado de cada columna: docs/DICCIONARIO_FEATURES_P2.md.

  Prueba de recorte: con --vars '{fecha_recorte: "2026-07-01", sufijo_tabla: "_recorte"}' el modelo descarta todo evento
  con ts_local >= fecha_recorte y escribe en features_corte_recorte (ver flows/prueba_recorte.py).
#}
{{ config(alias='features_corte' ~ var('sufijo_tabla', '')) }}
{% set ventana = var('ventana_features_dias') %}
with ev as (
    select usuario_sk, persona_id, operador_cod, ts_local, fecha, hora, estacion_id_original, zona_id,
           monto_gtq, es_transbordo_operador
    from {{ ref('silver_evento_unificado') }}
    {% if var('fecha_recorte', '') != '' %}
    where ts_local < cast('{{ var("fecha_recorte") }}' as timestamp)
    {% endif %}
),

base as (
    select unidad_id, corte, fecha_corte, operador_cod, persona_id, etiqueta
    from {{ ref('poblacion_etiqueta') }}
),

ventana as (
    select b.unidad_id, b.corte, e.*
    from base b
    join ev e on e.usuario_sk = b.unidad_id
             and e.ts_local >= b.fecha_corte - interval '{{ ventana }} days'
             and e.ts_local <  b.fecha_corte
),

por_unidad as (
    select
        v.unidad_id, v.corte,
        count(*)                                                                     as viajes_28d,
        count(*) filter (where v.ts_local >= c.fecha_corte - interval '7 days')      as viajes_7d,
        count(*) filter (where v.ts_local >= c.fecha_corte - interval '14 days')     as viajes_14d,
        count(*) filter (where v.ts_local <  c.fecha_corte - interval '14 days')     as viajes_14d_previos,
        count(distinct v.fecha)                                                      as dias_activos_28d,
        date_diff('day', cast(max(v.ts_local) as date), cast(c.fecha_corte as date)) as dias_desde_ultimo_viaje,
        coalesce(sum(v.monto_gtq), 0)                                                as gasto_28d,
        count(distinct v.estacion_id_original)                                       as estaciones_distintas_28d,
        count(distinct v.zona_id) filter (where v.zona_id <> -1)                     as zonas_distintas_28d,
        count(*) filter (where v.es_transbordo_operador)                             as transbordos_28d,
        avg(case when dayofweek(v.ts_local) in (0, 6) then 1.0 else 0.0 end)         as prop_fin_de_semana_28d,
        avg(case when v.hora in (6, 7, 8, 17, 18, 19) then 1.0 else 0.0 end)         as prop_hora_pico_28d
    from ventana v
    join base c on c.unidad_id = v.unidad_id and c.corte = v.corte
    group by v.unidad_id, v.corte, c.fecha_corte
),

-- la persona (hipótesis de identidad del Proyecto 1) ¿en cuántos operadores abordó en la ventana?
por_persona as (
    select b.persona_id, b.corte, count(distinct e.operador_cod) as persona_operadores_28d
    from (select distinct persona_id, corte, fecha_corte from base) b
    join ev e on e.persona_id = b.persona_id
             and e.ts_local >= b.fecha_corte - interval '{{ ventana }} days'
             and e.ts_local <  b.fecha_corte
    group by 1, 2
)

select
    b.unidad_id,
    b.fecha_corte,
    b.corte,
    b.operador_cod,
    u.viajes_28d,
    u.viajes_7d,
    u.viajes_14d,
    u.viajes_14d_previos,
    u.viajes_14d - u.viajes_14d_previos                              as tendencia_14d,
    u.dias_activos_28d,
    u.dias_desde_ultimo_viaje,
    u.gasto_28d,
    cast(u.gasto_28d / u.viajes_28d as double)                       as tarifa_media_28d,
    u.estaciones_distintas_28d,
    u.zonas_distintas_28d,
    u.transbordos_28d,
    u.prop_fin_de_semana_28d,
    u.prop_hora_pico_28d,
    p.persona_operadores_28d,
    b.etiqueta
from base b
join por_unidad u  on u.unidad_id = b.unidad_id and u.corte = b.corte
join por_persona p on p.persona_id = b.persona_id and p.corte = b.corte
