"""
Exercicio 9 - Composicao de transformacoes

Dado o ponto P(3, 2), aplique as seguintes transformacoes consecutivas:
  1. translacao com vetor (1, -1);
  2. rotacao de 90 graus no sentido anti-horario;
  3. escala uniforme com fator 2.
Pergunta: qual e a nova posicao do ponto P' apos todas as transformacoes?

A sequencia vira uma unica matriz  M = S(2) . R(90) . T(1, -1)  — a primeira
transformacao aplicada fica mais a direita, encostada no ponto.
"""

import numpy as np
import matplotlib.pyplot as plt

import transformacoes as T

TITULO = "Exercício 9 — Composição de transformações em um ponto"
ARQUIVO = "ex09_composicao_ponto.png"


def calcular():
    P = np.array([3.0, 2.0])
    passos = [
        ("1) Translação T(1, −1)", T.translacao(1, -1)),
        ("2) Rotação R(90°)", T.rotacao(90)),
        ("3) Escala S(2)", T.escala(2)),
    ]
    trajetoria = [P]
    for _, M in passos:
        q = T.aplicar(M, trajetoria[-1])
        q[np.abs(q) < 1e-12] = 0.0
        trajetoria.append(q)
    M_total = T.compor(*[M for _, M in passos])
    P_final = T.aplicar(M_total, P)
    P_final[np.abs(P_final) < 1e-12] = 0.0
    assert np.allclose(P_final, trajetoria[-1])
    return {"matriz": M_total, "original": P, "transformado": P_final,
            "passos": passos, "trajetoria": trajetoria}


CORES = [T.COR_ORIGINAL, T.COR_INTERMEDIARIO, T.COR_INTERMEDIARIO2,
         T.COR_TRANSFORMADO]
NOMES = ["P", "P₁", "P₂", "P'"]


def _painel_passo(ax, r, i):
    """Painel do passo i (1..3): mostra o ponto antes e depois desse passo."""
    traj = r["trajetoria"]
    titulo, M = r["passos"][i - 1]
    antes, depois = traj[i - 1], traj[i]
    T.preparar_eixos(ax, titulo, *traj, margem=1.0)
    # rastro dos passos anteriores, apagado
    for j in range(i - 1):
        ax.scatter(*traj[j], color=T.COR_APAGADO, s=40, zorder=3)
        T.desenhar_seta(ax, traj[j], traj[j + 1], cor=T.COR_APAGADO, tracejada=True)
    if "Rotação" in titulo:
        raio = np.linalg.norm(antes)
        ang0 = np.degrees(np.arctan2(antes[1], antes[0]))
        T.desenhar_arco_rotacao(ax, raio, ang0, ang0 + 90, texto="+90°")
        ax.plot([0, antes[0]], [0, antes[1]], color=T.COR_APAGADO, lw=0.8, ls="--")
        ax.plot([0, depois[0]], [0, depois[1]], color=T.COR_APAGADO, lw=0.8, ls="--")
    elif "Escala" in titulo:
        ax.plot([0, depois[0]], [0, depois[1]], color=T.COR_APAGADO, lw=0.8, ls="--")
        T.desenhar_seta(ax, antes, depois, cor="dimgray")
    else:
        T.desenhar_seta(ax, antes, depois, cor="dimgray", texto="(1, −1)")
    T.desenhar_ponto(ax, antes, CORES[i - 1], "antes", NOMES[i - 1], dx=0.3, dy=0.3)
    T.desenhar_ponto(ax, depois, CORES[i], "depois", NOMES[i], dx=0.3, dy=0.3)
    T.texto_matriz(ax, M, "M =", casas=0, canto="inferior esquerdo")
    T.legenda(ax)


def desenhar(ax, r=None, compacto=False):
    """Painel-resumo: P -> P1 -> P2 -> P' e a matriz composta."""
    r = r or calcular()
    traj = r["trajetoria"]
    T.preparar_eixos(ax, "Resumo — P' = S·R·T·P" if not compacto
                     else "Ex. 9 — Composição (ponto)", *traj, margem=1.0)
    for j in range(3):
        T.desenhar_seta(ax, traj[j], traj[j + 1], cor="dimgray", tracejada=True)
    for j, (p, nome, cor) in enumerate(zip(traj, NOMES, CORES)):
        rot = "Original" if j == 0 else ("Final" if j == 3 else None)
        if j in (0, 3):
            T.desenhar_ponto(ax, p, cor, rot, nome, dx=0.3, dy=0.3)
        else:
            ax.scatter(*p, color=cor, s=45, zorder=5)
            ax.annotate(f"{nome}{T.fmt_ponto(p)}", xy=p, xytext=(p[0] + 0.3, p[1] + 0.3),
                        fontsize=8, color=cor, zorder=6)
    if not compacto:
        T.texto_matriz(ax, r["matriz"], "M = S·R·T =", casas=0,
                       canto="inferior esquerdo")
    T.legenda(ax)


def figura(r):
    fig, axs = plt.subplots(2, 2, figsize=(12, 11))
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
    traj = r["trajetoria"]
    print(f"  P{T.fmt_ponto(traj[0])}")
    for (titulo, M), q in zip(r["passos"], traj[1:]):
        print(f"  {titulo:<26} -> {T.fmt_ponto(q)}")
    print("\nMatriz composta M = S . R . T:")
    print(T.fmt_matriz(r["matriz"]))
    print(f"\n  P' = M . P = {T.fmt_ponto(r['transformado'])}\n")
    fig = figura(r)
    T.salvar(fig, ARQUIVO, pasta)
    if mostrar:
        plt.show()
    plt.close(fig)
    return r


if __name__ == "__main__":
    executar(mostrar=True)
