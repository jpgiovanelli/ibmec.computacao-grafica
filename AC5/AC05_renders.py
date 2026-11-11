"""
AC05 - renders de entrega (roda sobre o arquivo montado pela AC05).

USO
    blender -b AC5/AC05_JoaoGiovanelli.blend --python AC5/AC05_renders.py
    (depois: python AC5/montar_paineis.py)

GERA EM AC5/imagens/
    AC05_render_final.png      camera principal, 1920x1080 (cena final)
    detalhe_livro/ponte/torre  closes para conferir escala, orientacao e
                               repeticao das texturas sob a luz da cena
    amostras_pbr_bruto.png     esferas-amostra dos seis materiais PBR
O arquivo .blend nao e salvo por este script.
"""

from pathlib import Path

import bpy

PASTA = Path(bpy.data.filepath).parent / "imagens"
PASTA.mkdir(exist_ok=True)
cena = bpy.context.scene
auxiliar = bpy.data.collections["AC05_Materiais_Texturas"]


def render(camera, arquivo, rx=1920, ry=1080):
    auxiliar.hide_render = camera == "CAM_Principal"
    cena.camera = bpy.data.objects[camera]
    cena.render.resolution_x, cena.render.resolution_y = rx, ry
    cena.render.resolution_percentage = 100
    cena.render.filepath = str(PASTA / arquivo)
    bpy.ops.render.render(write_still=True)
    print("render:", arquivo)


render("CAM_Principal", "AC05_render_final.png")
for nome in ("Livro", "Ponte", "Torre"):
    render("CAM_AC05_" + nome, f"detalhe_{nome.lower()}.png", 1200, 1200)
render("CAM_AC05_Amostras", "amostras_pbr_bruto.png", 1920, 700)
auxiliar.hide_render = True
cena.camera = bpy.data.objects["CAM_Principal"]
