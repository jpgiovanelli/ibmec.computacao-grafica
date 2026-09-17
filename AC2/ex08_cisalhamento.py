"""
Exercicio 8 - Cisalhamento horizontal

Dado o ponto P(2, 3), aplique um cisalhamento horizontal com k = 2.
Pergunta: qual e a nova posicao do ponto P'?

No cisalhamento horizontal x' = x + k*y e y' = y: cada ponto e deslocado em x
de uma quantidade proporcional a sua altura y. Para deixar isso visivel, a
figura tambem cisalha o retangulo [0, 2] x [0, 3] que tem P como canto.
"""

import numpy as np
import matplotlib.pyplot as plt

import transformacoes as T

TITULO = "Exercício 8 — Cisalhamento horizontal (k = 2)"
ARQUIVO = "ex08_cisalhamento.png"


def calcular():
    P = np.array([2.0, 3.0])
    k = 2.0
    M = T.cisalhamento(kx=k)
    P2 = T.aplicar(M, P)
    # retangulo de apoio, so para ilustrar a deformacao
    ret = np.array([[0.0, 0.0], [P[0], 0.0], [P[0], P[1]], [0.0, P[1]]])
    ret2 = T.aplicar(M, ret)
    return {"matriz": M, "original": P, "transformado": P2, "k": k,
            "retangulo": ret, "retangulo_cisalhado": ret2}


def desenhar(ax, r=None, compacto=False):
    r = r or calcular()
    P, P2, k = r["original"], r["transformado"], r["k"]

    T.preparar_eixos(ax, TITULO if not compacto else "Ex. 8 — Cisalhamento",
                     P, P2, r["retangulo_cisalhado"], margem=1.0)

    # retangulo de apoio e sua versao cisalhada (paralelogramo)
    T.desenhar_poligono(ax, r["retangulo"], T.COR_ORIGINAL,
                        "retângulo de apoio", rotular=False, largura=1.0,
                        alpha=0.5)
    T.desenhar_poligono(ax, r["retangulo_cisalhado"], T.COR_TRANSFORMADO,
                        "retângulo cisalhado", rotular=False, largura=1.0,
                        estilo="--", alpha=0.5)
    # linhas horizontais em alturas intermediarias: quanto maior y, maior o
    # deslocamento em x
    for y in np.linspace(0, P[1], 4)[1:]:
        ax.plot([0, k * y], [y, y], color=T.COR_APAGADO, lw=0.8,
                linestyle=":", zorder=1)

    T.desenhar_seta(ax, P, P2, cor="dimgray",
                    texto=None if compacto else f"k·y = {T.fmt(k)}·{T.fmt(P[1])} = {T.fmt(k * P[1])}")
    T.desenhar_ponto(ax, P, T.COR_ORIGINAL, "Original", "P", dx=-0.5, dy=0.35)
    T.desenhar_ponto(ax, P2, T.COR_TRANSFORMADO, "Transformado", "P'",
                     dx=0.25, dy=0.35)
    if not compacto:
        T.texto_matriz(ax, r["matriz"], "H(k = 2) =", casas=0)
    T.legenda(ax)


def figura(r):
    fig, ax = plt.subplots(figsize=(8, 5))
    desenhar(ax, r)
    fig.tight_layout()
    return fig


def executar(pasta=T.SAIDAS, mostrar=False):
    r = calcular()
    T.imprimir_resultado(TITULO, r["matriz"], r["original"], r["transformado"], ["P"])
    print("x' = x + k*y = 2 + 2*3 = 8 ;  y' = y = 3\n")
    fig = figura(r)
    T.salvar(fig, ARQUIVO, pasta)
    if mostrar:
        plt.show()
    plt.close(fig)
    return r


if __name__ == "__main__":
    executar(mostrar=True)
