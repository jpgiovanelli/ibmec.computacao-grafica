"""
=============================================================================
 AREA 1 - SINTESE DE IMAGENS
 Experimento: convergencia de Monte Carlo (ruido x numero de amostras)
=============================================================================

O path tracer resolve a EQUACAO DE RENDERIZACAO (Kajiya, 1986) por integracao
numerica de Monte Carlo. O erro do estimador cai com O(1/sqrt(N)), onde N e o
numero de amostras por pixel: para reduzir o ruido pela metade e preciso
QUADRUPLICAR o numero de amostras.

Este script renderiza a mesma cena com 1, 4, 16 e 64 amostras/pixel e monta
um painel comparativo, evidenciando esse comportamento - um aspecto que so
existe na sintese de imagens (nao ha "ruido de amostragem" em processamento
de imagens ou em visao computacional).

USO:
    python convergencia_amostras.py
"""

import os
import time

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from raytracer import renderizar  # noqa: E402


def main():
    largura, spps = 300, [1, 4, 16, 64]
    imagens, tempos = [], []

    print("=" * 70)
    print(" AREA 1 - SINTESE | Convergencia de Monte Carlo")
    print("=" * 70)

    for spp in spps:
        t0 = time.time()
        img = renderizar(largura, int(round(largura * 9 / 16)), spp, 8)
        dt = time.time() - t0
        imagens.append(img)
        tempos.append(dt)
        print(f"  {spp:3d} amostras/pixel -> {dt:6.2f}s")

    referencia = imagens[-1].astype(np.float64)
    fig, eixos = plt.subplots(2, 2, figsize=(11, 6.8), constrained_layout=True)
    for eixo, img, spp, dt in zip(eixos.ravel(), imagens, spps, tempos):
        erro = np.sqrt(np.mean((img.astype(np.float64) - referencia) ** 2))
        rotulo = ("(referencia)" if spp == spps[-1] else f"RMSE={erro:5.1f}")
        eixo.imshow(img)
        eixo.set_title(f"{spp} amostra(s)/pixel | {dt:.1f}s | {rotulo}",
                       fontsize=10)
        eixo.axis("off")
    fig.suptitle("Ruido de amostragem em Monte Carlo: erro ~ O(1/raiz(N))",
                 fontsize=13, fontweight="bold")

    raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    destino = os.path.join(raiz, "saidas", "01_sintese", "convergencia_monte_carlo.png")
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    fig.savefig(destino, dpi=110, facecolor="white")
    plt.close(fig)
    print(f"  Imagem salva em: {destino}")
    print("=" * 70)


if __name__ == "__main__":
    main()
