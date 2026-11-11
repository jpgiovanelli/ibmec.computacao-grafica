"""
AP2 - capturas de tela do Dope Sheet e do Graph Editor (precisa da interface).

USO (abre o Blender com janela, tira as capturas sozinho e fecha):
    blender AP2/AP2_JoaoGiovanelli.blend --python AP2/AP2_capturas_interface.py

GERA EM AP2/imagens/
    AP2_dopesheet.png        Dope Sheet com todos os keyframes da peca (timing dos 3 planos)
    AP2_graph_letras.png     Graph Editor: escala das 5 letras (Y com BACK = overshoot)
    AP2_graph_blocos.png     Graph Editor: Z de alguns blocos (queda com BOUNCE)
    AP2_graph_camera.png     Graph Editor: posicao da camera e do alvo (Bezier auto-clamped)
O arquivo .blend nao e salvo.
"""

from pathlib import Path

import bpy

PASTA = Path(bpy.data.filepath).parent / "imagens"
PASTA.mkdir(exist_ok=True)


def janela_e_area():
    janela = bpy.context.window_manager.windows[0]
    area = max(janela.screen.areas, key=lambda a: a.width * a.height)
    regiao = next(r for r in area.regions if r.type == "WINDOW")
    return janela, area, regiao


def selecionar(nomes):
    vl = bpy.context.view_layer
    for o in vl.objects:
        o.select_set(o.name in nomes)
    vl.objects.active = bpy.data.objects[nomes[0]]


def preparar(editor, nomes=None, frame=180):
    bpy.context.scene.frame_set(frame)
    if nomes:
        selecionar(nomes)
    janela, area, regiao = janela_e_area()
    if editor == "DOPESHEET":
        area.type = "DOPESHEET_EDITOR"
        area.ui_type = "DOPESHEET"
    else:
        area.type = "GRAPH_EDITOR"
        area.ui_type = "FCURVES"
    espaco = area.spaces.active
    espaco.dopesheet.show_only_selected = bool(nomes)
    espaco.show_region_ui = False
    if editor != "DOPESHEET":
        # sem a curva de exposicao da cena (fade-in) e com as curvas
        # normalizadas (-1 a 1), para comparar a FORMA da interpolacao
        espaco.dopesheet.show_scenes = False
        espaco.use_normalization = True


def enquadrar():
    janela, area, regiao = janela_e_area()
    with bpy.context.temp_override(window=janela, area=area, region=regiao):
        if area.type == "GRAPH_EDITOR":
            bpy.ops.graph.reveal()
            bpy.ops.graph.select_all(action="SELECT")
            bpy.ops.graph.view_all()
            bpy.ops.graph.select_all(action="DESELECT")
        else:
            bpy.ops.anim.channels_expand(all=False)
            bpy.ops.action.view_all()


def capturar(arquivo):
    janela, area, regiao = janela_e_area()
    with bpy.context.temp_override(window=janela, area=area):
        bpy.ops.screen.screenshot_area(filepath=str(PASTA / arquivo))
    print("captura:", arquivo)


LETRAS = ["Ibmec_I", "Ibmec_b", "Ibmec_m", "Ibmec_e", "Ibmec_c"]
BLOCOS = ["Bloco_01", "Bloco_02", "Bloco_03", "Bloco_04", "Bloco_05", "Bloco_06"]
PASSOS = [
    lambda: preparar("DOPESHEET"), enquadrar, lambda: capturar("AP2_dopesheet.png"),
    lambda: preparar("GRAPH", LETRAS), enquadrar, lambda: capturar("AP2_graph_letras.png"),
    lambda: preparar("GRAPH", BLOCOS, 30), enquadrar, lambda: capturar("AP2_graph_blocos.png"),
    lambda: preparar("GRAPH", ["CAM_Principal", "Alvo_Camera"]), enquadrar,
    lambda: capturar("AP2_graph_camera.png"),
]


def proximo():
    if not PASSOS:
        bpy.ops.wm.quit_blender()
        return None
    passo = PASSOS.pop(0)
    try:
        passo()
    except Exception as erro:
        import traceback
        traceback.print_exc()
        print("falhou:", erro)
        PASSOS.clear()
    return 1.0


bpy.app.timers.register(proximo, first_interval=3.0)
