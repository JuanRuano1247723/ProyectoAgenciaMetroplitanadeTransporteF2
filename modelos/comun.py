"""Datos y folds compartidos por todos los modelos del Proyecto 2.

Los folds se definen UNA vez aquí para que toda comparación (baselines, logística, ensemble) use los mismos 5 folds del corte A.
El corte B no se carga en ningún modelo de la Fase 1: solo se usa en 2.2, una sola vez.
"""
from __future__ import annotations

import duckdb
import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold

from bronze.config import Config

SEMILLA = 42
N_FOLDS = 5
FEATURES_NUM = ["viajes_28d", "viajes_7d", "viajes_14d", "viajes_14d_previos", "tendencia_14d", "dias_activos_28d",
                "dias_desde_ultimo_viaje", "gasto_28d", "tarifa_media_28d", "estaciones_distintas_28d",
                "zonas_distintas_28d", "transbordos_28d", "prop_fin_de_semana_28d", "prop_hora_pico_28d",
                "persona_operadores_28d"]
OPERADORES = ["AM", "MR", "TM", "TU"]


def cargar_corte(corte: str = "A", cfg: Config | None = None) -> tuple[pd.DataFrame, np.ndarray]:
    """X (features numéricas y un indicador por operador) e y (etiqueta 0/1) de un corte. Solo A en la Fase 1."""
    cfg = cfg or Config.desde_entorno()
    con = duckdb.connect(str(cfg.lake_dir / "warehouse.duckdb"), read_only=True)
    df = con.execute("select * from features.features_corte where corte = ? order by unidad_id", [corte]).df()
    con.close()
    if df["etiqueta"].isna().any():
        raise ValueError(f"El corte {corte} no tiene etiqueta completa: no se puede entrenar ni evaluar con él.")
    for op in OPERADORES:
        df[f"op_{op}"] = (df["operador_cod"] == op).astype(int)
    X = df[FEATURES_NUM + [f"op_{o}" for o in OPERADORES]].astype(float)
    return X, df["etiqueta"].astype(int).to_numpy()


def folds(y: np.ndarray) -> list[tuple[np.ndarray, np.ndarray]]:
    """Los 5 folds estratificados del corte A (mismos índices en cada llamada)."""
    return list(StratifiedKFold(n_splits=N_FOLDS, shuffle=True, random_state=SEMILLA).split(np.zeros(len(y)), y))
