"""
AP2 - renderiza a animacao em quadros PNG (retomavel) para depois codificar o MP4.

USO
    blender -b AP2/AP2_JoaoGiovanelli.blend --python AP2/AP2_render.py -- <pasta> [inicio fim [porcentagem]]
    blender -b AP2/AP2_JoaoGiovanelli.blend --python AP2/AP2_render.py -- <pasta> lista 1,60,120 [porcentagem]
    depois: ffmpeg -framerate 24 -i <pasta>/%04d.png -c:v libx264 -profile:v high -level:v 4.1
                   -crf 18 -pix_fmt yuv420p -colorspace bt709 -color_primaries bt709
                   -color_trc bt709 -movflags +faststart AP2/AP2_JoaoGiovanelli.mp4

Os quadros ja existentes sao pulados (use_overwrite = False), entao o render pode
ser interrompido e retomado. O .blend nao e salvo.
"""

import sys
import time
from pathlib import Path

import bpy

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
pasta = Path(args[0])
pasta.mkdir(parents=True, exist_ok=True)
cena = bpy.context.scene
cena.render.image_settings.file_format = "PNG"
cena.render.image_settings.color_mode = "RGB"
cena.render.use_overwrite = False
cena.render.use_placeholder = True

if len(args) > 1 and args[1] == "lista":
    quadros = [int(x) for x in args[2].split(",")]
    cena.render.resolution_percentage = int(args[3]) if len(args) > 3 else 100
    for f in quadros:
        cena.frame_set(f)
        cena.render.filepath = str(pasta / f"{f:04d}.png")
        t = time.time()
        bpy.ops.render.render(write_still=True)
        print(f"quadro {f}: {time.time() - t:.1f} s")
else:
    if len(args) > 2:
        cena.frame_start, cena.frame_end = int(args[1]), int(args[2])
    if len(args) > 3:
        cena.render.resolution_percentage = int(args[3])
    cena.render.filepath = str(pasta) + "/####"
    t = time.time()
    bpy.ops.render.render(animation=True)
    print(f"animacao {cena.frame_start}-{cena.frame_end}: {time.time() - t:.1f} s")
