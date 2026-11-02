-- Proyecto 2, 1.2: una sola fila por (unidad_id, corte). Devuelve las repetidas; la prueba pasa si no hay filas.
select unidad_id, corte, count(*) as n
from {{ ref('poblacion_etiqueta') }}
group by 1, 2
having count(*) > 1
