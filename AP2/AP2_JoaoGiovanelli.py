"""
AP2 - Peca audiovisual "Ibmec em 15 segundos" (animacao da cena da AP1/AC04/AC05)
Aluno: Joao Pedro Giovanelli Berla
Disciplina: Computacao Grafica - CG_26.2_8001

COMO USAR
    1. Abra AC5/AC05_JoaoGiovanelli.blend no Blender 4.5 LTS.
    2. Aba Scripting -> Text -> Open -> este arquivo -> "Run Script" (Alt+P).
       (ou: blender -b AC5/AC05_JoaoGiovanelli.blend --python AP2/AP2_JoaoGiovanelli.py)
    3. O script NAO altera os arquivos anteriores: salva AP2/AP2_JoaoGiovanelli.blend
       com a animacao (frames 1-360, 24 fps) e a saida configurada para MP4 H.264.

ROTEIRO (segue o storyboard da AP1)
    Plano 1 - Inicio (frames 1-120, 0-5 s)
        fade-in; camera baixa rente as paginas, deslizando para a direita;
        os 26 blocos amarelos caem um a um sobre o livro (quique: BOUNCE).
    Plano 2 - Construcao da palavra (frames 121-264, 5-11 s)
        camera fecha na palavra; as letras I-b-m-e-c crescem dos blocos, uma
        apos a outra (escala vertical 0 -> 1 com overshoot: BACK); ao fundo a
        ponte se estende tabua por tabua (Array fit_length + bevel da curva).
    Plano 3 - Encerramento (frames 265-360, 11-15 s)
        a camera recua e sobe ate o enquadramento principal da AP1; a torre
        se ergue no fim da ponte e torce (Simple Deform animado); as janelas
        acendem; ultimos ~1,4 s parados na composicao final.
"""

import math
from pathlib import Path

import bmesh
import bpy
from mathutils import Matrix, Vector

ARQ_AC05 = "AC05_JoaoGiovanelli.blend"
ARQ_AP2 = "AP2_JoaoGiovanelli.blend"
FPS, INICIO, FIM = 24, 1, 360

CAMERA = [   # (frame, posicao da camera, posicao do alvo, lente mm)
    (1, (-9.5, -9.0, 2.0), (-2.5, 0.6, 0.5), 28),       # plano 1: baixa, lateral
    (100, (-4.0, -11.2, 2.4), (0.0, 0.6, 0.9), 28),     # desliza para a direita
    (150, (0.8, -11.5, 3.2), (0.0, 0.8, 2.1), 35),      # plano 2: close na palavra
    (226, (1.6, -11.2, 3.2), (0.5, 0.8, 2.1), 35),      # acompanha as letras
    (262, (0.5, -14.0, 4.0), (2.5, 1.8, 2.5), 28),      # plano 3: recua e sobe
    (326, (-1.0, -17.0, 5.2), (3.4, 2.8, 3.0), 26),     # enquadramento principal
    (360, (-1.0, -17.0, 5.2), (3.4, 2.8, 3.0), 26),     # parado ate o fim
]
BLOCOS_INICIO, BLOCOS_PASSO, BLOCOS_QUEDA, BLOCOS_ALTURA = 14, 3, 18, 2.6
LETRAS_INICIO, LETRAS_PASSO, LETRAS_DURACAO = 132, 16, 22


# ---------------------------------------------------------------------------
# Keyframes
# ---------------------------------------------------------------------------
def _atribuir(alvo, caminho, valor, indice):
    dono_caminho, _, prop = caminho.rpartition(".")
    dono = alvo.path_resolve(dono_caminho) if dono_caminho else alvo
    if indice >= 0:
        getattr(dono, prop)[indice] = valor
    else:
        setattr(dono, prop, valor)


def chaves(alvo, caminho, pontos, indice=-1, acao_de=None):
    """Insere keyframes e define a interpolacao de cada um.
    pontos: [(frame, valor, interpolacao, easing), ...] - a interpolacao de
    um keyframe vale para o trecho ate o keyframe seguinte."""
    for frame, valor, _, _ in pontos:
        _atribuir(alvo, caminho, valor, indice)
        alvo.keyframe_insert(data_path=caminho, index=indice, frame=frame)
    acao = (acao_de or alvo).animation_data.action
    prefixo = "" if acao_de is None else alvo.path_from_id() + "."
    curvas = [fc for fc in acao.fcurves if fc.data_path == prefixo + caminho
              and (indice < 0 or fc.array_index == indice)]
    for fc in curvas:
        for kp in fc.keyframe_points:
            for frame, _, interp, easing in pontos:
                if abs(kp.co.x - frame) < 0.01:
                    kp.interpolation = interp
                    kp.easing = easing
                    kp.handle_left_type = kp.handle_right_type = "AUTO_CLAMPED"
                    if interp == "BACK":
                        kp.back = 1.7
        fc.update()
    return curvas


# ---------------------------------------------------------------------------
# Preparacao: arquivo, colecoes, modelagem ajustada para a animacao
# ---------------------------------------------------------------------------
def caminho_destino():
    atual = Path(bpy.data.filepath)
    if atual.name not in (ARQ_AC05, ARQ_AP2):
        raise RuntimeError("Abra AC5/AC05_JoaoGiovanelli.blend antes de rodar este script.")
    return atual.parent.parent / "AP2" / ARQ_AP2


def remover_colecao(nome):
    col = bpy.data.collections.get(nome)
    if col is None:
        return
    for obj in list(col.objects):
        dados = obj.data
        bpy.data.objects.remove(obj, do_unlink=True)
        if dados is not None and dados.users == 0:
            if isinstance(dados, bpy.types.Mesh):
                bpy.data.meshes.remove(dados)
            elif isinstance(dados, bpy.types.Camera):
                bpy.data.cameras.remove(dados)
    bpy.data.collections.remove(col)


def separar_blocos():
    """Na AP1 os blocos eram UM objeto com Array X x Array Y. Para cada bloco
    ter sua propria queda, a AP2 troca o Array por 26 objetos que compartilham
    a mesma malha (linked duplicates), filhos do Empty Blocos_Construcao, que
    ocupa a mesma posicao/rotacao do objeto original."""
    original = bpy.data.objects.get("Blocos_Construcao")
    if original is None or original.type == "EMPTY":
        return sorted((o for o in bpy.data.objects if o.name.startswith("Bloco_")),
                      key=lambda o: o.name)
    col = original.users_collection[0]
    arr_x, arr_y = original.modifiers["Array_X"], original.modifiers["Array_Y"]
    bevel = original.modifiers["Bevel_blocos"]
    lado = max(v.co.x for v in original.data.vertices)          # cubo de 0 a 0,8 m
    passo = lado * arr_x.relative_offset_displace[0]
    material = original.data.materials[0]
    matriz, nx, ny = original.matrix_world.copy(), arr_x.count, arr_y.count
    largura_bevel, segmentos = bevel.width, bevel.segments
    malha_antiga = original.data
    bpy.data.objects.remove(original, do_unlink=True)
    bpy.data.meshes.remove(malha_antiga)

    # malha unica: cubo com origem no centro da base (bom para quicar/escalar)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=lado)
    bmesh.ops.translate(bm, vec=(0, 0, lado / 2), verts=bm.verts)
    malha = bpy.data.meshes.new("Bloco_mesh")
    bm.to_mesh(malha)
    bm.free()
    malha.materials.append(material)

    pai = bpy.data.objects.new("Blocos_Construcao", None)
    pai.empty_display_type = "PLAIN_AXES"
    pai.empty_display_size = 0.5
    col.objects.link(pai)
    pai.matrix_world = matriz

    blocos = []
    for i in range(nx):
        for j in range(ny):
            nome = f"Bloco_{len(blocos) + 1:02d}"
            bloco = bpy.data.objects.new(nome, malha)
            col.objects.link(bloco)
            bloco.parent = pai
            bloco.location = (i * passo + lado / 2, j * passo + lado / 2, 0.0)
            mod = bloco.modifiers.new("Bevel_blocos", "BEVEL")
            mod.width, mod.segments = largura_bevel, segmentos
            blocos.append(bloco)
    return blocos


def preparar_ponte():
    """Array das tabuas e dos postes: de 'Fit Curve' para 'Fit Length', para
    o comprimento ocupado poder ser animado (a ponte cresce tabua por tabua).
    A viga e o guarda-corpo crescem pelo 'bevel_factor_end' das curvas."""
    arco = bpy.data.objects["Ponte_Arco"]
    comprimento = arco.data.splines[0].calc_length()
    for nome, mod in (("Ponte_Tabuleiro", "Array_tabuas"), ("Ponte_Postes", "Array_postes")):
        arr = bpy.data.objects[nome].modifiers[mod]
        arr.fit_type = "FIT_LENGTH"
        arr.fit_length = comprimento
    for curva in (arco.data, bpy.data.objects["Ponte_Guarda"].data):
        curva.bevel_factor_mapping_start = "SPLINE"
        curva.bevel_factor_mapping_end = "SPLINE"
    return comprimento


# ---------------------------------------------------------------------------
# Animacao
# ---------------------------------------------------------------------------
def animar_abertura(cena):
    # fade-in: exposicao -5 -> 0 no primeiro 0,8 s
    chaves(cena, "view_settings.exposure", [(1, -5.0, "SINE", "EASE_OUT"),
                                            (20, 0.0, "SINE", "EASE_OUT")])


def animar_blocos(blocos):
    """Cada bloco aparece (escala 0 -> 1) e cai 2,6 m ate o livro, quicando
    (interpolacao BOUNCE). Ordem: da esquerda para a direita, alternando a
    fileira da frente e a de tras, 3 frames entre um bloco e o seguinte."""
    for k, bloco in enumerate(blocos):
        f = BLOCOS_INICIO + k * BLOCOS_PASSO
        z = bloco.location.z
        chaves(bloco, "location", [(f, z + BLOCOS_ALTURA, "BOUNCE", "EASE_OUT"),
                                   (f + BLOCOS_QUEDA, z, "BEZIER", "AUTO")], indice=2)
        for eixo in range(3):
            chaves(bloco, "scale", [(f - 1, 0.0, "CONSTANT", "AUTO"),
                                    (f, 0.3, "CUBIC", "EASE_OUT"),
                                    (f + 6, 1.0, "BEZIER", "AUTO")], indice=eixo)


def animar_letras():
    """As letras crescem a partir da base (origem de cada letra), da esquerda
    para a direita. O eixo vertical da letra e o Y local (a palavra esta
    girada 90 graus em X). Y: 0 -> 1 com overshoot (BACK); X e Z: 0,75 -> 1."""
    for i, nome in enumerate(("Ibmec_I", "Ibmec_b", "Ibmec_m", "Ibmec_e", "Ibmec_c")):
        letra = bpy.data.objects[nome]
        f0, f1 = LETRAS_INICIO + i * LETRAS_PASSO, LETRAS_INICIO + i * LETRAS_PASSO + LETRAS_DURACAO
        chaves(letra, "scale", [(f0, 0.0, "BACK", "EASE_OUT"), (f1, 1.0, "BEZIER", "AUTO")],
               indice=1)
        for eixo in (0, 2):
            chaves(letra, "scale", [(f0, 0.75, "CUBIC", "EASE_OUT"),
                                    (f1, 1.0, "BEZIER", "AUTO")], indice=eixo)


def animar_ponte(comprimento):
    partes = ["Ponte_Arco", "Ponte_Tabuleiro", "Ponte_Guarda", "Ponte_Postes"]
    for nome in partes:                     # a ponte so existe a partir do frame 196
        obj = bpy.data.objects[nome]
        for prop in ("hide_render", "hide_viewport"):
            chaves(obj, prop, [(1, True, "CONSTANT", "AUTO"), (196, False, "CONSTANT", "AUTO")])
    arco = bpy.data.objects["Ponte_Arco"]
    guarda = bpy.data.objects["Ponte_Guarda"]
    # viga e guarda-corpo: a curva "e desenhada" do livro ate a torre
    chaves(arco.data, "bevel_factor_end", [(196, 0.0, "SINE", "EASE_IN_OUT"),
                                           (262, 1.0, "BEZIER", "AUTO")])
    chaves(guarda.data, "bevel_factor_end", [(214, 0.0, "SINE", "EASE_IN_OUT"),
                                             (280, 1.0, "BEZIER", "AUTO")])
    # tabuas e postes: o Array ocupa um comprimento crescente (ritmo constante)
    tab = bpy.data.objects["Ponte_Tabuleiro"]
    chaves(tab, 'modifiers["Array_tabuas"].fit_length',
           [(204, 0.40, "LINEAR", "AUTO"), (272, comprimento, "LINEAR", "AUTO")])
    postes = bpy.data.objects["Ponte_Postes"]
    chaves(postes, 'modifiers["Array_postes"].fit_length',
           [(214, 0.40, "LINEAR", "AUTO"), (280, comprimento, "LINEAR", "AUTO")])


def animar_torre():
    torre = bpy.data.objects["Torre_Futuro"]
    escala_final = torre.scale.z            # 1,1 (escala nao uniforme da AP1)
    chaves(torre, "scale", [(262, 0.0, "BACK", "EASE_OUT"), (306, escala_final, "BEZIER", "AUTO")],
           indice=2)
    chaves(torre, 'modifiers["SimpleDeform_twist"].angle',
           [(272, 0.0, "SINE", "EASE_IN_OUT"), (322, math.radians(75), "BEZIER", "AUTO")])
    # janelas acendem (emissao do vidro) quando a torre termina de torcer
    vidro = bpy.data.materials["MAT_Torre_Vidro_Espelhado_PBR"]
    bsdf = next(n for n in vidro.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    caminho = bsdf.inputs["Emission Strength"].path_from_id("default_value")
    bsdf.inputs["Emission Color"].default_value = (0.35, 0.68, 1.0, 1.0)
    chaves(vidro.node_tree, caminho, [(310, 0.0, "SINE", "EASE_IN_OUT"),
                                      (334, 0.7, "BEZIER", "AUTO")])


def animar_camera(cena):
    cam = bpy.data.objects["CAM_Principal"]
    alvo = bpy.data.objects["Alvo_Camera"]
    for frame, pos_cam, pos_alvo, lente in CAMERA:
        cam.location, alvo.location, cam.data.lens = pos_cam, pos_alvo, lente
        cam.keyframe_insert("location", frame=frame)
        alvo.keyframe_insert("location", frame=frame)
        cam.data.keyframe_insert("lens", frame=frame)
    # Bezier com alcas auto-clamped: acelera e desacelera sem passar do ponto
    for dono in (cam, alvo, cam.data):
        for fc in dono.animation_data.action.fcurves:
            for kp in fc.keyframe_points:
                kp.interpolation = "BEZIER"
                kp.handle_left_type = kp.handle_right_type = "AUTO_CLAMPED"
            fc.update()
    cam.data.sensor_fit = "AUTO"
    cena.camera = cam


# ---------------------------------------------------------------------------
# Render e saida
# ---------------------------------------------------------------------------
def ajustar_iluminacao(cena):
    """Iluminacao final: a mesma da AC04/AC05 (Sun frente-esquerda + ceu em
    degrade), com um pouco mais de contraste e um sol um pouco mais forte
    para a peca nao ficar acinzentada no video."""
    luz = bpy.data.objects["Luz_Principal"]
    luz.data.energy = 4.5
    cena.view_settings.view_transform = "AgX"
    cena.view_settings.look = "AgX - Medium High Contrast"


def configurar_saida(cena):
    cena.frame_start, cena.frame_end = INICIO, FIM
    cena.render.fps, cena.render.fps_base = FPS, 1.0
    cena.render.resolution_x, cena.render.resolution_y = 1920, 1080
    cena.render.resolution_percentage = 100
    cena.eevee.taa_render_samples = 48
    cena.render.use_motion_blur = True
    cena.render.motion_blur_shutter = 0.5
    s = cena.render.image_settings
    s.file_format = "FFMPEG"
    cena.render.ffmpeg.format = "MPEG4"
    cena.render.ffmpeg.codec = "H264"
    cena.render.ffmpeg.constant_rate_factor = "HIGH"
    cena.render.ffmpeg.ffmpeg_preset = "GOOD"
    cena.render.ffmpeg.audio_codec = "NONE"
    cena.render.filepath = "//AP2_JoaoGiovanelli.mp4"


# ---------------------------------------------------------------------------
# Montagem
# ---------------------------------------------------------------------------
destino = caminho_destino()
cena = bpy.context.scene
if bpy.context.object and bpy.context.object.mode != "OBJECT":
    bpy.ops.object.mode_set(mode="OBJECT")

remover_colecao("AC05_Materiais_Texturas")      # auxiliares da AC05 (ficam no AC05)
blocos = separar_blocos()
comprimento = preparar_ponte()

animar_abertura(cena)
animar_blocos(blocos)
animar_letras()
animar_ponte(comprimento)
animar_torre()
animar_camera(cena)
ajustar_iluminacao(cena)
configurar_saida(cena)

cena.frame_set(INICIO)
destino.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(destino))
print("AP2: cena salva em", destino, "| blocos:", len(blocos), "| ponte:", round(comprimento, 3), "m")
