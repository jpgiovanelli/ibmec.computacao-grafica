"""
AC05 - Evolucao da cena: materiais PBR e texturas
Aluno: Joao Pedro Giovanelli Berla
Disciplina: Computacao Grafica - CG_26.2_8001

COMO USAR
    1. Abra AC4/AC04_JoaoGiovanelli.blend no Blender 4.5 LTS.
    2. Aba Scripting -> Text -> Open -> este arquivo -> "Run Script" (Alt+P).
       (ou: blender -b AC4/AC04_JoaoGiovanelli.blend --python AC5/AC05_JoaoGiovanelli.py)
    3. O script NAO altera os arquivos da AP1 e da AC04: salva a copia evoluida
       em AC5/AC05_JoaoGiovanelli.blend, com as imagens EMPACOTADAS no .blend.

O QUE ESTE SCRIPT FAZ
    - Troca os materiais de estudo da AC04 (Lambert/Phong/Blinn-Phong) por
      materiais PBR (Principled BSDF) com nomes descritivos:
          Livro_Aberto    MAT_Livro_Couro_PBR       imagem: Base Color + Roughness + Normal
          Livro_Paginas   MAT_Livro_Papel_PBR       procedural (linhas de "texto" + fibra)
          Ponte_Tabuleiro MAT_Ponte_Madeira_PBR     imagem: Base Color + Roughness + Normal
          Ponte (arco, guarda-corpo, postes)
                          MAT_Ponte_Aco_PBR         metal (Metallic 1)
          Torre_Futuro    MAT_Torre_Aluminio_Escovado_PBR (estrutura, procedural)
                          MAT_Torre_Vidro_Espelhado_PBR   (janelas: espelho azulado)
          Ibmec_*         MAT_Ibmec_Azul_PBR        mesma cor da AP1, sem textura
    - Cria/revisa os mapas UV dos objetos com textura de imagem
      (Cube Projection na capa e nas tabuas, Unwrap nas paginas).
    - Espaco de cor: Base Color em sRGB; Roughness e Normal em Non-Color;
      o mapa normal passa pelo no Normal Map antes do Principled BSDF.
    - Organiza os elementos auxiliares (cameras de detalhe e esferas-amostra)
      na colecao AC05_Materiais_Texturas.
    - Empacota as imagens no .blend (File > External Data > Pack Resources).

TEXTURAS (Poly Haven, licenca CC0) - arquivos em AC5/texturas/
    leather_red_03 (Rob Tuytel)        https://polyhaven.com/a/leather_red_03
    oak_veneer_01  (Jenelle van Heerden) https://polyhaven.com/a/oak_veneer_01
"""

import math
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector

ARQ_AC04 = "AC04_JoaoGiovanelli.blend"
ARQ_AC05 = "AC05_JoaoGiovanelli.blend"
COL_AC04 = "07_AC04_Comparacao"
COL_AC05 = "AC05_Materiais_Texturas"

# Texturas de imagem: (arquivo, espaco de cor)
COURO = {
    "cor": ("leather_red_03_coll1_1k.jpg", "sRGB"),
    "rugosidade": ("leather_red_03_rough_1k.jpg", "Non-Color"),
    "normal": ("leather_red_03_nor_gl_1k.jpg", "Non-Color"),
}
MADEIRA = {
    "cor": ("oak_veneer_01_diff_1k.jpg", "sRGB"),
    "rugosidade": ("oak_veneer_01_rough_1k.jpg", "Non-Color"),
    "normal": ("oak_veneer_01_nor_gl_1k.jpg", "Non-Color"),
}
# Escala das texturas: definida no proprio Cube Projection (cube_size = metros
# cobertos por 1 ladrilho da imagem), assim o no Mapping fica em escala 1.
LADRILHO_COURO = 2.5           # m por ladrilho na capa do livro gigante
LADRILHO_MADEIRA = 1.83        # tamanho real da amostra oak_veneer_01 (1,83 m)
DESLOC_U_TABUAS = 0.37         # cada copia do Array usa outra regiao da madeira


# ---------------------------------------------------------------------------
# Auxiliares
# ---------------------------------------------------------------------------
def caminhos():
    atual = Path(bpy.data.filepath)
    if atual.name not in (ARQ_AC04, ARQ_AC05):
        raise RuntimeError("Abra AC4/AC04_JoaoGiovanelli.blend antes de rodar este script.")
    raiz = atual.parent.parent
    return raiz / "AC5" / ARQ_AC05, raiz / "AC5" / "texturas"


def no(nt, tipo, x, y, rotulo=None):
    n = nt.nodes.new(tipo)
    n.location = (x, y)
    if rotulo:
        n.label = rotulo
    return n


def novo_material(nome):
    """Material limpo: so Principled BSDF + Material Output."""
    mat = bpy.data.materials.get(nome) or bpy.data.materials.new(nome)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    bsdf = no(nt, "ShaderNodeBsdfPrincipled", 300, 300)
    saida = no(nt, "ShaderNodeOutputMaterial", 650, 300)
    nt.links.new(bsdf.outputs["BSDF"], saida.inputs["Surface"])
    return mat, nt, bsdf


def ajustar(bsdf, cor=None, metalico=0.0, rugosidade=0.5, especular=0.5, **extra):
    if cor is not None:
        bsdf.inputs["Base Color"].default_value = cor
    bsdf.inputs["Metallic"].default_value = metalico
    bsdf.inputs["Roughness"].default_value = rugosidade
    bsdf.inputs["Specular IOR Level"].default_value = especular
    for nome, valor in extra.items():
        bsdf.inputs[nome].default_value = valor


def imagem(pasta, arquivo, espaco):
    img = bpy.data.images.load(str(pasta / arquivo), check_existing=True)
    img.colorspace_settings.name = espaco
    return img


def material_imagens(nome, pasta, mapas, escala, cor_viewport, metalico=0.0):
    """Principled BSDF com o conjunto Base Color + Roughness + Normal.

    UV -> Mapping (escala) -> 3 Image Texture
        cor        (sRGB)      -> Base Color
        rugosidade (Non-Color) -> Roughness
        normal     (Non-Color) -> Normal Map (Tangent Space) -> Normal
    """
    mat, nt, bsdf = novo_material(nome)
    coord = no(nt, "ShaderNodeTexCoord", -1100, 300)
    mapeamento = no(nt, "ShaderNodeMapping", -900, 300)
    mapeamento.inputs["Scale"].default_value = (escala, escala, 1.0)
    nt.links.new(coord.outputs["UV"], mapeamento.inputs["Vector"])

    rotulos = {"cor": "Base Color (sRGB)", "rugosidade": "Roughness (Non-Color)",
               "normal": "Normal (Non-Color)"}
    texs = {}
    for i, chave in enumerate(("cor", "rugosidade", "normal")):
        arquivo, espaco = mapas[chave]
        tex = no(nt, "ShaderNodeTexImage", -600, 560 - i * 300, rotulos[chave])
        tex.image = imagem(pasta, arquivo, espaco)
        tex.interpolation = "Linear"
        tex.extension = "REPEAT"
        nt.links.new(mapeamento.outputs["Vector"], tex.inputs["Vector"])
        texs[chave] = tex

    mapa_normal = no(nt, "ShaderNodeNormalMap", -50, -60)
    mapa_normal.space = "TANGENT"
    mapa_normal.inputs["Strength"].default_value = 1.0
    nt.links.new(texs["cor"].outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(texs["rugosidade"].outputs["Color"], bsdf.inputs["Roughness"])
    nt.links.new(texs["normal"].outputs["Color"], mapa_normal.inputs["Color"])
    nt.links.new(mapa_normal.outputs["Normal"], bsdf.inputs["Normal"])
    ajustar(bsdf, metalico=metalico)
    mat.diffuse_color = cor_viewport
    return mat


def aplicar(nomes, *mats):
    for nome in nomes:
        dados = bpy.data.objects[nome].data
        dados.materials.clear()
        for m in mats:
            dados.materials.append(m)


def uv_operador(obj, operador, **kw):
    """Edit Mode -> seleciona tudo -> operador de UV -> Object Mode."""
    vl = bpy.context.view_layer
    for o in vl.objects:
        o.select_set(False)
    vl.objects.active = obj
    obj.select_set(True)
    if not obj.data.uv_layers:
        obj.data.uv_layers.new(name="UVMap")
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    operador(**kw)
    bpy.ops.object.mode_set(mode="OBJECT")


# ---------------------------------------------------------------------------
# 1. Materiais PBR dos objetos autorais
# ---------------------------------------------------------------------------
def material_papel():
    """Papel procedural: cor creme, linhas de "texto" geradas a partir das UVs
    e relevo de fibra (Noise -> Bump). Nao usa imagem."""
    mat, nt, bsdf = novo_material("MAT_Livro_Papel_PBR")
    coord = no(nt, "ShaderNodeTexCoord", -1500, 300)
    separa = no(nt, "ShaderNodeSeparateXYZ", -1300, 300)
    nt.links.new(coord.outputs["UV"], separa.inputs["Vector"])

    def mat_op(op, x, y, a=None, b=None, valor=None):
        n = no(nt, "ShaderNodeMath", x, y)
        n.operation = op
        if valor is not None:
            n.inputs[1].default_value = valor
        if a is not None:
            nt.links.new(a, n.inputs[0])
        if b is not None:
            nt.links.new(b, n.inputs[1])
        return n

    u, v = separa.outputs["X"], separa.outputs["Y"]
    # linhas: fract(v * 34) < 0.38  (34 linhas na altura da pagina)
    linhas = mat_op("MULTIPLY", -1100, 500, v, valor=34.0)
    linhas = mat_op("FRACT", -950, 500, linhas.outputs[0])
    linhas = mat_op("LESS_THAN", -800, 500, linhas.outputs[0], valor=0.32)
    # mancha de texto: margens nas quatro bordas (UV do Unwrap vai de 0 a ~0,75 em U)
    m1 = mat_op("GREATER_THAN", -1100, 300, u, valor=0.08)
    m2 = mat_op("LESS_THAN", -1100, 150, u, valor=0.66)
    m3 = mat_op("GREATER_THAN", -1100, 0, v, valor=0.07)
    m4 = mat_op("LESS_THAN", -1100, -150, v, valor=0.93)
    mancha = mat_op("MULTIPLY", -950, 220, m1.outputs[0], m2.outputs[0])
    mancha = mat_op("MULTIPLY", -800, 120, mancha.outputs[0], m3.outputs[0])
    mancha = mat_op("MULTIPLY", -650, 60, mancha.outputs[0], m4.outputs[0])
    # "palavras": ruido esticado na direcao das linhas, com limiar
    palavras = no(nt, "ShaderNodeTexNoise", -1100, -350, "Palavras (Noise)")
    palavras.inputs["Scale"].default_value = 60.0
    palavras.inputs["Detail"].default_value = 0.0
    escala_pal = no(nt, "ShaderNodeMapping", -1300, -350)
    escala_pal.inputs["Scale"].default_value = (1.0, 0.08, 1.0)
    nt.links.new(coord.outputs["UV"], escala_pal.inputs["Vector"])
    nt.links.new(escala_pal.outputs["Vector"], palavras.inputs["Vector"])
    pal = mat_op("GREATER_THAN", -900, -350, palavras.outputs["Fac"], valor=0.42)

    texto = mat_op("MULTIPLY", -650, 400, linhas.outputs[0], mancha.outputs[0])
    texto = mat_op("MULTIPLY", -500, 300, texto.outputs[0], pal.outputs[0])
    texto = mat_op("MULTIPLY", -350, 300, texto.outputs[0], valor=0.40)

    mistura = no(nt, "ShaderNodeMix", -150, 400, "Papel + tinta")
    mistura.data_type = "RGBA"
    # o no Mix tem sockets "A"/"B"/"Result" para float, vetor e cor:
    # os de cor sao escolhidos pelo identificador
    socket = {s.identifier: s for s in mistura.inputs}
    socket["A_Color"].default_value = (0.86, 0.83, 0.74, 1.0)      # papel
    socket["B_Color"].default_value = (0.20, 0.20, 0.24, 1.0)      # tinta
    nt.links.new(texto.outputs[0], socket["Factor_Float"])
    resultado = next(s for s in mistura.outputs if s.identifier == "Result_Color")
    nt.links.new(resultado, bsdf.inputs["Base Color"])

    fibra = no(nt, "ShaderNodeTexNoise", -350, -150, "Fibra (Noise)")
    fibra.inputs["Scale"].default_value = 180.0
    fibra.inputs["Detail"].default_value = 4.0
    relevo = no(nt, "ShaderNodeBump", 0, -150)
    relevo.inputs["Strength"].default_value = 0.08
    nt.links.new(coord.outputs["UV"], fibra.inputs["Vector"])
    nt.links.new(fibra.outputs["Fac"], relevo.inputs["Height"])
    nt.links.new(relevo.outputs["Normal"], bsdf.inputs["Normal"])
    ajustar(bsdf, metalico=0.0, rugosidade=0.85, especular=0.4)
    mat.diffuse_color = (0.86, 0.83, 0.74, 1.0)
    return mat


def material_aluminio():
    """Aluminio escovado procedural: metalico, com riscos horizontais
    (ruido esticado em Z) variando a rugosidade."""
    mat, nt, bsdf = novo_material("MAT_Torre_Aluminio_Escovado_PBR")
    coord = no(nt, "ShaderNodeTexCoord", -900, 300)
    mapeamento = no(nt, "ShaderNodeMapping", -700, 300)
    mapeamento.inputs["Scale"].default_value = (1.5, 1.5, 120.0)
    ruido = no(nt, "ShaderNodeTexNoise", -500, 300, "Riscos (Noise)")
    ruido.inputs["Scale"].default_value = 4.0
    ruido.inputs["Detail"].default_value = 6.0
    faixa = no(nt, "ShaderNodeMapRange", -300, 300)
    faixa.inputs["To Min"].default_value = 0.18
    faixa.inputs["To Max"].default_value = 0.38
    nt.links.new(coord.outputs["Object"], mapeamento.inputs["Vector"])
    nt.links.new(mapeamento.outputs["Vector"], ruido.inputs["Vector"])
    nt.links.new(ruido.outputs["Fac"], faixa.inputs["Value"])
    nt.links.new(faixa.outputs["Result"], bsdf.inputs["Roughness"])
    ajustar(bsdf, cor=(0.80, 0.82, 0.85, 1.0), metalico=1.0, rugosidade=0.28)
    mat.diffuse_color = (0.80, 0.82, 0.85, 1.0)
    return mat


def material_simples(nome, cor, **kw):
    mat, nt, bsdf = novo_material(nome)
    ajustar(bsdf, cor=cor, **kw)
    mat.diffuse_color = cor
    return mat


def marcar_janelas(torre):
    """Indice de material 1 nas faces internas das janelas (as faces que o
    inset da AP1 afundou): laterais, area > 0,15 m2, abaixo da coroa."""
    bm = bmesh.new()
    bm.from_mesh(torre.data)
    n = 0
    for f in bm.faces:
        janela = (abs(f.normal.z) < 0.2 and f.calc_area() > 0.15
                  and f.calc_center_median().z < 8.4)
        f.material_index = 1 if janela else 0
        n += janela
    bm.to_mesh(torre.data)
    bm.free()
    return n


def criar_materiais(pasta_tex):
    couro = material_imagens("MAT_Livro_Couro_PBR", pasta_tex, COURO, 1.0,
                             (0.35, 0.06, 0.05, 1.0))
    madeira = material_imagens("MAT_Ponte_Madeira_PBR", pasta_tex, MADEIRA, 1.0,
                               (0.62, 0.45, 0.28, 1.0))
    papel = material_papel()
    aco = material_simples("MAT_Ponte_Aco_PBR", (0.42, 0.44, 0.47, 1.0),
                           metalico=1.0, rugosidade=0.35)
    aluminio = material_aluminio()
    vidro = material_simples("MAT_Torre_Vidro_Espelhado_PBR", (0.42, 0.64, 0.86, 1.0),
                             metalico=1.0, rugosidade=0.05,
                             **{"Emission Color": (0.55, 0.85, 1.0, 1.0),
                                "Emission Strength": 0.0})
    ibmec = material_simples("MAT_Ibmec_Azul_PBR", (0.02, 0.10, 0.32, 1.0),
                             metalico=0.0, rugosidade=0.32,
                             **{"Coat Weight": 0.25, "Coat Roughness": 0.15})
    blocos = material_simples("MAT_Blocos_Plastico_PBR", (0.95, 0.62, 0.08, 1.0),
                              metalico=0.0, rugosidade=0.38)
    chao = material_simples("MAT_Chao_PBR", (0.70, 0.72, 0.75, 1.0),
                            metalico=0.0, rugosidade=0.85)

    aplicar(["Livro_Aberto"], couro)
    aplicar(["Livro_Paginas"], papel)
    aplicar(["Ponte_Tabuleiro"], madeira)
    aplicar(["Ponte_Arco", "Ponte_Guarda", "Ponte_Postes"], aco)
    aplicar(["Torre_Futuro"], aluminio, vidro)
    janelas = marcar_janelas(bpy.data.objects["Torre_Futuro"])
    aplicar(["Ibmec_I", "Ibmec_b", "Ibmec_m", "Ibmec_e", "Ibmec_c"], ibmec)
    aplicar(["Blocos_Construcao"], blocos)
    aplicar(["Chao"], chao)
    print("janelas com vidro:", janelas)
    return {"couro": couro, "papel": papel, "madeira": madeira, "aco": aco,
            "aluminio": aluminio, "vidro": vidro}


# ---------------------------------------------------------------------------
# 2. UVs dos objetos com textura de imagem
# ---------------------------------------------------------------------------
def preparar_uvs():
    # Capa do livro: caixa com lombada -> Cube Projection. A mesma escala em
    # todas as faces (1 ladrilho = 2,5 m) mantem a densidade uniforme, sem esticar.
    uv_operador(bpy.data.objects["Livro_Aberto"], bpy.ops.uv.cube_project,
                cube_size=LADRILHO_COURO, correct_aspect=True, clip_to_bounds=False,
                scale_to_bounds=False)
    # Tabua da ponte: tambem uma caixa -> Cube Projection (o veio da madeira,
    # vertical na imagem, fica no eixo Y = comprimento da tabua)
    uv_operador(bpy.data.objects["Ponte_Tabuleiro"], bpy.ops.uv.cube_project,
                cube_size=LADRILHO_MADEIRA, correct_aspect=True, clip_to_bounds=False,
                scale_to_bounds=False)
    arr = bpy.data.objects["Ponte_Tabuleiro"].modifiers["Array_tabuas"]
    arr.offset_u = DESLOC_U_TABUAS      # cada tabua mostra outro trecho do veio
    # Paginas: faixa curva (superficie desenvolvivel) -> Unwrap Angle Based
    # planifica sem distorcao num retangulo (U = largura, V = altura da pagina)
    uv_operador(bpy.data.objects["Livro_Paginas"], bpy.ops.uv.unwrap,
                method="ANGLE_BASED", margin=0.0)


# ---------------------------------------------------------------------------
# 3. Colecao auxiliar AC05_Materiais_Texturas
# ---------------------------------------------------------------------------
def nova_esfera(nome, col, raio):
    malha = bpy.data.meshes.get(nome + "_mesh") or bpy.data.meshes.new(nome + "_mesh")
    bm = bmesh.new()
    camada = bm.loops.layers.uv.new("UVMap")       # calc_uvs preenche esta camada
    bmesh.ops.create_uvsphere(bm, u_segments=64, v_segments=32, radius=raio, calc_uvs=True)
    # UV proporcional ao tamanho real (U = perimetro, V = meia volta), em
    # ladrilhos de 2 m, para a textura ter escala parecida com a da cena
    for f in bm.faces:
        f.smooth = True
        for laco in f.loops:
            laco[camada].uv.x *= 2 * math.pi * raio / 2.0
            laco[camada].uv.y *= math.pi * raio / 2.0
    bm.to_mesh(malha)
    bm.free()
    obj = bpy.data.objects.get(nome) or bpy.data.objects.new(nome, malha)
    if not obj.users_collection:
        col.objects.link(obj)
    return obj


def apontar(obj, alvo):
    obj.rotation_euler = (Vector(alvo) - obj.location).to_track_quat("-Z", "Y").to_euler()


def organizar_colecao(mats):
    col = bpy.data.collections.get(COL_AC05) or bpy.data.collections.get(COL_AC04)
    col.name = COL_AC05
    # esferas da AC04 saem (o arquivo da AC04 continua guardando a comparacao)
    for obj in list(col.objects):
        if obj.name.startswith("Amostra_"):
            malha = obj.data
            bpy.data.objects.remove(obj, do_unlink=True)
            if malha.users == 0:
                bpy.data.meshes.remove(malha)
    # cameras de detalhe: mesmas posicoes da AC04, mais perto das superficies
    cams = {
        "Livro": ((-7.5, -9.5, 3.4), (-3.0, -2.5, 0.3), 35),
        "Ponte": ((7.0, -2.0, 4.2), (10.6, 3.4, 1.4), 35),
        "Torre": ((10.0, -3.5, 4.5), (15.8, 7.0, 5.5), 35),
    }
    for nome, (local, alvo, lente) in cams.items():
        cam = bpy.data.objects.get("CAM_AC04_" + nome) or bpy.data.objects.get("CAM_AC05_" + nome)
        cam.name = cam.data.name = "CAM_AC05_" + nome
        cam.location = local
        cam.data.lens = lente
        apontar(cam, alvo)
    # esferas-amostra dos materiais PBR, sobre o mesmo fundo neutro da AC04
    base = Vector((-24.0, -24.0, 0.0))
    ordem = [("couro", "Couro"), ("papel", "Papel"), ("madeira", "Madeira"),
             ("aco", "Aco"), ("aluminio", "Aluminio"), ("vidro", "Vidro")]
    for i, (chave, rotulo) in enumerate(ordem):
        esfera = nova_esfera("Amostra_PBR_" + rotulo, col, 0.8)
        esfera.location = base + Vector(((i - 2.5) * 2.1, 0.0, 0.8))
        esfera.data.materials.clear()
        esfera.data.materials.append(mats[chave])
    cam = bpy.data.objects.get("CAM_AC04_Amostras") or bpy.data.objects.get("CAM_AC05_Amostras")
    cam.name = cam.data.name = "CAM_AC05_Amostras"
    cam.location = base + Vector((0.0, -12.0, 1.9))
    cam.data.lens = 34
    apontar(cam, base + Vector((0.0, 0.0, 0.8)))
    col.hide_render = True        # fora do render principal (F12)
    return col


# ---------------------------------------------------------------------------
# Montagem
# ---------------------------------------------------------------------------
destino, pasta_tex = caminhos()
cena = bpy.context.scene
if bpy.context.object and bpy.context.object.mode != "OBJECT":
    bpy.ops.object.mode_set(mode="OBJECT")

mats = criar_materiais(pasta_tex)
preparar_uvs()
organizar_colecao(mats)

# materiais da AC04 que ficaram sem uso nao vao para o arquivo da AC05
for m in list(bpy.data.materials):
    if m.users == 0:
        bpy.data.materials.remove(m)

cena.camera = bpy.data.objects["CAM_Principal"]
cena.frame_set(1)
destino.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(destino))
bpy.ops.file.make_paths_relative()          # //texturas/... em vez de C:\...
bpy.ops.file.pack_all()                      # imagens dentro do .blend
bpy.ops.wm.save_mainfile()
print("AC05: cena salva em", destino)
