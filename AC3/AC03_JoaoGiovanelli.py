"""
AC03 - Parque Geometrico: transformacoes geometricas 2D e 3D no Blender 4.5 LTS
Aluno: Joao Pedro Giovanelli Berla
Disciplina: Computacao Grafica - CG_26.2_8001

COMO USAR
    1. Abra o Blender 4.5 LTS (arquivo novo, cena "General").
    2. Aba Scripting -> Text -> Open -> este arquivo -> botao "Run Script" (Alt+P).
    3. O script cria a colecao AC03_transformacoes com os objetos 2D e 3D,
       aplica as transformacoes, insere os keyframes, e posiciona camera e luz.

O QUE ESTE SCRIPT FAZ (parte automatizada da atividade)
    - Cria 6 objetos (3 planos no XY + 3 solidos) com nomes coerentes.
    - Aplica transformacoes via script: location, rotation_euler (com
      math.radians) e scale, cobrindo os tres eixos X, Y e Z.
    - Anima o quadrado (translacao + rotacao) e o cubo (escala + rotacao em
      eixos diferentes) com keyframes nos frames 1 e 120, mais um keyframe
      intermediario e easing (bonus).
    - Cria a hierarquia cilindro -> esfera (parent/child) para mostrar uma
      transformacao composta (bonus).

O QUE FICA PARA A INTERFACE (parte manual da atividade)
    - obj2d_triangulo: mover (G), rotacionar (R) e escalar (S) na mao.
    - obj3d_cilindro: keyframes de rotacao em Z nos frames 1 e 120 com a
      tecla I. Como a esfera e filha do cilindro, ela passa a orbitar em volta
      dele -- a rotacao do pai vira translacao circular do filho.
"""

import math

import bpy

# ---------------------------------------------------------------------------
# Parametros gerais
# ---------------------------------------------------------------------------
NOME_COLECAO = "AC03_transformacoes"
FRAME_INICIAL = 1
FRAME_FINAL = 120          # 120 frames a 24 fps = 5 segundos
FPS = 24

CORES = {                  # RGBA (0-1) usadas no Principled BSDF de cada objeto
    "obj2d_quadrado": (0.90, 0.30, 0.20, 1.0),
    "obj2d_triangulo": (0.95, 0.75, 0.15, 1.0),
    "obj2d_circulo": (0.25, 0.60, 0.90, 1.0),
    "obj3d_cubo": (0.20, 0.70, 0.40, 1.0),
    "obj3d_cilindro": (0.55, 0.35, 0.80, 1.0),
    "obj3d_esfera": (0.95, 0.45, 0.65, 1.0),
    "chao": (0.70, 0.70, 0.68, 1.0),
}


# ---------------------------------------------------------------------------
# Funcoes auxiliares
# ---------------------------------------------------------------------------
def limpar_cena():
    """Remove tudo que este script cria (para poder rodar mais de uma vez) e
    os objetos padrao do arquivo novo (Cube, Light, Camera)."""
    cena = bpy.context.scene
    col = bpy.data.collections.get(NOME_COLECAO)
    if col is not None:
        for obj in list(col.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.collections.remove(col)
    for nome in ("Cube", "Light", "Camera", "cam_AC03", "luz_sol", "chao", "alvo_camera"):
        obj = bpy.data.objects.get(nome)
        if obj is not None:
            bpy.data.objects.remove(obj, do_unlink=True)
    # limpa dados orfaos (malhas/materiais sem usuario)
    for bloco in (bpy.data.meshes, bpy.data.materials, bpy.data.cameras,
                  bpy.data.lights):
        for dado in list(bloco):
            if dado.users == 0:
                bloco.remove(dado)
    cena.frame_set(FRAME_INICIAL)


def obter_colecao():
    """Cria (ou reaproveita) a colecao AC03_transformacoes ligada a cena."""
    col = bpy.data.collections.get(NOME_COLECAO)
    if col is None:
        col = bpy.data.collections.new(NOME_COLECAO)
        bpy.context.scene.collection.children.link(col)
    return col


def mover_para_colecao(obj, col):
    """Tira o objeto das outras colecoes e o coloca so na nossa."""
    for outra in list(obj.users_collection):
        outra.objects.unlink(obj)
    col.objects.link(obj)


def novo_material(nome, cor):
    """Material simples com a cor no Principled BSDF (afeta o render, nao so o
    viewport). O no e procurado pelo tipo, porque o nome muda com o idioma."""
    mat = bpy.data.materials.new(nome)
    mat.use_nodes = True
    bsdf = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = cor
    bsdf.inputs["Roughness"].default_value = 0.5
    mat.diffuse_color = cor                  # cor tambem no viewport solido
    return mat


def registrar(obj, nome, col):
    """Renomeia, coloca na colecao e aplica o material padrao do objeto."""
    obj.name = nome
    obj.data.name = nome + "_mesh"
    mover_para_colecao(obj, col)
    if nome in CORES:
        obj.data.materials.append(novo_material("mat_" + nome, CORES[nome]))
    return obj


def criar_triangulo(nome, location, col):
    """Um Plane tem 4 vertices; aqui a malha e construida direto com 3
    vertices e 1 face -- equivale a editar o Plane e apagar um vertice."""
    malha = bpy.data.meshes.new(nome + "_mesh")
    vertices = [(-1.0, -0.8, 0.0), (1.0, -0.8, 0.0), (0.0, 1.0, 0.0)]
    faces = [(0, 1, 2)]
    malha.from_pydata(vertices, [], faces)
    malha.update()
    obj = bpy.data.objects.new(nome, malha)
    obj.location = location
    col.objects.link(obj)
    obj.data.materials.append(novo_material("mat_" + nome, CORES[nome]))
    return obj


def keyframe(obj, frame, location=None, rotation_deg=None, scale=None):
    """Define os valores no frame indicado e insere os keyframes
    correspondentes. Rotacao entra em GRAUS e e convertida com math.radians,
    porque rotation_euler espera radianos."""
    bpy.context.scene.frame_set(frame)
    if location is not None:
        obj.location = location
        obj.keyframe_insert(data_path="location", frame=frame)
    if rotation_deg is not None:
        obj.rotation_euler = tuple(math.radians(a) for a in rotation_deg)
        obj.keyframe_insert(data_path="rotation_euler", frame=frame)
    if scale is not None:
        obj.scale = scale
        obj.keyframe_insert(data_path="scale", frame=frame)


def aplicar_easing(obj, interpolacao="SINE", easing="EASE_IN_OUT"):
    """Bonus: troca a interpolacao das curvas de animacao do objeto, para o
    movimento acelerar e desacelerar suavemente em vez de ser linear."""
    if obj.animation_data is None or obj.animation_data.action is None:
        return
    for fcurve in obj.animation_data.action.fcurves:
        for kp in fcurve.keyframe_points:
            kp.interpolation = interpolacao
            kp.easing = easing


# ---------------------------------------------------------------------------
# 1. Cena, timeline e colecao
# ---------------------------------------------------------------------------
limpar_cena()
cena = bpy.context.scene
cena.frame_start = FRAME_INICIAL
cena.frame_end = FRAME_FINAL
cena.render.fps = FPS
col = obter_colecao()

# ---------------------------------------------------------------------------
# 2. Elementos 2D (plano XY, z = 0)
# ---------------------------------------------------------------------------
# Quadrado: Plane de lado 2, transladado em X e Y (transformacao 2D)
bpy.ops.mesh.primitive_plane_add(size=2, location=(-4.0, -2.5, 0.0))
quadrado = registrar(bpy.context.active_object, "obj2d_quadrado", col)

# Triangulo: malha de 3 vertices. Fica em (0, -2, 0) e recebe as
# transformacoes MANUAIS (G, R, S) na interface.
triangulo = criar_triangulo("obj2d_triangulo", (0.0, -2.0, 0.0), col)

# Circulo: Mesh Circle preenchido (NGON), escalado no plano (escala 2D)
bpy.ops.mesh.primitive_circle_add(vertices=48, radius=1.0, fill_type="NGON",
                                  location=(4.0, -2.5, 0.0))
circulo = registrar(bpy.context.active_object, "obj2d_circulo", col)
circulo.scale = (1.3, 1.3, 1.0)                       # escala uniforme em X e Y
circulo.rotation_euler = (0.0, 0.0, math.radians(15))  # rotacao 2D em Z

# ---------------------------------------------------------------------------
# 3. Elementos 3D (acima do plano)
# ---------------------------------------------------------------------------
# Cubo: sera animado (escala + rotacao em eixos diferentes)
bpy.ops.mesh.primitive_cube_add(size=2, location=(-4.0, 2.5, 1.0))
cubo = registrar(bpy.context.active_object, "obj3d_cubo", col)

# Cilindro: transformacao 3D por script (escala em Z, rotacao em Y).
# Os keyframes de rotacao em Z dele sao inseridos MANUALMENTE na interface.
bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=0.8, depth=2.0,
                                    location=(0.0, 2.5, 1.0))
cilindro = registrar(bpy.context.active_object, "obj3d_cilindro", col)
cilindro.scale = (1.0, 1.0, 1.25)                      # transformacao no eixo Z
cilindro.rotation_euler = (0.0, math.radians(10), 0.0)  # rotacao no eixo Y

# Esfera UV: transladada e escalada por script
bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=0.6,
                                     location=(4.0, 2.5, 0.8))
esfera = registrar(bpy.context.active_object, "obj3d_esfera", col)
for face in esfera.data.polygons:      # sombreamento suave (so estetica)
    face.use_smooth = True

# ---------------------------------------------------------------------------
# 4. Hierarquia parent/child (bonus): a esfera vira filha do cilindro
# ---------------------------------------------------------------------------
# A posicao da esfera passa a ser relativa ao cilindro (espaco LOCAL do pai).
# Quando o cilindro rotacionar em Z, a esfera descreve uma orbita em volta
# dele: rotacao do pai + deslocamento do filho = transformacao composta.
esfera.parent = cilindro
esfera.matrix_parent_inverse.identity()
esfera.location = (2.2, 0.0, 0.9)      # 2.2 unidades ao lado do cilindro (local)

# ---------------------------------------------------------------------------
# 5. Animacao por script (frames 1 a 120)
# ---------------------------------------------------------------------------
# Quadrado (objeto 2D): translada em X e Y e rotaciona em Z, com um keyframe
# intermediario no frame 60 para uma etapa a mais no movimento (bonus).
keyframe(quadrado, FRAME_INICIAL, location=(-4.0, -2.5, 0.0), rotation_deg=(0, 0, 0))
keyframe(quadrado, 60, location=(-3.4, -3.3, 0.0), rotation_deg=(0, 0, 45))
keyframe(quadrado, FRAME_FINAL, location=(-2.6, -2.0, 0.0), rotation_deg=(0, 0, 135))

# Cubo (objeto 3D): escala (cresce em Z, encolhe em X) e rotaciona em dois
# eixos diferentes (X e Z). Com easing suave de entrada e saida (bonus).
keyframe(cubo, FRAME_INICIAL, rotation_deg=(0, 0, 0), scale=(1.0, 1.0, 1.0))
keyframe(cubo, FRAME_FINAL, rotation_deg=(90, 0, 45), scale=(0.7, 1.0, 1.6))
aplicar_easing(cubo)

# ---------------------------------------------------------------------------
# 6. Chao, camera, luz e configuracao de render
# ---------------------------------------------------------------------------
bpy.ops.mesh.primitive_plane_add(size=100, location=(0.0, 0.0, -0.02))
chao = bpy.context.active_object
chao.name = "chao"
mover_para_colecao(chao, col)
chao.data.materials.append(novo_material("mat_chao", CORES["chao"]))

cam_data = bpy.data.cameras.new("cam_AC03")
cam_data.lens = 35
camera = bpy.data.objects.new("cam_AC03", cam_data)
camera.location = (10.5, -12.5, 8.5)
col.objects.link(camera)
alvo_cam = bpy.data.objects.new("alvo_camera", None)   # Empty no centro da cena
alvo_cam.location = (0.0, 0.0, 0.4)
alvo_cam.empty_display_size = 0.5
col.objects.link(alvo_cam)
alvo = camera.constraints.new(type="TRACK_TO")   # camera sempre olha o Empty
alvo.target = alvo_cam
alvo.track_axis = "TRACK_NEGATIVE_Z"
alvo.up_axis = "UP_Y"
cena.camera = camera

luz_data = bpy.data.lights.new("luz_sol", type="SUN")
luz_data.energy = 1.6
luz_data.angle = math.radians(4)
luz = bpy.data.objects.new("luz_sol", luz_data)
luz.location = (5.0, -4.0, 10.0)
luz.rotation_euler = (math.radians(50), math.radians(-15), math.radians(-60))
col.objects.link(luz)

mundo = cena.world or bpy.data.worlds.new("World")
cena.world = mundo
mundo.use_nodes = True
fundo = next(n for n in mundo.node_tree.nodes if n.type == "BACKGROUND")
fundo.inputs["Color"].default_value = (0.75, 0.80, 0.88, 1.0)
fundo.inputs["Strength"].default_value = 0.25

# "Standard" mantem as cores dos materiais como foram definidas (o padrao AgX
# deixa tudo mais pastel). A lista de opcoes vem do OpenColorIO e nao aparece
# no RNA, entao a atribuicao e protegida com try/except.
try:
    cena.view_settings.view_transform = "Standard"
except TypeError:
    pass

cena.render.resolution_x = 1920
cena.render.resolution_y = 1080
cena.render.resolution_percentage = 100
cena.render.image_settings.file_format = "PNG"
cena.render.filepath = "//AC03_JoaoGiovanelli.png"

cena.frame_set(FRAME_INICIAL)
print("AC03: cena 'Parque Geometrico' criada. Agora faca a parte manual "
      "(G/R/S no obj2d_triangulo e keyframes no obj3d_cilindro).")
