"""Diagnostica la calibración de P(abandono) con las predicciones OOF del corte A."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import PercentFormatter
from sklearn.metrics import average_precision_score

from modelos.comun import N_FOLDS, SEMILLA, cargar_corte
from modelos.umbral import MODELO_FINAL, SALIDA, UMBRAL_JSON, predicciones_cv


CURVA_OOF = SALIDA / "p2_2_2_curva_ganancia.csv"
N_INTERVALOS = 10


def cargar_conteos():
    """Recupera los conteos de positivos y totales con puntaje >= cada umbral."""
    curva = pd.read_csv(CURVA_OOF)
    referencia = json.loads(UMBRAL_JSON.read_text(encoding="utf-8"))
    umbrales = np.r_[0.0, curva["umbral"].to_numpy(), 1.0]
    totales = np.r_[referencia["n_A"], curva["contactados"].to_numpy(), 0]
    positivos = np.r_[referencia["positivos_A"], curva["tp"].to_numpy(), 0]

    # 1 es un borde derecho inclusivo: el cero terminal representa P > 1.
    if (
        (np.diff(umbrales) <= 0).any()
        or (np.diff(totales) > 0).any()
        or (np.diff(positivos) > 0).any()
        or (np.diff(totales - positivos) > 0).any()
        or not np.array_equal(curva["contactados"], curva["tp"] + curva["fp"])
        or not (curva["tp"] + curva["fn"]).eq(referencia["positivos_A"]).all()
        or not (curva["fp"] + curva["tn"]).eq(referencia["n_A"] - referencia["positivos_A"]).all()
    ):
        raise ValueError("Los conteos del barrido OOF de A no son consistentes.")
    return umbrales, totales, positivos, referencia


def verificar_poblacion_oof(y, puntajes, n, positivos):
    if (
        len(y) != n
        or len(puntajes) != len(y)
        or not np.isin(y, [0, 1]).all()
        or not np.isfinite(puntajes).all()
        or not ((0 <= puntajes) & (puntajes <= 1)).all()
    ):
        raise ValueError("Se requieren las etiquetas binarias y las probabilidades OOF del corte A.")
    if y.sum() != positivos:
        raise ValueError("La cantidad de positivos difiere de la del corte A original.")


def verificar_oof(y, puntajes, umbrales, totales, positivos, referencia):
    verificar_poblacion_oof(y, puntajes, totales[0], positivos[0])
    for t, n, tp in zip(umbrales[:-1], totales[:-1], positivos[:-1], strict=True):
        seleccion = puntajes >= t
        if seleccion.sum() != n or y[seleccion].sum() != tp:
            raise ValueError(
                f"Las predicciones OOF no reproducen el barrido original en t={t:.3f}. "
                "Usa el warehouse original (mismo orden de unidades) o el OOF original."
            )
    if not np.isclose(average_precision_score(y, puntajes), referencia["pr_auc_cv"], rtol=0, atol=1e-8):
        raise ValueError("La PR-AUC OOF no coincide con el registro original del corte A.")


def resumir_intervalos(umbrales, totales, positivos, y=None, puntajes=None):
    """Agrupa puntajes en décimos y acota la media usando el barrido si falta el OOF por fila."""
    bordes = np.linspace(0, 1, N_INTERVALOS + 1).round(3)
    indices = np.searchsorted(umbrales, bordes)
    if not np.array_equal(umbrales[indices], bordes):
        raise ValueError("El barrido debe contener los bordes de los intervalos de calibración.")
    intervalos = []
    for i, j in zip(indices[:-1], indices[1:], strict=True):
        n = int(totales[i] - totales[j])
        tp = int(positivos[i] - positivos[j])
        fila = {
            "desde": float(umbrales[i]), "hasta": float(umbrales[j]),
            "n": n, "positivos": tp, "tasa_observada": None,
            "probabilidad_media": None, "media_min": None, "media_max": None,
        }
        if n:
            inferior, superior = umbrales[i], umbrales[j]
            fila["tasa_observada"] = tp / n
            if puntajes is None:
                cantidad = totales[i:j] - totales[i + 1:j + 1]
                fila["media_min"] = float(cantidad @ umbrales[i:j] / n)
                fila["media_max"] = float(cantidad @ umbrales[i + 1:j + 1] / n)
                fila["probabilidad_media"] = (fila["media_min"] + fila["media_max"]) / 2
            else:
                dentro = (puntajes >= inferior) & (puntajes < superior)
                if j == len(umbrales) - 1:
                    dentro |= puntajes == 1
                if dentro.sum() != n or y[dentro].sum() != tp:
                    raise ValueError("El intervalo no coincide con los conteos OOF registrados.")
                media = float(puntajes[dentro].mean())
                fila.update(probabilidad_media=media, media_min=media, media_max=media)
        intervalos.append(fila)
    return intervalos


def calcular_ece(intervalos: list[dict]) -> tuple[float, float, float]:
    ece = minimo = maximo = 0.0
    total = sum(fila["n"] for fila in intervalos)
    for fila in intervalos:
        if not fila["n"]:
            continue
        peso = fila["n"] / total
        tasa, inferior, superior = fila["tasa_observada"], fila["media_min"], fila["media_max"]
        ece += peso * abs(tasa - fila["probabilidad_media"])
        minimo += peso * max(inferior - tasa, tasa - superior, 0)
        maximo += peso * max(abs(tasa - inferior), abs(tasa - superior))
    return ece, minimo, maximo


def graficar(intervalos, ece, minimo, maximo, aproximado, ruta, *, recalculado=False):
    fig, (ax, ax_n) = plt.subplots(2, 1, figsize=(7.4, 7), sharex=True, height_ratios=[3.5, 1])
    llenos = [f for f in intervalos if f["n"]]
    medias = np.array([f["probabilidad_media"] for f in llenos])
    tasas = [f["tasa_observada"] for f in llenos]
    ax.plot([0, 1], [0, 1], "--", color="#64748b", label="Calibración ideal")
    etiqueta = "Media estimada del OOF de A" if aproximado else "Media del OOF de A"
    ax.plot(medias, tasas, "o-", color="#155e75", label=etiqueta, clip_on=False)
    if aproximado:
        ax.errorbar(medias, tasas, xerr=[medias - [f["media_min"] for f in llenos],
                                       [f["media_max"] for f in llenos] - medias],
                    fmt="none", capsize=4, color="#155e75", label="Rango posible de la media")
        detalle = f"ECE estimado {ece:.2%}  |  Rango posible {minimo:.2%} a {maximo:.2%}"
    else:
        serie = "OOF recalculado" if recalculado else "OOF original"
        detalle = f"{serie}  |  ECE {ece:.3%}"
    ax.set_title(f"Calibración de abandono en el corte A\n{detalle}")
    ax.set(ylabel="Tasa de abandono observada", xlim=(0, 1), ylim=(0, 1))
    ax.yaxis.set_major_formatter(PercentFormatter(1))
    ax.grid(alpha=0.24)
    ax.legend(loc="upper left", fontsize=8.5)
    ax_n.bar([f["desde"] + 0.05 for f in intervalos], [f["n"] for f in intervalos],
             width=0.09, color="#155e75")
    ax_n.set(xlabel="Probabilidad de abandono", ylabel="Tarjetas", xticks=np.linspace(0, 1, 11))
    ax_n.xaxis.set_major_formatter(PercentFormatter(1))
    ax_n.grid(axis="y", alpha=0.24)
    fig.tight_layout()
    fig.savefig(ruta, dpi=160)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    entrada = parser.add_mutually_exclusive_group()
    entrada.add_argument("--desde-conteos", action="store_true", help="acota el ECE con el barrido OOF archivado")
    entrada.add_argument("--oof", type=Path, help="CSV original con columnas etiqueta,puntaje")
    entrada.add_argument(
        "--reconstruir", action="store_true",
        help="recalcula el OOF de A ordenado por operador y llave, independiente del secreto"
    )
    parser.add_argument("--salida", type=Path, default=SALIDA)
    args = parser.parse_args()

    umbrales, totales, positivos, referencia = cargar_conteos()
    y = puntajes = None
    coincide_barrido = None
    sufijo = "_acotada"
    fuente = str(CURVA_OOF.relative_to(SALIDA.parent))
    if not args.desde_conteos:
        sufijo = ""
        fuente = "probabilidades OOF por fila de la corrida original"
        if args.oof:
            oof = pd.read_csv(args.oof, float_precision="round_trip")
            y, puntajes = oof["etiqueta"].to_numpy(), oof["puntaje"].to_numpy()
        else:
            X, y = cargar_corte("A", orden_estable=args.reconstruir)
            puntajes = predicciones_cv(X, y)
        if args.reconstruir:
            verificar_poblacion_oof(y, puntajes, totales[0], positivos[0])
            fuente = "OOF recalculado del corte A, con orden de operador y llave por tarjeta"
            sufijo = "_recalculada"
            umbrales = np.linspace(0, 1, N_INTERVALOS + 1).round(3)
            totales = np.array([int((puntajes >= t).sum()) for t in umbrales[:-1]] + [0])
            positivos = np.array([int(y[puntajes >= t].sum()) for t in umbrales[:-1]] + [0])
        else:
            verificar_oof(y, puntajes, umbrales, totales, positivos, referencia)
            coincide_barrido = True

    intervalos = resumir_intervalos(umbrales, totales, positivos, y, puntajes)
    ece, minimo, maximo = calcular_ece(intervalos)
    resultado = {
        "corte": "A", "modelo": MODELO_FINAL, "folds": N_FOLDS, "semilla": SEMILLA,
        "n": int(totales[0]), "positivos": int(positivos[0]), "n_intervalos": N_INTERVALOS,
        "metodo": "intervalos de igual ancho; [desde, hasta), último incluye 1",
        "fuente": fuente,
        "coincide_barrido_original": coincide_barrido,
        "pr_auc_oof": referencia["pr_auc_cv"] if puntajes is None else float(average_precision_score(y, puntajes)),
        "ece_aproximado": args.desde_conteos, "ece": ece, "ece_min": minimo, "ece_max": maximo,
        "intervalos": intervalos,
    }
    args.salida.mkdir(parents=True, exist_ok=True)
    base = args.salida / f"p2_calibracion_oof_a{sufijo}"
    base.with_suffix(".json").write_text(json.dumps(resultado, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    graficar(intervalos, ece, minimo, maximo, args.desde_conteos, base.with_suffix(".png"),
             recalculado=args.reconstruir)
    if args.desde_conteos:
        print(f"ECE estimado {ece:.6f} (rango {minimo:.6f} a {maximo:.6f})")
    else:
        print(f"ECE directo {ece:.6f}")


if __name__ == "__main__":
    main()
