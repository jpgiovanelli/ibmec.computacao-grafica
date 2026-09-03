"""
=============================================================================
 AREA 4 - VISUALIZACAO COMPUTACIONAL (Visualizacao Cientifica)
 Aplicacao: Matplotlib + scikit-image (pipeline equivalente ao do VTK/ParaView)
   https://github.com/matplotlib/matplotlib          (BSD)
   https://github.com/scikit-image/scikit-image      (BSD-3)
   Pipeline de referencia: https://github.com/Kitware/VTK  (BSD)
=============================================================================

O QUE ESTE CODIGO DEMONSTRA (aspectos especificos da VISUALIZACAO):

  DADOS (nao sao imagens)  ---->  [ mapeamento visual ]  ---->  IMAGEM

  A diferenca para a Area 1 e a origem: na sintese de imagens o dado de
  entrada e um MODELO GEOMETRICO criado para ser bonito/realista; aqui a
  entrada e um CONJUNTO DE DADOS medido ou simulado (uma matriz de
  temperaturas, um campo de velocidades, um volume tomografico) e o objetivo
  nao e realismo: e revelar estrutura, permitir ANALISE e evitar enganar
  quem olha.

  Pipeline de visualizacao (o mesmo do VTK: source -> filter -> mapper -> actor)
    1. FONTE DE DADOS   : simulacao da equacao do calor 2D (diferencas finitas)
    2. FILTRO           : isolinhas (contour), cortes, extracao de isosuperficie
    3. MAPEAMENTO VISUAL: escalar -> cor (colormap), vetor -> glifo/linha
    4. RENDERIZACAO     : a imagem final

  Experimentos:
    A. Campo ESCALAR 2D  - simulacao de difusao de calor + isolinhas + perfil
    B. Campo VETORIAL 2D - escoamento potencial: glifos (quiver) e linhas de
                           corrente (streamlines)
    C. Volume 3D         - cortes ortogonais + ISOSUPERFICIE por marching cubes
    D. MAPAS DE COR      - por que 'jet' distorce e 'viridis' nao (percepcao)

USO:
    python visualizacao.py
"""

import csv
import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.colors import LightSource  # noqa: E402
from mpl_toolkits.mplot3d.art3d import Poly3DCollection  # noqa: E402
from skimage import measure  # noqa: E402

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAIDA = os.path.join(RAIZ, "saidas", "04_visualizacao")
os.makedirs(SAIDA, exist_ok=True)


def salvar(fig, nome):
    caminho = os.path.join(SAIDA, nome)
    fig.savefig(caminho, dpi=110, facecolor="white")
    plt.close(fig)
    print(f"  [ok] {caminho}")


# ---------------------------------------------------------------------------
# A) Campo escalar: simulacao da equacao do calor 2D
# ---------------------------------------------------------------------------


def simular_calor(n=180, passos=4000, alfa=0.22, salvar_em=(0, 200, 900, 4000)):
    """
    Resolve numericamente  dT/dt = alfa * laplaciano(T)  por diferencas
    finitas explicitas. Contorno isolado (Neumann) e tres fontes fixas.
    Retorna os instantes pedidos e a serie temporal de temperatura media.
    """
    T = np.full((n, n), 20.0)                      # 20 C iniciais
    fontes = [(int(0.25 * n), int(0.25 * n), 260.0),
              (int(0.72 * n), int(0.62 * n), 210.0),
              (int(0.30 * n), int(0.78 * n), -30.0)]   # a terceira e um sorvedouro
    raio = max(3, n // 40)
    yy, xx = np.mgrid[0:n, 0:n]
    mascaras = [((yy - cy) ** 2 + (xx - cx) ** 2 <= raio ** 2, val)
                for cy, cx, val in fontes]

    instantes, serie = {}, []
    for passo in range(max(salvar_em) + 1):
        for mascara, val in mascaras:
            T[mascara] = val
        lap = (-4 * T
               + np.roll(T, 1, 0) + np.roll(T, -1, 0)
               + np.roll(T, 1, 1) + np.roll(T, -1, 1))
        # contorno isolado: derivada normal nula
        lap[0, :] = lap[1, :]
        lap[-1, :] = lap[-2, :]
        lap[:, 0] = lap[:, 1]
        lap[:, -1] = lap[:, -2]
        T += alfa * lap
        serie.append(float(T.mean()))
        if passo in salvar_em:
            instantes[passo] = T.copy()
    return instantes, np.array(serie)


def campo_escalar():
    print("\n[A] CAMPO ESCALAR 2D - simulacao da equacao do calor")
    instantes, serie = simular_calor()
    passos = sorted(instantes)
    final = instantes[passos[-1]]
    print(f"    malha 180x180, 4000 iteracoes | T media final = {serie[-1]:.2f} C")

    fig = plt.figure(figsize=(15, 8.4), constrained_layout=True)
    grade = fig.add_gridspec(2, 4)

    vmin, vmax = -30, 260
    for i, passo in enumerate(passos):
        eixo = fig.add_subplot(grade[0, i])
        im = eixo.imshow(instantes[passo], cmap="inferno", vmin=vmin, vmax=vmax,
                         origin="lower")
        eixo.set_title(f"t = {passo} iteracoes", fontsize=10)
        eixo.set_xticks([])
        eixo.set_yticks([])
        if i == 3:
            fig.colorbar(im, ax=eixo, fraction=0.046, label="temperatura (C)")

    # --- filtro 1: isolinhas (contour) --------------------------------------
    eixo = fig.add_subplot(grade[1, 0])
    eixo.imshow(final, cmap="inferno", origin="lower", alpha=0.85)
    cs = eixo.contour(final, levels=[0, 25, 50, 90, 140, 200], colors="white",
                      linewidths=1.0)
    eixo.clabel(cs, inline=True, fontsize=7, fmt="%d C")
    eixo.set_title("Filtro: ISOLINHAS sobre o campo", fontsize=10)
    eixo.set_xticks([])
    eixo.set_yticks([])

    # --- filtro 2: relevo sombreado (mapeia escalar -> altura + luz) --------
    eixo = fig.add_subplot(grade[1, 1])
    ls = LightSource(azdeg=315, altdeg=45)
    sombreado = ls.shade(final, cmap=plt.cm.inferno, vert_exag=0.6,
                         blend_mode="soft")
    eixo.imshow(sombreado, origin="lower")
    eixo.set_title("Mapeamento alternativo:\nrelevo sombreado (escalar -> altura)",
                   fontsize=10)
    eixo.set_xticks([])
    eixo.set_yticks([])

    # --- filtro 3: sonda / perfil de linha ---------------------------------
    eixo = fig.add_subplot(grade[1, 2])
    linha = final[final.shape[0] // 2, :]
    eixo.plot(linha, color="#c0392b", lw=1.8)
    eixo.fill_between(np.arange(len(linha)), 20, linha, alpha=0.2, color="#c0392b")
    eixo.set_title("Sonda: perfil ao longo da linha central", fontsize=10)
    eixo.set_xlabel("coluna da malha")
    eixo.set_ylabel("temperatura (C)")
    eixo.grid(alpha=0.3)

    # --- serie temporal escalar --------------------------------------------
    eixo = fig.add_subplot(grade[1, 3])
    eixo.plot(serie, color="#2c3e50", lw=1.8)
    eixo.set_title("Grandeza derivada:\ntemperatura media x tempo", fontsize=10)
    eixo.set_xlabel("iteracao")
    eixo.set_ylabel("T media (C)")
    eixo.grid(alpha=0.3)

    fig.suptitle("Visualizacao de CAMPO ESCALAR: dados simulados -> imagem",
                 fontsize=14, fontweight="bold")
    salvar(fig, "01_campo_escalar_calor.png")

    caminho = os.path.join(SAIDA, "serie_temperatura_media.csv")
    with open(caminho, "w", newline="", encoding="utf-8") as f:
        escritor = csv.writer(f)
        escritor.writerow(["iteracao", "temperatura_media_C"])
        for i in range(0, len(serie), 25):
            escritor.writerow([i, round(serie[i], 4)])
    print(f"  [ok] {caminho}")
    return final, serie


# ---------------------------------------------------------------------------
# B) Campo vetorial: escoamento potencial ao redor de um cilindro
# ---------------------------------------------------------------------------


def campo_vetorial():
    print("\n[B] CAMPO VETORIAL 2D - escoamento potencial com circulacao")
    n = 260
    x = np.linspace(-3.0, 3.0, n)
    y = np.linspace(-2.0, 2.0, n)
    X, Y = np.meshgrid(x, y)
    R, a, U, gama = np.hypot(X, Y), 0.6, 1.0, 2.2   # raio do cilindro, veloc., circulacao

    theta = np.arctan2(Y, X)
    # solucao analitica: escoamento uniforme + dipolo + vortice
    u = U * (1 - (a ** 2) * np.cos(2 * theta) / R ** 2) + gama * np.sin(theta) / (2 * np.pi * R)
    v = -U * (a ** 2) * np.sin(2 * theta) / R ** 2 - gama * np.cos(theta) / (2 * np.pi * R)
    dentro = R < a
    u[dentro] = np.nan
    v[dentro] = np.nan
    magnitude = np.hypot(u, v)

    fig, eixos = plt.subplots(1, 3, figsize=(16, 4.8), constrained_layout=True)

    passo = 12
    eixos[0].quiver(X[::passo, ::passo], Y[::passo, ::passo],
                    u[::passo, ::passo], v[::passo, ::passo],
                    magnitude[::passo, ::passo], cmap="viridis", scale=28)
    eixos[0].set_title("Glifos (quiver): 1 seta por amostra\ndirecao + intensidade", fontsize=10)

    strm = eixos[1].streamplot(x, y, u, v, color=magnitude, cmap="viridis",
                               density=1.4, linewidth=1.0)
    eixos[1].set_title("Linhas de corrente (streamlines):\ntrajetorias integradas do campo", fontsize=10)
    fig.colorbar(strm.lines, ax=eixos[1], label="|V| (m/s)")

    im = eixos[2].contourf(X, Y, magnitude, levels=24, cmap="magma")
    eixos[2].contour(X, Y, magnitude, levels=12, colors="white", linewidths=0.4)
    eixos[2].set_title("Campo derivado: modulo da velocidade\n(mapa preenchido + isolinhas)", fontsize=10)
    fig.colorbar(im, ax=eixos[2], label="|V| (m/s)")

    for eixo in eixos:
        eixo.add_patch(plt.Circle((0, 0), a, color="#2c3e50", zorder=5))
        eixo.set_aspect("equal")
        eixo.set_xlim(-3, 3)
        eixo.set_ylim(-2, 2)

    fig.suptitle("Visualizacao de CAMPO VETORIAL: tres mapeamentos do MESMO dado",
                 fontsize=14, fontweight="bold")
    salvar(fig, "02_campo_vetorial.png")

    finito = np.isfinite(magnitude)
    print(f"    malha {n}x{n} | |V| max = {np.nanmax(magnitude):.2f} m/s "
          f"| |V| medio = {magnitude[finito].mean():.2f} m/s")
    return float(np.nanmax(magnitude))


# ---------------------------------------------------------------------------
# C) Volume 3D: cortes ortogonais + isosuperficie (marching cubes)
# ---------------------------------------------------------------------------


def gerar_volume(n=90):
    """Volume escalar sintetico (estilo tomografia): elipsoides + gaussianas."""
    z, y, x = np.mgrid[0:n, 0:n, 0:n] / (n - 1.0) * 2 - 1
    volume = np.zeros((n, n, n))

    def elipsoide(cx, cy, cz, rx, ry, rz, valor):
        d = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 + ((z - cz) / rz) ** 2
        volume[d <= 1.0] += valor

    elipsoide(0, 0, 0, 0.78, 0.62, 0.70, 0.35)          # "corpo" externo
    elipsoide(-0.22, 0.10, 0.05, 0.26, 0.24, 0.28, 0.45)  # estrutura interna 1
    elipsoide(0.30, -0.14, -0.05, 0.20, 0.30, 0.22, 0.55)  # estrutura interna 2
    elipsoide(0.05, 0.32, -0.28, 0.13, 0.13, 0.13, 0.70)   # nodulo denso

    # textura suave para nao ficar artificial demais
    rng = np.random.default_rng(11)
    volume += 0.03 * rng.normal(size=volume.shape)
    from scipy.ndimage import gaussian_filter
    return gaussian_filter(volume, 1.4)


def volume_3d():
    print("\n[C] VOLUME 3D - cortes ortogonais e isosuperficie (marching cubes)")
    volume = gerar_volume()
    n = volume.shape[0]
    print(f"    volume {volume.shape} = {volume.size:,} voxels "
          f"| faixa [{volume.min():.2f}, {volume.max():.2f}]")

    fig = plt.figure(figsize=(15, 8.6), constrained_layout=True)
    grade = fig.add_gridspec(2, 3)

    cortes = [(volume[n // 2, :, :], "Corte AXIAL (z = 50%)"),
              (volume[:, n // 2, :], "Corte CORONAL (y = 50%)"),
              (volume[:, :, n // 2], "Corte SAGITAL (x = 50%)")]
    for i, (corte, titulo) in enumerate(cortes):
        eixo = fig.add_subplot(grade[0, i])
        im = eixo.imshow(corte, cmap="bone", origin="lower")
        eixo.contour(corte, levels=[0.45, 0.75], colors=["#f39c12", "#e74c3c"],
                     linewidths=1.2)
        eixo.set_title(titulo + "\n(+ isolinhas nos niveis 0,45 e 0,75)", fontsize=10)
        eixo.set_xticks([])
        eixo.set_yticks([])
        if i == 2:
            fig.colorbar(im, ax=eixo, fraction=0.046, label="densidade")

    # --- ISOSUPERFICIES por marching cubes ---------------------------------
    eixo = fig.add_subplot(grade[1, :2], projection="3d")
    cores = {0.30: ("#5dade2", 0.16), 0.62: ("#f39c12", 0.55), 0.95: ("#e74c3c", 1.0)}
    contagem = {}
    for nivel, (cor, alfa) in cores.items():
        verts, faces, _, _ = measure.marching_cubes(volume, level=nivel)
        contagem[nivel] = (len(verts), len(faces))
        # "corte de revelacao": a casca externa e mostrada so em metade do
        # dominio, tecnica classica para expor a estrutura interna
        if nivel == 0.30:
            manter = np.all(verts[faces][:, :, 1] < n * 0.55, axis=1)
            faces = faces[manter]
        eixo.plot_trisurf(verts[:, 0], verts[:, 1], faces, verts[:, 2],
                          color=cor, alpha=alfa, linewidth=0,
                          antialiased=True, shade=True)
        print(f"    isosuperficie nivel {nivel:.2f}: "
              f"{len(verts):,} vertices / {len(faces):,} triangulos")
    eixo.set_xlim(0, n)
    eixo.set_ylim(0, n)
    eixo.set_zlim(0, n)
    eixo.set_box_aspect((1, 1, 1), zoom=1.15)
    eixo.view_init(elev=20, azim=-62)
    eixo.set_xlabel("x (voxel)", fontsize=8)
    eixo.set_ylabel("y (voxel)", fontsize=8)
    eixo.set_zlabel("z (voxel)", fontsize=8)
    eixo.tick_params(labelsize=7)
    eixo.set_title("ISOSUPERFICIES extraidas por MARCHING CUBES\n"
                   "azul 0,30 (com corte de revelacao) | laranja 0,62 | vermelho 0,95",
                   fontsize=11)

    # --- histograma do volume: escolha dos niveis nao e arbitraria ----------
    eixo = fig.add_subplot(grade[1, 2])
    eixo.hist(volume.ravel(), bins=120, color="#34495e")
    for nivel, (cor, _) in cores.items():
        eixo.axvline(nivel, color=cor, lw=2.2, label=f"iso = {nivel}")
    eixo.set_yscale("log")
    eixo.set_title("Histograma do volume\n(os niveis saem da distribuicao dos dados)",
                   fontsize=10)
    eixo.set_xlabel("densidade")
    eixo.set_ylabel("voxels (escala log)")
    eixo.legend(fontsize=8)
    eixo.grid(alpha=0.3)

    fig.suptitle("Visualizacao VOLUMETRICA: 729.000 voxels -> geometria interpretavel",
                 fontsize=14, fontweight="bold")
    salvar(fig, "03_volume_3d_isosuperficie.png")
    return contagem


# ---------------------------------------------------------------------------
# D) Mapas de cor: a decisao mais critica da area
# ---------------------------------------------------------------------------


def mapas_de_cor(campo):
    print("\n[D] MAPAS DE COR - percepcao e honestidade da representacao")
    fig, eixos = plt.subplots(2, 4, figsize=(16, 7.2), constrained_layout=True)

    nomes = ["jet", "viridis", "inferno", "coolwarm"]
    notas = ["NAO perceptualmente uniforme:\ncria bordas falsas e esconde detalhe",
             "perceptualmente uniforme,\nseguro para daltonismo",
             "perceptualmente uniforme,\nbom para fundo escuro",
             "divergente: use so quando\nexiste um valor central de referencia"]
    for i, (nome, nota) in enumerate(zip(nomes, notas)):
        eixos[0, i].imshow(campo, cmap=nome, origin="lower")
        eixos[0, i].set_title(f"'{nome}'\n{nota}", fontsize=9)
        eixos[0, i].axis("off")

        # luminosidade percebida ao longo do mapa de cor
        cores = plt.get_cmap(nome)(np.linspace(0, 1, 256))[:, :3]
        lum = 0.2126 * cores[:, 0] + 0.7152 * cores[:, 1] + 0.0722 * cores[:, 2]
        eixos[1, i].plot(np.linspace(0, 1, 256), lum, color="#2c3e50", lw=2)
        eixos[1, i].set_ylim(0, 1)
        eixos[1, i].set_title("luminosidade percebida", fontsize=9)
        eixos[1, i].set_xlabel("valor normalizado do dado")
        eixos[1, i].grid(alpha=0.3)
        derivada = np.diff(lum)
        monotona = bool(np.all(derivada >= -1e-3) or np.all(derivada <= 1e-3))
        eixos[1, i].text(0.03, 0.9, "monotona: " + ("SIM" if monotona else "NAO"),
                         transform=eixos[1, i].transAxes, fontsize=9,
                         color="#27ae60" if monotona else "#c0392b",
                         fontweight="bold")
        print(f"    {nome:9s} -> luminosidade monotona: {'sim' if monotona else 'NAO'}")

    fig.suptitle("Mapeamento visual: o colormap muda a LEITURA do mesmo dado",
                 fontsize=14, fontweight="bold")
    salvar(fig, "04_mapas_de_cor.png")


def main():
    print("=" * 70)
    print(" AREA 4 - VISUALIZACAO COMPUTACIONAL (Matplotlib / scikit-image)")
    print("=" * 70)
    campo, serie = campo_escalar()
    vmax = campo_vetorial()
    contagem = volume_3d()
    mapas_de_cor(campo)

    resumo = {
        "campo_escalar": {"malha": "180x180", "iteracoes": 4000,
                          "temperatura_media_final_C": round(float(serie[-1]), 3)},
        "campo_vetorial": {"malha": "260x260", "velocidade_maxima": round(vmax, 3)},
        "volume_3d": {"voxels": 90 ** 3,
                      "isosuperficies": {str(k): {"vertices": v[0], "triangulos": v[1]}
                                         for k, v in contagem.items()}},
    }
    caminho = os.path.join(SAIDA, "resumo_visualizacao.json")
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(resumo, f, indent=2, ensure_ascii=False)
    print(f"\n  [ok] {caminho}")
    print("=" * 70)


if __name__ == "__main__":
    main()
