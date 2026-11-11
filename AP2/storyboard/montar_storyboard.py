"""
Monta o storyboard ATUALIZADO da AP2 (storyboard_ap2.png) com quadros reais do
render final (sb_XXXX.jpg = quadro XXXX da animacao, 1280x720).

Uso:  python AP2/storyboard/montar_storyboard.py      (requer matplotlib)
"""

from pathlib import Path

import matplotlib.image as mpimg
import matplotlib.pyplot as plt

PASTA = Path(__file__).resolve().parent

PLANOS = [
    ("sb_0040.jpg", "Plano 1 · Início", "quadro 40 (1,6 s)",
     "Fade-in. Câmera baixa (28 mm) rente às páginas,\n"
     "deslizando para a direita. Os blocos caem um a um\n"
     "sobre o livro e quicam (BOUNCE)."),
    ("sb_0110.jpg", "Plano 1 · Base pronta", "quadro 110 (4,6 s)",
     "Os 26 blocos formam a base. A câmera começa a\n"
     "subir e fechar (28 → 35 mm) em direção à palavra."),
    ("sb_0164.jpg", "Plano 2 · Construção", "quadro 164 (6,8 s)",
     "Close frontal. As letras crescem dos blocos\n"
     "(escala vertical 0 → 1 com overshoot: BACK),\n"
     "uma a cada 16 quadros: I, b, m, e, c."),
    ("sb_0240.jpg", "Plano 2 · Palavra completa", "quadro 240 (10 s)",
     "\"Ibmec\" completa e legível. Ao fundo, a ponte\n"
     "começa a se estender tábua por tábua e a câmera\n"
     "inicia o recuo."),
    ("sb_0290.jpg", "Plano 3 · Encerramento", "quadro 290 (12,1 s)",
     "A câmera recua e sobe. A torre se ergue no fim da\n"
     "ponte e torce (Twist 0° → 75°)."),
    ("sb_0360.jpg", "Plano 3 · Composição final", "quadros 326–360 (13,6–15 s)",
     "Enquadramento principal da AP1 (CAM_Principal,\n"
     "26 mm). As janelas da torre acendem. Câmera\n"
     "parada nos últimos 1,4 s."),
]


def main():
    fig, eixos = plt.subplots(2, 3, figsize=(18, 10.6))
    fig.suptitle("AP2 · Storyboard atualizado — \"Ibmec em 15 segundos\" (quadros reais do render, "
                 "360 quadros a 24 fps)", fontsize=15, fontweight="bold", y=0.985)
    for ax, (arquivo, titulo, tempo, texto) in zip(eixos.flat, PLANOS):
        ax.imshow(mpimg.imread(PASTA / arquivo))
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_title(f"{titulo}\n{tempo}", fontsize=12, loc="left")
        ax.text(0.0, -0.04, texto, transform=ax.transAxes, va="top", fontsize=10.5)
    fig.subplots_adjust(left=0.02, right=0.98, top=0.88, bottom=0.08, wspace=0.05, hspace=0.42)
    saida = PASTA / "storyboard_ap2.png"
    fig.savefig(saida, dpi=110)
    print("salvo:", saida)


if __name__ == "__main__":
    main()
