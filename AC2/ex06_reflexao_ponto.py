"""
Exercicio 6 - Reflexao simples

Dado o ponto P(2, 5), aplique uma reflexao em relacao ao eixo y.
Pergunta: qual e a nova posicao do ponto P'?
"""

import numpy as np
import matplotlib.pyplot as plt

import transformacoes as T

TITULO = "Exercício 6 — Reflexão em relação ao eixo y"
ARQUIVO = "ex06_reflexao_ponto.png"


def calcular():
    P = np.array([2.0, 5.0])
    M = T.reflexao_eixo_y()
    P2 = T.aplicar(M, P)
    return {"matriz": M, "original": P, "transformado": P2}


def desenhar(ax, r=None, compacto=False):
    r = r or calcular()
    P, P2 = r["original"], r["transformado"]

    T.preparar_eixos(ax, TITULO if not compacto else "Ex. 6 — Reflexão (eixo y)",
                     P, P2, margem=1.5)
    # eixo de reflexao em destaque
    ax.axvline(0, color="purple", lw=2.2, alpha=0.6, zorder=2,
               label="eixo de reflexão (x = 0)")
    # segmento P -> P' e o pe da perpendicular
    ax.plot([P[0], P2[0]], [P[1], P2[1]], color=T.COR_APAGADO, lw=1.2,
            linestyle="--", zorder=2)
    ax.scatter([0], [P[1]], marker="|", color="purple", s=120, zorder=4)
    if not compacto:
        ax.annotate(f"d = {T.fmt(P[0])}", xy=(P[0] / 2, P[1]), xytext=(0, 5),
                    textcoords="offset points", ha="center", fontsize=8,
                    color="dimgray")
        ax.annotate(f"d = {T.fmt(P[0])}", xy=(P2[0] / 2, P[1]), xytext=(0, 5),
                    textcoords="offset points", ha="center", fontsize=8,
                    color="dimgray")

    T.desenhar_ponto(ax, P, T.COR_ORIGINAL, "Original", "P", dx=0.3, dy=0.3)
    T.desenhar_ponto(ax, P2, T.COR_TRANSFORMADO, "Transformado", "P'",
                     dx=-1.9, dy=0.3)
    if not compacto:
        T.texto_matriz(ax, r["matriz"], "F_y =", casas=0,
                       canto="inferior esquerdo")
    T.legenda(ax)


def figura(r):
    fig, ax = plt.subplots(figsize=(6.5, 6))
    desenhar(ax, r)
    fig.tight_layout()
    return fig


def executar(pasta=T.SAIDAS, mostrar=False):
    r = calcular()
    T.imprimir_resultado(TITULO, r["matriz"], r["original"], r["transformado"], ["P"])
    fig = figura(r)
    T.salvar(fig, ARQUIVO, pasta)
    if mostrar:
        plt.show()
    plt.close(fig)
    return r


if __name__ == "__main__":
    executar(mostrar=True)
