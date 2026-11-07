"""Proyecto 2, 2.4: formato de las predicciones entregadas y coherencia con el modelo guardado (no necesita el lake)."""
import json
from pathlib import Path

import pandas as pd
import pytest

RAIZ = Path(__file__).resolve().parents[1]
CSV = RAIZ / "predicciones" / "predicciones_corte_C.csv"
MODELOS = sorted((RAIZ / "modelos_guardados").glob("modelo_abandono_v*.joblib"))


@pytest.mark.skipif(not CSV.exists() or not MODELOS, reason="faltan las predicciones o el modelo guardado")
def test_predicciones_del_corte_c_tienen_el_formato_pedido():
    d = pd.read_csv(CSV, dtype={"tarjetas": str})
    assert list(d.columns) == ["unidad_id", "tarjetas", "puntaje", "contactar"]
    assert d["unidad_id"].is_unique and not d.isna().any().any()
    assert d["puntaje"].between(0, 1).all() and set(d["contactar"]) <= {0, 1}
    umbral = json.loads(MODELOS[-1].with_suffix(".json").read_text(encoding="utf-8"))["umbral"]
    assert (d["contactar"] == (d["puntaje"] >= umbral).astype(int)).all()
    assert d["unidad_id"].tolist() == sorted(d["unidad_id"])


@pytest.mark.skipif(not MODELOS, reason="no hay modelo guardado")
def test_el_modelo_guardado_trae_version_y_librerias_en_su_metadato():
    meta = json.loads(MODELOS[-1].with_suffix(".json").read_text(encoding="utf-8"))
    assert meta["version"] in MODELOS[-1].name
    assert {"sklearn", "numpy", "python", "semilla", "umbral", "features"} <= set(meta)


def test_predecir_no_entrena():
    fuente = (RAIZ / "predecir.py").read_text(encoding="utf-8")
    assert ".fit(" not in fuente and "fit_transform" not in fuente
