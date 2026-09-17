"""
Transformacoes geometricas 2D em coordenadas homogeneas.

Todas as transformacoes sao matrizes 3x3 e sao aplicadas a vetores-coluna
homogeneos, seguindo a notacao da aula:

        P' = M . P            [x' y' 1]^T = M . [x y 1]^T

Uma sequencia de transformacoes M1, depois M2, depois M3 vira uma unica
matriz  M = M3 . M2 . M1  (a primeira transformacao aplicada fica mais a
direita, encostada no ponto).

Este modulo tambem concentra os utilitarios de plotagem usados pelos dez
exercicios, para que todas as figuras tenham a mesma aparencia.
"""

import sys
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

# acentos no terminal do Windows (cp1252) sem quebrar os prints
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

RAIZ = Path(__file__).resolve().parent
SAIDAS = RAIZ / "saidas"

# --------------------------------------------------------------------------
# Matrizes elementares (3x3, coordenadas homogeneas)
# --------------------------------------------------------------------------


def translacao(tx, ty):
    """T(tx, ty): desloca cada ponto de (tx, ty)."""
    return np.array([[1.0, 0.0, tx],
                     [0.0, 1.0, ty],
                     [0.0, 0.0, 1.0]])


def escala(sx, sy=None):
    """S(sx, sy): escala em relacao a origem. Com um unico fator, e uniforme."""
    if sy is None:
        sy = sx
    return np.array([[sx, 0.0, 0.0],
                     [0.0, sy, 0.0],
                     [0.0, 0.0, 1.0]])


def rotacao(graus):
    """R(theta): rotacao em torno da origem.

    Angulo positivo = sentido anti-horario (convencao matematica e da aula).
    Para rotacionar no sentido horario basta passar o angulo negativo.
    """
    t = np.radians(graus)
    c, s = np.cos(t), np.sin(t)
    return np.array([[c, -s, 0.0],
                     [s, c, 0.0],
                     [0.0, 0.0, 1.0]])


def reflexao_eixo_x():
    """Reflexao em relacao ao eixo x (reta y = 0): (x, y) -> (x, -y)."""
    return np.array([[1.0, 0.0, 0.0],
                     [0.0, -1.0, 0.0],
                     [0.0, 0.0, 1.0]])


def reflexao_eixo_y():
    """Reflexao em relacao ao eixo y (reta x = 0): (x, y) -> (-x, y)."""
    return np.array([[-1.0, 0.0, 0.0],
                     [0.0, 1.0, 0.0],
                     [0.0, 0.0, 1.0]])


def cisalhamento(kx=0.0, ky=0.0):
    """H(kx, ky): cisalhamento. kx desloca x proporcionalmente a y
    (cisalhamento horizontal); ky desloca y proporcionalmente a x."""
    return np.array([[1.0, kx, 0.0],
                     [ky, 1.0, 0.0],
                     [0.0, 0.0, 1.0]])


def compor(*matrizes):
    """compor(M1, M2, M3) devolve M3 . M2 . M1.

    As matrizes sao passadas NA ORDEM EM QUE SERAO APLICADAS ao objeto; a
    funcao cuida de multiplica-las na ordem certa (da direita para a esquerda).
    """
    M = np.eye(3)
    for m in matrizes:
        M = m @ M
    return M


def aplicar(M, pontos):
    """Aplica a matriz 3x3 M a um ponto (2,) ou a uma lista de pontos (N, 2)."""
    P = np.asarray(pontos, dtype=float)
    um_ponto = P.ndim == 1
    P = np.atleast_2d(P)
    Ph = np.hstack([P, np.ones((P.shape[0], 1))])       # (N, 3) homogeneo
    Rh = (M @ Ph.T).T                                   # P' = M . P
    R = Rh[:, :2] / Rh[:, 2:3]                          # volta a cartesiano
    return R[0] if um_ponto else R


# --------------------------------------------------------------------------
# Formatacao de numeros e matrizes
# --------------------------------------------------------------------------


def fmt(v, casas=3):
    """Formata um numero: inteiros sem casas decimais, reais com `casas`."""
    v = float(v)
    if abs(v - round(v)) < 1e-9:
        return str(int(round(v)))
    return f"{v:.{casas}f}".rstrip("0").rstrip(".")


def fmt_ponto(p, casas=3):
    return "(" + ", ".join(fmt(c, casas) for c in np.asarray(p).ravel()) + ")"


def fmt_matriz(M, casas=3):
    """Matriz em texto alinhado, para o terminal."""
    linhas = []
    celulas = [[fmt(v, casas) for v in linha] for linha in M]
    larg = max(len(c) for linha in celulas for c in linha)
    for linha in celulas:
        linhas.append("| " + "  ".join(c.rjust(larg) for c in linha) + " |")
    return "\n".join(linhas)


def imprimir_resultado(titulo, matriz, antes, depois, nomes=None):
    """Impressao padronizada de um exercicio no terminal."""
    print("=" * 66)
    print(titulo)
    print("=" * 66)
    print("Matriz de transformacao (homogenea 3x3):")
    print(fmt_matriz(matriz))
    antes = np.atleast_2d(antes)
    depois = np.atleast_2d(depois)
    if nomes is None:
        nomes = ([f"P{i + 1}" for i in range(len(antes))]
                 if len(antes) > 1 else ["P"])
    print()
    for n, a, d in zip(nomes, antes, depois):
        print(f"  {n}{fmt_ponto(a):<14} ->  {n}'{fmt_ponto(d)}")
    print()


# --------------------------------------------------------------------------
# Utilitarios de plotagem
# --------------------------------------------------------------------------

COR_ORIGINAL = "#1f77b4"       # azul
COR_TRANSFORMADO = "#d62728"   # vermelho
COR_INTERMEDIARIO = "#2ca02c"  # verde
COR_INTERMEDIARIO2 = "#ff7f0e" # laranja
COR_APAGADO = "#9e9e9e"        # cinza


def preparar_eixos(ax, titulo, *conjuntos_de_pontos, margem=1.0):
    """Grade, eixos x=0 / y=0, proporcao 1:1 e limites que cobrem os pontos."""
    todos = np.vstack([np.atleast_2d(np.asarray(p, float))
                       for p in conjuntos_de_pontos] + [np.zeros((1, 2))])
    xmin, ymin = todos.min(axis=0) - margem
    xmax, ymax = todos.max(axis=0) + margem
    x0, x1 = np.floor(xmin), np.ceil(xmax)
    y0, y1 = np.floor(ymin), np.ceil(ymax)
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
    ax.set_aspect("equal", adjustable="box")
    ax.axhline(0, color="black", linewidth=0.9, zorder=1)
    ax.axvline(0, color="black", linewidth=0.9, zorder=1)
    ax.grid(True, linestyle=":", linewidth=0.7, alpha=0.8)
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_title(titulo, fontsize=11)
    passo = 1 if max(x1 - x0, y1 - y0) <= 16 else 2
    ax.set_xticks(np.arange(x0, x1 + 1, passo))
    ax.set_yticks(np.arange(y0, y1 + 1, passo))
    ax.tick_params(labelsize=8)


def _rotular_vertices(ax, pontos, nomes, cor, deslocamento=0.45, sufixo="",
                      tamanho=8):
    """Escreve NOME(x, y) ao lado de cada vertice, empurrado para fora do
    poligono (na direcao centroide -> vertice)."""
    P = np.atleast_2d(np.asarray(pontos, float))
    centro = P.mean(axis=0)
    for p, n in zip(P, nomes):
        d = p - centro
        norma = np.linalg.norm(d)
        d = d / norma if norma > 1e-9 else np.array([0.0, 1.0])
        pos = p + d * deslocamento
        ax.annotate(f"{n}{sufixo}{fmt_ponto(p)}", xy=p, xytext=pos,
                    fontsize=tamanho, color=cor, ha="center", va="center",
                    bbox=dict(boxstyle="round,pad=0.2", fc="white",
                              ec=cor, lw=0.6, alpha=0.9), zorder=6)


def desenhar_poligono(ax, pontos, cor, rotulo, nomes=None, estilo="-",
                      preencher=True, sufixo="", rotular=True, alpha=1.0,
                      largura=2.0):
    """Desenha um poligono fechado com vertices marcados e rotulados."""
    P = np.atleast_2d(np.asarray(pontos, float))
    fechado = np.vstack([P, P[:1]])
    ax.plot(fechado[:, 0], fechado[:, 1], estilo, color=cor, linewidth=largura,
            label=rotulo, alpha=alpha, zorder=3)
    if preencher:
        ax.fill(P[:, 0], P[:, 1], color=cor, alpha=0.12 * alpha, zorder=2)
    ax.scatter(P[:, 0], P[:, 1], color=cor, s=28, zorder=5, alpha=alpha)
    if rotular and nomes is not None:
        _rotular_vertices(ax, P, nomes, cor, sufixo=sufixo)


def desenhar_ponto(ax, p, cor, rotulo, nome, sufixo="", dx=0.3, dy=0.3):
    """Desenha um ponto isolado (plt.scatter) com nome e coordenadas."""
    p = np.asarray(p, float)
    ax.scatter([p[0]], [p[1]], color=cor, s=70, zorder=5, label=rotulo,
               edgecolor="black", linewidth=0.6)
    ax.annotate(f"{nome}{sufixo}{fmt_ponto(p)}", xy=p,
                xytext=(p[0] + dx, p[1] + dy),
                fontsize=9, color=cor, ha="left", va="bottom",
                bbox=dict(boxstyle="round,pad=0.25", fc="white", ec=cor,
                          lw=0.7), zorder=6)


def desenhar_seta(ax, origem, destino, cor="dimgray", texto=None,
                  estilo="-|>", tracejada=False):
    """Seta de `origem` ate `destino`, opcionalmente com um texto no meio."""
    origem = np.asarray(origem, float)
    destino = np.asarray(destino, float)
    ax.annotate("", xy=destino, xytext=origem,
                arrowprops=dict(arrowstyle=estilo, color=cor, lw=1.4,
                                linestyle="--" if tracejada else "-",
                                shrinkA=4, shrinkB=4), zorder=4)
    if texto:
        meio = (origem + destino) / 2
        ax.annotate(texto, xy=meio, fontsize=8, color=cor, ha="center",
                    va="bottom", bbox=dict(boxstyle="round,pad=0.15",
                                           fc="white", ec="none", alpha=0.8),
                    zorder=6)


def desenhar_arco_rotacao(ax, raio, ang_inicial, ang_final, cor="dimgray",
                          texto=None, centro=(0.0, 0.0)):
    """Arco centrado em `centro` indicando o sentido e o angulo da rotacao."""
    cx, cy = centro
    a0, a1 = np.radians(ang_inicial), np.radians(ang_final)
    ts = np.linspace(a0, a1, 40)
    ax.plot(cx + raio * np.cos(ts), cy + raio * np.sin(ts), color=cor, lw=1.2,
            linestyle="--", zorder=4)
    fim = np.array([cx + raio * np.cos(ts[-1]), cy + raio * np.sin(ts[-1])])
    antes = np.array([cx + raio * np.cos(ts[-3]), cy + raio * np.sin(ts[-3])])
    ax.annotate("", xy=fim, xytext=antes,
                arrowprops=dict(arrowstyle="-|>", color=cor, lw=1.2), zorder=4)
    if texto:
        tm = (a0 + a1) / 2
        ax.annotate(texto, xy=(cx + raio * 1.18 * np.cos(tm),
                               cy + raio * 1.18 * np.sin(tm)),
                    fontsize=9, color=cor, ha="center", va="center", zorder=6)


def texto_matriz(ax, M, titulo="M =", casas=3, canto="superior esquerdo"):
    """Escreve a matriz num canto do grafico, em fonte monoespacada."""
    x, ha = (0.02, "left") if "esquerdo" in canto else (0.98, "right")
    y, va = (0.98, "top") if "superior" in canto else (0.02, "bottom")
    corpo = fmt_matriz(M, casas)
    ax.text(x, y, f"{titulo}\n{corpo}", transform=ax.transAxes, fontsize=7.5,
            family="monospace", va=va, ha=ha,
            bbox=dict(boxstyle="round,pad=0.3", fc="lightyellow", ec="gray",
                      lw=0.6, alpha=0.95), zorder=7)


def legenda(ax, loc="lower right"):
    ax.legend(loc=loc, fontsize=8, framealpha=0.9)


def salvar(fig, nome, pasta=SAIDAS):
    """Grava a figura em `pasta/nome` e devolve o caminho."""
    pasta = Path(pasta)
    pasta.mkdir(parents=True, exist_ok=True)
    caminho = pasta / nome
    fig.savefig(caminho, dpi=150, bbox_inches="tight")
    try:
        mostrado = caminho.relative_to(RAIZ)
    except ValueError:
        mostrado = caminho
    print(f"figura gravada em: {mostrado}")
    return caminho
