"""Proyecto 2, 2.1: ensembles y sesgo-varianza, con los MISMOS 5 folds estratificados del corte A que 1.4.

    python -m modelos.ensemble

Entrena Random Forest y HistGradientBoosting (cada uno en una configuración flexible y una regularizada) y los compara con los
baselines y la logística de 1.4, reportando la métrica en entrenamiento y en validación. Calcula la importancia por permutación
EN VALIDACIÓN (no en entrenamiento) del mejor ensemble. No carga el corte B.

Escribe en evidencia/: p2_2_1_modelos.(csv|md), p2_2_1_importancias.(csv|md), p2_2_1_importancias.png.
"""
from __future__ import annotations

import argparse
import time
import warnings
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.inspection import permutation_importance
from sklearn.metrics import average_precision_score, roc_auc_score

from bronze.config import RAIZ
from modelos.comun import SEMILLA, cargar_corte, folds
from modelos.linea_base import logistica

SALIDA = RAIZ / "evidencia"
CURVA = SALIDA / "p2_1_4_curva_lambda.csv"
PENALIZACIONES = {"L2 (Ridge)": 0.0, "L1 (Lasso)": 1.0, "Elastic Net (l1_ratio 0.5)": 0.5}

ENSEMBLES = {
    "Random Forest flexible (árboles sin límite de profundidad)":
        lambda: RandomForestClassifier(n_estimators=300, min_samples_leaf=1, n_jobs=-1, random_state=SEMILLA),
    "Random Forest regularizado (hojas de al menos 100 filas)":
        lambda: RandomForestClassifier(n_estimators=300, min_samples_leaf=100, max_features="sqrt", n_jobs=-1,
                                       random_state=SEMILLA),
    "HistGradientBoosting flexible (lr 0.1, 63 hojas, 300 iter.)":
        lambda: HistGradientBoostingClassifier(learning_rate=0.1, max_iter=300, max_leaf_nodes=63,
                                               early_stopping=False, random_state=SEMILLA),
    "HistGradientBoosting regularizado (lr 0.05, prof. 3, 200 iter.)":
        lambda: HistGradientBoostingClassifier(learning_rate=0.05, max_iter=200, max_depth=3, min_samples_leaf=100,
                                               l2_regularization=1.0, early_stopping=False, random_state=SEMILLA),
}


def _metricas(y, p) -> tuple[float, float]:
    return average_precision_score(y, p), roc_auc_score(y, p)


def evaluar(nombre, X, y, FOLDS, fabrica=None, puntaje=None) -> dict:
    """Entrena en cada fold (si hay modelo) y mide PR-AUC / ROC-AUC en entrenamiento y en validación."""
    tr_ap, tr_auc, va_ap, va_auc, seg = [], [], [], [], 0.0
    for tr, va in FOLDS:
        if fabrica is not None:
            t0 = time.perf_counter()
            m = fabrica().fit(X.iloc[tr], y[tr])
            seg += time.perf_counter() - t0
            p_tr, p_va = m.predict_proba(X.iloc[tr])[:, 1], m.predict_proba(X.iloc[va])[:, 1]
        else:
            p_tr, p_va = puntaje(tr), puntaje(va)
        a, b = _metricas(y[tr], p_tr)
        c, d = _metricas(y[va], p_va)
        tr_ap.append(a); tr_auc.append(b); va_ap.append(c); va_auc.append(d)
    return {"modelo": nombre,
            "pr_auc_entrenamiento": np.mean(tr_ap), "pr_auc_validacion": np.mean(va_ap),
            "pr_auc_validacion_std": np.std(va_ap, ddof=1),
            "roc_auc_entrenamiento": np.mean(tr_auc), "roc_auc_validacion": np.mean(va_auc),
            "roc_auc_validacion_std": np.std(va_auc, ddof=1),
            "brecha_pr_auc": np.mean(tr_ap) - np.mean(va_ap), "segundos_entrenamiento": round(seg, 1)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--salida", type=Path, default=SALIDA)
    a = ap.parse_args()
    a.salida.mkdir(parents=True, exist_ok=True)
    warnings.filterwarnings("ignore")

    X, y = cargar_corte("A")
    FOLDS = folds(y)
    tasa_A = y.mean()
    viajes = X["viajes_28d"].to_numpy()
    filas = [
        evaluar("Baseline 1: tasa positiva de A para todos", X, y, FOLDS, puntaje=lambda idx: np.full(len(idx), tasa_A)),
        evaluar("Baseline 2: puntaje = −viajes_28d", X, y, FOLDS, puntaje=lambda idx: -viajes[idx]),
    ]
    curva = pd.read_csv(CURVA)
    for nombre, l1r in PENALIZACIONES.items():                      # el C elegido en 1.4 para cada castigo
        sub = curva[curva["penalizacion"] == nombre]
        C = float(sub.loc[sub["ap_media"].idxmax(), "C"])
        filas.append(evaluar(f"Logística {nombre}, C={C:.4g}", X, y, FOLDS, fabrica=lambda C=C, l=l1r: logistica(C, l)))
        print(filas[-1]["modelo"], round(filas[-1]["pr_auc_validacion"], 4), flush=True)
    for nombre, fab in ENSEMBLES.items():
        filas.append(evaluar(nombre, X, y, FOLDS, fabrica=fab))
        r = filas[-1]
        print(f"{nombre}: train={r['pr_auc_entrenamiento']:.4f} val={r['pr_auc_validacion']:.4f} ({r['segundos_entrenamiento']}s)", flush=True)

    tabla = pd.DataFrame(filas)
    tabla.to_csv(a.salida / "p2_2_1_modelos.csv", index=False)
    md = ["| modelo | PR-AUC entrenamiento | PR-AUC validación (media) | desv. est. | brecha | ROC-AUC entren. | ROC-AUC valid. | seg. entren. |",
          "|---|---:|---:|---:|---:|---:|---:|---:|"]
    md += [f"| {r.modelo} | {r.pr_auc_entrenamiento:.4f} | {r.pr_auc_validacion:.4f} | {r.pr_auc_validacion_std:.4f} | "
           f"{r.brecha_pr_auc:+.4f} | {r.roc_auc_entrenamiento:.4f} | {r.roc_auc_validacion:.4f} | {r.segundos_entrenamiento} |"
           for r in tabla.itertuples()]
    (a.salida / "p2_2_1_modelos.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))

    # importancia por permutación en VALIDACIÓN del mejor ensemble (por PR-AUC de validación)
    ens = tabla[tabla["modelo"].isin(ENSEMBLES)]
    mejor = ens.loc[ens["pr_auc_validacion"].idxmax(), "modelo"]
    imp = np.zeros((len(FOLDS), X.shape[1]))
    for i, (tr, va) in enumerate(FOLDS):
        m = ENSEMBLES[mejor]().fit(X.iloc[tr], y[tr])
        r = permutation_importance(m, X.iloc[va], y[va], scoring="average_precision", n_repeats=5,
                                   random_state=SEMILLA, n_jobs=-1)
        imp[i] = r.importances_mean
    df = pd.DataFrame({"feature": X.columns, "caida_pr_auc_media": imp.mean(0), "desv_est_entre_folds": imp.std(0, ddof=1)})
    df = df.sort_values("caida_pr_auc_media", ascending=False).reset_index(drop=True)
    df.to_csv(a.salida / "p2_2_1_importancias.csv", index=False)
    top = df.head(10)
    (a.salida / "p2_2_1_importancias.md").write_text(
        f"Modelo: {mejor}. Caída de PR-AUC al permutar cada feature en los folds de validación (5 repeticiones por fold).\n\n"
        "| # | feature | caída de PR-AUC | desv. est. entre folds |\n|---:|---|---:|---:|\n"
        + "\n".join(f"| {i + 1} | {r.feature} | {r.caida_pr_auc_media:.4f} | {r.desv_est_entre_folds:.4f} |"
                    for i, r in enumerate(top.itertuples())) + "\n", encoding="utf-8")
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.barh(top["feature"][::-1], top["caida_pr_auc_media"][::-1], xerr=top["desv_est_entre_folds"][::-1], capsize=3)
    ax.set_xlabel("Caída de PR-AUC en validación al permutar la feature")
    ax.set_title(f"Importancia por permutación (validación)\n{mejor}", fontsize=10)
    fig.tight_layout()
    fig.savefig(a.salida / "p2_2_1_importancias.png", dpi=140)
    print("\nMejor ensemble:", mejor, "\n", top.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
