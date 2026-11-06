"""Proyecto 2, 2.3: segmentación con KMeans y PCA sobre la tabla de features del corte A, ya escalada.

    python -m modelos.segmentos              # elige k por codo y silueta y escribe las tablas y gráficas
    python -m modelos.segmentos --k 4        # fuerza k

Solo usa el corte A y NO usa la etiqueta para formar los segmentos (la etiqueta solo se usa después, para describirlos).
El segmento no se usa como feature de ningún clasificador, así que no hace falta ajustar KMeans dentro de la validación cruzada.

Escribe en evidencia/: p2_2_3_k.(csv|png), p2_2_3_pca.png, p2_2_3_segmentos.(csv|md).
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
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

from bronze.config import RAIZ
from modelos.comun import FEATURES_NUM, SEMILLA, cargar_corte

SALIDA = RAIZ / "evidencia"
K_RANGO = range(2, 9)
RESUMEN = ["viajes_28d", "dias_activos_28d", "dias_desde_ultimo_viaje", "gasto_28d", "tarifa_media_28d",
           "persona_operadores_28d", "prop_fin_de_semana_28d", "prop_hora_pico_28d"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--k", type=int, help="forzar k en lugar del elegido por silueta")
    ap.add_argument("--salida", type=Path, default=SALIDA)
    a = ap.parse_args()
    a.salida.mkdir(parents=True, exist_ok=True)
    warnings.filterwarnings("ignore")

    X, y = cargar_corte("A")
    X = X[FEATURES_NUM]                                    # 15 features numéricas, sin indicadores de operador
    Z = StandardScaler().fit_transform(X)                  # escaladas con media 0 y desviación 1

    # elección de k: codo (inercia) y silueta (con una muestra fija de 10,000 filas, por costo)
    rng = np.random.RandomState(SEMILLA)
    muestra = rng.choice(len(Z), size=10_000, replace=False)
    filas = []
    for k in K_RANGO:
        km = KMeans(n_clusters=k, n_init=10, random_state=SEMILLA).fit(Z)
        sil = silhouette_score(Z[muestra], km.labels_[muestra], random_state=SEMILLA)
        filas.append({"k": k, "inercia": km.inertia_, "silueta": sil})
        print(f"k={k} inercia={km.inertia_:,.0f} silueta={sil:.4f}", flush=True)
    kdf = pd.DataFrame(filas)
    kdf.to_csv(a.salida / "p2_2_3_k.csv", index=False)
    # k=2 tiene la mayor silueta, pero solo separa a los viajeros intensos (~11%) del resto y no permite acciones distintas:
    # se elige el mejor k entre 3 y 8 (sale k=3: silueta 0.27, y cae a ~0.16 con k>=4; el codo también se dobla en 3).
    sub = kdf[kdf["k"] >= 3]
    k = a.k or int(sub.loc[sub["silueta"].idxmax(), "k"])

    fig, ax = plt.subplots(1, 2, figsize=(11, 4))
    ax[0].plot(kdf["k"], kdf["inercia"], marker="o")
    ax[0].axvline(k, color="red", ls="--", label=f"k elegido = {k}")
    ax[0].set(xlabel="k", ylabel="Inercia (suma de distancias al cuadrado)", title="Método del codo")
    ax[1].plot(kdf["k"], kdf["silueta"], marker="o", color="tab:green")
    ax[1].axvline(k, color="red", ls="--", label=f"k elegido = {k}")
    ax[1].set(xlabel="k", ylabel="Silueta media (muestra de 10,000)", title="Coeficiente de silueta")
    for x_ in ax:
        x_.legend(); x_.grid(alpha=.3)
    fig.tight_layout()
    fig.savefig(a.salida / "p2_2_3_k.png", dpi=140)

    km = KMeans(n_clusters=k, n_init=10, random_state=SEMILLA).fit(Z)
    etiqueta_seg = km.labels_

    # PCA a dos componentes para visualizar
    pca = PCA(n_components=2, random_state=SEMILLA).fit(Z)
    P = pca.transform(Z)
    var = pca.explained_variance_ratio_
    fig, ax = plt.subplots(figsize=(8, 6))
    ver = rng.choice(len(Z), size=12_000, replace=False)
    sc = ax.scatter(P[ver, 0], P[ver, 1], c=etiqueta_seg[ver], cmap="tab10", s=5, alpha=.5)
    ax.legend(*sc.legend_elements(), title="segmento", loc="best")
    ax.set(xlabel=f"Componente 1 ({var[0]:.1%} de la varianza)", ylabel=f"Componente 2 ({var[1]:.1%})",
           title=f"Segmentos en 2 componentes PCA (varianza explicada total: {var.sum():.1%}; muestra de 12,000)")
    fig.tight_layout()
    fig.savefig(a.salida / "p2_2_3_pca.png", dpi=140)

    # tabla de segmentos: tamaño, medianas y tasa de abandono (descriptiva, no causal)
    d = X.copy()
    d["segmento"] = etiqueta_seg
    d["etiqueta"] = y
    g = d.groupby("segmento")
    tabla = pd.DataFrame({"tamano": g.size(), "pct_poblacion": g.size() / len(d),
                          "positivos": g["etiqueta"].sum(), "tasa_abandono": g["etiqueta"].mean()})
    for c in RESUMEN:
        tabla[f"mediana_{c}"] = g[c].median()
    tabla = tabla.reset_index().sort_values("tasa_abandono", ascending=False)
    tabla.to_csv(a.salida / "p2_2_3_segmentos.csv", index=False)
    cols = list(tabla.columns)
    md = ["| " + " | ".join(cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    for r in tabla.itertuples(index=False):
        md.append("| " + " | ".join(f"{v:,.4f}" if isinstance(v, float) else f"{v:,}" for v in r) + " |")
    (a.salida / "p2_2_3_segmentos.md").write_text(
        f"k = {k}; varianza explicada por 2 componentes PCA: {var[0]:.1%} + {var[1]:.1%} = {var.sum():.1%}; "
        f"tasa de abandono global del corte A: {y.mean():.4f}\n\n" + "\n".join(md) + "\n", encoding="utf-8")
    print(f"\nk={k}, varianza PCA {var[0]:.3f}+{var[1]:.3f}={var.sum():.3f}, tasa global {y.mean():.4f}")
    print(tabla.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
