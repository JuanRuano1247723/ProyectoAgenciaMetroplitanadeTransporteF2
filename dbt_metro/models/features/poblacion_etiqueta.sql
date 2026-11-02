{#
  poblacion_etiqueta  (Proyecto 2, 1.2)
  GRANO: una fila por unidad y fecha de corte. UNIDAD = tarjeta = usuario_sk, es decir, cada (operador, llave) de Silver.
  Solo lee Silver (silver_evento_unificado, silver_padron_scd2); expone seudónimos, nunca llaves crudas.

  Fecha de corte t = 00:00 hora local. Mirando atrás: [t - 28 d, t). Mirando adelante: [t, t + 30 d).
  Población: unidades con >= 2 abordajes válidos en los 28 días anteriores y sin un DELETE del CDC vigente en t.
  Etiqueta:  1 si la unidad no tiene ningún abordaje válido en los 30 días que empiezan en t, 0 si tiene al menos uno.
             NULL cuando esa ventana sale de los datos (corte C): no se puede calcular.
  "Abordaje válido" = una fila de silver_evento_unificado (aceptada por las reglas de Silver; lo de cuarentena no entra).
  viaja_con_otra_tarjeta = la persona_id de la unidad (hipótesis de identidad del Proyecto 1) sí abordó en el horizonte
  con OTRA tarjeta: es el costo de haber elegido la tarjeta como unidad.
#}
{% set dias_atras = var('ventana_features_dias') %}
{% set dias_adelante = var('horizonte_etiqueta_dias') %}
with ev as (
    select usuario_sk, persona_id, operador_cod, ts_local from {{ ref('silver_evento_unificado') }}
),

limites as (
    select max(cast(ts_local as date)) + 1 as fin_datos from ev   -- primer día sin datos
),

cortes as (
    {% for nombre, fecha in var('cortes_p2').items() %}
    select '{{ nombre }}' as corte, cast('{{ fecha }}' as timestamp) as fecha_corte
    {% if not loop.last %}union all{% endif %}
    {% endfor %}
),

atras as (
    select e.usuario_sk, c.corte, count(*) as n_abordajes_28d, min(e.operador_cod) as operador_cod
    from ev e join cortes c
      on e.ts_local >= c.fecha_corte - interval '{{ dias_atras }} days' and e.ts_local < c.fecha_corte
    group by 1, 2
),

adelante as (
    select e.usuario_sk, c.corte, count(*) as n_abordajes_30d
    from ev e join cortes c
      on e.ts_local >= c.fecha_corte and e.ts_local < c.fecha_corte + interval '{{ dias_adelante }} days'
    group by 1, 2
),

adelante_persona as (
    select e.persona_id, c.corte, count(*) as n_abordajes_30d_persona
    from ev e join cortes c
      on e.ts_local >= c.fecha_corte and e.ts_local < c.fecha_corte + interval '{{ dias_adelante }} days'
    group by 1, 2
),

persona as (
    select usuario_sk, any_value(persona_id) as persona_id from ev group by 1
),

-- DELETE del CDC vigente en el corte: la versión del padrón válida en t está inactiva
borrados as (
    select {{ pseudonimo("'transmetro:' || p.tarjeta") }} as usuario_sk, c.corte
    from {{ ref('silver_padron_scd2') }} p
    join cortes c on p.valido_desde_ts < c.fecha_corte
                 and (p.valido_hasta_ts is null or p.valido_hasta_ts >= c.fecha_corte)
    where not p.activa
)

select
    a.usuario_sk                                              as unidad_id,
    a.corte,
    c.fecha_corte,
    a.operador_cod,
    pe.persona_id,
    a.n_abordajes_28d,
    coalesce(f.n_abordajes_30d, 0)                            as n_abordajes_30d,
    case when c.fecha_corte + interval '{{ dias_adelante }} days' <= cast(l.fin_datos as timestamp)
         then cast(coalesce(f.n_abordajes_30d, 0) = 0 as integer) end   as etiqueta,
    case when c.fecha_corte + interval '{{ dias_adelante }} days' <= cast(l.fin_datos as timestamp)
         then coalesce(fp.n_abordajes_30d_persona, 0) - coalesce(f.n_abordajes_30d, 0) > 0 end as viaja_con_otra_tarjeta
from atras a
join cortes c      on c.corte = a.corte
cross join limites l
join persona pe    on pe.usuario_sk = a.usuario_sk
left join adelante f           on f.usuario_sk = a.usuario_sk and f.corte = a.corte
left join adelante_persona fp  on fp.persona_id = pe.persona_id and fp.corte = a.corte
where a.n_abordajes_28d >= {{ var('min_abordajes_poblacion', 2) }}
  and not exists (select 1 from borrados b where b.usuario_sk = a.usuario_sk and b.corte = a.corte)
