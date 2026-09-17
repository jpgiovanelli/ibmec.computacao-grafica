"""
Executa os dez exercicios do AC02 em sequencia e regrava a pasta saidas/.

USO:
    python run_all.py            # gera todas as figuras + respostas.json
    python run_all.py --mostrar  # idem, abrindo cada figura numa janela

Alem das figuras de cada exercicio, este script produz:
    saidas/respostas.json          coordenadas e matrizes de todos os exercicios
    saidas/painel_geral.png        os dez exercicios numa unica imagem
    saidas/extra_ordem_importa.png a mesma sequencia do Ex. 9 em ordem invertida
"""

import argparse
import json
import sys
import time

import numpy as np
import matplotlib

if "--mostrar" not in sys.argv:
    matplotlib.use("Agg")          # sem janelas: so grava arquivos

import matplotlib.pyplot as plt    # noqa: E402

import transformacoes as T         # noqa: E402
import ex01_translacao             # noqa: E402
import ex02_escala_uniforme        # noqa: E402
import ex03_escala_nao_uniforme    # noqa: E402
import ex04_rotacao_ponto          # noqa: E402
import ex05_rotacao_quadrado       # noqa: E402
import ex06_reflexao_ponto         # noqa: E402
import ex07_reflexao_triangulo     # noqa: E402
import ex08_cisalhamento           # noqa: E402
import ex09_composicao_ponto       # noqa: E402
import ex10_composicao_retangulo   # noqa: E402

EXERCICIOS = [
    ex01_translacao, ex02_escala_uniforme, ex03_escala_nao_uniforme,
    ex04_rotacao_ponto, ex05_rotacao_quadrado, ex06_reflexao_ponto,
    ex07_reflexao_triangulo, ex08_cisalhamento, ex09_composicao_ponto,
    ex10_composicao_retangulo,
]


def para_json(obj):
    """Converte arrays NumPy (e tuplas de passos) para tipos serializaveis."""
    if isinstance(obj, np.ndarray):
        return np.round(obj, 6).tolist()
    if isinstance(obj, (np.floating, float)):
        return round(float(obj), 6)
    if isinstance(obj, (np.integer, int)):
        return int(obj)
    if isinstance(obj, dict):
        return {k: para_json(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [para_json(v) for v in obj]
    return obj


def painel_geral(resultados, pasta):
    """Os dez exercicios numa grade 2 x 5, usando o painel principal de cada um."""
    fig, axs = plt.subplots(2, 5, figsize=(26, 11))
    for ax, mod, r in zip(axs.ravel(), EXERCICIOS, resultados):
        mod.desenhar(ax, r, compacto=True)
    fig.suptitle("AC02 — Transformações geométricas 2D: os dez exercícios",
                 fontsize=16)
    fig.tight_layout()
    T.salvar(fig, "painel_geral.png", pasta)
    plt.close(fig)


def extra_ordem_importa(pasta):
    """Ex. 9 na ordem pedida (T, R, S) e na ordem inversa (S, R, T): o
    resultado muda porque o produto de matrizes nao e comutativo."""
    P = np.array([3.0, 2.0])
    Tm, Rm, Sm = T.translacao(1, -1), T.rotacao(90), T.escala(2)
    ordens = [("Ordem do enunciado:  T → R → S   (M = S·R·T)", [Tm, Rm, Sm]),
              ("Ordem invertida:  S → R → T   (M = T·R·S)", [Sm, Rm, Tm])]
    fig, axs = plt.subplots(1, 2, figsize=(13, 6))
    for ax, (titulo, seq) in zip(axs, ordens):
        traj = [P]
        for M in seq:
            q = T.aplicar(M, traj[-1])
            q[np.abs(q) < 1e-12] = 0.0
            traj.append(q)
        M_total = T.compor(*seq)
        T.preparar_eixos(ax, titulo, *traj, margem=1.0)
        cores = [T.COR_ORIGINAL, T.COR_INTERMEDIARIO, T.COR_INTERMEDIARIO2,
                 T.COR_TRANSFORMADO]
        nomes = ["P", "P₁", "P₂", "P'"]
        for j in range(3):
            T.desenhar_seta(ax, traj[j], traj[j + 1], cor="dimgray", tracejada=True)
        for j, (p, n, c) in enumerate(zip(traj, nomes, cores)):
            if j in (0, 3):
                T.desenhar_ponto(ax, p, c, "Original" if j == 0 else "Final", n,
                                 dx=0.3, dy=0.3)
            else:
                ax.scatter(*p, color=c, s=45, zorder=5)
                ax.annotate(f"{n}{T.fmt_ponto(p)}", xy=p,
                            xytext=(p[0] + 0.3, p[1] + 0.3), fontsize=8, color=c)
        T.texto_matriz(ax, M_total, "M =", casas=0, canto="inferior esquerdo")
        T.legenda(ax)
    fig.suptitle("Extra — a ordem das transformações importa (M₂·M₁ ≠ M₁·M₂)",
                 fontsize=13)
    fig.tight_layout()
    T.salvar(fig, "extra_ordem_importa.png", pasta)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mostrar", action="store_true",
                    help="abre cada figura numa janela alem de grava-la")
    args = ap.parse_args()

    pasta = T.SAIDAS
    pasta.mkdir(exist_ok=True)

    resultados = []
    t0 = time.time()
    for mod in EXERCICIOS:
        resultados.append(mod.executar(pasta, mostrar=args.mostrar))

    print("#" * 66)
    print("# Painel geral e figura extra")
    print("#" * 66)
    painel_geral(resultados, pasta)
    extra_ordem_importa(pasta)

    respostas = {}
    for mod, r in zip(EXERCICIOS, resultados):
        r = dict(r)
        if "passos" in r:      # (titulo, matriz) -> {"titulo":..., "matriz":...}
            r["passos"] = [{"titulo": t, "matriz": M} for t, M in r["passos"]]
        respostas[mod.__name__] = {"titulo": mod.TITULO, **para_json(r)}
    with open(pasta / "respostas.json", "w", encoding="utf-8") as f:
        json.dump(respostas, f, ensure_ascii=False, indent=2)
    print(f"respostas gravadas em: saidas/respostas.json")
    print(f"\nconcluido em {time.time() - t0:.1f} s")


if __name__ == "__main__":
    main()
