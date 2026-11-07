"""Proyecto 2, 2.4: entrena el modelo FINAL con todo el corte A y lo guarda con su versión.

    python -m modelos.guardar_modelo

Es exactamente el modelo evaluado una sola vez en el corte B (2.2): HistGradientBoosting regularizado, entrenado con todo el corte A,
con el mismo umbral (evidencia/p2_2_2_umbral.json). Se guarda el PIPELINE COMPLETO (indicadores de operador + modelo), no solo el modelo,
para que predecir.py reciba la tabla de features tal como sale de dbt. predecir.py solo carga este archivo: nunca entrena.

Escribe modelos_guardados/modelo_abandono_v<VERSION>.joblib y .json (versiones de las librerías, semilla, features, umbral).
"""
from __future__ import annotations

import json
import platform
import sys
from datetime import datetime
from pathlib import Path

import duckdb
import joblib
import numpy as np
import sklearn
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from bronze.config import RAIZ, Config
from modelos.comun import FEATURES_NUM, OPERADORES, SEMILLA

VERSION = "1.0.0"
DIR = RAIZ / "modelos_guardados"
UMBRAL_JSON = RAIZ / "evidencia" / "p2_2_2_umbral.json"


def construir_pipeline() -> Pipeline:
    """Mismos hiperparámetros del modelo elegido en 2.1 ('HistGradientBoosting regularizado')."""
    prep = ColumnTransformer(
        [("num", "passthrough", FEATURES_NUM),
         ("operador", OneHotEncoder(categories=[OPERADORES], sparse_output=False), ["operador_cod"])],
        verbose_feature_names_out=False)
    modelo = HistGradientBoostingClassifier(learning_rate=0.05, max_iter=200, max_depth=3, min_samples_leaf=100,
                                            l2_regularization=1.0, early_stopping=False, random_state=SEMILLA)
    return Pipeline([("preparacion", prep), ("modelo", modelo)])


def main() -> int:
    cfg = Config.desde_entorno()
    con = duckdb.connect(str(cfg.lake_dir / "warehouse.duckdb"), read_only=True)
    df = con.execute("select * from features.features_corte where corte = 'A' order by unidad_id").df()
    con.close()
    y = df["etiqueta"].astype(int).to_numpy()
    pipe = construir_pipeline().fit(df[FEATURES_NUM + ["operador_cod"]], y)
    umbral = json.loads(UMBRAL_JSON.read_text(encoding="utf-8"))["umbral"]

    DIR.mkdir(exist_ok=True)
    ruta = DIR / f"modelo_abandono_v{VERSION}.joblib"
    joblib.dump(pipe, ruta, compress=3)
    meta = {"version": VERSION, "modelo": "HistGradientBoostingClassifier regularizado (lr 0.05, profundidad 3, 200 iteraciones)",
            "entrenado_con": "todo el corte A (2026-07-01)", "n_entrenamiento": int(len(y)), "positivos": int(y.sum()),
            "semilla": SEMILLA, "umbral": umbral, "features": FEATURES_NUM, "categoricas": ["operador_cod"],
            "etiqueta": "1 si la unidad no tiene ningún abordaje válido en los 30 días desde el corte",
            "fecha_entrenamiento": datetime.now().isoformat(timespec="seconds"),
            "python": platform.python_version(), "sklearn": sklearn.__version__, "numpy": np.__version__,
            "joblib": joblib.__version__, "plataforma": platform.platform()}
    ruta.with_suffix(".json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Guardado {ruta.relative_to(RAIZ)} ({ruta.stat().st_size / 1024:.0f} KB), umbral {umbral}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
