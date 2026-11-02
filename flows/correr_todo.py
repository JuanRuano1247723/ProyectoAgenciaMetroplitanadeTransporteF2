"""Proyecto 2, entregable 1.1: datos nuevos desde cero con un solo comando.

    python -m flows.correr_todo

Vacía el lake, el warehouse (y con él los snapshots/tablas incrementales de dbt) y Kafka, y corre el flujo completo:
batch, CDC, streaming, conciliación contra los conteos esperados y dbt (staging, Silver, Gold, features).
Escribe en salidas/:  conteos_p2.csv / conteos_p2.md (9 filas) y tiempos_p2.csv / tiempos_p2.md (una fila por etapa).
"""
from __future__ import annotations

import argparse
import csv
import shutil
import subprocess
import sys
import time
from pathlib import Path

from bronze.config import RAIZ, Config
from bronze.conciliacion import conciliar
from flows.dbt_runner import construir_silver

ESPERADOS = RAIZ / "docs" / "conteos_esperados_p2.csv"
SALIDAS = RAIZ / "salidas"


def _cli(*args: str) -> None:
    subprocess.run([sys.executable, "-m", "bronze.cli", *args], cwd=str(RAIZ), check=True)


def _docker(*args: str) -> None:
    subprocess.run(["docker", *args], cwd=str(RAIZ), check=True)


def _esperar_kafka(cfg: Config, intentos: int = 60) -> None:
    from confluent_kafka.admin import AdminClient
    admin = AdminClient({"bootstrap.servers": cfg.kafka_bootstrap})
    for _ in range(intentos):
        try:
            admin.list_topics(timeout=3)
            return
        except Exception:
            time.sleep(2)
    raise RuntimeError("Kafka no respondió; revisa `docker compose logs kafka`")


def _vaciar(cfg: Config, con_kafka: bool) -> None:
    """Entorno vacío: lake (Bronze, checkpoints, bitácora, vistas, warehouse) y el volumen de Kafka."""
    if cfg.lake_dir.exists():
        shutil.rmtree(cfg.lake_dir)
    if con_kafka:
        _docker("compose", "down", "-v")


def _etapas(cfg: Config, con_kafka: bool, pausa: float):
    yield "vaciar_entorno", lambda: _vaciar(cfg, con_kafka)
    yield "bronze_batch", lambda: _cli("batch")
    yield "bronze_cdc", lambda: _cli("cdc")
    if con_kafka:
        yield "kafka_arranque", lambda: (_docker("compose", "up", "-d"), _esperar_kafka(cfg))
        yield "kafka_topics", lambda: _cli("topics")
        yield "kafka_produce", lambda: _cli("produce", "ambos", "--pausa", str(pausa))
        yield "kafka_consume", lambda: _cli("consume", "ambos")
    yield "conciliacion", lambda: _cli("conciliar", "--csv", str(SALIDAS / "conteos_bronze.csv"))
    yield "silver_gold_dbt", lambda: construir_silver(cfg)


def tabla_conteos(cfg: Config) -> list[dict]:
    esperados = {r["archivo"]: int(r["filas_esperadas"]) for r in csv.DictReader(ESPERADOS.open(encoding="utf-8"))}
    filas = []
    for r in conciliar(cfg):
        esp = esperados[r["archivo"]]
        cargadas = r["filas_bronze"]
        malf = r["filas_malformadas"]
        dif = esp - cargadas
        if dif == 0:
            expl = "sin diferencia"
        elif dif == malf:
            expl = f"{malf:,} filas con formato inválido, guardadas en la tabla malformadas (no se pierden)"
        else:
            expl = "REVISAR: la diferencia no coincide con las malformadas"
        filas.append({"archivo": r["archivo"], "filas_esperadas": esp, "filas_cargadas": cargadas,
                      "diferencia": dif, "filas_malformadas": malf, "explicacion": expl})
    return filas


def _escribir(ruta: Path, filas: list[dict], titulo: str) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    cols = list(filas[0])
    with ruta.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(filas)
    md = [f"# {titulo}", "", "| " + " | ".join(cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    md += ["| " + " | ".join(f"{v:,}" if isinstance(v, int) else str(v) for v in r.values()) + " |" for r in filas]
    ruta.with_suffix(".md").write_text("\n".join(md) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sin-streaming", action="store_true", help="omite Kafka (Transmetro y Aerómetro no se cargan)")
    ap.add_argument("--pausa", type=float, default=0.0, help="pausa entre ráfagas al publicar (0 = lo más rápido)")
    a = ap.parse_args()
    cfg = Config.desde_entorno()
    tiempos = []
    t_total = time.perf_counter()
    for nombre, fn in _etapas(cfg, not a.sin_streaming, a.pausa):
        print(f"\n=== {nombre} ===", flush=True)
        t0 = time.perf_counter()
        fn()
        tiempos.append({"etapa": nombre, "segundos": round(time.perf_counter() - t0, 1)})
    t0 = time.perf_counter()
    conteos = tabla_conteos(cfg)
    _escribir(SALIDAS / "conteos_p2.csv", conteos, "Conteos: archivo crudo vs Bronze")
    tiempos.append({"etapa": "tabla_de_conteos", "segundos": round(time.perf_counter() - t0, 1)})
    tiempos.append({"etapa": "TOTAL", "segundos": round(time.perf_counter() - t_total, 1)})
    _escribir(SALIDAS / "tiempos_p2.csv", tiempos, "Tiempo por etapa")
    print("\n" + (SALIDAS / "conteos_p2.md").read_text(encoding="utf-8"))
    print((SALIDAS / "tiempos_p2.md").read_text(encoding="utf-8"))
    return 0 if all(r["explicacion"] != "REVISAR: la diferencia no coincide con las malformadas" for r in conteos) else 1


if __name__ == "__main__":
    sys.exit(main())
