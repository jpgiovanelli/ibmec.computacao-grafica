"""
Monta a prancha do storyboard da AP1 (storyboard.png) a partir das tres
capturas de viewport feitas pelas cameras CAM_SB_* do arquivo .blend.

Uso:  python montar_storyboard.py      (requer matplotlib)
"""

from pathlib import Path

import matplotlib.image as mpimg
import matplotlib.pyplot as plt

PASTA = Path(__file__).resolve().parent

MOMENTOS = [
    ("sb_01_inicio.png", "1. Início", "0 s – 5 s  ·  frames 1–120",
     "Câmera baixa desliza rente às páginas do livro aberto.\n"
     "Os blocos amarelos surgem um a um sobre as folhas:\n"
     "o conhecimento como base da construção."),
    ("sb_02_construcao.png", "2. Construção da palavra", "5 s – 11 s  ·  frames 121–264",
     "As letras de \"Ibmec\" sobem dos blocos (escala Z de 0 a 1),\n"
     "uma após a outra, em close frontal. Ao fundo, a ponte\n"
     "se estende tábua por tábua a partir do livro."),
    ("sb_03_final.png", "3. Encerramento", "11 s – 15 s  ·  frames 265–360",
     "A câmera recua e sobe até o plano geral: a torre torcida\n"
     "se ergue no fim da ponte e a palavra \"Ibmec\" fica\n"
     "em destaque na composição final (conhecimento → futuro)."),
]


def main():
    fig, eixos = plt.subplots(1, 3, figsize=(18, 5.6))
    fig.suptitle("AP1 · Storyboard — \"Ibmec: Construindo o Futuro\" (15 s a 24 fps = 360 frames)",
                 fontsize=15, fontweight="bold", y=0.98)
    for ax, (arquivo, titulo, tempo, texto) in zip(eixos, MOMENTOS):
        ax.imshow(mpimg.imread(PASTA / arquivo))
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_title(f"{titulo}\n{tempo}", fontsize=12, loc="left")
        ax.text(0.0, -0.05, texto, transform=ax.transAxes, va="top", fontsize=10.5)
    fig.subplots_adjust(left=0.02, right=0.98, top=0.83, bottom=0.2, wspace=0.05)
    saida = PASTA / "storyboard.png"
    fig.savefig(saida, dpi=110)
    print("salvo:", saida)


if __name__ == "__main__":
    main()
