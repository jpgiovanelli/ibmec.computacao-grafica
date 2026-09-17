"""
Exercicio 1 - Translacao simples

Dado o ponto P(2, 3), aplique a translacao com vetor (4, -2).
Perguntas: qual e o novo ponto P'? Quais coordenadas foram alteradas?
"""

import numpy as np
import matplotlib.pyplot as plt

import transformacoes as T

TITULO = "Exercício 1 — Translação simples"
ARQUIVO = "ex01_translacao.png"


def calcular():
    P = np.array([2.0, 3.0])
    vetor = (4.0, -2.0)
    M = T.translacao(*vetor)
    P2 = T.aplicar(M, P)
    return {"matriz": M, "original": P, "transformado": P2, "vetor": vetor}


def desenhar(ax, r=None, compacto=False):
    r = r or calcular()
    P, P2 = r["original"], r["transformado"]
    tx, ty = r["vetor"]

    T.preparar_eixos(ax, TITULO if not compacto else "Ex. 1 — Translação",
                     P, P2, margem=1.5)

    # decomposicao do deslocamento em x e depois em y
    canto = np.array([P2[0], P[1]])
    T.desenhar_seta(ax, P, canto, cor=T.COR_APAGADO, tracejada=True,
                    texto=None if compacto else f"tx = {T.fmt(tx)}")
    T.desenhar_seta(ax, canto, P2, cor=T.COR_APAGADO, tracejada=True,
                    texto=None if compacto else f"ty = {T.fmt(ty)}")
    # vetor de translacao
    T.desenhar_seta(ax, P, P2, cor="dimgray",
                    texto=None if compacto else f"T = ({T.fmt(tx)}, {T.fmt(ty)})")

    T.desenhar_ponto(ax, P, T.COR_ORIGINAL, "Original", "P", dx=-0.9, dy=0.35)
    T.desenhar_ponto(ax, P2, T.COR_TRANSFORMADO, "Transformado", "P'", dx=0.3, dy=0.3)
    if not compacto:
        T.texto_matriz(ax, r["matriz"], "T(4, -2) =")
    T.legenda(ax)


def figura(r):
    fig, ax = plt.subplots(figsize=(6.5, 6))
    desenhar(ax, r)
    fig.tight_layout()
    return fig


def executar(pasta=T.SAIDAS, mostrar=False):
    r = calcular()
    T.imprimir_resultado(TITULO, r["matriz"], r["original"], r["transformado"], ["P"])
    print("Coordenadas alteradas: x (2 -> 6, +4) e y (3 -> 1, -2); as duas mudaram.\n")
    fig = figura(r)
    T.salvar(fig, ARQUIVO, pasta)
    if mostrar:
        plt.show()
    plt.close(fig)
    return r


if __name__ == "__main__":
    executar(mostrar=True)
