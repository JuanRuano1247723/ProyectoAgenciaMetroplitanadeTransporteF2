.print '=== 1.2 TABLA DE POBLACION (cuenta completa) ==='
select corte, fecha_corte::date as fecha_corte,
       count(*) as poblacion,
       sum(etiqueta) as positivos,
       cast(sum(etiqueta) as varchar) || ' / ' || cast(count(*) as varchar) || ' = ' || cast(round(sum(etiqueta)::double / count(*), 4) as varchar) as cuenta_tasa_positiva
from features.poblacion_etiqueta
where corte in ('A', 'B')
group by 1, 2 order by 1;

.print '=== 1.2 POBLACION POR OPERADOR (la unidad es la tarjeta de cada operador) ==='
select corte, operador_cod, count(*) as poblacion, sum(etiqueta) as positivos,
       round(sum(etiqueta)::double / count(*), 4) as tasa
from features.poblacion_etiqueta
where corte in ('A', 'B')
group by 1, 2 order by 1, 2;

.print '=== 1.2 COSTO DE LA UNIDAD: positivos cuya persona siguio viajando con OTRA tarjeta ==='
select corte,
       count(*) filter (where etiqueta = 1) as positivos,
       count(*) filter (where etiqueta = 1 and viaja_con_otra_tarjeta) as positivos_que_siguen_con_otra_tarjeta,
       cast(count(*) filter (where etiqueta = 1 and viaja_con_otra_tarjeta) as varchar) || ' de ' || cast(count(*) filter (where etiqueta = 1) as varchar)
         || ' = ' || cast(round(count(*) filter (where etiqueta = 1 and viaja_con_otra_tarjeta)::double / count(*) filter (where etiqueta = 1), 4) as varchar) as costo
from features.poblacion_etiqueta
where corte in ('A', 'B')
group by 1 order by 1;

.print '=== 1.2 COSTO: positivos de Aerometro (su hash opaco no se puede enlazar con otro operador) ==='
select corte,
       count(*) filter (where etiqueta = 1 and operador_cod = 'AM') as positivos_aerometro,
       count(*) filter (where etiqueta = 1) as positivos,
       round(count(*) filter (where etiqueta = 1 and operador_cod = 'AM')::double / count(*) filter (where etiqueta = 1), 4) as proporcion
from features.poblacion_etiqueta
where corte in ('A', 'B')
group by 1 order by 1;

.print '=== Corte C (etiqueta oculta): filas y etiquetas calculables ==='
select corte, count(*) as poblacion, count(etiqueta) as etiquetas_calculadas
from features.poblacion_etiqueta
where corte = 'C'
group by 1;
