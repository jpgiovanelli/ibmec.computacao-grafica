"""
Exercicio 5 - Rotacao de um poligono

Um quadrado tem vertices A(1, 1), B(1, 4), C(4, 4), D(4, 1). Aplique uma
rotacao de 45 graus no sentido horario.
Pergunta: quais sao as novas coordenadas dos vertices?

Como o enunciado nao fixa o ponto de referencia, a resposta principal usa a
origem (a rotacao R(theta) da aula). Como complemento, o segundo painel mostra
a rotacao em torno do centro do quadrado, feita com a composicao
T(c) . R(-45) . T(-c) dos slides ("rotacao com ponto de referencia").
"""

import numpy as np
import matplotlib.pyplot as plt

import transformacoes as T

TITULO = "Exercício 5 — Rotação de 45° no sentido horário"
ARQUIVO = "ex05_rotacao_quadrado.png"
NOMES = ["A", "B", "C", "D"]


def calcular():
    quad = np.array([[1.0, 1.0], [1.0, 4.0], [4.0, 4.0], [4.0, 1.0]])
    angulo = -45.0                              # horario = angulo negativo
    M = T.rotacao(angulo)
    quad2 = T.aplicar(M, quad)
    quad2[np.abs(quad2) < 1e-12] = 0.0

    # complemento: mesma rotacao, mas em torno do centro do quadrado
    centro = quad.mean(axis=0)                  # (2.5, 2.5)
    M_centro = T.compor(T.translacao(-centro[0], -centro[1]),
                        T.rotacao(angulo),
                        T.translacao(centro[0], centro[1]))
    quad_centro = T.aplicar(M_centro, quad)
    return {"matriz": M, "original": quad, "transformado": quad2,
            "angulo": angulo, "centro": centro,
            "matriz_centro": M_centro, "transformado_centro": quad_centro}


def desenhar(ax, r=None, compacto=False):
    """Painel principal: rotacao em torno da origem."""
    r = r or calcular()
    quad, quad2 = r["original"], r["transformado"]

    T.preparar_eixos(ax, (TITULO + "\n(em torno da origem)") if not compacto
                     else "Ex. 5 — Rotação de 45° horária", quad, quad2,
                     margem=1.0)

    # arco que leva o vertice C (a 45 graus) ate C' (sobre o eixo x)
    raio_c = np.linalg.norm(quad[2])
    T.desenhar_arco_rotacao(ax, raio_c, 45, 0, texto="−45°")
    ax.plot([0, quad[2][0]], [0, quad[2][1]], color=T.COR_APAGADO, lw=0.9,
            linestyle="--", zorder=1)
    ax.plot([0, quad2[2][0]], [0, quad2[2][1]], color=T.COR_APAGADO, lw=0.9,
            linestyle="--", zorder=1)

    T.desenhar_poligono(ax, quad, T.COR_ORIGINAL, "Original", NOMES)
    T.desenhar_poligono(ax, quad2, T.COR_TRANSFORMADO, "Rotacionado (−45°)",
                        NOMES, estilo="--", sufixo="'")
    if not compacto:
        T.texto_matriz(ax, r["matriz"], "R(−45°) =", canto="inferior direito")
    T.legenda(ax, loc="lower left")


def desenhar_centro(ax, r=None):
    """Painel complementar: rotacao em torno do centro (2.5, 2.5)."""
    r = r or calcular()
    quad, quad_c, c = r["original"], r["transformado_centro"], r["centro"]

    T.preparar_eixos(ax, "Complemento — mesma rotação em torno do\ncentro do "
                     f"quadrado c = {T.fmt_ponto(c)}", quad, quad_c, margem=1.0)
    ax.scatter([c[0]], [c[1]], marker="x", color="black", s=50, zorder=6)
    ax.annotate("c", xy=c, xytext=(c[0] + 0.15, c[1] + 0.15), fontsize=9)
    T.desenhar_arco_rotacao(ax, np.linalg.norm(quad[2] - c), 45, 0,
                            centro=c, texto="−45°")

    T.desenhar_poligono(ax, quad, T.COR_ORIGINAL, "Original", NOMES)
    T.desenhar_poligono(ax, quad_c, T.COR_INTERMEDIARIO,
                        "Rotacionado em torno de c", NOMES, estilo="--",
                        sufixo="'")
    T.texto_matriz(ax, r["matriz_centro"], "T(c)·R(−45°)·T(−c) =",
                   canto="inferior direito")
    T.legenda(ax, loc="lower left")


def figura(r):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 6))
    desenhar(ax1, r)
    desenhar_centro(ax2, r)
    fig.tight_layout()
    return fig


def executar(pasta=T.SAIDAS, mostrar=False):
    r = calcular()
    T.imprimir_resultado(TITULO + " (em torno da origem)", r["matriz"],
                         r["original"], r["transformado"], NOMES)
    T.imprimir_resultado("Complemento: em torno do centro (2.5, 2.5)",
                         r["matriz_centro"], r["original"],
                         r["transformado_centro"], NOMES)
    fig = figura(r)
    T.salvar(fig, ARQUIVO, pasta)
    if mostrar:
        plt.show()
    plt.close(fig)
    return r


if __name__ == "__main__":
    executar(mostrar=True)
