"""Proyecto 2, 2.4: simula la prueba de invariancia recortando los datos crudos a eventos anteriores a un corte.

    python -m flows.recortar_datos datos_red <carpeta_salida> 2026-07-31T00:00:00

Recorta los 9 archivos (los catálogos pasan completos). Aerómetro viene en UTC y se corrige a hora local (UTC-6). Después:
    LAKE_DIR=<otro_lake> python predecir.py --datos <carpeta_salida> --fecha-corte 2026-07-31 --salida a.csv
    python predecir.py --datos datos_red --fecha-corte 2026-07-31 --salida b.csv        # y comparar a.csv con b.csv: deben ser idénticos
"""
import csv
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

src, dst, corte = Path(sys.argv[1]), Path(sys.argv[2]), datetime.fromisoformat(sys.argv[3])
dst.mkdir(parents=True, exist_ok=True)
for cat in ("tm_estaciones.csv", "tu_paradas.csv", "mr_estaciones.csv", "am_estaciones.csv"):
    shutil.copy(src / cat, dst / cat)

def filtrar_csv(nombre, ts_fn):
    n_in = n_out = 0
    with (src / nombre).open(newline="", encoding="utf-8") as fi, (dst / nombre).open("w", newline="", encoding="utf-8") as fo:
        r, w = csv.reader(fi), csv.writer(fo, lineterminator="\n")
        enc = next(r); w.writerow(enc); idx = {c: i for i, c in enumerate(enc)}
        for fila in r:
            n_in += 1
            try:
                t = ts_fn(fila, idx)
            except Exception:
                continue                       # fecha ilegible: no se puede ubicar en un día, se descarta
            if t < corte:
                w.writerow(fila); n_out += 1
    print(nombre, n_in, "->", n_out)

filtrar_csv("transmetro_validaciones.csv", lambda f, i: datetime.fromisoformat(f[i["fecha_hora"]].strip()))
filtrar_csv("transurbano_transacciones.csv", lambda f, i: datetime.strptime(f[i["fecha"]].strip() + " " + f[i["hora"]].strip(), "%d/%m/%Y %H:%M:%S"))
filtrar_csv("cdc_padron_usuarios.csv", lambda f, i: datetime.fromisoformat(f[i["commit_ts"]].strip()))
# Aerómetro viene en UTC; la hora local es UTC-6
from datetime import timedelta
filtrar_csv("aerometro_boardings.csv", lambda f, i: datetime.fromisoformat(f[i["timestamp_utc"]].strip().replace("Z", "")) - timedelta(hours=6))
n_in = n_out = 0
with (src / "metroriel_viajes.jsonl").open(encoding="utf-8") as fi, (dst / "metroriel_viajes.jsonl").open("w", encoding="utf-8") as fo:
    for linea in fi:
        n_in += 1
        try:
            t = datetime.fromisoformat(json.loads(linea)["entry"]["ts"])
        except Exception:
            continue
        if t < corte:
            fo.write(linea if linea.endswith("\n") else linea + "\n"); n_out += 1
print("metroriel_viajes.jsonl", n_in, "->", n_out)
