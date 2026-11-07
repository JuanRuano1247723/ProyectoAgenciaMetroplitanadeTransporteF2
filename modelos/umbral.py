"""Proyecto 2, 2.2: umbral según costo y test único en el corte B.

Escenario de la Agencia (valores simulados, iguales para todos los grupos):
    contactar a un usuario cuesta Q5; si el usuario se iba a ir, la campaña lo retiene en el 25% de los casos; un usuario retenido vale Q60.

Ganancia esperada de contactar a un grupo con TP usuarios que se iban a ir y FP que no:
    G = (0.25 * 60) * TP - 5 * (TP + FP) = 15*TP - 5*TP - 5*FP = 10*TP - 5*FP
Por usuario con probabilidad p de irse:  g(p) = 15*p - 5,  positiva si p > 5/15 = 1/3 (umbral teórico con probabilidades calibradas).

Dos pasos, en este orden y sin mezclarse:
    python -m modelos.umbral elegir      # solo corte A: predicciones de validación cruzada -> curva de ganancia -> umbral CONGELADO
    python -m modelos.umbral evaluar-b   # entrena con TODO el corte A y evalúa en el corte B UNA SOLA VEZ; se niega a repetirse
    python -m modelos.umbral ensayo      # prueba el camino de evaluación con un fold de A (nunca toca B)

El corte B no se carga en ningún otro lugar del proyecto.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import warnings
from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, roc_auc_score

from bronze.config import RAIZ
from modelos.comun import cargar_corte, folds
from modelos.ensemble import ENSEMBLES

SALIDA = RAIZ / "evidencia"
UMBRAL_JSON = SALIDA / "p2_2_2_umbral.json"
TEST_B_JSON = SALIDA / "p2_2_2_test_b.json"
BITACORA = RAIZ / "docs" / "BITACORA_P2.md"
MODELO_FINAL = "HistGradientBoosting regularizado (lr 0.05, prof. 3, 200 iter.)"   # elegido en 2.1, antes de ver B

COSTO_CONTACTO = 5.0
P_RETENCION = 0.25
VALOR_RETENIDO = 60.0
BENEFICIO_TP = P_RETENCION * VALOR_RETENIDO            # Q15 esperados por cada usuario que se iba y fue contactado
UMBRAL_TEORICO = COSTO_CONTACTO / BENEFICIO_TP         # 1/3


def ganancia(tp: int, fp: int) -> float:
    """G = 15*TP - 5*(TP + FP) = 10*TP - 5*FP, en quetzales."""
    return BENEFICIO_TP * tp - COSTO_CONTACTO * (tp + fp)


def confusion(y, contactar) -> dict:
    tp = int(((contactar == 1) & (y == 1)).sum()); fp = int(((contactar == 1) & (y == 0)).sum())
    fn = int(((contactar == 0) & (y == 1)).sum()); tn = int(((contactar == 0) & (y == 0)).sum())
    prec = tp / (tp + fp) if tp + fp else 0.0
    rec = tp / (tp + fn) if tp + fn else 0.0
    return {"tp": tp, "fp": fp, "fn": fn, "tn": tn, "contactados": tp + fp, "precision": prec, "recall": rec,
            "ganancia_gtq": ganancia(tp, fp)}


def _git() -> dict:
    def run(*a):
        return subprocess.run(["git", *a], cwd=str(RAIZ), capture_output=True, text=True).stdout.strip()
    return {"commit_base": run("rev-parse", "HEAD"), "rama": run("branch", "--show-current"),
            "arbol_con_cambios_sin_commit": bool(run("status", "--porcelain"))}


def predicciones_cv(X, y) -> np.ndarray:
    """Probabilidad de cada unidad del corte A predicha por un modelo que NO la vio (5 folds de 1.4/2.1)."""
    oof = np.zeros(len(y))
    for tr, va in folds(y):
        oof[va] = ENSEMBLES[MODELO_FINAL]().fit(X.iloc[tr], y[tr]).predict_proba(X.iloc[va])[:, 1]
    return oof


def evaluar(modelo, X_te, y_te, umbral: float, X_ref_viajes=None) -> dict:
    """Evaluación de un modelo ya entrenado: matriz de confusión, ganancia y los baselines al lado."""
    p = modelo.predict_proba(X_te)[:, 1]
    contactar = (p >= umbral).astype(int)
    r = {"n": int(len(y_te)), "positivos": int(y_te.sum()), "tasa_positiva": float(y_te.mean()), "umbral": umbral,
         "pr_auc": float(average_precision_score(y_te, p)), "roc_auc": float(roc_auc_score(y_te, p)),
         "modelo": confusion(y_te, contactar)}
    n_pos = int(y_te.sum()); n = len(y_te)
    r["baseline_nadie"] = confusion(y_te, np.zeros(n, dtype=int))
    r["baseline_todos"] = confusion(y_te, np.ones(n, dtype=int))
    # baseline 1 (misma probabilidad para todos = tasa positiva de A): con p < 1/3 la regla de costo no contacta a nadie
    r["baseline_2_pr_auc"] = float(average_precision_score(y_te, -X_te["viajes_28d"].to_numpy()))
    k = r["modelo"]["contactados"]                       # baseline 2: contactar a los mismos k usuarios con menos viajes
    orden = np.argsort(X_te["viajes_28d"].to_numpy(), kind="stable")[:k]
    c2 = np.zeros(n, dtype=int); c2[orden] = 1
    r["baseline_2_mismo_numero_de_contactos"] = confusion(y_te, c2)
    r["baseline_1_pr_auc"] = float(y_te.mean())          # puntaje constante: PR-AUC = tasa positiva
    return r


def cmd_elegir() -> int:
    warnings.filterwarnings("ignore")
    X, y = cargar_corte("A")
    oof = predicciones_cv(X, y)
    ts = np.round(np.arange(0.02, 0.9801, 0.005), 3)
    filas = []
    for t in ts:
        c = confusion(y, (oof >= t).astype(int))
        filas.append({"umbral": t, **c})
    curva = pd.DataFrame(filas)
    curva.to_csv(SALIDA / "p2_2_2_curva_ganancia.csv", index=False)
    mejor = curva.loc[curva["ganancia_gtq"].idxmax()]
    teorico = confusion(y, (oof >= UMBRAL_TEORICO).astype(int))
    congelado = {"modelo": MODELO_FINAL, "umbral": float(mejor["umbral"]), "umbral_teorico": UMBRAL_TEORICO,
                 "elegido_con": "predicciones de validación cruzada del corte A (5 folds)",
                 "validacion_cv_en_umbral": {k: float(mejor[k]) for k in
                                             ("tp", "fp", "fn", "tn", "contactados", "precision", "recall", "ganancia_gtq")},
                 "validacion_cv_en_umbral_teorico": teorico,
                 "pr_auc_cv": float(average_precision_score(y, oof)), "n_A": int(len(y)), "positivos_A": int(y.sum()),
                 "fecha": datetime.now().isoformat(timespec="seconds"), **_git()}
    UMBRAL_JSON.write_text(json.dumps(congelado, indent=2, ensure_ascii=False), encoding="utf-8")

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(curva["umbral"], curva["ganancia_gtq"] / 1000)
    ax.axvline(mejor["umbral"], color="red", ls="--", label=f"umbral elegido = {mejor['umbral']:.3f}")
    ax.axvline(UMBRAL_TEORICO, color="gray", ls=":", label=f"umbral teórico 5/15 = {UMBRAL_TEORICO:.3f}")
    ax.scatter([mejor["umbral"]], [mejor["ganancia_gtq"] / 1000], color="red", zorder=5)
    ax.axhline(0, color="black", lw=.6)
    ax.set(xlabel="Umbral de probabilidad (se contacta si p ≥ umbral)", ylabel="Ganancia en miles de quetzales (corte A, validación cruzada)",
           title="Ganancia contra umbral")
    ax.legend(); ax.grid(alpha=.3)
    fig.tight_layout(); fig.savefig(SALIDA / "p2_2_2_curva_ganancia.png", dpi=140)

    t = congelado["validacion_cv_en_umbral"]
    print(f"Umbral elegido (solo A): {mejor['umbral']:.3f}  | teórico: {UMBRAL_TEORICO:.4f}")
    print(f"Con umbral {mejor['umbral']:.3f}: TP={t['tp']:.0f} FP={t['fp']:.0f}  precisión={t['precision']:.4f} recall={t['recall']:.4f}")
    print(f"Ganancia: 10*{t['tp']:.0f} - 5*{t['fp']:.0f} = Q{t['ganancia_gtq']:,.0f}")
    print(f"Con el umbral teórico: ganancia Q{teorico['ganancia_gtq']:,.0f}")
    print(f"Contactar a todos: Q{confusion(y, np.ones(len(y), dtype=int))['ganancia_gtq']:,.0f}")
    return 0


def cmd_ensayo() -> int:
    """Prueba el camino de evaluación con el último fold de A como si fuera el test. NO carga B."""
    warnings.filterwarnings("ignore")
    X, y = cargar_corte("A")
    u = json.loads(UMBRAL_JSON.read_text(encoding="utf-8"))["umbral"]
    tr, va = folds(y)[-1]
    m = ENSEMBLES[MODELO_FINAL]().fit(X.iloc[tr], y[tr])
    r = evaluar(m, X.iloc[va], y[va], u)
    print(json.dumps(r, indent=1)[:900])
    assert r["modelo"]["tp"] + r["modelo"]["fn"] == r["positivos"]
    assert r["modelo"]["tp"] + r["modelo"]["fp"] + r["modelo"]["fn"] + r["modelo"]["tn"] == r["n"]
    assert abs(r["modelo"]["ganancia_gtq"] - (10 * r["modelo"]["tp"] - 5 * r["modelo"]["fp"])) < 1e-6
    print("\nENSAYO OK (no se tocó el corte B)")
    return 0


def cmd_evaluar_b() -> int:
    if TEST_B_JSON.exists():
        raise SystemExit(f"{TEST_B_JSON.name} ya existe: el corte B se evalúa UNA sola vez. No se repite ni se ajusta nada después de verlo.")
    if not UMBRAL_JSON.exists():
        raise SystemExit("Primero `python -m modelos.umbral elegir`: el umbral se fija con el corte A antes de abrir B.")
    warnings.filterwarnings("ignore")
    u = json.loads(UMBRAL_JSON.read_text(encoding="utf-8"))
    X, y = cargar_corte("A")
    modelo = ENSEMBLES[MODELO_FINAL]().fit(X, y)                  # modelo final: TODO el corte A
    Xb, yb = cargar_corte("B")                                    # única lectura de B en el proyecto
    r = evaluar(modelo, Xb, yb, u["umbral"])
    r.update({"modelo_nombre": MODELO_FINAL, "fecha": datetime.now().isoformat(timespec="seconds"), **_git(),
              "validacion_cv_a": u["validacion_cv_en_umbral"], "pr_auc_cv_a": u["pr_auc_cv"], "n_A": int(len(y))})
    TEST_B_JSON.write_text(json.dumps(r, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(r, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("comando", choices=["elegir", "ensayo", "evaluar-b"])
    a = ap.parse_args()
    raise SystemExit({"elegir": cmd_elegir, "ensayo": cmd_ensayo, "evaluar-b": cmd_evaluar_b}[a.comando]())
