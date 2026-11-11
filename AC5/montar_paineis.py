"""
AC05 - recorta as capturas de interface e monta a prancha de detalhes.
Rodar com o Python do sistema (requer matplotlib e Pillow):

    python AC5/montar_paineis.py

Entradas (AC5/imagens/): tela_*.png (AC05_capturas_interface.py) e os renders
de AC05_renders.py. Saidas:
    AC05_shader_madeira.png, AC05_shader_couro.png   Shader Editor recortado nos nos
    AC05_uv_tabua.png, AC05_uv_paginas.png           UV Editor recortado nas ilhas
    AC05_detalhes_texturas.png                       closes + esferas-amostra
    AC05_material_preview_x_rendered.png             viewport: Material Preview x Rendered
"""

from pathlib import Path

import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

PASTA = Path(__file__).resolve().parent / "imagens"

CLOSES = [
    ("detalhe_livro.png", "Livro_Aberto + Livro_Paginas",
     "capa: MAT_Livro_Couro_PBR (imagem: cor, rugosidade, normal)\n"
     "páginas: MAT_Livro_Papel_PBR (procedural: linhas + fibra)"),
    ("detalhe_ponte.png", "Ponte_Arco (tabuleiro, guarda-corpo, postes)",
     "tábuas: MAT_Ponte_Madeira_PBR (imagem: cor, rugosidade, normal)\n"
     "estrutura: MAT_Ponte_Aco_PBR (Metallic 1, Roughness 0,35)"),
    ("detalhe_torre.png", "Torre_Futuro",
     "estrutura: MAT_Torre_Aluminio_Escovado_PBR (procedural)\n"
     "janelas: MAT_Torre_Vidro_Espelhado_PBR (Metallic 1, Roughness 0,05)"),
]
ESFERAS = ["Couro", "Papel", "Madeira", "Aço", "Alumínio\nescovado", "Vidro\nespelhado"]


def recortar(origem, destino, margem=60, topo=70):
    """Recorta a captura no retangulo que contem o conteudo (tudo o que
    difere bastante da cor de fundo do editor), ignorando o cabecalho, as
    bordas da area e os pontinhos da grade do Node Editor."""
    img = Image.open(PASTA / origem).convert("RGB")
    a = np.asarray(img).astype(int)
    fundo = np.median(a[200:-200:40, 60:-60:40].reshape(-1, 3), axis=0)
    diferente = np.abs(a - fundo).sum(axis=2) > 60
    diferente[:topo] = False
    diferente[-25:] = False
    diferente[:, :25] = False
    diferente[:, -60:] = False
    ys, xs = np.nonzero(diferente)
    caixa = (max(xs.min() - margem, 0), max(ys.min() - margem, 0),
             min(xs.max() + margem, img.width), min(ys.max() + margem, img.height))
    img.crop(caixa).save(PASTA / destino)
    print("recorte:", destino, caixa)


def material_x_rendered():
    """Lado a lado: viewport em Material Preview (HDRI de estudio do Blender)
    e em Rendered (luz e ceu da cena), recortados no quadro da camera."""
    fig, eixos = plt.subplots(1, 2, figsize=(18, 5.6))
    titulos = ["Material Preview (HDRI de estúdio do Blender)",
               "Rendered (Luz_Principal + céu da cena)"]
    for ax, nome, titulo in zip(eixos, ("material", "rendered"), titulos):
        img = Image.open(PASTA / f"tela_viewport_{nome}.png").convert("RGB")
        topo = 40
        largura = int((img.height - topo) * 16 / 9)
        x0 = (img.width - largura) // 2
        ax.imshow(img.crop((x0, topo, x0 + largura, img.height)))
        sem_eixos(ax)
        ax.set_title(titulo, fontsize=13, fontweight="bold", loc="left")
    fig.suptitle("AC05 · Mesma cena, mesma câmera: Material Preview × Rendered", fontsize=15,
                 fontweight="bold", y=0.99)
    fig.subplots_adjust(left=0.01, right=0.99, top=0.86, bottom=0.01, wspace=0.03)
    fig.savefig(PASTA / "AC05_material_preview_x_rendered.png", dpi=110)
    plt.close(fig)


def sem_eixos(ax):
    ax.set_xticks([])
    ax.set_yticks([])
    for borda in ax.spines.values():
        borda.set_visible(False)


def prancha():
    fig = plt.figure(figsize=(18, 10.6))
    grade = fig.add_gridspec(2, 3, height_ratios=[1.0, 0.52], hspace=0.3, wspace=0.04)
    fig.suptitle("AC05 · Materiais PBR e texturas sob a luz da AC04 (Sun az −150°, elev. 35° + céu)",
                 fontsize=16, fontweight="bold", y=0.985)
    for i, (arquivo, titulo, texto) in enumerate(CLOSES):
        ax = fig.add_subplot(grade[0, i])
        ax.imshow(mpimg.imread(PASTA / arquivo))
        sem_eixos(ax)
        ax.set_title(titulo, fontsize=12.5, fontweight="bold", loc="left")
        ax.text(0.0, -0.03, texto, transform=ax.transAxes, va="top", fontsize=10.8)
    ax = fig.add_subplot(grade[1, :])
    ax.imshow(mpimg.imread(PASTA / "amostras_pbr_bruto.png"))
    sem_eixos(ax)
    ax.set_title("Esferas-amostra (coleção AC05_Materiais_Texturas), mesma luz da cena",
                 fontsize=12.5, fontweight="bold", loc="left")
    for k, rotulo in enumerate(ESFERAS):
        ax.text(0.087 + k * 0.1653, 0.04, rotulo, transform=ax.transAxes, ha="center",
                va="bottom", fontsize=11.5, fontweight="bold", color="#222222")
    fig.subplots_adjust(left=0.01, right=0.99, top=0.93, bottom=0.01)
    fig.savefig(PASTA / "AC05_detalhes_texturas.png", dpi=110)
    plt.close(fig)


if __name__ == "__main__":
    recortar("tela_shader_madeira.png", "AC05_shader_madeira.png")
    recortar("tela_shader_couro.png", "AC05_shader_couro.png")
    recortar("tela_uv_tabua.png", "AC05_uv_tabua.png")
    recortar("tela_uv_paginas.png", "AC05_uv_paginas.png")
    prancha()
    material_x_rendered()
    print("ok:", PASTA)
