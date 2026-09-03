"""
=============================================================================
 AREA 1 - SINTESE DE IMAGENS (Computacao Grafica)
 Aplicacao complementar: RASTERIZADOR POR SOFTWARE (pipeline grafico classico)
=============================================================================

Enquanto o `raytracer.py` mostra a sintese por TRACADO DE RAIOS (da camera
para a cena), este script implementa o outro paradigma da area: a
RASTERIZACAO (da geometria para a tela) - exatamente o que a GPU faz via
OpenGL/DirectX/Vulkan, e o que a disciplina exercita com PyOpenGL + GLFW.

PIPELINE IMPLEMENTADO PASSO A PASSO:

   Vertices do modelo (espaco do objeto)
        |  M  - matriz de modelo   (escala, rotacao, translacao)
        v
   Espaco do mundo
        |  V  - matriz de visao    (lookAt: camera na origem olhando -Z)
        v
   Espaco da camera
        |  P  - matriz de projecao (perspectiva, frustum)
        v
   Coordenadas de recorte (clip space, homogeneas)
        |  divisao por w  - divisao perspectiva
        v
   NDC [-1,1]^3
        |  transformacao de viewport
        v
   Coordenadas de tela (pixels)  ->  RASTERIZACAO
        - remocao de faces traseiras (back-face culling)
        - coordenadas baricentricas por pixel
        - Z-BUFFER (teste de profundidade / visibilidade)
        - sombreamento (flat, Gouraud) com modelo de Phong

Saida: painel 2x2 comparando wireframe, flat shading, Gouraud shading e o
proprio Z-buffer visualizado como mapa de profundidade.

USO:
    python rasterizador.py
"""

import os

import numpy as np

LARGURA = 460
ALTURA = 460

# ---------------------------------------------------------------------------
# 1) Geometria: malha de triangulos
# ---------------------------------------------------------------------------


def icosfera(subdivisoes=2):
    """Cria uma esfera geodesica subdividindo um icosaedro regular."""
    t = (1.0 + np.sqrt(5.0)) / 2.0
    v = np.array([
        [-1, t, 0], [1, t, 0], [-1, -t, 0], [1, -t, 0],
        [0, -1, t], [0, 1, t], [0, -1, -t], [0, 1, -t],
        [t, 0, -1], [t, 0, 1], [-t, 0, -1], [-t, 0, 1],
    ], dtype=np.float64)
    v /= np.linalg.norm(v, axis=1, keepdims=True)

    f = [
        [0, 11, 5], [0, 5, 1], [0, 1, 7], [0, 7, 10], [0, 10, 11],
        [1, 5, 9], [5, 11, 4], [11, 10, 2], [10, 7, 6], [7, 1, 8],
        [3, 9, 4], [3, 4, 2], [3, 2, 6], [3, 6, 8], [3, 8, 9],
        [4, 9, 5], [2, 4, 11], [6, 2, 10], [8, 6, 7], [9, 8, 1],
    ]

    vertices = list(v)
    for _ in range(subdivisoes):
        cache, novas = {}, []

        def meio(a, b):
            chave = (min(a, b), max(a, b))
            if chave not in cache:
                m = (vertices[a] + vertices[b]) / 2.0
                m /= np.linalg.norm(m)
                vertices.append(m)
                cache[chave] = len(vertices) - 1
            return cache[chave]

        for a, b, c in f:
            ab, bc, ca = meio(a, b), meio(b, c), meio(c, a)
            novas += [[a, ab, ca], [b, bc, ab], [c, ca, bc], [ab, bc, ca]]
        f = novas

    vertices = np.array(vertices)
    # numa esfera unitaria centrada na origem, a normal do vertice E o vertice
    normais = vertices.copy()
    return vertices, np.array(f, dtype=np.int32), normais


def cubo():
    """
    Cubo com vertices DUPLICADOS por face: assim cada face tem sua propria
    normal e o objeto aparece facetado (aresta viva), como deve ser.
    Malha suave (esfera) x malha facetada (cubo) e uma decisao de modelagem.
    """
    faces_def = [
        ((0, 0, 1), [(-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)]),
        ((0, 0, -1), [(1, -1, -1), (-1, -1, -1), (-1, 1, -1), (1, 1, -1)]),
        ((1, 0, 0), [(1, -1, 1), (1, -1, -1), (1, 1, -1), (1, 1, 1)]),
        ((-1, 0, 0), [(-1, -1, -1), (-1, -1, 1), (-1, 1, 1), (-1, 1, -1)]),
        ((0, 1, 0), [(-1, 1, 1), (1, 1, 1), (1, 1, -1), (-1, 1, -1)]),
        ((0, -1, 0), [(-1, -1, -1), (1, -1, -1), (1, -1, 1), (-1, -1, 1)]),
    ]
    vertices, normais, faces = [], [], []
    for normal, quad in faces_def:
        base = len(vertices)
        for p in quad:
            vertices.append(p)
            normais.append(normal)
        faces.append([base, base + 1, base + 2])
        faces.append([base, base + 2, base + 3])
    return (np.array(vertices, dtype=np.float64),
            np.array(faces, dtype=np.int32),
            np.array(normais, dtype=np.float64))


# ---------------------------------------------------------------------------
# 2) Matrizes do pipeline (4x4 homogeneas)
# ---------------------------------------------------------------------------


def translacao(tx, ty, tz):
    m = np.eye(4)
    m[:3, 3] = [tx, ty, tz]
    return m


def escala(s):
    m = np.eye(4)
    m[0, 0] = m[1, 1] = m[2, 2] = s
    return m


def rotacao_y(graus):
    a = np.radians(graus)
    m = np.eye(4)
    m[0, 0], m[0, 2] = np.cos(a), np.sin(a)
    m[2, 0], m[2, 2] = -np.sin(a), np.cos(a)
    return m


def rotacao_x(graus):
    a = np.radians(graus)
    m = np.eye(4)
    m[1, 1], m[1, 2] = np.cos(a), -np.sin(a)
    m[2, 1], m[2, 2] = np.sin(a), np.cos(a)
    return m


def look_at(olho, alvo, cima):
    """Matriz de visao: leva o mundo para o sistema de coordenadas da camera."""
    f = alvo - olho
    f = f / np.linalg.norm(f)
    s = np.cross(f, cima)
    s = s / np.linalg.norm(s)
    u = np.cross(s, f)
    m = np.eye(4)
    m[0, :3], m[1, :3], m[2, :3] = s, u, -f
    m[:3, 3] = [-s @ olho, -u @ olho, f @ olho]
    return m


def perspectiva(fov_graus, aspecto, perto, longe):
    """Matriz de projecao em perspectiva (mesma convencao do gluPerspective)."""
    f = 1.0 / np.tan(np.radians(fov_graus) / 2.0)
    m = np.zeros((4, 4))
    m[0, 0] = f / aspecto
    m[1, 1] = f
    m[2, 2] = (longe + perto) / (perto - longe)
    m[2, 3] = (2 * longe * perto) / (perto - longe)
    m[3, 2] = -1.0
    return m


# ---------------------------------------------------------------------------
# 3) Rasterizacao com Z-buffer
# ---------------------------------------------------------------------------


def rasterizar(objetos, modo="gouraud"):
    """
    modo: 'flat' | 'gouraud' | 'wireframe' | 'profundidade'
    Retorna (imagem RGB uint8, z-buffer).
    """
    cor_fundo = np.array([0.09, 0.10, 0.14])
    framebuffer = np.tile(cor_fundo, (ALTURA, LARGURA, 1))
    zbuffer = np.full((ALTURA, LARGURA), np.inf)

    view = look_at(np.array([2.6, 2.0, 4.2]),
                   np.array([0.0, 0.0, 0.0]),
                   np.array([0.0, 1.0, 0.0]))
    proj = perspectiva(45.0, LARGURA / ALTURA, 0.1, 100.0)

    luz = np.array([0.6, 0.9, 0.7])
    luz = luz / np.linalg.norm(luz)
    olho = np.array([2.6, 2.0, 4.2])

    for vertices, faces, normais, modelo, cor_base, brilho in objetos:
        # ---- estagio de vertices ------------------------------------------
        vh = np.hstack([vertices, np.ones((len(vertices), 1))])
        mundo = (modelo @ vh.T).T[:, :3]
        # normais transformadas pela parte linear da matriz de modelo
        normal_mundo = (modelo[:3, :3] @ normais.T).T
        normal_mundo /= np.maximum(
            np.linalg.norm(normal_mundo, axis=1, keepdims=True), 1e-9)

        clip = (proj @ view @ np.hstack(
            [mundo, np.ones((len(mundo), 1))]).T).T

        w = clip[:, 3:4]
        visivel = (w[:, 0] > 1e-6)
        ndc = clip[:, :3] / np.where(np.abs(w) < 1e-9, 1e-9, w)   # div. persp.

        # ---- transformacao de viewport ------------------------------------
        sx = (ndc[:, 0] * 0.5 + 0.5) * (LARGURA - 1)
        sy = (1.0 - (ndc[:, 1] * 0.5 + 0.5)) * (ALTURA - 1)
        sz = w[:, 0]                       # profundidade em espaco de camera

        # ---- iluminacao por vertice (Gouraud) -----------------------------
        vis_dir = olho - mundo
        vis_dir /= np.maximum(np.linalg.norm(vis_dir, axis=1, keepdims=True), 1e-9)
        difusa = np.maximum((normal_mundo @ luz), 0.0)[:, None]
        meio = luz + vis_dir
        meio /= np.maximum(np.linalg.norm(meio, axis=1, keepdims=True), 1e-9)
        especular = np.maximum(np.sum(normal_mundo * meio, axis=1), 0.0)[:, None] ** brilho
        cor_vertice = np.clip(0.12 * cor_base + 0.85 * difusa * cor_base
                              + 0.45 * especular, 0, 1)

        for (i0, i1, i2) in faces:
            if not (visivel[i0] and visivel[i1] and visivel[i2]):
                continue
            x0, y0 = sx[i0], sy[i0]
            x1, y1 = sx[i1], sy[i1]
            x2, y2 = sx[i2], sy[i2]

            # ---- back-face culling pela area orientada em tela ------------
            area = (x1 - x0) * (y2 - y0) - (x2 - x0) * (y1 - y0)
            if area >= -1e-9:
                continue

            if modo == "wireframe":
                for (xa, ya, xb, yb) in ((x0, y0, x1, y1), (x1, y1, x2, y2),
                                         (x2, y2, x0, y0)):
                    n = int(max(abs(xb - xa), abs(yb - ya))) + 1
                    xs = np.clip(np.linspace(xa, xb, n).astype(int), 0, LARGURA - 1)
                    ys = np.clip(np.linspace(ya, yb, n).astype(int), 0, ALTURA - 1)
                    framebuffer[ys, xs] = np.array([0.45, 0.95, 0.75])
                continue

            # ---- caixa envolvente do triangulo ---------------------------
            xmin = max(int(np.floor(min(x0, x1, x2))), 0)
            xmax = min(int(np.ceil(max(x0, x1, x2))), LARGURA - 1)
            ymin = max(int(np.floor(min(y0, y1, y2))), 0)
            ymax = min(int(np.ceil(max(y0, y1, y2))), ALTURA - 1)
            if xmin > xmax or ymin > ymax:
                continue

            px, py = np.meshgrid(np.arange(xmin, xmax + 1),
                                 np.arange(ymin, ymax + 1))

            # ---- coordenadas baricentricas -------------------------------
            l0 = ((x1 - px) * (y2 - py) - (x2 - px) * (y1 - py)) / area
            l1 = ((x2 - px) * (y0 - py) - (x0 - px) * (y2 - py)) / area
            l2 = 1.0 - l0 - l1
            dentro = (l0 >= 0) & (l1 >= 0) & (l2 >= 0)
            if not np.any(dentro):
                continue

            z = l0 * sz[i0] + l1 * sz[i1] + l2 * sz[i2]
            trecho_z = zbuffer[ymin:ymax + 1, xmin:xmax + 1]
            passa = dentro & (z < trecho_z)                  # TESTE DE Z
            if not np.any(passa):
                continue
            trecho_z[passa] = z[passa]

            if modo == "gouraud":
                c = (l0[..., None] * cor_vertice[i0]
                     + l1[..., None] * cor_vertice[i1]
                     + l2[..., None] * cor_vertice[i2])
            elif modo == "flat":
                c = np.broadcast_to(
                    (cor_vertice[i0] + cor_vertice[i1] + cor_vertice[i2]) / 3.0,
                    l0.shape + (3,))
            else:  # profundidade
                c = np.zeros(l0.shape + (3,))

            trecho_cor = framebuffer[ymin:ymax + 1, xmin:xmax + 1]
            trecho_cor[passa] = c[passa]

    if modo == "profundidade":
        z = zbuffer.copy()
        finito = np.isfinite(z)
        if np.any(finito):
            zmin, zmax = z[finito].min(), z[finito].max()
            norm = np.zeros_like(z)
            norm[finito] = 1.0 - (z[finito] - zmin) / max(zmax - zmin, 1e-9)
            framebuffer = np.dstack([norm] * 3)

    return (np.clip(framebuffer, 0, 1) * 255).astype(np.uint8), zbuffer


def main():
    v_esfera, f_esfera, n_esfera = icosfera(2)
    v_cubo, f_cubo, n_cubo = cubo()

    objetos = [
        (v_esfera, f_esfera, n_esfera,
         translacao(-0.9, 0.1, 0.0) @ escala(1.0), np.array([0.90, 0.32, 0.28]), 48),
        (v_cubo, f_cubo, n_cubo,
         translacao(1.2, -0.15, 0.4) @ rotacao_y(28) @ rotacao_x(18) @ escala(0.72),
         np.array([0.30, 0.55, 0.92]), 24),
        (v_esfera, f_esfera, n_esfera,
         translacao(0.5, 1.15, -1.6) @ escala(0.55), np.array([0.95, 0.78, 0.22]), 64),
    ]

    print("=" * 70)
    print(" AREA 1 - SINTESE DE IMAGENS | Rasterizador por software")
    print("=" * 70)
    total_tri = sum(len(o[1]) for o in objetos)
    print(f"  Triangulos na cena ..: {total_tri}")
    print(f"  Resolucao ...........: {LARGURA}x{ALTURA}")

    modos = ["wireframe", "flat", "gouraud", "profundidade"]
    imagens = {}
    for m in modos:
        img, _ = rasterizar(objetos, modo=m)
        imagens[m] = img
        print(f"  [ok] modo '{m}' rasterizado")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    titulos = {
        "wireframe": "1. Wireframe\n(apenas arestas projetadas)",
        "flat": "2. Flat shading\n(1 cor por face)",
        "gouraud": "3. Gouraud shading\n(cor interpolada por baricentricas)",
        "profundidade": "4. Z-buffer\n(mapa de profundidade)",
    }
    fig, eixos = plt.subplots(2, 2, figsize=(9, 10), constrained_layout=True)
    for eixo, m in zip(eixos.ravel(), modos):
        eixo.imshow(imagens[m])
        eixo.set_title(titulos[m], fontsize=11)
        eixo.axis("off")
    fig.suptitle("Sintese de imagens por RASTERIZACAO: modelo 3D -> imagem 2D",
                 fontsize=14, fontweight="bold")

    raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    destino = os.path.join(raiz, "saidas", "01_sintese", "rasterizador_pipeline.png")
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    fig.savefig(destino, dpi=110, facecolor="white")
    plt.close(fig)
    print(f"  Imagem salva em .....: {destino}")
    print("=" * 70)


if __name__ == "__main__":
    main()
