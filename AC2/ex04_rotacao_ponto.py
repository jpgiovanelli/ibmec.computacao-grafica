"""
Exercicio 4 - Rotacao em torno da origem

Rotacione o ponto P(1, 0) em 90 graus no sentido anti-horario em torno da
origem.
Pergunta: qual e a nova posicao do ponto P' apos a rotacao?
"""

import numpy as np
import matplotlib.pyplot as plt

import transformacoes as T

TITULO = "Exercício 4 — Rotação de 90° anti-horária em torno da origem"
ARQUIVO = "ex04_rotacao_ponto.png"


def calcular():
    P = np.array([1.0, 0.0])
    angulo = 90.0
    M = T.rotacao(angulo)
    P2 = T.aplicar(M, P)
    P2[np.abs(P2) < 1e-12] = 0.0        # limpa o ruido de ponto flutuante (6e-17)
    return {"matriz": M, "original": P, "transformado": P2, "angulo": angulo}


def desenhar(ax, r=None, compacto=False):
    r = r or calcular()
    P, P2 = r["original"], r["transformado"]

    T.preparar_eixos(ax, TITULO if not compacto else "Ex. 4 — Rotação de um ponto",
                     P, P2, margem=1.0)

    # circulo unitario (o raio nao muda numa rotacao)
    ts = np.linspace(0, 2 * np.pi, 200)
    ax.plot(np.cos(ts), np.sin(ts), color=T.COR_APAGADO, lw=0.8,
            linestyle=":", zorder=1)
    # raios da origem ate P e P'
    ax.plot([0, P[0]], [0, P[1]], color=T.COR_ORIGINAL, lw=1.2, zorder=2)
    ax.plot([0, P2[0]], [0, P2[1]], color=T.COR_TRANSFORMADO, lw=1.2, zorder=2)
    T.desenhar_arco_rotacao(ax, 0.55, 0, r["angulo"], texto="θ = 90°")

    T.desenhar_ponto(ax, P, T.COR_ORIGINAL, "Original", "P", dx=0.15, dy=-0.4)
    T.desenhar_ponto(ax, P2, T.COR_TRANSFORMADO, "Transformado", "P'", dx=0.15, dy=0.15)
    if not compacto:
        T.texto_matriz(ax, r["matriz"], "R(90°) =", casas=0)
    T.legenda(ax)


def figura(r):
    fig, ax = plt.subplots(figsize=(6, 6))
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
