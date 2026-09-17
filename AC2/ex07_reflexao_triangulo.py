"""
Exercicio 7 - Reflexao de um triangulo

Considere um triangulo com vertices A(2, 3), B(4, 3) e C(3, 5). Aplique uma
reflexao em relacao ao eixo x.
Pergunta: quais sao as novas coordenadas dos vertices apos a transformacao?
"""

import numpy as np
import matplotlib.pyplot as plt

import transformacoes as T

TITULO = "Exercício 7 — Reflexão de um triângulo em relação ao eixo x"
ARQUIVO = "ex07_reflexao_triangulo.png"
NOMES = ["A", "B", "C"]


def calcular():
    tri = np.array([[2.0, 3.0], [4.0, 3.0], [3.0, 5.0]])
    M = T.reflexao_eixo_x()
    tri2 = T.aplicar(M, tri)
    return {"matriz": M, "original": tri, "transformado": tri2}


def desenhar(ax, r=None, compacto=False):
    r = r or calcular()
    tri, tri2 = r["original"], r["transformado"]

    T.preparar_eixos(ax, TITULO if not compacto else "Ex. 7 — Reflexão (eixo x)",
                     tri, tri2, margem=1.2)
    ax.axhline(0, color="purple", lw=2.2, alpha=0.6, zorder=2,
               label="eixo de reflexão (y = 0)")
    # cada vertice e ligado a sua imagem por uma perpendicular ao eixo
    for p, p2 in zip(tri, tri2):
        ax.plot([p[0], p2[0]], [p[1], p2[1]], color=T.COR_APAGADO, lw=1.0,
                linestyle="--", zorder=2)

    T.desenhar_poligono(ax, tri, T.COR_ORIGINAL, "Original", NOMES)
    T.desenhar_poligono(ax, tri2, T.COR_TRANSFORMADO, "Refletido", NOMES,
                        estilo="--", sufixo="'")
    if not compacto:
        T.texto_matriz(ax, r["matriz"], "F_x =", casas=0,
                       canto="inferior esquerdo")
    T.legenda(ax, loc="upper left")


def figura(r):
    fig, ax = plt.subplots(figsize=(6.5, 7))
    desenhar(ax, r)
    fig.tight_layout()
    return fig


def executar(pasta=T.SAIDAS, mostrar=False):
    r = calcular()
    T.imprimir_resultado(TITULO, r["matriz"], r["original"], r["transformado"], NOMES)
    fig = figura(r)
    T.salvar(fig, ARQUIVO, pasta)
    if mostrar:
        plt.show()
    plt.close(fig)
    return r


if __name__ == "__main__":
    executar(mostrar=True)
