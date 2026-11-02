"""Proyecto 2, 1.4: baselines y regresión logística regularizada, validación cruzada estratificada de 5 folds SOLO con el corte A.

    python -m modelos.linea_base

Escribe en evidencia/: p2_1_4_modelos.(csv|md), p2_1_4_curva_lambda.png, p2_1_4_curva_lambda.csv y p2_1_4_coeficientes.csv.
"""
from __future__ import annotations

import argparse
import warnings
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from bronze.config import RAIZ
from modelos.comun import cargar_corte, folds

SALIDA = RAIZ / "evidencia"
PENALIZACIONES = {"L2 (Ridge)": 0.0, "L1 (Lasso)": 1.0, "Elastic Net (l1_ratio 0.5)": 0.5}
GRILLA_C = np.logspace(-4, 1, 11)          # C = 1 / lambda


def evaluar(y, puntaje_por_fold) -> dict:
    ap = [average_precision_score(y[v], p) for (_, v), p in zip(FOLDS, puntaje_por_fold)]
    auc = [roc_auc_score(y[v], p) for (_, v), p in zip(FOLDS, puntaje_por_fold)]
    return {"ap_media": np.mean(ap), "ap_std": np.std(ap, ddof=1), "auc_media": np.mean(auc), "auc_std": np.std(auc, ddof=1)}


def logistica(C: float, l1_ratio: float):
    return make_pipeline(StandardScaler(),
                         LogisticRegression(C=C, l1_ratio=l1_ratio, solver="saga", max_iter=500, tol=1e-3,
                                            random_state=0))


def puntajes_cv(X, y, C, l1_ratio):
    out = []
    for tr, va in FOLDS:
        m = logistica(C, l1_ratio).fit(X.iloc[tr], y[tr])
        out.append(m.predict_proba(X.iloc[va])[:, 1])
    return out


def main() -> int:
    global FOLDS
    ap = argparse.ArgumentParser()
    ap.add_argument("--salida", type=Path, default=SALIDA)
    a = ap.parse_args()
    a.salida.mkdir(parents=True, exist_ok=True)
    warnings.filterwarnings("ignore")

    X, y = cargar_corte("A")
    FOLDS = folds(y)
    tasa_A = y.mean()
    print(f"Corte A: {len(y):,} unidades, {y.sum():,} positivos, tasa {y.sum():,} / {len(y):,} = {tasa_A:.4f}")

    filas = []
    # baseline 1: todos reciben la tasa positiva del corte A
    filas.append({"modelo": "Baseline 1: tasa positiva de A para todos", **evaluar(y, [np.full(len(v), tasa_A) for _, v in FOLDS])})
    # baseline 2: una sola feature como puntaje, sin entrenar (menos viajes en 28 días = más riesgo)
    filas.append({"modelo": "Baseline 2: puntaje = −viajes_28d", **evaluar(y, [-X["viajes_28d"].to_numpy()[v] for _, v in FOLDS])})

    curva, mejor = [], {}
    for nombre, l1r in PENALIZACIONES.items():
        for C in GRILLA_C:
            r = evaluar(y, puntajes_cv(X, y, C, l1r))
            curva.append({"penalizacion": nombre, "C": C, "lambda": 1 / C, **r})
            print(f"{nombre:28s} C={C:9.4f} AP={r['ap_media']:.4f} ± {r['ap_std']:.4f}", flush=True)
        sub = [c for c in curva if c["penalizacion"] == nombre]
        mejor[nombre] = max(sub, key=lambda c: c["ap_media"])
        b = mejor[nombre]
        filas.append({"modelo": f"Logística {nombre}, C={b['C']:.4g} (λ={b['lambda']:.4g})",
                      **{k: b[k] for k in ("ap_media", "ap_std", "auc_media", "auc_std")}})

    tabla = pd.DataFrame(filas)
    tabla.to_csv(a.salida / "p2_1_4_modelos.csv", index=False)
    pd.DataFrame(curva).to_csv(a.salida / "p2_1_4_curva_lambda.csv", index=False)
    md = ["| modelo | PR-AUC media | PR-AUC desv. est. | ROC-AUC media | ROC-AUC desv. est. |", "|---|---:|---:|---:|---:|"]
    md += [f"| {r.modelo} | {r.ap_media:.4f} | {r.ap_std:.4f} | {r.auc_media:.4f} | {r.auc_std:.4f} |" for r in tabla.itertuples()]
    (a.salida / "p2_1_4_modelos.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))

    # gráfica: métrica de validación contra λ
    fig, ax = plt.subplots(figsize=(8, 5))
    for nombre in PENALIZACIONES:
        sub = pd.DataFrame([c for c in curva if c["penalizacion"] == nombre])
        ax.errorbar(sub["lambda"], sub["ap_media"], yerr=sub["ap_std"], marker="o", capsize=3, label=nombre)
        b = mejor[nombre]
        ax.scatter([b["lambda"]], [b["ap_media"]], s=160, facecolors="none", edgecolors="black", zorder=5)
    ax.axhline(tasa_A, ls="--", color="gray", label=f"Baseline 1 (tasa A = {tasa_A:.3f})")
    ax.set_xscale("log")
    ax.set_xlabel("λ = 1 / C  (más λ = más castigo)")
    ax.set_ylabel("PR-AUC en validación (media de 5 folds, barras = desv. est.)")
    ax.set_title("Corte A: métrica de validación contra λ (círculo = λ elegido por penalización)")
    ax.legend()
    ax.grid(alpha=.3)
    fig.tight_layout()
    fig.savefig(a.salida / "p2_1_4_curva_lambda.png", dpi=140)

    # coeficientes del mejor modelo logístico, ajustado con todo el corte A (solo para interpretar, no para evaluar)
    # Se interpreta la L2: las tres penalizaciones empatan dentro de una desviación estándar y la L2 no anula coeficientes.
    nombre_mejor = "L2 (Ridge)"
    b = mejor[nombre_mejor]
    m = logistica(b["C"], PENALIZACIONES[nombre_mejor]).fit(X, y)
    coef = pd.DataFrame({"feature": X.columns, "coeficiente": m[-1].coef_[0]}).sort_values("coeficiente", ascending=False)
    coef.to_csv(a.salida / "p2_1_4_coeficientes.csv", index=False)
    print(f"\nMejor: {nombre_mejor}, C={b['C']:.4g}\n", coef.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
