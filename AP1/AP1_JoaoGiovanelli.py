"""
AP1 - "Ibmec: Construindo o Futuro" (conceito e modelagem da peca "Ibmec em 15 segundos")
Aluno: Joao Pedro Giovanelli Berla
Disciplina: Computacao Grafica - CG_26.2_8001

COMO USAR
    1. Abra o Blender 4.5 LTS (arquivo novo, cena "General").
    2. Aba Scripting -> Text -> Open -> este arquivo -> botao "Run Script" (Alt+P).
    3. O script monta a colecao AP1_Ibmec_Conceito inteira. Pode ser rodado de
       novo: ele apaga o que criou antes e reconstroi.

O QUE ESTE SCRIPT FAZ
    - Palavra "Ibmec": objeto Texto com extrusao + bevel, convertido em malha e
      separado em 5 letras (cada letra com origem na base, pronta para a AP2).
    - Tres objetos autorais, modelados a partir de primitivas:
        Livro_Aberto  -> caixa com loop cuts (bisect) e lombada afundada;
                         paginas curvas com Mirror + Solidify; Bevel na capa.
        Ponte_Arco    -> curva Bezier com bevel (viga), tabuleiro de tabuas com
                         Array (Fit Curve) + Curve, guarda-corpo em curva e
                         postes com Array + Mirror + Curve.
        Torre_Futuro  -> cilindro com loop cuts, janelas por inset + extrusao,
                         coroa e antena por inset/extrude no topo, Simple
                         Deform (Twist) e Bevel.
    - Elementos auxiliares (chao, blocos de construcao), camera principal com
      Track To, luz, e tres cameras de referencia do storyboard.
    - Timeline de 15 s a 24 fps (frames 1 a 360).

Os modificadores ficam SEM aplicar, de proposito: assim cada tecnica continua
visivel e editavel no painel de modificadores (e animavel na AP2).
"""

import math
import os

import bmesh
import bpy
from mathutils import Matrix, Vector

# ---------------------------------------------------------------------------
# Parametros gerais
# ---------------------------------------------------------------------------
NOME_COLECAO = "AP1_Ibmec_Conceito"
SUB = {                    # subcolecoes (a ordem numerica organiza o Outliner)
    "palavra": "01_Palavra",
    "autorais": "02_Objetos_Autorais",
    "aux": "03_Auxiliares",
    "camera": "04_Camera_Luz",
    "story": "05_Storyboard",
}
FRAME_INICIAL = 1
FRAME_FINAL = 360          # 360 frames a 24 fps = 15 segundos
FPS = 24

FONTES = (                 # primeira fonte encontrada e usada; senao, a padrao
    r"C:\Windows\Fonts\ariblk.ttf",
    r"C:\Windows\Fonts\arialbd.ttf",
    "/System/Library/Fonts/Supplemental/Arial Black.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
)

CORES = {                  # RGBA (0-1) do Principled BSDF / viewport
    "Ibmec": (0.02, 0.10, 0.32, 1.0),
    "Blocos_Construcao": (0.95, 0.62, 0.08, 1.0),
    "Livro_Aberto": (0.42, 0.05, 0.07, 1.0),
    "Livro_Paginas": (0.95, 0.93, 0.86, 1.0),
    "Ponte_Arco": (0.30, 0.32, 0.36, 1.0),
    "Ponte_Tabuleiro": (0.62, 0.45, 0.28, 1.0),
    "Ponte_Guarda": (0.30, 0.32, 0.36, 1.0),
    "Torre_Futuro": (0.40, 0.75, 0.92, 1.0),
    "Chao": (0.80, 0.82, 0.86, 1.0),
}

# Ponte: sai da borda direita do livro e chega na base da torre
PONTE_INICIO = Vector((7.9, 1.5, 0.0))
PONTE_ANGULO = 35.0        # graus, rotacao em Z da ponte
PONTE_COMPRIMENTO = 8.0
PONTE_ALTURA = 2.2         # altura do meio do arco


# ---------------------------------------------------------------------------
# Funcoes auxiliares: cena, colecoes e materiais
# ---------------------------------------------------------------------------
def limpar_cena():
    """Remove tudo que este script cria (para rodar mais de uma vez) e os
    objetos padrao do arquivo novo (Cube, Light, Camera)."""
    def apagar_colecao(col):
        for filha in list(col.children):
            apagar_colecao(filha)
        for obj in list(col.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.collections.remove(col)

    col = bpy.data.collections.get(NOME_COLECAO)
    if col is not None:
        apagar_colecao(col)
    for nome in ("Cube", "Light", "Camera"):
        obj = bpy.data.objects.get(nome)
        if obj is not None:
            bpy.data.objects.remove(obj, do_unlink=True)
    # dados orfaos (sem usuario) de execucoes anteriores
    for bloco in (bpy.data.meshes, bpy.data.curves, bpy.data.materials,
                  bpy.data.cameras, bpy.data.lights):
        for dado in list(bloco):
            if dado.users == 0:
                bloco.remove(dado)
    bpy.context.scene.frame_set(FRAME_INICIAL)


def obter_colecao(nome, pai=None):
    """Cria (ou reaproveita) uma colecao ligada ao pai (ou a cena)."""
    col = bpy.data.collections.get(nome)
    if col is None:
        col = bpy.data.collections.new(nome)
        (pai or bpy.context.scene.collection).children.link(col)
    return col


def novo_material(nome, cor, rugosidade=0.5):
    """Material simples com a cor no Principled BSDF. O no e procurado pelo
    tipo, porque o nome muda com o idioma da interface."""
    mat = bpy.data.materials.get(nome)
    if mat is None:
        mat = bpy.data.materials.new(nome)
        mat.use_nodes = True
    bsdf = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = cor
    bsdf.inputs["Roughness"].default_value = rugosidade
    mat.diffuse_color = cor                  # cor tambem no viewport solido
    return mat


def pintar(obj, chave):
    obj.data.materials.clear()
    obj.data.materials.append(novo_material("mat_" + chave, CORES[chave]))


def objeto_de_bmesh(nome, bm, col):
    """Converte um bmesh em malha + objeto dentro da colecao."""
    malha = bpy.data.meshes.new(nome + "_mesh")
    bm.to_mesh(malha)
    bm.free()
    obj = bpy.data.objects.new(nome, malha)
    col.objects.link(obj)
    return obj


def filho(obj, pai):
    """Parent sem 'compensacao': o filho passa a usar o espaco local do pai."""
    obj.parent = pai
    obj.matrix_parent_inverse.identity()


def suavizar(obj, angulo=35.0):
    """Shade Auto Smooth manual: suaviza as faces e marca como 'sharp' as
    arestas com angulo maior que o limite."""
    malha = obj.data
    bm = bmesh.new()
    bm.from_mesh(malha)
    limite = math.radians(angulo)
    for f in bm.faces:
        f.smooth = True
    for e in bm.edges:
        e.smooth = not (e.is_boundary or (e.is_manifold and e.calc_face_angle(0) > limite))
    bm.to_mesh(malha)
    bm.free()


# ---------------------------------------------------------------------------
# 1. Palavra "Ibmec": texto -> malha -> 5 letras
# ---------------------------------------------------------------------------
def carregar_fonte():
    for caminho in FONTES:
        if os.path.exists(caminho):
            return bpy.data.fonts.load(caminho, check_existing=True)
    return None


def separar_partes(bm_origem):
    """Divide um bmesh em partes conectadas (equivale a Edit Mode -> P ->
    By Loose Parts). Devolve uma lista de bmesh, um por parte."""
    bm_origem.faces.ensure_lookup_table()
    restantes = set(range(len(bm_origem.faces)))
    grupos = []
    while restantes:
        semente = restantes.pop()
        grupo, pilha = {semente}, [semente]
        while pilha:
            f = bm_origem.faces[pilha.pop()]
            for e in f.edges:
                for vizinha in e.link_faces:
                    if vizinha.index in restantes:
                        restantes.remove(vizinha.index)
                        grupo.add(vizinha.index)
                        pilha.append(vizinha.index)
        grupos.append(grupo)

    partes = []
    for grupo in grupos:
        bm = bm_origem.copy()
        bm.faces.ensure_lookup_table()
        fora = [f for f in bm.faces if f.index not in grupo]
        bmesh.ops.delete(bm, geom=fora, context="FACES")
        soltos = [v for v in bm.verts if not v.link_faces]
        bmesh.ops.delete(bm, geom=soltos, context="VERTS")
        partes.append(bm)
    return partes


def criar_palavra(col):
    """Texto 3D (extrude + bevel) convertido em malha. Cada letra vira um
    objeto com origem no centro da base, filho do Empty Ibmec_Palavra."""
    texto = bpy.data.curves.new("Ibmec_texto", type="FONT")
    texto.body = "Ibmec"
    fonte = carregar_fonte()
    if fonte is not None:
        texto.font = fonte
    texto.size = 3.8
    texto.space_character = 1.06
    texto.extrude = 0.30            # profundidade da letra
    texto.bevel_depth = 0.045       # chanfro arredondado nas bordas
    texto.bevel_resolution = 3
    texto.resolution_u = 8
    texto.align_x = "CENTER"
    obj_texto = bpy.data.objects.new("Ibmec_texto", texto)
    col.objects.link(obj_texto)

    # Texto -> malha (equivale a Object -> Convert -> Mesh)
    depsgraph = bpy.context.evaluated_depsgraph_get()
    malha = bpy.data.meshes.new_from_object(obj_texto.evaluated_get(depsgraph))
    bpy.data.objects.remove(obj_texto, do_unlink=True)
    bpy.data.curves.remove(texto)
    # a malha nao depende mais da fonte: remove para o .blend nao guardar
    # um caminho de fonte do sistema (evita "arquivo faltando" em outro PC)
    if fonte is not None and fonte.users == 0:
        bpy.data.fonts.remove(fonte)

    bm = bmesh.new()
    bm.from_mesh(malha)
    bpy.data.meshes.remove(malha)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0005)
    partes = separar_partes(bm)
    bm.free()

    # Empty que representa a palavra inteira: e ele que fica em pe (rot X 90)
    palavra = bpy.data.objects.new("Ibmec_Palavra", None)
    palavra.empty_display_type = "PLAIN_AXES"
    palavra.empty_display_size = 0.6
    col.objects.link(palavra)

    def centro_x(parte):
        return sum(v.co.x for v in parte.verts) / len(parte.verts)

    partes.sort(key=centro_x)
    largura = (max(v.co.x for p in partes for v in p.verts)
               - min(v.co.x for p in partes for v in p.verts))
    letras = []
    for letra_txt, parte in zip("Ibmec", partes):
        xs = [v.co.x for v in parte.verts]
        ys = [v.co.y for v in parte.verts]
        zs = [v.co.z for v in parte.verts]
        base = Vector(((min(xs) + max(xs)) / 2, min(ys), (min(zs) + max(zs)) / 2))
        bmesh.ops.translate(parte, verts=parte.verts, vec=-base)
        letra = objeto_de_bmesh("Ibmec_" + letra_txt, parte, col)
        letra.location = base                      # posicao no espaco da palavra
        filho(letra, palavra)
        pintar(letra, "Ibmec")
        suavizar(letra, 40.0)
        letras.append(letra)
    return palavra, letras, largura


# ---------------------------------------------------------------------------
# 2. Objeto autoral 1: Livro_Aberto
# ---------------------------------------------------------------------------
def criar_livro(col):
    # Capa: cubo escalado para 15 x 10 x 0.2 (dois lados abertos)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(15.0, 10.0, 0.2), verts=bm.verts)
    bmesh.ops.translate(bm, vec=(0, 0, 0.1), verts=bm.verts)
    # Loop cuts: tres cortes paralelos a YZ (lombada e suas bordas)
    for x in (-0.45, 0.0, 0.45):
        geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
        bmesh.ops.bisect_plane(bm, geom=geom, plane_co=(x, 0, 0), plane_no=(1, 0, 0))
    # Lombada: o loop central desce e as laterais sobem um pouco -> "V" do livro
    for v in bm.verts:
        if abs(v.co.x) < 1e-4:
            v.co.z -= 0.22
        elif abs(abs(v.co.x) - 0.45) < 1e-4:
            v.co.z -= 0.08
    # Extrusao para baixo da face inferior central (reforco da lombada)
    inferiores = [f for f in bm.faces
                  if f.normal.z < -0.5 and abs(f.calc_center_median().x) < 0.5]
    ext = bmesh.ops.extrude_face_region(bm, geom=inferiores)
    novos = [g for g in ext["geom"] if isinstance(g, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, vec=(0, 0, -0.08), verts=novos)
    capa = objeto_de_bmesh("Livro_Aberto", bm, col)
    pintar(capa, "Livro_Aberto")
    bevel = capa.modifiers.new("Bevel_bordas", "BEVEL")
    bevel.width = 0.06
    bevel.segments = 3
    bevel.limit_method = "ANGLE"

    # Paginas (lado direito), espelhadas em X pelo Mirror.
    # Perfil tipico de livro aberto: sobe rapido perto da lombada e desce
    # suavemente ate a borda.
    n = 32
    largura, profundidade = 7.05, 9.4
    verts, faces = [], []
    for i in range(n + 1):
        t = i / n
        x = 0.12 + largura * t
        z = 0.10 + 0.62 * (1 - (1 - t) ** 3) * (1 - 0.45 * t)
        verts.append((x, -profundidade / 2, z))
        verts.append((x, profundidade / 2, z))
    for i in range(n):
        a = 2 * i
        faces.append((a, a + 2, a + 3, a + 1))
    malha = bpy.data.meshes.new("Livro_Paginas_mesh")
    malha.from_pydata(verts, [], faces)
    malha.update()
    paginas = bpy.data.objects.new("Livro_Paginas", malha)
    col.objects.link(paginas)
    filho(paginas, capa)
    pintar(paginas, "Livro_Paginas")
    for f in malha.polygons:
        f.use_smooth = True
    espelho = paginas.modifiers.new("Mirror_X", "MIRROR")
    espelho.use_axis[0] = True
    espelho.use_clip = True
    solid = paginas.modifiers.new("Solidify_folhas", "SOLIDIFY")
    solid.thickness = 0.32          # espessura do bloco de folhas
    solid.offset = -1.0

    # Transformacoes do objeto: leve rotacao para quebrar a frontalidade
    capa.location = (0.0, 0.0, 0.0)
    capa.rotation_euler = (0.0, 0.0, math.radians(-4))
    return capa, paginas


# ---------------------------------------------------------------------------
# 3. Objeto autoral 2: Ponte_Arco (curvas + modificadores)
# ---------------------------------------------------------------------------
def pontos_arco(n=9, dy=0.0, dz=0.0):
    """Pontos de um arco parabolico de comprimento PONTE_COMPRIMENTO."""
    pts = []
    for i in range(n):
        t = i / (n - 1)
        x = PONTE_COMPRIMENTO * t
        z = 0.35 + PONTE_ALTURA * 4 * t * (1 - t)
        pts.append((x, dy, z + dz))
    return pts


def curva_bezier(nome, splines, col, bevel=0.0):
    dados = bpy.data.curves.new(nome + "_curve", type="CURVE")
    dados.dimensions = "3D"
    dados.bevel_depth = bevel
    dados.bevel_resolution = 4
    dados.use_fill_caps = True
    for pts in splines:
        sp = dados.splines.new("BEZIER")
        sp.bezier_points.add(len(pts) - 1)
        for bp, co in zip(sp.bezier_points, pts):
            bp.co = co
            bp.handle_left_type = "AUTO"
            bp.handle_right_type = "AUTO"
    obj = bpy.data.objects.new(nome, dados)
    col.objects.link(obj)
    return obj


def criar_ponte(col):
    # Viga do arco: curva Bezier com bevel (e o caminho que guia o resto)
    arco = curva_bezier("Ponte_Arco", [pontos_arco()], col, bevel=0.10)
    arco.data.materials.append(novo_material("mat_Ponte_Arco", CORES["Ponte_Arco"]))
    arco.location = PONTE_INICIO
    arco.rotation_euler = (0.0, 0.0, math.radians(PONTE_ANGULO))

    # Tabuleiro: UMA tabua repetida por Array (Fit Curve) e dobrada pelo Curve
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(0.34, 2.0, 0.08), verts=bm.verts)
    bmesh.ops.translate(bm, vec=(0.17, 0, 0.18), verts=bm.verts)
    tabuleiro = objeto_de_bmesh("Ponte_Tabuleiro", bm, col)
    filho(tabuleiro, arco)
    pintar(tabuleiro, "Ponte_Tabuleiro")
    arr = tabuleiro.modifiers.new("Array_tabuas", "ARRAY")
    arr.fit_type = "FIT_CURVE"
    arr.curve = arco
    arr.relative_offset_displace = (1.25, 0, 0)
    bev = tabuleiro.modifiers.new("Bevel_tabua", "BEVEL")
    bev.width = 0.02
    bev.segments = 2
    curva = tabuleiro.modifiers.new("Curve_arco", "CURVE")
    curva.object = arco
    curva.deform_axis = "POS_X"

    # Guarda-corpo: duas curvas paralelas ao arco (y = +-0.95), 0.75 acima
    guarda = curva_bezier(
        "Ponte_Guarda",
        [pontos_arco(dy=0.95, dz=0.95), pontos_arco(dy=-0.95, dz=0.95)],
        col, bevel=0.045)
    filho(guarda, arco)
    guarda.data.materials.append(novo_material("mat_Ponte_Guarda", CORES["Ponte_Guarda"]))

    # Postes: um cilindro -> Array (constante) -> Mirror em Y -> Curve
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=8,
                          radius1=0.04, radius2=0.04, depth=0.85)
    bmesh.ops.translate(bm, vec=(0.1, 0.95, 0.6), verts=bm.verts)
    postes = objeto_de_bmesh("Ponte_Postes", bm, col)
    filho(postes, arco)
    pintar(postes, "Ponte_Guarda")
    arr = postes.modifiers.new("Array_postes", "ARRAY")
    arr.fit_type = "FIT_CURVE"
    arr.curve = arco
    arr.use_relative_offset = False
    arr.use_constant_offset = True
    arr.constant_offset_displace = (0.75, 0, 0)
    esp = postes.modifiers.new("Mirror_Y", "MIRROR")
    esp.use_axis[0] = False
    esp.use_axis[1] = True
    curva = postes.modifiers.new("Curve_arco", "CURVE")
    curva.object = arco
    curva.deform_axis = "POS_X"
    return arco


# ---------------------------------------------------------------------------
# 4. Objeto autoral 3: Torre_Futuro
# ---------------------------------------------------------------------------
def criar_torre(col):
    andares, altura, raio = 12, 8.5, 1.4
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=12,
                          radius1=raio, radius2=raio, depth=altura)
    bmesh.ops.translate(bm, vec=(0, 0, altura / 2), verts=bm.verts)
    # Loop cuts horizontais: subdivide as arestas verticais (andares)
    verticais = [e for e in bm.edges
                 if abs(e.verts[0].co.z - e.verts[1].co.z) > altura / 2]
    bmesh.ops.subdivide_edges(bm, edges=verticais, cuts=andares - 1,
                              use_grid_fill=False)
    # Janelas: inset individual em cada face lateral e extrusao para dentro
    laterais = [f for f in bm.faces if abs(f.normal.z) < 0.1]
    res = bmesh.ops.inset_individual(bm, faces=laterais, thickness=0.09,
                                     depth=-0.07, use_even_offset=True)
    # Topo: inset + extrusao (coroa), inset + extrusao longa (antena)
    topo = next(f for f in bm.faces if f.normal.z > 0.9)
    bmesh.ops.inset_region(bm, faces=[topo], thickness=0.25)
    ext = bmesh.ops.extrude_face_region(bm, geom=[topo])
    vs = [g for g in ext["geom"] if isinstance(g, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, vec=(0, 0, 0.9), verts=vs)
    bmesh.ops.scale(bm, vec=(0.75, 0.75, 1.0), verts=vs,
                    space=Matrix.Translation((0, 0, -(altura + 0.9))))
    topo = next(f for f in bm.faces
                if f.normal.z > 0.9 and f.calc_center_median().z > altura + 0.5)
    bmesh.ops.inset_region(bm, faces=[topo], thickness=0.85)
    ext = bmesh.ops.extrude_face_region(bm, geom=[topo])
    vs = [g for g in ext["geom"] if isinstance(g, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, vec=(0, 0, 2.6), verts=vs)
    bmesh.ops.scale(bm, vec=(0.3, 0.3, 1.0), verts=vs,
                    space=Matrix.Translation((0, 0, -(altura + 3.5))))
    torre = objeto_de_bmesh("Torre_Futuro", bm, col)
    pintar(torre, "Torre_Futuro")

    torcao = torre.modifiers.new("SimpleDeform_twist", "SIMPLE_DEFORM")
    torcao.deform_method = "TWIST"
    torcao.deform_axis = "Z"
    torcao.angle = math.radians(75)
    bev = torre.modifiers.new("Bevel_quinas", "BEVEL")
    bev.width = 0.025
    bev.segments = 2
    bev.limit_method = "ANGLE"

    # Transformacoes: posicao no fim da ponte, rotacao em Z e escala em Z
    fim = PONTE_INICIO + Matrix.Rotation(math.radians(PONTE_ANGULO), 3, "Z") @ \
        Vector((PONTE_COMPRIMENTO + raio + 0.3, 0, 0))
    torre.location = (fim.x, fim.y, 0.0)
    torre.rotation_euler = (0.0, 0.0, math.radians(15))
    torre.scale = (1.0, 1.0, 1.1)
    return torre


# ---------------------------------------------------------------------------
# 5. Auxiliares: blocos de construcao e chao
# ---------------------------------------------------------------------------
def criar_blocos(col, largura_palavra):
    """Base de blocos sob a palavra: um cubo + Array em X e em Y + Bevel.
    A quantidade de blocos acompanha a largura da palavra."""
    lado = 0.8
    quantidade = math.ceil(largura_palavra / (lado * 1.04)) + 1
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=lado)
    bmesh.ops.translate(bm, vec=(lado / 2, lado / 2, lado / 2), verts=bm.verts)
    blocos = objeto_de_bmesh("Blocos_Construcao", bm, col)
    pintar(blocos, "Blocos_Construcao")
    arr_x = blocos.modifiers.new("Array_X", "ARRAY")
    arr_x.count = quantidade
    arr_x.relative_offset_displace = (1.04, 0, 0)
    arr_y = blocos.modifiers.new("Array_Y", "ARRAY")
    arr_y.count = 2
    arr_y.relative_offset_displace = (0, 1.04, 0)
    bev = blocos.modifiers.new("Bevel_blocos", "BEVEL")
    bev.width = 0.06
    bev.segments = 3
    largura = quantidade * lado * 1.04 - 0.04 * lado
    profundidade = 2 * lado * 1.04 - 0.04 * lado
    # mesma rotacao Z da palavra; centralizado na origem da palavra
    giro = math.radians(-4)
    canto = Matrix.Rotation(giro, 3, "Z") @ Vector((-largura / 2, -profundidade / 2, 0))
    blocos.location = (canto.x, 0.75 + canto.y, 0.28)
    blocos.rotation_euler = (0.0, 0.0, giro)
    return blocos, lado


def criar_chao(col):
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=45.0)
    chao = objeto_de_bmesh("Chao", bm, col)
    chao.location = (4.0, 4.0, -0.02)
    pintar(chao, "Chao")
    return chao


# ---------------------------------------------------------------------------
# 6. Cameras e luz
# ---------------------------------------------------------------------------
def criar_camera(nome, col, local, alvo, lente=35.0):
    dados = bpy.data.cameras.new(nome)
    dados.lens = lente
    dados.clip_end = 300
    cam = bpy.data.objects.new(nome, dados)
    cam.location = local
    col.objects.link(cam)
    # aponta a camera para o alvo (rotacao calculada, sem restricao)
    direcao = Vector(alvo) - Vector(local)
    cam.rotation_euler = direcao.to_track_quat("-Z", "Y").to_euler()
    return cam


# ---------------------------------------------------------------------------
# Montagem da cena
# ---------------------------------------------------------------------------
limpar_cena()
cena = bpy.context.scene
cena.frame_start = FRAME_INICIAL
cena.frame_end = FRAME_FINAL
cena.render.fps = FPS
cena.render.fps_base = 1.0

raiz = obter_colecao(NOME_COLECAO)
cols = {chave: obter_colecao(nome, raiz) for chave, nome in SUB.items()}

# Palavra sobre a base de blocos, em pe (rotacao X 90) e levemente girada
palavra, letras, largura_palavra = criar_palavra(cols["palavra"])
blocos, lado_bloco = criar_blocos(cols["aux"], largura_palavra)
palavra.location = (0.0, 0.75, 0.28 + lado_bloco)
palavra.rotation_euler = (math.radians(90), 0.0, math.radians(-4))
palavra.scale = (1.0, 1.0, 1.0)

livro, paginas = criar_livro(cols["autorais"])
ponte = criar_ponte(cols["autorais"])
torre = criar_torre(cols["autorais"])
chao = criar_chao(cols["aux"])

# Camera principal: Track To para um Empty (facil de animar na AP2)
alvo = bpy.data.objects.new("Alvo_Camera", None)
alvo.empty_display_type = "SPHERE"
alvo.empty_display_size = 0.3
alvo.location = (3.4, 2.8, 3.0)
cols["camera"].objects.link(alvo)
cam = criar_camera("CAM_Principal", cols["camera"], (-1.0, -17.0, 5.2), alvo.location,
                   lente=26)
rastreio = cam.constraints.new(type="TRACK_TO")
rastreio.target = alvo
rastreio.track_axis = "TRACK_NEGATIVE_Z"
rastreio.up_axis = "UP_Y"
cena.camera = cam

luz_dados = bpy.data.lights.new("Luz_Sol", type="SUN")
luz_dados.energy = 3.0
luz_dados.angle = math.radians(5)
luz = bpy.data.objects.new("Luz_Sol", luz_dados)
luz.location = (6.0, -8.0, 14.0)
luz.rotation_euler = (math.radians(45), math.radians(10), math.radians(30))
cols["camera"].objects.link(luz)

# Cameras de referencia do storyboard (tres momentos da peca)
sb = cols["story"]
criar_camera("CAM_SB_01_Inicio", sb, (-9.0, -9.5, 2.2), (0.0, 0.5, 0.6), lente=28)
criar_camera("CAM_SB_02_Construcao", sb, (1.0, -11.5, 3.2), (0.0, 0.8, 2.2), lente=35)
criar_camera("CAM_SB_03_Final", sb, (-6.0, -25.0, 12.0), (5.0, 3.5, 3.0), lente=35)

# Fundo e gerenciamento de cor
mundo = cena.world or bpy.data.worlds.new("World")
cena.world = mundo
mundo.use_nodes = True
fundo = next(n for n in mundo.node_tree.nodes if n.type == "BACKGROUND")
fundo.inputs["Color"].default_value = (0.62, 0.75, 0.92, 1.0)
fundo.inputs["Strength"].default_value = 0.8
try:
    cena.view_settings.view_transform = "Standard"
except TypeError:
    pass

cena.render.resolution_x = 1920
cena.render.resolution_y = 1080
cena.render.resolution_percentage = 100
cena.render.image_settings.file_format = "PNG"
cena.render.filepath = "//imagens/"

cena.frame_set(FRAME_INICIAL)
print("AP1: cena 'Ibmec: Construindo o Futuro' criada na colecao", NOME_COLECAO)
