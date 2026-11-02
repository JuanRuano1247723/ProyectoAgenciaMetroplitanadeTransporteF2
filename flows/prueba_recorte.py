"""Proyecto 2, 1.3: auditoría de fuga por recorte.

Calcula las features del corte A dos veces: con los datos completos y con los datos recortados al 30 de junio
(todo evento con ts_local >= 2026-07-01 00:00 se descarta). Si alguna feature usa datos posteriores al corte,
las dos tablas difieren. Escribe evidencia/p2_1_3_prueba_recorte.md.

    python -m flows.prueba_recorte
"""
from __future__ import annotations

import argparse
from datetime import datetime

import duckdb

from bronze.config import RAIZ, Config
from flows.dbt_runner import dbt

CORTE_A = "2026-07-01"
NO_FEATURES = {"unidad_id", "fecha_corte", "corte", "operador_cod", "etiqueta"}   # la etiqueta mira al futuro por diseño


def correr(cfg: Config) -> tuple[list[str], int, int, dict[str, int], dict]:
    dbt(cfg, "run", "-s", "features_corte")
    dbt(cfg, "run", "-s", "features_corte", variables={"fecha_recorte": CORTE_A, "sufijo_tabla": "_recorte"})
    con = duckdb.connect(str(cfg.lake_dir / "warehouse.duckdb"), read_only=True)
    cols = [r[0] for r in con.execute("describe features.features_corte").fetchall() if r[0] not in NO_FEATURES]
    n_completo = con.execute("select count(*) from features.features_corte where corte = 'A'").fetchone()[0]
    n_recorte = con.execute("select count(*) from features.features_corte_recorte where corte = 'A'").fetchone()[0]
    union_ids = con.execute(
        "select count(*) from (select unidad_id from features.features_corte where corte='A' "
        "union select unidad_id from features.features_corte_recorte where corte='A')").fetchone()[0]
    dif_feature = {}
    for c in cols:
        dif_feature[c] = con.execute(
            f"select count(*) from features.features_corte f full join features.features_corte_recorte r "
            f"on f.unidad_id = r.unidad_id and r.corte = 'A' where f.corte = 'A' "
            f"and (r.unidad_id is null or f.{c} is distinct from r.{c})").fetchone()[0]
    # filas que aparecen solo en una de las dos tablas
    solo_una = con.execute(
        "select count(*) from features.features_corte f full join features.features_corte_recorte r "
        "on f.unidad_id = r.unidad_id and f.corte = r.corte "
        "where coalesce(f.corte, r.corte) = 'A' and (f.unidad_id is null or r.unidad_id is null)").fetchone()[0]
    # control negativo: una feature que SÍ mira al futuro debe ser detectada por la misma prueba
    control = con.execute(f"""
        with completo as (select usuario_sk, count(*) n from silver.silver_evento_unificado group by 1),
             recorte  as (select usuario_sk, count(*) n from silver.silver_evento_unificado
                          where ts_local < timestamp '{CORTE_A}' group by 1)
        select count(*) from features.features_corte f
        join completo c on c.usuario_sk = f.unidad_id
        left join recorte r on r.usuario_sk = f.unidad_id
        where f.corte = 'A' and c.n is distinct from r.n""").fetchone()[0]
    con.close()
    return cols, n_completo, n_recorte, dif_feature, {"solo_una": solo_una, "union": union_ids, "control": control}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--salida", default=str(RAIZ / "evidencia" / "p2_1_3_prueba_recorte.md"))
    a = ap.parse_args()
    cfg = Config.desde_entorno()
    cols, n_c, n_r, dif, extra = correr(cfg)
    total_dif = sum(dif.values()) + extra["solo_una"]
    fallaron = [c for c, n in dif.items() if n > 0]
    md = ["# Prueba de recorte (1.3)", "",
          f"Generado: {datetime.now().isoformat(timespec='seconds')}", "",
          f"Corte A ({CORTE_A}), features con datos completos vs datos recortados al 30 de junio (ts_local < {CORTE_A}).", "",
          f"- Filas comparadas (unidades del corte A): {extra['union']:,} (completo: {n_c:,}; recortado: {n_r:,})",
          f"- Filas que solo existen en una de las dos tablas: {extra['solo_una']:,}",
          f"- Diferencias (celdas distintas en las {len(cols)} features): {sum(dif.values()):,}",
          f"- **Número de diferencias: {total_dif}**" + ("  (las dos tablas son idénticas)" if total_dif == 0 else ""),
          f"- Features que fallaron: {', '.join(fallaron) if fallaron else 'ninguna'}", "",
          "| feature | filas distintas |", "|---|---:|"]
    md += [f"| {c} | {n:,} |" for c, n in dif.items()]
    md += ["", "## Control negativo",
           f"Una feature deliberadamente con fuga (total de viajes de la unidad con todos los datos, sin cortar en el corte) "
           f"difiere en {extra['control']:,} de las {n_c:,} filas del corte A, así que esta misma prueba la habría detectado.",
           "", "## Cómo repetirla", "```bash", "python -m flows.prueba_recorte", "```"]
    ruta = __import__("pathlib").Path(a.salida)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))
    return 0 if total_dif == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
