"""
Exercicio 2 - Escala uniforme

Considere um triangulo com vertices A(1, 1), B(3, 1) e C(2, 4). Aplique uma
escala uniforme de fator 2.
Perguntas: quais sao as novas coordenadas dos vertices? O que acontece com o
tamanho do triangulo?
"""

import numpy as np
import matplotlib.pyplot as plt

import transformacoes as T

TITULO = "Exercício 2 — Escala uniforme (fator 2)"
ARQUIVO = "ex02_escala_uniforme.png"
NOMES = ["A", "B", "C"]


def area(poligono):
    """Area de um poligono simples pela formula do cadarco (shoelace)."""
    P = np.asarray(poligono, float)
    x, y = P[:, 0], P[:, 1]
    return 0.5 * abs(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))


def perimetro(poligono):
    P = np.asarray(poligono, float)
    return float(np.sum(np.linalg.norm(np.roll(P, -1, axis=0) - P, axis=1)))


def calcular():
    tri = np.array([[1.0, 1.0], [3.0, 1.0], [2.0, 4.0]])
    fator = 2.0
    M = T.escala(fator)
    tri2 = T.aplicar(M, tri)
    return {"matriz": M, "original": tri, "transformado": tri2, "fator": fator,
            "area_original": area(tri), "area_transformada": area(tri2),
            "perimetro_original": perimetro(tri),
            "perimetro_transformado": perimetro(tri2)}


def desenhar(ax, r=None, compacto=False):
    r = r or calcular()
    tri, tri2 = r["original"], r["transformado"]

    T.preparar_eixos(ax, TITULO if not compacto else "Ex. 2 — Escala uniforme",
                     tri, tri2, margem=1.2)

    # raios a partir da origem: a escala "empurra" cada vertice ao longo da
    # reta que o liga a origem
    for p, p2 in zip(tri, tri2):
        ax.plot([0, p2[0]], [0, p2[1]], color=T.COR_APAGADO, lw=0.9,
                linestyle="--", zorder=1)
        T.desenhar_seta(ax, p, p2, cor=T.COR_APAGADO)

    T.desenhar_poligono(ax, tri, T.COR_ORIGINAL, "Original", NOMES)
    T.desenhar_poligono(ax, tri2, T.COR_TRANSFORMADO, "Transformado (×2)",
                        NOMES, estilo="--", sufixo="'")
    if not compacto:
        T.texto_matriz(ax, r["matriz"], "S(2, 2) =")
        ax.text(0.98, 0.02,
                f"área: {T.fmt(r['area_original'])} → "
                f"{T.fmt(r['area_transformada'])}  (×4)\n"
                f"perímetro: {T.fmt(r['perimetro_original'], 2)} → "
                f"{T.fmt(r['perimetro_transformado'], 2)}  (×2)",
                transform=ax.transAxes, fontsize=8, ha="right", va="bottom",
                bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="gray",
                          lw=0.6), zorder=7)
    T.legenda(ax, loc="upper right")


def figura(r):
    fig, ax = plt.subplots(figsize=(6.5, 6.5))
    desenhar(ax, r)
    fig.tight_layout()
    return fig


def executar(pasta=T.SAIDAS, mostrar=False):
    r = calcular()
    T.imprimir_resultado(TITULO, r["matriz"], r["original"], r["transformado"], NOMES)
    print(f"Área: {T.fmt(r['area_original'])} -> {T.fmt(r['area_transformada'])} "
          f"(x{T.fmt(r['area_transformada'] / r['area_original'])})")
    print(f"Perímetro: {T.fmt(r['perimetro_original'])} -> "
          f"{T.fmt(r['perimetro_transformado'])} "
          f"(x{T.fmt(r['perimetro_transformado'] / r['perimetro_original'])})\n")
    fig = figura(r)
    T.salvar(fig, ARQUIVO, pasta)
    if mostrar:
        plt.show()
    plt.close(fig)
    return r


if __name__ == "__main__":
    executar(mostrar=True)
