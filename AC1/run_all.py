"""
Executa TODOS os experimentos do trabalho, na ordem, e mede o tempo de cada um.

USO:
    python run_all.py              # execucao completa
    python run_all.py --rapido     # render do ray tracer em qualidade menor
"""

import argparse
import os
import subprocess
import sys
import time

RAIZ = os.path.dirname(os.path.abspath(__file__))

EXPERIMENTOS = [
    ("00_comparativo", "diagrama_areas.py", [], "Diagramas comparativos"),
    ("01_sintese_de_imagens", "raytracer.py",
     ["--largura", "480", "--spp", "128"], "Area 1 - Path tracer"),
    ("01_sintese_de_imagens", "rasterizador.py", [], "Area 1 - Rasterizador"),
    ("01_sintese_de_imagens", "convergencia_amostras.py", [],
     "Area 1 - Convergencia de Monte Carlo"),
    ("02_processamento_de_imagens", "processamento.py", [],
     "Area 2 - Processamento de imagens"),
    ("03_visao_computacional", "visao.py", [], "Area 3 - Visao computacional"),
    ("04_visualizacao_computacional", "visualizacao.py", [],
     "Area 4 - Visualizacao computacional"),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rapido", action="store_true",
                    help="reduz a qualidade do ray tracer (execucao mais rapida)")
    args = ap.parse_args()

    tempos = []
    for pasta, script, extras, descricao in EXPERIMENTOS:
        if args.rapido and script == "raytracer.py":
            extras = ["--largura", "300", "--spp", "32"]

        print("\n" + "#" * 70)
        print(f"# {descricao}")
        print(f"# {pasta}/{script} {' '.join(extras)}")
        print("#" * 70)

        t0 = time.time()
        resultado = subprocess.run([sys.executable, script] + extras,
                                   cwd=os.path.join(RAIZ, pasta))
        dt = time.time() - t0
        tempos.append((descricao, dt, resultado.returncode))
        if resultado.returncode != 0:
            print(f"!! falhou: {pasta}/{script}")

    print("\n" + "=" * 70)
    print(" RESUMO DA EXECUCAO")
    print("=" * 70)
    for descricao, dt, codigo in tempos:
        estado = "ok " if codigo == 0 else "ERRO"
        print(f"  [{estado}] {descricao:45s} {dt:7.1f}s")
    print("-" * 70)
    print(f"  Tempo total: {sum(t for _, t, _ in tempos):.1f}s")
    print(f"  Saidas em:   {os.path.join(RAIZ, 'saidas')}")
    print("=" * 70)


if __name__ == "__main__":
    main()
