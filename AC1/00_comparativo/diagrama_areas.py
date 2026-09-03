"""
=============================================================================
 QUADRO COMPARATIVO - as quatro areas da COMPUTACAO VISUAL
=============================================================================

Gera o diagrama que organiza as quatro areas segundo a natureza da ENTRADA e
da SAIDA de cada uma. Essa e a forma classica de diferencia-las (Gomes &
Velho, "Computacao Grafica: Imagem"), e e o fio condutor de todo o trabalho:

                        SAIDA: IMAGEM        SAIDA: DADOS/MODELO
    ENTRADA: DADOS   |  Sintese de imagens |  (fora do escopo:
    OU MODELO        |  Visualizacao       |   modelagem geometrica)
    -----------------+---------------------+---------------------------
    ENTRADA: IMAGEM  |  Processamento      |  Visao computacional
                     |  de imagens         |

USO:
    python diagrama_areas.py
"""

import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAIDA = os.path.join(RAIZ, "saidas", "00_comparativo")
os.makedirs(SAIDA, exist_ok=True)

AREAS = [
    {
        "titulo": "1. SINTESE DE IMAGENS\n(Computacao Grafica)",
        "entrada": "MODELO 3D\n(geometria, materiais,\nluzes, camera)",
        "saida": "IMAGEM",
        "cor": "#2e86c1",
        "exemplos": "Blender, Unreal, OpenGL,\nray tracing, jogos, CAD, VFX",
        "pergunta": "\"Como isso deveria\nse parecer?\"",
    },
    {
        "titulo": "2. PROCESSAMENTO\nDE IMAGENS",
        "entrada": "IMAGEM",
        "saida": "IMAGEM\n(melhorada ou\ntransformada)",
        "cor": "#28b463",
        "exemplos": "OpenCV, GIMP, Photoshop,\nfiltros, compressao, restauracao",
        "pergunta": "\"Como melhorar\nesta imagem?\"",
    },
    {
        "titulo": "3. VISAO\nCOMPUTACIONAL",
        "entrada": "IMAGEM",
        "saida": "DADOS\n(o que ha na cena:\nclasses, posicoes,\nmedidas)",
        "cor": "#ca6f1e",
        "exemplos": "OpenCV, YOLO, MediaPipe,\nOCR, biometria, SLAM",
        "pergunta": "\"O que ha nesta\nimagem?\"",
    },
    {
        "titulo": "4. VISUALIZACAO\nCOMPUTACIONAL",
        "entrada": "DADOS\n(medidos ou\nsimulados; sem\nforma visual previa)",
        "saida": "IMAGEM",
        "cor": "#7d3c98",
        "exemplos": "ParaView, VTK, Matplotlib,\nD3.js, simulacoes, tomografia",
        "pergunta": "\"O que estes dados\nestao dizendo?\"",
    },
]


def caixa(eixo, x, y, largura, altura, texto, cor, tamanho=9, negrito=False,
          alpha=1.0, cor_texto="white"):
    eixo.add_patch(FancyBboxPatch(
        (x, y), largura, altura, boxstyle="round,pad=0.012,rounding_size=0.02",
        facecolor=cor, edgecolor="none", alpha=alpha, zorder=2))
    eixo.text(x + largura / 2, y + altura / 2, texto, ha="center", va="center",
              fontsize=tamanho, color=cor_texto, zorder=3,
              fontweight="bold" if negrito else "normal", linespacing=1.35)


def seta(eixo, x0, y0, x1, y1, cor):
    eixo.add_patch(FancyArrowPatch(
        (x0, y0), (x1, y1), arrowstyle="-|>", mutation_scale=18,
        linewidth=2.2, color=cor, zorder=3))


def diagrama_fluxos():
    fig, eixo = plt.subplots(figsize=(13.5, 8.4))
    eixo.set_xlim(-0.9, 10.5)
    eixo.set_ylim(1.2, 10)
    eixo.axis("off")

    eixo.text(4.6, 9.6, "COMPUTACAO VISUAL: as quatro areas e seus fluxos",
              ha="center", fontsize=17, fontweight="bold", color="#1b2631")
    eixo.text(4.6, 9.15,
              "o que distingue as areas nao e a tecnica, e a NATUREZA DA ENTRADA "
              "e a NATUREZA DA SAIDA",
              ha="center", fontsize=10.5, color="#566573", style="italic")

    y = 7.55
    for area in AREAS:
        cor = area["cor"]
        caixa(eixo, 0.25, y, 2.05, 1.35, area["titulo"], cor, 10, True)
        caixa(eixo, 2.75, y + 0.08, 1.9, 1.2, area["entrada"], "#d5d8dc", 8.5,
              cor_texto="#1b2631")
        seta(eixo, 2.35, y + 0.68, 2.7, y + 0.68, cor)
        caixa(eixo, 5.1, y + 0.08, 1.35, 1.2, "processo\nda area", cor, 8.5,
              alpha=0.75)
        seta(eixo, 4.7, y + 0.68, 5.05, y + 0.68, cor)
        caixa(eixo, 6.9, y + 0.08, 1.9, 1.2, area["saida"], "#d5d8dc", 8.5,
              cor_texto="#1b2631")
        seta(eixo, 6.5, y + 0.68, 6.85, y + 0.68, cor)
        eixo.text(10.45, y + 0.9, area["pergunta"], ha="right", va="center",
                  fontsize=8.5, style="italic", color=cor, fontweight="bold")
        eixo.text(10.45, y + 0.38, area["exemplos"], ha="right", va="center",
                  fontsize=7.5, color="#566573")
        y -= 1.72

    eixo.annotate("", xy=(-0.15, 8.2), xytext=(-0.15, 4.85),
                  arrowprops=dict(arrowstyle="<->", color="#85929e", lw=1.6,
                                  connectionstyle="arc3,rad=0.35"))
    eixo.text(-0.72, 6.5, "areas INVERSAS", fontsize=8.5, color="#85929e",
              ha="center", va="center", rotation=90, style="italic",
              fontweight="bold")

    eixo.text(4.6, 1.75,
              "Fronteiras sao porosas: o pre-processamento da Area 2 alimenta a "
              "Area 3, que reconstroi modelos usados pela Area 1;\n"
              "a Area 4 usa o motor de renderizacao da Area 1 para desenhar dados "
              "que nunca tiveram forma visual.",
              ha="center", fontsize=9, color="#566573", style="italic",
              bbox=dict(boxstyle="round,pad=0.5", facecolor="#f4f6f7",
                        edgecolor="#d5d8dc"))

    caminho = os.path.join(SAIDA, "01_fluxos_das_areas.png")
    fig.savefig(caminho, dpi=120, facecolor="white", bbox_inches="tight")
    plt.close(fig)
    print(f"  [ok] {caminho}")


def diagrama_quadrantes():
    fig, eixo = plt.subplots(figsize=(10, 8.4))
    eixo.set_xlim(0, 10)
    eixo.set_ylim(0, 10)
    eixo.axis("off")

    eixo.text(5, 9.6, "Mapa das areas por entrada x saida",
              ha="center", fontsize=16, fontweight="bold", color="#1b2631")

    # eixos do quadrante
    eixo.plot([1.6, 9.2], [4.9, 4.9], color="#1b2631", lw=1.6, zorder=1)
    eixo.plot([5.4, 5.4], [1.1, 8.7], color="#1b2631", lw=1.6, zorder=1)
    eixo.text(5.4, 9.0, "SAIDA", ha="center", fontsize=10, fontweight="bold")
    eixo.text(3.5, 8.75, "IMAGEM", ha="center", fontsize=9.5, color="#566573")
    eixo.text(7.3, 8.75, "DADOS / MODELO", ha="center", fontsize=9.5, color="#566573")
    eixo.text(1.0, 4.9, "ENTRADA", ha="center", va="center", rotation=90,
              fontsize=10, fontweight="bold")
    eixo.text(1.45, 6.8, "DADOS /\nMODELO", ha="right", va="center",
              fontsize=9.5, color="#566573")
    eixo.text(1.45, 3.0, "IMAGEM", ha="right", va="center", fontsize=9.5,
              color="#566573")

    quadrantes = [
        (2.0, 7.05, 3.4, 1.45, "#2e86c1",
         "1. SINTESE DE IMAGENS\nmodelo 3D -> imagem\nray tracing, rasterizacao, OpenGL"),
        (2.0, 5.35, 3.4, 1.45, "#7d3c98",
         "4. VISUALIZACAO COMPUTACIONAL\ndados medidos/simulados -> imagem\nisosuperficies, campos, mapas de cor"),
        (2.0, 1.55, 3.4, 3.1, "#28b463",
         "2. PROCESSAMENTO\nDE IMAGENS\n\nimagem -> imagem\n\nfiltros, realce, Fourier,\nmorfologia, compressao"),
        (5.75, 1.55, 3.4, 3.1, "#ca6f1e",
         "3. VISAO COMPUTACIONAL\n\nimagem -> dados\n\ndeteccao, segmentacao,\nmedicao, reconhecimento"),
    ]
    for x, y, largura, altura, cor, texto in quadrantes:
        caixa(eixo, x, y, largura, altura, texto, cor, 9.0)

    # quadrante vazio: dado/modelo -> dado/modelo nao e computacao visual
    caixa(eixo, 5.75, 5.35, 3.4, 3.1,
          "(quadrante vazio)\n\ndados -> dados nao produz\nnem consome imagem:\ne modelagem, simulacao\nou analise numerica",
          "#eaecee", 9.0, cor_texto="#85929e")

    eixo.text(3.7, 5.13, "mesmo quadrante, intencoes opostas: realismo x fidelidade ao dado",
              ha="center", fontsize=8, color="#566573", style="italic")

    eixo.text(5, 0.55,
              "As Areas 1 e 3 sao inversas uma da outra. As Areas 1 e 4 compartilham a saida, "
              "mas nao a intencao.\nAs Areas 2 e 3 compartilham a entrada, mas nao o objetivo: "
              "tratar o sinal x extrair significado.",
              ha="center", fontsize=8.8, color="#566573", style="italic")

    caminho = os.path.join(SAIDA, "02_quadrantes.png")
    fig.savefig(caminho, dpi=120, facecolor="white", bbox_inches="tight")
    plt.close(fig)
    print(f"  [ok] {caminho}")


def main():
    print("=" * 70)
    print(" QUADRO COMPARATIVO - diagramas das quatro areas")
    print("=" * 70)
    diagrama_fluxos()
    diagrama_quadrantes()
    print("=" * 70)


if __name__ == "__main__":
    main()
