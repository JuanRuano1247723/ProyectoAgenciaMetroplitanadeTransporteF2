"""Construye un warehouse de DuckDB con datos SINTÉTICOS para el CI (GitHub Actions).

Corre todo el pipeline sin Kafka real ni datos reales: genera los 9 archivos de prueba, ingiere Bronze (batch, CDC y
streaming con el doble en memoria de Kafka), construye Silver, Gold y features con dbt (con sus pruebas) y copia el
resultado a --out. Los pasos siguientes del CI (verificar_linaje, exportar_tableau, consultas) leen ese archivo.

Uso:  python -m tests.build_ci_warehouse --out .ci/warehouse.duckdb
Nunca usa datos reales ni un secreto real: si falta PSEUDONIMO_SECRETO usa uno de prueba, solo válido para este CI.
"""
from __future__ import annotations

import argparse
import os
import shutil
import tempfile
from pathlib import Path

os.environ.setdefault("PSEUDONIMO_SECRETO", "secreto-de-ci-no-productivo")

from bronze.common import nuevo_run_id
from bronze.config import Config
from bronze.fuentes import BATCH, CDC, FUENTES
from bronze.ingesta_archivos import ingerir_archivo
from bronze.streaming import ConsumidorBronze, publicar_archivo
from flows.dbt_runner import construir_silver
from tests.datos_sinteticos import generar
from tests.fake_kafka import BrokerFake, ConsumidorFake, ProductorFake


def construir(base: Path) -> Config:
    generar(base / "datos_red")
    cfg = Config(data_dir=base / "datos_red", lake_dir=base / "lake")
    run = nuevo_run_id()
    for f in BATCH + CDC:
        ingerir_archivo(cfg, f, run)
    broker = BrokerFake(3)
    for clave in ("transmetro_validaciones", "aerometro_boardings"):
        publicar_archivo(cfg, FUENTES[clave], cliente=ProductorFake(broker), tamano_rafaga=1000, pausa=0,
                         dormir=lambda s: None)
        ConsumidorBronze(cfg, FUENTES[clave], cliente=ConsumidorFake(broker)).ejecutar()
    construir_silver(cfg)
    return cfg


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, default=Path(".ci/warehouse.duckdb"))
    a = ap.parse_args()
    with tempfile.TemporaryDirectory() as tmp:
        cfg = construir(Path(tmp))
        a.out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(cfg.lake_dir / "warehouse.duckdb", a.out)
    print(f"Warehouse sintético escrito en {a.out}")


if __name__ == "__main__":
    main()
