"""
Exercicio 10 - Combinacao de transformacoes em uma figura

Dado um retangulo com vertices A(1, 1), B(5, 1), C(5, 3), D(1, 3), aplique em
sequencia:
  1. translacao com vetor (-2, 3);
  2. escala nao uniforme com fatores 1,5 no eixo x e 0,5 no eixo y;
  3. reflexao em relacao ao eixo y.
Pergunta: quais sao as novas coordenadas dos vertices apos as tres
transformacoes?

A sequencia vira a matriz  M = F_y . S(1.5, 0.5) . T(-2, 3).
"""

import numpy as np
import matplotlib.pyplot as plt

import transformacoes as T

TITULO = "Exercício 10 — Combinação de transformações em um retângulo"
ARQUIVO = "ex10_composicao_retangulo.png"
NOMES = ["A", "B", "C", "D"]


def calcular():
    ret = np.array([[1.0, 1.0], [5.0, 1.0], [5.0, 3.0], [1.0, 3.0]])
    passos = [
        ("1) Translação T(−2, 3)", T.translacao(-2, 3)),
        ("2) Escala S(1,5; 0,5)", T.escala(1.5, 0.5)),
        ("3) Reflexão no eixo y (F_y)", T.reflexao_eixo_y()),
    ]
    etapas = [ret]
    for _, M in passos:
        etapas.append(T.aplicar(M, etapas[-1]))
    M_total = T.compor(*[M for _, M in passos])
    ret_final = T.aplicar(M_total, ret)
    assert np.allclose(ret_final, etapas[-1])
    return {"matriz": M_total, "original": ret, "transformado": ret_final,
            "passos": passos, "etapas": etapas}


CORES = [T.COR_ORIGINAL, T.COR_INTERMEDIARIO, T.COR_INTERMEDIARIO2,
         T.COR_TRANSFORMADO]
SUFIXOS = ["", "₁", "₂", "'"]


def _painel_passo(ax, r, i):
    """Painel do passo i (1..3): figura antes e depois desse passo."""
    etapas = r["etapas"]
    titulo, M = r["passos"][i - 1]
    antes, depois = etapas[i - 1], etapas[i]
    T.preparar_eixos(ax, titulo, *etapas, margem=1.0)
    # etapas anteriores, apagadas
    for j in range(i - 1):
        T.desenhar_poligono(ax, etapas[j], T.COR_APAGADO, None, rotular=False,
                            largura=1.0, alpha=0.6, preencher=False)
    if "Reflexão" in titulo:
        ax.axvline(0, color="purple", lw=2.2, alpha=0.5, zorder=2)
        for p, p2 in zip(antes, depois):
            ax.plot([p[0], p2[0]], [p[1], p2[1]], color=T.COR_APAGADO, lw=0.8, ls="--")
    else:
        for p, p2 in zip(antes, depois):
            T.desenhar_seta(ax, p, p2, cor=T.COR_APAGADO, tracejada=True)
    T.desenhar_poligono(ax, antes, CORES[i - 1], "antes", NOMES,
                        sufixo=SUFIXOS[i - 1])
    T.desenhar_poligono(ax, depois, CORES[i], "depois", NOMES, estilo="--",
                        sufixo=SUFIXOS[i])
    T.texto_matriz(ax, M, "M =", casas=1, canto="inferior esquerdo")
    T.legenda(ax)


def desenhar(ax, r=None, compacto=False):
    """Painel-resumo: original, final e a matriz composta."""
    r = r or calcular()
    etapas = r["etapas"]
    T.preparar_eixos(ax, "Resumo — P' = F_y·S·T·P" if not compacto
                     else "Ex. 10 — Composição (retângulo)", *etapas, margem=1.0)
    for j in (1, 2):
        T.desenhar_poligono(ax, etapas[j], CORES[j], f"etapa {j}", rotular=False,
                            largura=1.0, alpha=0.5, preencher=False, estilo=":")
    T.desenhar_poligono(ax, etapas[0], T.COR_ORIGINAL, "Original", NOMES)
    T.desenhar_poligono(ax, etapas[3], T.COR_TRANSFORMADO, "Final", NOMES,
                        estilo="--", sufixo="'")
    if not compacto:
        T.texto_matriz(ax, r["matriz"], "M = F_y·S·T =", casas=1,
                       canto="inferior esquerdo")
    T.legenda(ax, loc="upper right" if compacto else "lower right")


def figura(r):
    fig, axs = plt.subplots(2, 2, figsize=(13, 10))
    axs = axs.ravel()
    for i in (1, 2, 3):
        _painel_passo(axs[i - 1], r, i)
    desenhar(axs[3], r)
    fig.suptitle(TITULO, fontsize=13)
    fig.tight_layout()
    return fig


def executar(pasta=T.SAIDAS, mostrar=False):
    r = calcular()
    print("=" * 66)
    print(TITULO)
    print("=" * 66)
    etapas = r["etapas"]
    cab = ["original"] + [t for t, _ in r["passos"]]
    for titulo, e in zip(cab, etapas):
        print(f"  {titulo:<28} " + "  ".join(
            f"{n}{T.fmt_ponto(p)}" for n, p in zip(NOMES, e)))
    print("\nMatriz composta M = F_y . S . T:")
    print(T.fmt_matriz(r["matriz"]))
    print()
    for n, a, d in zip(NOMES, r["original"], r["transformado"]):
        print(f"  {n}{T.fmt_ponto(a):<14} ->  {n}'{T.fmt_ponto(d)}")
    print()
    fig = figura(r)
    T.salvar(fig, ARQUIVO, pasta)
    if mostrar:
        plt.show()
    plt.close(fig)
    return r


if __name__ == "__main__":
    executar(mostrar=True)
