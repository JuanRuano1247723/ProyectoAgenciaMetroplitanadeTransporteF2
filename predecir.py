#!/usr/bin/env python
"""Proyecto 2, 2.4: predicciones de abandono (probabilidad de dejar de usar la red en los 30 días siguientes al corte).

    python predecir.py --datos datos_red --fecha-corte 2026-08-30

Produce un CSV con las columnas  unidad_id, tarjetas, puntaje, contactar  (una fila por unidad de la población del corte).
  unidad_id  operador:llave de la tarjeta (no depende del secreto de seudonimización, así que es igual en cualquier máquina)
  tarjetas   llaves originales de la unidad, separadas por ';' (con la tarjeta como unidad es una sola)
  puntaje    probabilidad de abandono del modelo, con 6 decimales
  contactar  1 si puntaje >= umbral (0.32, derivado del costo en 2.2), 0 si no

NO reentrena: carga modelos_guardados/modelo_abandono_v*.joblib. Qué hace, en orden:
  1. Verifica que el lake/warehouse se construyó con ESTOS archivos (hash de los 9 archivos); si no, corre flows.correr_todo
     (necesita Docker para Kafka). Usa --reconstruir para forzarlo.
  2. Calcula las features del corte con dbt (mismo código que 1.3): solo eventos anteriores al corte.
  3. Carga el modelo guardado, puntúa y escribe el CSV.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ))

CORTES = {"A": "2026-07-01", "B": "2026-07-31", "C": "2026-08-30"}


def _huella_datos(carpeta: Path) -> str:
    """SHA-256 combinado de los 9 archivos de origen (nombre y contenido)."""
    from bronze.fuentes import FUENTES
    h = hashlib.sha256()
    for nombre in sorted(f.archivo for f in FUENTES.values()):
        ruta = carpeta / nombre
        if not ruta.exists():
            raise SystemExit(f"Falta {ruta}: la carpeta de datos debe traer los 9 archivos del proyecto.")
        h.update(nombre.encode())
        with ruta.open("rb") as f:
            for bloque in iter(lambda: f.read(1 << 20), b""):
                h.update(bloque)
    return h.hexdigest()


def asegurar_warehouse(datos: Path, lake: Path, reconstruir: bool, tiempos: dict) -> None:
    marca = lake / "datos_origen.json"
    huella = _huella_datos(datos)
    ok = (not reconstruir and marca.exists() and (lake / "warehouse.duckdb").exists()
          and json.loads(marca.read_text(encoding="utf-8")).get("sha256") == huella)
    if ok:
        print(f"[1/3] El warehouse en {lake} ya se construyó con estos archivos: se reutiliza.")
        tiempos["carga_desde_cero_s"] = 0.0
        return
    print("[1/3] Construyendo el lake y el warehouse desde cero con estos archivos (flows.correr_todo; necesita Docker)...", flush=True)
    t0 = time.perf_counter()
    r = subprocess.run([sys.executable, "-m", "flows.correr_todo", "--sin-esperados"], cwd=str(RAIZ),
                       env={**os.environ, "DATA_DIR": str(datos), "LAKE_DIR": str(lake)})
    if r.returncode != 0:
        raise SystemExit("flows.correr_todo falló: revisa que Docker esté abierto y que PSEUDONIMO_SECRETO esté en .env")
    lake.mkdir(parents=True, exist_ok=True)
    marca.write_text(json.dumps({"sha256": huella, "datos": str(datos)}), encoding="utf-8")
    tiempos["carga_desde_cero_s"] = round(time.perf_counter() - t0, 1)


def calcular_features(cfg, fecha: str, tiempos: dict) -> None:
    """Corre los modelos dbt de población y features con los cortes del proyecto y, si hace falta, el corte pedido."""
    from flows.dbt_runner import dbt
    cortes = dict(CORTES)
    if fecha not in cortes.values():
        cortes["P"] = fecha
    print(f"[2/3] Calculando features con dbt (cortes: {', '.join(cortes.values())})...", flush=True)
    t0 = time.perf_counter()
    dbt(cfg, "run", "-s", "poblacion_etiqueta", "features_corte", variables={"cortes_p2": cortes})
    tiempos["features_s"] = round(time.perf_counter() - t0, 1)


def predecir(cfg, fecha: str, ruta_modelo: Path, tiempos: dict):
    import duckdb
    import joblib
    import pandas as pd
    import sklearn
    from modelos.comun import FEATURES_NUM

    t0 = time.perf_counter()
    meta = json.loads(ruta_modelo.with_suffix(".json").read_text(encoding="utf-8"))
    if meta["sklearn"] != sklearn.__version__:
        print(f"AVISO: el modelo se guardó con scikit-learn {meta['sklearn']} y aquí hay {sklearn.__version__}; "
              f"instala las versiones de requirements.txt.", file=sys.stderr)
    pipe = joblib.load(ruta_modelo)
    con = duckdb.connect(str(cfg.lake_dir / "warehouse.duckdb"), read_only=True)
    df = con.execute(
        "select f.unidad_id as usuario_sk, f.operador_cod, " + ", ".join(f"f.{c}" for c in FEATURES_NUM) + ", "
        "u.operador, u.llave_original from features.features_corte f join silver.silver_usuario u on u.usuario_sk = f.unidad_id "
        "where cast(f.fecha_corte as date) = ? order by u.operador, u.llave_original", [fecha]).df()
    con.close()
    if df.empty:
        raise SystemExit(f"No hay población para el corte {fecha}.")
    p = pipe.predict_proba(df[FEATURES_NUM + ["operador_cod"]])[:, 1]       # solo predice: no hay fit en este archivo
    out = pd.DataFrame({
        "unidad_id": df["operador"] + ":" + df["llave_original"],
        "tarjetas": df["llave_original"],
        "puntaje": p.round(6),
        "contactar": (p >= meta["umbral"]).astype(int)})
    tiempos["prediccion_s"] = round(time.perf_counter() - t0, 1)
    return out.sort_values("unidad_id").reset_index(drop=True), meta


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--datos", required=True, type=Path, help="carpeta con los 9 archivos de datos (p. ej. datos_red)")
    ap.add_argument("--fecha-corte", required=True, help="AAAA-MM-DD; el corte son las 00:00 de ese día")
    ap.add_argument("--salida", type=Path, help="CSV de salida (por defecto salidas/predicciones_<fecha>.csv)")
    ap.add_argument("--modelo", type=Path, help="archivo .joblib (por defecto la versión más reciente de modelos_guardados/)")
    ap.add_argument("--reconstruir", action="store_true", help="vuelve a construir el lake aunque ya coincida")
    a = ap.parse_args()
    date.fromisoformat(a.fecha_corte)
    modelo = a.modelo or sorted((RAIZ / "modelos_guardados").glob("modelo_abandono_v*.joblib"))[-1]
    salida = a.salida or RAIZ / "salidas" / f"predicciones_{a.fecha_corte}.csv"

    from bronze.config import Config
    os.environ["DATA_DIR"] = str(a.datos.resolve())
    cfg = Config.desde_entorno()
    tiempos: dict = {}
    asegurar_warehouse(a.datos.resolve(), cfg.lake_dir, a.reconstruir, tiempos)
    calcular_features(cfg, a.fecha_corte, tiempos)
    print("[3/3] Cargando el modelo guardado y puntuando (sin reentrenar)...", flush=True)
    out, meta = predecir(cfg, a.fecha_corte, modelo, tiempos)
    salida.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(salida, index=False)
    print(f"\n{len(out):,} unidades -> {salida}\nmodelo v{meta['version']}, umbral {meta['umbral']}; "
          f"contactar = 1 en {int(out['contactar'].sum()):,} ({out['contactar'].mean():.1%})\nTiempos (s): {tiempos}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
