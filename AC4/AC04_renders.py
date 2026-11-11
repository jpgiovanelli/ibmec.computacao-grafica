"""
AC04 - renders de entrega (roda sobre o arquivo ja montado pela AC04).

USO
    blender -b AC4/AC04_JoaoGiovanelli.blend --python AC4/AC04_renders.py
    (depois: python AC4/montar_paineis.py, que monta as pranchas comparativas)

GERA EM AC4/imagens/
    AC04_render_final.png        camera principal, 1920x1080 (imagem da cena final)
    detalhe_livro/ponte/torre    closes quadrados de cada objeto autoral, MESMA luz
    amostras_esferas_bruto.png   as tres esferas-amostra (Lambert, Phong, Blinn-Phong)
    angulo_*.png                 estudo do angulo da luz: a luz principal e girada
                                 temporariamente para 3 direcoes; camera, intensidade
                                 e cor ficam fixas. No fim a luz volta a posicao padrao.
O arquivo .blend nao e salvo por este script.
"""

import math
from pathlib import Path

import bpy
from mathutils import Vector

PASTA = Path(bpy.data.filepath).parent / "imagens"
PASTA.mkdir(exist_ok=True)
cena = bpy.context.scene
comparacao = bpy.data.collections["07_AC04_Comparacao"]
luz = bpy.data.objects["Luz_Principal"]

# direcoes de luz do estudo (azimute, elevacao em graus); a primeira e a padrao
ANGULOS = {
    "a_padrao": (-150.0, 35.0),     # frente-esquerda (configuracao final)
    "b_frontal": (-105.0, 35.0),    # quase atras da camera
    "c_rasante": (-20.0, 15.0),     # lateral direita, baixa
}


def posicionar_sol(azimute, elevacao, centro=Vector((4.0, 2.0, 2.0))):
    az, el = math.radians(azimute), math.radians(elevacao)
    para_luz = Vector((math.cos(el) * math.cos(az), math.cos(el) * math.sin(az), math.sin(el)))
    luz.location = centro + para_luz * 22.0
    luz.rotation_euler = (-para_luz).to_track_quat("-Z", "Y").to_euler()


def render(camera, arquivo, rx=1920, ry=1080, amostras=64):
    # a colecao de comparacao (esferas e fundo) so aparece nas cameras dela
    comparacao.hide_render = camera == "CAM_Principal"
    cena.camera = bpy.data.objects[camera]
    cena.render.resolution_x, cena.render.resolution_y = rx, ry
    cena.render.resolution_percentage = 100
    cena.eevee.taa_render_samples = amostras
    cena.render.filepath = str(PASTA / arquivo)
    bpy.ops.render.render(write_still=True)
    print("render:", arquivo)


posicionar_sol(*ANGULOS["a_padrao"])
render("CAM_Principal", "AC04_render_final.png")
for nome in ("Livro", "Ponte", "Torre"):
    render("CAM_AC04_" + nome, f"detalhe_{nome.lower()}.png", 1200, 1200)
render("CAM_AC04_Amostras", "amostras_esferas_bruto.png")

for chave, (az, el) in ANGULOS.items():
    posicionar_sol(az, el)
    render("CAM_Principal", f"angulo_{chave}_cena.png", 960, 540, 48)
    render("CAM_AC04_Amostras", f"angulo_{chave}_esferas.png", 960, 540, 48)

posicionar_sol(*ANGULOS["a_padrao"])          # restaura a luz escolhida
comparacao.hide_render = True
cena.camera = bpy.data.objects["CAM_Principal"]
