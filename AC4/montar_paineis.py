"""
Monta as pranchas comparativas da AC04 a partir dos renders gerados por
AC04_renders.py (rodar este com o Python do sistema: requer matplotlib).

    python AC4/montar_paineis.py

Saidas em AC4/imagens/:
    AC04_comparacao_materiais.png  closes dos tres objetos + esferas-amostra
    AC04_estudo_angulo_luz.png     cena e esferas com a luz em 3 direcoes
"""

from pathlib import Path

import matplotlib.image as mpimg
import matplotlib.pyplot as plt

PASTA = Path(__file__).resolve().parent / "imagens"

OBJETOS = [
    ("detalhe_livro.png", "Livro_Aberto  ·  MAT_Lambert",
     "Roughness 1,0 · Specular IOR Level 0,0\nsó componente difusa: fosco, sem brilho"),
    ("detalhe_ponte.png", "Ponte_Arco  ·  MAT_Phong",
     "Roughness 0,2 · Specular IOR Level 0,5\ndifusa + especular: brilho largo e suave"),
    ("detalhe_torre.png", "Torre_Futuro  ·  MAT_BlinnPhong",
     "Roughness 0,1 · Specular IOR Level 0,8\nbrilho pequeno, nítido e mais intenso"),
]

ANGULOS = [
    ("a_padrao", "A · padrão: frente-esquerda, elevação 35°"),
    ("b_frontal", "B · frontal: por trás da câmera, elevação 35°"),
    ("c_rasante", "C · rasante: lateral direita, elevação 15°"),
]


def sem_eixos(ax):
    ax.set_xticks([])
    ax.set_yticks([])
    for borda in ax.spines.values():
        borda.set_visible(False)


def comparacao():
    fig = plt.figure(figsize=(18, 11.6))
    grade = fig.add_gridspec(2, 3, height_ratios=[1.0, 0.62], hspace=0.28, wspace=0.04)
    fig.suptitle("AC04 · Lambert × Phong × Blinn-Phong sob a MESMA luz (Sun 4 W/m², az −150°, elev. 35°)",
                 fontsize=16, fontweight="bold", y=0.985)
    for i, (arquivo, titulo, texto) in enumerate(OBJETOS):
        ax = fig.add_subplot(grade[0, i])
        ax.imshow(mpimg.imread(PASTA / arquivo))
        sem_eixos(ax)
        ax.set_title(titulo, fontsize=13, fontweight="bold", loc="left")
        ax.text(0.0, -0.03, texto, transform=ax.transAxes, va="top", fontsize=11.5)
    ax = fig.add_subplot(grade[1, :])
    ax.imshow(mpimg.imread(PASTA / "amostras_esferas_bruto.png"))
    sem_eixos(ax)
    ax.set_title("Esferas-amostra (mesma forma, mesma luz): só o material muda", fontsize=13,
                 fontweight="bold", loc="left")
    for x, rotulo in ((0.19, "MAT_Lambert"), (0.5, "MAT_Phong"), (0.775, "MAT_BlinnPhong")):
        ax.text(x, 0.05, rotulo, transform=ax.transAxes, ha="center", fontsize=13,
                fontweight="bold", color="#222222")
    fig.subplots_adjust(left=0.01, right=0.99, top=0.93, bottom=0.01)
    fig.savefig(PASTA / "AC04_comparacao_materiais.png", dpi=110)
    plt.close(fig)


def angulos():
    fig, eixos = plt.subplots(2, 3, figsize=(18, 7.4))
    fig.suptitle("AC04 · Influência do ângulo da luz (só a direção da Luz_Principal muda; câmera, "
                 "intensidade e cor fixas)", fontsize=15, fontweight="bold", y=0.99)
    for col, (chave, titulo) in enumerate(ANGULOS):
        for lin, tipo in enumerate(("cena", "esferas")):
            ax = eixos[lin][col]
            ax.imshow(mpimg.imread(PASTA / f"angulo_{chave}_{tipo}.png"))
            sem_eixos(ax)
            if lin == 0:
                ax.set_title(titulo, fontsize=12.5, loc="left")
    fig.subplots_adjust(left=0.01, right=0.99, top=0.9, bottom=0.01, hspace=0.04, wspace=0.03)
    fig.savefig(PASTA / "AC04_estudo_angulo_luz.png", dpi=110)
    plt.close(fig)


if __name__ == "__main__":
    comparacao()
    angulos()
    print("pranchas salvas em", PASTA)
