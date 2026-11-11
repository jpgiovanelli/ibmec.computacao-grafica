"""
AC04 - Evolucao da cena: modelos de iluminacao (Lambert, Phong e Blinn-Phong)
Aluno: Joao Pedro Giovanelli Berla
Disciplina: Computacao Grafica - CG_26.2_8001

COMO USAR
    1. Abra AP1/AP1_JoaoGiovanelli.blend no Blender 4.5 LTS.
    2. Aba Scripting -> Text -> Open -> este arquivo -> "Run Script" (Alt+P).
       (ou, pelo terminal:
        blender -b AP1/AP1_JoaoGiovanelli.blend --python AC4/AC04_JoaoGiovanelli.py)
    3. O script NAO altera o arquivo da AP1: ele salva uma copia evoluida em
       AC4/AC04_JoaoGiovanelli.blend. Pode ser rodado de novo sobre o AC04.

O QUE ESTE SCRIPT FAZ
    - Cria os materiais MAT_Lambert, MAT_Phong e MAT_BlinnPhong (Principled BSDF)
      e aplica um em cada objeto autoral da AP1:
          Livro_Aberto (+ paginas)  -> MAT_Lambert     (so difusa, fosco)
          Ponte_Arco   (+ partes)   -> MAT_Phong       (difusa + especular)
          Torre_Futuro              -> MAT_BlinnPhong  (especular mais nitido)
      A palavra "Ibmec" continua com o material da AP1 (identidade preservada).
    - Troca a luz da AP1 por uma luz principal Sun posicionada para mostrar
      areas iluminadas, sombras e brilhos especulares; o World (ceu em
      degrade) faz o papel de luz de preenchimento suave.
    - Organiza as luzes na colecao 06_AC04_Iluminacao e cria a colecao
      07_AC04_Comparacao com as cameras de detalhe e tres esferas-amostra
      (uma por material) para comparar os modelos sem a influencia da forma.
"""

import math
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector

ARQ_AP1 = "AP1_JoaoGiovanelli.blend"
ARQ_AC04 = "AC04_JoaoGiovanelli.blend"
COLECAO_RAIZ = "AP1_Ibmec_Conceito"
COL_LUZES = "06_AC04_Iluminacao"
COL_COMPARACAO = "07_AC04_Comparacao"

# ---------------------------------------------------------------------------
# Materiais: os tres modelos como aproximacoes no Principled BSDF.
#   rugosidade -> "Roughness" (espalhamento do brilho especular)
#   especular  -> "Specular IOR Level" (no Blender 4.x substitui o antigo
#                 "Specular"; 0.5 = sem ajuste, 0 = sem reflexo especular)
# ---------------------------------------------------------------------------
MATERIAIS = {
    "MAT_Lambert": {
        "cor": (0.50, 0.07, 0.05, 1.0),        # vermelho tijolo
        "rugosidade": 1.0,
        "especular": 0.0,
        "objetos": ("Livro_Aberto", "Livro_Paginas"),
    },
    "MAT_Phong": {
        "cor": (0.05, 0.32, 0.09, 1.0),        # verde
        "rugosidade": 0.2,
        "especular": 0.5,
        "objetos": ("Ponte_Arco", "Ponte_Tabuleiro", "Ponte_Guarda", "Ponte_Postes"),
    },
    "MAT_BlinnPhong": {
        "cor": (0.02, 0.26, 0.40, 1.0),        # azul-petroleo
        "rugosidade": 0.1,
        "especular": 0.8,
        "objetos": ("Torre_Futuro",),
    },
}

# Luz principal (Sun): direcao de onde a luz vem (azimute e elevacao, graus)
SOL_AZIMUTE = -150.0       # frente-esquerda em relacao a camera principal
SOL_ELEVACAO = 35.0
SOL_FORCA = 4.0            # irradiancia (W/m2)
SOL_ANGULO = 3.0           # diametro angular do disco: sombra levemente suave
SOL_COR = (1.0, 0.96, 0.90)

MUNDO_HORIZONTE = (0.85, 0.88, 0.92, 1.0)
MUNDO_ZENITE = (0.12, 0.32, 0.78, 1.0)
MUNDO_FORCA = 0.55


# ---------------------------------------------------------------------------
# Auxiliares
# ---------------------------------------------------------------------------
def caminho_destino():
    atual = Path(bpy.data.filepath)
    if atual.name not in (ARQ_AP1, ARQ_AC04):
        raise RuntimeError("Abra AP1/AP1_JoaoGiovanelli.blend antes de rodar este script.")
    return atual.parent.parent / "AC4" / ARQ_AC04


def obter_colecao(nome, pai):
    col = bpy.data.collections.get(nome)
    if col is None:
        col = bpy.data.collections.new(nome)
        pai.children.link(col)
    return col


def mover_para(obj, col):
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    col.objects.link(obj)


def principled(mat):
    return next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")


def material_modelo(nome, cor, rugosidade, especular):
    mat = bpy.data.materials.get(nome) or bpy.data.materials.new(nome)
    mat.use_nodes = True
    bsdf = principled(mat)
    bsdf.inputs["Base Color"].default_value = cor
    bsdf.inputs["Metallic"].default_value = 0.0
    bsdf.inputs["Roughness"].default_value = rugosidade
    bsdf.inputs["Specular IOR Level"].default_value = especular
    bsdf.inputs["IOR"].default_value = 1.5
    # parcela difusa lambertiana pura (Oren-Nayar desligado)
    bsdf.inputs["Diffuse Roughness"].default_value = 0.0
    bsdf.inputs["Coat Weight"].default_value = 0.0
    bsdf.inputs["Sheen Weight"].default_value = 0.0
    mat.diffuse_color = cor               # cor no viewport Solid
    mat.roughness = rugosidade
    return mat


def aplicar(nome_obj, mat):
    obj = bpy.data.objects[nome_obj]
    obj.data.materials.clear()
    obj.data.materials.append(mat)


def apontar(obj, alvo):
    direcao = Vector(alvo) - obj.location
    obj.rotation_euler = direcao.to_track_quat("-Z", "Y").to_euler()


def nova_camera(nome, col, local, alvo, lente):
    dados = bpy.data.cameras.get(nome) or bpy.data.cameras.new(nome)
    dados.lens = lente
    dados.clip_end = 300
    cam = bpy.data.objects.get(nome) or bpy.data.objects.new(nome, dados)
    if not cam.users_collection:
        col.objects.link(cam)
    cam.location = local
    apontar(cam, alvo)
    return cam


def direcao_sol(azimute, elevacao):
    az, el = math.radians(azimute), math.radians(elevacao)
    return Vector((math.cos(el) * math.cos(az), math.cos(el) * math.sin(az), math.sin(el)))


def posicionar_sol(luz, azimute, elevacao, centro=Vector((4.0, 2.0, 2.0))):
    para_luz = direcao_sol(azimute, elevacao)
    luz.location = centro + para_luz * 22.0
    # a luz emite ao longo do seu -Z: alinha -Z com o sentido da luz (-para_luz)
    luz.rotation_euler = (-para_luz).to_track_quat("-Z", "Y").to_euler()


# ---------------------------------------------------------------------------
# 1. Materiais Lambert / Phong / Blinn-Phong nos tres objetos autorais
# ---------------------------------------------------------------------------
def criar_materiais():
    for nome, cfg in MATERIAIS.items():
        mat = material_modelo(nome, cfg["cor"], cfg["rugosidade"], cfg["especular"])
        for nome_obj in cfg["objetos"]:
            aplicar(nome_obj, mat)
    # materiais da AP1 que ficaram sem uso nao sao salvos
    for mat in list(bpy.data.materials):
        if mat.users == 0:
            bpy.data.materials.remove(mat)


# ---------------------------------------------------------------------------
# 2. Iluminacao: luz principal Sun + World como preenchimento
# ---------------------------------------------------------------------------
def configurar_luz(raiz):
    col_luz = obter_colecao(COL_LUZES, raiz)
    luz = bpy.data.objects.get("Luz_Principal") or bpy.data.objects.get("Luz_Sol")
    luz.name = "Luz_Principal"
    luz.data.name = "Luz_Principal"
    mover_para(luz, col_luz)
    luz.data.type = "SUN"
    luz.data.energy = SOL_FORCA
    luz.data.angle = math.radians(SOL_ANGULO)
    luz.data.color = SOL_COR
    luz.data.use_shadow = True
    posicionar_sol(luz, SOL_AZIMUTE, SOL_ELEVACAO)

    # a colecao 04 ficou so com a camera e o alvo
    col_cam = bpy.data.collections.get("04_Camera_Luz")
    if col_cam is not None:
        col_cam.name = "04_Camera"
    return luz


def configurar_mundo(cena):
    """Ceu em degrade (horizonte claro -> zenite azul). Funciona como luz de
    preenchimento suave e da aos materiais polidos algo para refletir."""
    mundo = cena.world
    mundo.use_nodes = True
    nt = mundo.node_tree
    nt.nodes.clear()
    coord = nt.nodes.new("ShaderNodeTexCoord")
    separa = nt.nodes.new("ShaderNodeSeparateXYZ")
    rampa = nt.nodes.new("ShaderNodeValToRGB")
    fundo = nt.nodes.new("ShaderNodeBackground")
    saida = nt.nodes.new("ShaderNodeOutputWorld")
    coord.location, separa.location = (-900, 0), (-700, 0)
    rampa.location, fundo.location, saida.location = (-500, 0), (-200, 0), (0, 0)
    # "Generated" no World = direcao de visada; Z = altura no ceu (-1 a 1)
    nt.links.new(coord.outputs["Generated"], separa.inputs["Vector"])
    nt.links.new(separa.outputs["Z"], rampa.inputs["Fac"])
    nt.links.new(rampa.outputs["Color"], fundo.inputs["Color"])
    nt.links.new(fundo.outputs["Background"], saida.inputs["Surface"])
    elementos = rampa.color_ramp.elements
    elementos[0].position, elementos[0].color = 0.0, MUNDO_HORIZONTE
    elementos[1].position, elementos[1].color = 0.35, MUNDO_ZENITE
    fundo.inputs["Strength"].default_value = MUNDO_FORCA


# ---------------------------------------------------------------------------
# 3. Comparacao: cameras de detalhe e esferas-amostra
# ---------------------------------------------------------------------------
def criar_comparacao(raiz):
    col = obter_colecao(COL_COMPARACAO, raiz)
    # cameras de detalhe, uma por objeto autoral (mesma luz da cena)
    nova_camera("CAM_AC04_Livro", col, (-9.5, -10.5, 4.2), (-2.5, -0.5, 0.4), 35)
    nova_camera("CAM_AC04_Ponte", col, (7.0, -5.5, 5.0), (11.2, 3.9, 1.0), 35)
    nova_camera("CAM_AC04_Torre", col, (8.5, -7.5, 5.0), (15.8, 7.0, 6.8), 38)

    # tres esferas iguais, uma por material, sobre um fundo neutro curvo,
    # longe do enquadramento principal (a esquerda e atras da camera)
    base = Vector((-24.0, -24.0, 0.0))
    for i, nome in enumerate(MATERIAIS):
        obj_nome = "Amostra_" + nome.removeprefix("MAT_")
        obj = bpy.data.objects.get(obj_nome)
        if obj is None:
            malha = bpy.data.meshes.new(obj_nome + "_mesh")
            bm = bmesh.new()
            bmesh.ops.create_uvsphere(bm, u_segments=64, v_segments=32, radius=0.9)
            for f in bm.faces:
                f.smooth = True
            bm.to_mesh(malha)
            bm.free()
            obj = bpy.data.objects.new(obj_nome, malha)
            col.objects.link(obj)
        obj.location = base + Vector(((i - 1) * 2.6, 0.0, 0.9))
        aplicar(obj_nome, bpy.data.materials[nome])

    fundo = bpy.data.objects.get("Amostras_Fundo")
    if fundo is None:
        # perfil em L arredondado (chao + parede) extrudado em X
        verts, faces = [], []
        perfil = []
        for k in range(12):                     # chao (passa por tras da camera)
            perfil.append((-14.0 + k * (13.75 / 11), 0.0))
        for k in range(1, 13):                  # quarto de circulo r = 1.5
            a = math.radians(90 * k / 12)
            perfil.append((-0.25 + 1.5 * math.sin(a), 1.5 - 1.5 * math.cos(a)))
        for k in range(1, 9):                   # parede
            perfil.append((1.25, 1.5 + k * 0.5))
        for x in (-9.0, 9.0):
            for (y, z) in perfil:
                verts.append((x, y, z))
        n = len(perfil)
        for k in range(n - 1):
            faces.append((k, k + 1, n + k + 1, n + k))
        malha = bpy.data.meshes.new("Amostras_Fundo_mesh")
        malha.from_pydata(verts, [], faces)
        for p in malha.polygons:
            p.use_smooth = True
        fundo = bpy.data.objects.new("Amostras_Fundo", malha)
        col.objects.link(fundo)
    fundo.location = base + Vector((0.0, 0.6, 0.0))
    fundo.rotation_euler = (0.0, 0.0, math.radians(-13))   # de frente para a camera
    mat_fundo = bpy.data.materials.get("MAT_Fundo_Neutro") or \
        material_modelo("MAT_Fundo_Neutro", (0.55, 0.55, 0.55, 1.0), 0.9, 0.2)
    fundo.data.materials.clear()
    fundo.data.materials.append(mat_fundo)

    nova_camera("CAM_AC04_Amostras", col, base + Vector((-2.0, -9.6, 1.7)),
                base + Vector((0.0, 0.0, 0.9)), 40)
    # a colecao de comparacao nao aparece no render principal (F12);
    # o script de renders liga e desliga quando precisa
    col.hide_render = True
    return col


# ---------------------------------------------------------------------------
# 4. Render
# ---------------------------------------------------------------------------
def configurar_render(cena):
    try:
        cena.render.engine = "BLENDER_EEVEE_NEXT"
    except TypeError:
        cena.render.engine = "BLENDER_EEVEE"
    ee = cena.eevee
    ee.taa_render_samples = 64
    ee.taa_samples = 16
    ee.use_raytracing = True               # reflexos dos materiais polidos
    ee.use_shadows = True
    ee.shadow_ray_count = 2
    ee.shadow_step_count = 8
    cena.view_settings.view_transform = "AgX"
    cena.view_settings.look = "AgX - Base Contrast"
    cena.render.resolution_x = 1920
    cena.render.resolution_y = 1080
    cena.render.resolution_percentage = 100
    cena.render.image_settings.file_format = "PNG"
    cena.render.filepath = "//imagens/"
    cena.camera = bpy.data.objects["CAM_Principal"]
    cena.frame_set(1)


# ---------------------------------------------------------------------------
# Montagem
# ---------------------------------------------------------------------------
destino = caminho_destino()
cena = bpy.context.scene
raiz = bpy.data.collections[COLECAO_RAIZ]

criar_materiais()
configurar_luz(raiz)
configurar_mundo(cena)
criar_comparacao(raiz)
configurar_render(cena)

destino.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(destino))
print("AC04: cena salva em", destino)
