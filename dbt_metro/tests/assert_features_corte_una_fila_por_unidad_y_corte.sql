-- Proyecto 2, 1.3: una fila por (unidad_id, corte), la misma que tiene poblacion_etiqueta. Devuelve las anomalías.
with f as (select unidad_id, corte, count(*) as n from {{ ref('features_corte') }} group by 1, 2),
     p as (select unidad_id, corte from {{ ref('poblacion_etiqueta') }})
select coalesce(f.unidad_id, p.unidad_id) as unidad_id, coalesce(f.corte, p.corte) as corte
from f full join p on f.unidad_id = p.unidad_id and f.corte = p.corte
where f.n is null or p.unidad_id is null or f.n > 1
