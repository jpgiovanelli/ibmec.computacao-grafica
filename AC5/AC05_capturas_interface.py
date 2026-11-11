"""
AC05 - capturas de tela do Shader Editor e do UV Editor (precisa da interface).

USO (abre o Blender com janela, tira as capturas sozinho e fecha):
    blender AC5/AC05_JoaoGiovanelli.blend --python AC5/AC05_capturas_interface.py

GERA EM AC5/imagens/ (capturas da area inteira; montar_paineis.py recorta)
    tela_shader_madeira.png  Shader Editor: MAT_Ponte_Madeira_PBR
                             (Base Color sRGB, Roughness e Normal Non-Color -> Normal Map)
    tela_shader_couro.png    Shader Editor: MAT_Livro_Couro_PBR (mesmo conjunto de mapas)
    tela_uv_tabua.png        UV Editor: ilhas do Ponte_Tabuleiro sobre a imagem da madeira
    tela_uv_paginas.png      UV Editor: Livro_Paginas sobre uma grade UV (checa distorcao)
    tela_viewport_material.png / tela_viewport_rendered.png
                             3D Viewport pela camera principal em Material Preview
                             (HDRI de estudio do Blender) e em Rendered (luz da cena)
O arquivo .blend nao e salvo (a grade UV gerada nao vai para o arquivo).
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


def ativar(nome, modo="OBJECT"):
    vl = bpy.context.view_layer
    janela, _, _ = janela_e_area()
    with bpy.context.temp_override(window=janela):
        if bpy.context.object and bpy.context.object.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")
        for o in vl.objects:
            o.select_set(False)
        obj = bpy.data.objects[nome]
        vl.objects.active = obj
        obj.select_set(True)
        if modo != "OBJECT":
            bpy.ops.object.mode_set(mode=modo)
            bpy.ops.mesh.select_all(action="SELECT")


def preparar_shader(objeto):
    ativar(objeto)
    janela, area, regiao = janela_e_area()
    area.type = "NODE_EDITOR"
    area.ui_type = "ShaderNodeTree"
    espaco = area.spaces.active
    espaco.show_region_ui = False
    espaco.show_region_toolbar = False


def enquadrar_shader():
    janela, area, regiao = janela_e_area()
    with bpy.context.temp_override(window=janela, area=area, region=regiao):
        bpy.ops.node.select_all(action="DESELECT")
        bpy.ops.node.view_all()


def preparar_uv(objeto, nome_imagem):
    ativar(objeto, "EDIT")
    janela, area, regiao = janela_e_area()
    area.type = "IMAGE_EDITOR"
    area.ui_type = "UV"
    espaco = area.spaces.active
    imagem = bpy.data.images.get(nome_imagem)
    if imagem is None:            # grade de teste gerada pelo Blender (UV Grid)
        imagem = bpy.data.images.new(nome_imagem, 1024, 1024)
        imagem.generated_type = "UV_GRID"
    espaco.image = imagem
    espaco.show_region_ui = False
    espaco.show_region_toolbar = False
    espaco.uv_editor.show_stretch = False


def enquadrar_uv():
    janela, area, regiao = janela_e_area()
    with bpy.context.temp_override(window=janela, area=area, region=regiao):
        bpy.ops.image.view_all(fit_view=True)
        bpy.ops.image.view_zoom_out()


def preparar_viewport(sombreamento):
    ativar("CAM_Principal")
    janela, area, regiao = janela_e_area()
    area.type = "VIEW_3D"
    espaco = area.spaces.active
    espaco.shading.type = sombreamento
    # Material Preview "de fabrica": HDRI de estudio, sem as luzes e o ceu da cena;
    # Rendered: luzes e World da cena
    espaco.shading.use_scene_lights = False
    espaco.shading.use_scene_world = False
    espaco.shading.use_scene_lights_render = True
    espaco.shading.use_scene_world_render = True
    espaco.overlay.show_overlays = False
    espaco.show_gizmo = False
    espaco.show_region_ui = False
    espaco.show_region_toolbar = False
    espaco.region_3d.view_perspective = "CAMERA"


def centralizar_camera():
    janela, area, regiao = janela_e_area()     # regioes novas depois da troca de editor
    with bpy.context.temp_override(window=janela, area=area, region=regiao):
        bpy.ops.view3d.view_center_camera()


def capturar(arquivo):
    janela, area, regiao = janela_e_area()
    with bpy.context.temp_override(window=janela, area=area):
        bpy.ops.screen.screenshot_area(filepath=str(PASTA / arquivo))
    print("captura:", arquivo)


# cada passo roda num tick do timer, para a interface redesenhar entre eles
PASSOS = [
    lambda: preparar_shader("Ponte_Tabuleiro"),
    enquadrar_shader,
    lambda: capturar("tela_shader_madeira.png"),
    lambda: preparar_shader("Livro_Aberto"),
    enquadrar_shader,
    lambda: capturar("tela_shader_couro.png"),
    lambda: preparar_uv("Ponte_Tabuleiro", "oak_veneer_01_diff_1k.jpg"),
    enquadrar_uv,
    lambda: capturar("tela_uv_tabua.png"),
    lambda: preparar_uv("Livro_Paginas", "Grade_UV"),
    enquadrar_uv,
    lambda: capturar("tela_uv_paginas.png"),
    lambda: preparar_viewport("MATERIAL"),
    centralizar_camera,
    lambda: None, lambda: None, lambda: None,           # tempo para compilar shaders
    lambda: capturar("tela_viewport_material.png"),
    lambda: preparar_viewport("RENDERED"),
    centralizar_camera,
    lambda: None, lambda: None, lambda: None, lambda: None, lambda: None, lambda: None,
    lambda: capturar("tela_viewport_rendered.png"),
]


def proximo():
    if not PASSOS:
        bpy.ops.wm.quit_blender()
        return None
    passo = PASSOS.pop(0)
    try:
        passo()
    except Exception as erro:          # nao deixa a janela aberta se algo falhar
        import traceback
        traceback.print_exc()
        print("falhou:", erro)
        PASSOS.clear()
    return 1.0


bpy.app.timers.register(proximo, first_interval=3.0)
