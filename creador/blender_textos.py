"""Dibuja los textos en pantalla como PNG transparentes de 1080x1920 con Blender.

Se usa cuando el ffmpeg instalado no trae libass (pasa con el de Homebrew).
Recibe un JSON con [{"texto", "estilo", "archivo"}, ...].

    blender -b --factory-startup -P creador/blender_textos.py -- textos.json
"""
import json
import os
import sys

import bpy

ESTILOS = {
    #          tamaño color               ancla     y
    "titulo": (0.95, (1.0, 1.0, 1.0),    "TOP",    7.4),
    "paso":   (0.50, (1.0, 0.80, 0.0),   "TOP",    8.1),
    "texto":  (0.66, (1.0, 1.0, 1.0),    "BOTTOM", -6.2),
    "final":  (0.86, (1.0, 0.80, 0.0),   "CENTER", 0.0),
}

FUENTES = [
    os.environ.get("CREADOR_FUENTE_ARCHIVO", ""),
    "/System/Library/Fonts/Supplemental/Arial Black.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/usr/share/fonts/opentype/inter/Inter-Black.otf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    r"C:\Windows\Fonts\ariblk.ttf",
]


def fuente():
    for f in FUENTES:
        if f and os.path.exists(f):
            return bpy.data.fonts.load(f)
    return None


def material(nombre, rgb):
    m = bpy.data.materials.new(nombre)
    if bpy.app.version < (5, 0, 0):
        m.use_nodes = True
    nodos = m.node_tree.nodes
    for n in list(nodos):
        nodos.remove(n)
    salida = nodos.new("ShaderNodeOutputMaterial")
    em = nodos.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*rgb, 1)
    m.node_tree.links.new(em.outputs[0], salida.inputs[0])
    return m


def texto(cuerpo, estilo, fnt, mat, mat_borde):
    tam, _, ancla, y = ESTILOS[estilo]
    objs = []
    for borde in (True, False):
        cu = bpy.data.curves.new("txt", "FONT")
        cu.body = cuerpo
        if fnt:
            cu.font = fnt
        cu.size = tam
        cu.align_x = "CENTER"
        cu.align_y = ancla
        cu.text_boxes[0].width = 9.4
        cu.text_boxes[0].x = -4.7
        cu.space_line = 0.95
        if borde:
            cu.offset = tam * 0.06
        ob = bpy.data.objects.new("txt", cu)
        ob.location = (0, y, -0.01 if borde else 0)
        ob.data.materials.append(mat_borde if borde else mat)
        bpy.context.scene.collection.objects.link(ob)
        objs.append(ob)
    return objs


def main():
    ruta = sys.argv[sys.argv.index("--") + 1]
    with open(ruta, encoding="utf-8") as f:
        trabajos = json.load(f)

    bpy.ops.wm.read_factory_settings(use_empty=True)
    s = bpy.context.scene
    s.render.engine = "CYCLES"
    s.cycles.samples = 8
    s.cycles.use_denoising = False
    s.cycles.device = "CPU"
    s.render.film_transparent = True
    s.render.resolution_x, s.render.resolution_y = 1080, 1920
    s.render.image_settings.file_format = "PNG"
    s.render.image_settings.color_mode = "RGBA"
    s.view_settings.view_transform = "Standard"

    cam_data = bpy.data.cameras.new("cam")
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = 19.2
    cam = bpy.data.objects.new("cam", cam_data)
    cam.location = (0, 0, 10)
    s.collection.objects.link(cam)
    s.camera = cam

    fnt = fuente()
    negro = material("borde", (0, 0, 0))
    colores = {}
    for t in trabajos:
        rgb = ESTILOS[t["estilo"]][1]
        if rgb not in colores:
            colores[rgb] = material(f"c{len(colores)}", rgb)
        objs = texto(t["texto"], t["estilo"], fnt, colores[rgb], negro)
        s.render.filepath = t["archivo"]
        bpy.ops.render.render(write_still=True)
        for o in objs:
            bpy.data.objects.remove(o)
    print(f"[creador] {len(trabajos)} textos dibujados")


main()
