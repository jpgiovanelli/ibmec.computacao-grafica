"""
Exercicio 3 - Escala nao uniforme

Aplique uma escala nao uniforme no triangulo do Exercicio 2 (A(1, 1), B(3, 1),
C(2, 4)), com fator 2 no eixo x e fator 0,5 no eixo y.
Pergunta: quais sao as novas coordenadas dos vertices?
"""

import numpy as np
import matplotlib.pyplot as plt

import transformacoes as T
from ex02_escala_uniforme import area, perimetro

TITULO = "Exercício 3 — Escala não uniforme (sx = 2, sy = 0,5)"
ARQUIVO = "ex03_escala_nao_uniforme.png"
NOMES = ["A", "B", "C"]


def calcular():
    tri = np.array([[1.0, 1.0], [3.0, 1.0], [2.0, 4.0]])
    sx, sy = 2.0, 0.5
    M = T.escala(sx, sy)
    tri2 = T.aplicar(M, tri)
    return {"matriz": M, "original": tri, "transformado": tri2,
            "fatores": (sx, sy),
            "area_original": area(tri), "area_transformada": area(tri2),
            "perimetro_original": perimetro(tri),
            "perimetro_transformado": perimetro(tri2)}


def desenhar(ax, r=None, compacto=False):
    r = r or calcular()
    tri, tri2 = r["original"], r["transformado"]

    T.preparar_eixos(ax, TITULO if not compacto else "Ex. 3 — Escala não uniforme",
                     tri, tri2, margem=1.2)

    for p, p2 in zip(tri, tri2):
        T.desenhar_seta(ax, p, p2, cor=T.COR_APAGADO, tracejada=True)

    T.desenhar_poligono(ax, tri, T.COR_ORIGINAL, "Original", NOMES)
    T.desenhar_poligono(ax, tri2, T.COR_TRANSFORMADO,
                        "Transformado (×2 em x, ×0,5 em y)", NOMES,
                        estilo="--", sufixo="'")
    if not compacto:
        T.texto_matriz(ax, r["matriz"], "S(2, 0.5) =")
        ax.text(0.98, 0.02,
                f"área: {T.fmt(r['area_original'])} → "
                f"{T.fmt(r['area_transformada'])}  (×(2·0,5) = ×1)\n"
                "largura ×2, altura ×0,5",
                transform=ax.transAxes, fontsize=8, ha="right", va="bottom",
                bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="gray",
                          lw=0.6), zorder=7)
    T.legenda(ax, loc="upper right")


def figura(r):
    fig, ax = plt.subplots(figsize=(7, 5.5))
    desenhar(ax, r)
    fig.tight_layout()
    return fig


def executar(pasta=T.SAIDAS, mostrar=False):
    r = calcular()
    T.imprimir_resultado(TITULO, r["matriz"], r["original"], r["transformado"], NOMES)
    print(f"Área: {T.fmt(r['area_original'])} -> {T.fmt(r['area_transformada'])} "
          f"(x{T.fmt(r['area_transformada'] / r['area_original'])}, "
          f"pois sx*sy = 2*0.5 = 1)\n")
    fig = figura(r)
    T.salvar(fig, ARQUIVO, pasta)
    if mostrar:
        plt.show()
    plt.close(fig)
    return r


if __name__ == "__main__":
    executar(mostrar=True)
