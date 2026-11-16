"""Renderiza una estructura pieza por pieza con Blender.

Uso (lo llama pipeline.py, pero se puede ejecutar a mano):
    blender -b --factory-startup -P creador/blender_construir.py -- \
        --estructura creador/estructuras/golden_gate.py \
        --linea-tiempo salida/golden_gate/linea_tiempo.json \
        --salida salida/golden_gate/frames --calidad baja

Opciones extra:
    --gpu            usa la tarjeta gráfica (CUDA/OptiX/HIP/Metal) si existe
    --frame N        renderiza solo el frame N (para revisar el encuadre)
    --guardar-blend  guarda también el .blend para abrirlo y retocarlo
"""
import argparse
import importlib.util
import json
import math
import os
import sys

import bpy
from mathutils import Euler, Vector

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from piezas import COLORES  # noqa: E402

CALIDADES = {
    #          ancho alto  fps muestras
    "baja":  (360, 640, 24, 6),
    "media": (720, 1280, 30, 24),
    "alta":  (1080, 1920, 30, 96),
}

DURACION_ANIM = {"caer": 0.55, "crecer": 0.9, "aparecer": 0.35}
ALTURA_CAIDA = 9.0


def args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--estructura", required=True)
    ap.add_argument("--linea-tiempo", required=True)
    ap.add_argument("--salida", required=True)
    ap.add_argument("--calidad", default="baja", choices=CALIDADES)
    ap.add_argument("--gpu", action="store_true")
    ap.add_argument("--frame", type=int)
    ap.add_argument("--guardar-blend", action="store_true")
    return ap.parse_args(argv)


def cargar_estructura(ruta):
    spec = importlib.util.spec_from_file_location("estructura", ruta)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def limpiar_escena():
    bpy.ops.wm.read_factory_settings(use_empty=True)


_materiales = {}


def material(nombre):
    if nombre in _materiales:
        return _materiales[nombre]
    m = bpy.data.materials.new(nombre)
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    r, g, b = COLORES.get(nombre, (0.8, 0.0, 0.8))
    bsdf.inputs["Base Color"].default_value = (r, g, b, 1)
    bsdf.inputs["Roughness"].default_value = 0.15 if nombre in ("agua", "vidrio") else 0.55
    if nombre in ("acero", "dorado"):
        bsdf.inputs["Metallic"].default_value = 0.8
    _materiales[nombre] = m
    return m


def malla_base(tipo):
    """Malla de tamaño 1x1x1 centrada en el origen (se reutiliza entre piezas)."""
    clave = "_base_" + tipo
    if clave in bpy.data.meshes:
        return bpy.data.meshes[clave]
    if tipo == "cubo":
        bpy.ops.mesh.primitive_cube_add(size=1)
    else:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.5, depth=1, vertices=16)
        bpy.ops.object.shade_smooth()
    obj = bpy.context.active_object
    malla = obj.data
    malla.name = clave
    bpy.data.objects.remove(obj)
    return malla


def crear_pieza(p, indice):
    """Crea el objeto. Devuelve (obj, posición_final, escala_final)."""
    dx, dy, dz = p["dim"]
    malla = malla_base(p["tipo"]).copy()
    # La geometría se escala dentro de la malla para que la escala del
    # objeto sea 1 y las animaciones de escala sean limpias.
    desplaz_z = 0.5 if p["anim"] == "crecer" else 0.0   # origen en la base
    for v in malla.vertices:
        v.co = Vector((v.co.x * dx, v.co.y * dy, (v.co.z + desplaz_z) * dz))
    obj = bpy.data.objects.new(f"pieza_{indice:04d}", malla)
    bpy.context.scene.collection.objects.link(obj)
    obj.data.materials.append(material(p["color"]))
    rot = Euler([math.radians(a) for a in p["rot"]], "XYZ")
    obj.rotation_euler = rot
    centro = Vector(p["pos"])
    if p["anim"] == "crecer":
        # El origen está en la base: bajar medio alto a lo largo del eje Z local
        centro = centro - rot.to_matrix() @ Vector((0, 0, dz / 2))
    obj.location = centro
    return obj, centro.copy()


def poner_interp(obj, interp, easing):
    ad = obj.animation_data
    if not ad or not ad.action:
        return
    for fc in ad.action.fcurves:
        if fc.data_path in ("location", "scale"):
            for kp in fc.keyframe_points:
                kp.interpolation = interp
                kp.easing = easing


def animar_pieza(obj, final_loc, anim, f_ini, fps):
    if anim == "ninguna":
        return
    f_fin = f_ini + max(2, round(DURACION_ANIM[anim] * fps))

    # Invisible hasta que le toca
    obj.hide_render = True
    obj.keyframe_insert("hide_render", frame=f_ini - 1)
    obj.hide_render = False
    obj.keyframe_insert("hide_render", frame=f_ini)

    if anim == "caer":
        obj.location = final_loc + Vector((0, 0, ALTURA_CAIDA))
        obj.keyframe_insert("location", frame=f_ini)
        obj.location = final_loc
        obj.keyframe_insert("location", frame=f_fin)
        poner_interp(obj, "BOUNCE", "EASE_OUT")
    elif anim == "crecer":
        obj.scale = (1, 1, 0.001)
        obj.keyframe_insert("scale", frame=f_ini)
        obj.scale = (1, 1, 1)
        obj.keyframe_insert("scale", frame=f_fin)
        poner_interp(obj, "BACK", "EASE_OUT")
    elif anim == "aparecer":
        obj.scale = (0.001, 0.001, 0.001)
        obj.keyframe_insert("scale", frame=f_ini)
        obj.scale = (1, 1, 1)
        obj.keyframe_insert("scale", frame=f_fin)
        poner_interp(obj, "BACK", "EASE_OUT")


def crear_camara(cfg, total_frames):
    centro = Vector(cfg["centro"])
    pivote = bpy.data.objects.new("pivote", None)
    pivote.location = centro
    bpy.context.scene.collection.objects.link(pivote)

    cam_data = bpy.data.cameras.new("camara")
    cam_data.lens = cfg.get("lente", 30)
    cam = bpy.data.objects.new("camara", cam_data)
    bpy.context.scene.collection.objects.link(cam)
    cam.parent = pivote
    cam.location = (cfg["distancia"], 0, cfg["altura"])
    track = cam.constraints.new("TRACK_TO")
    track.target = pivote
    track.track_axis = "TRACK_NEGATIVE_Z"
    track.up_axis = "UP_Y"

    pivote.rotation_euler = (0, 0, math.radians(cfg["angulo_inicio"]))
    pivote.keyframe_insert("rotation_euler", frame=1)
    pivote.rotation_euler = (0, 0, math.radians(cfg["angulo_fin"]))
    pivote.keyframe_insert("rotation_euler", frame=total_frames)
    for fc in pivote.animation_data.action.fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = "SINE"
            kp.easing = "EASE_IN_OUT"
    bpy.context.scene.camera = cam


def crear_luces():
    sol_data = bpy.data.lights.new("sol", "SUN")
    sol_data.energy = 4.0
    sol_data.angle = math.radians(3)
    sol = bpy.data.objects.new("sol", sol_data)
    sol.rotation_euler = (math.radians(50), math.radians(10), math.radians(35))
    bpy.context.scene.collection.objects.link(sol)

    mundo = bpy.data.worlds.new("cielo")
    mundo.use_nodes = True
    fondo = mundo.node_tree.nodes["Background"]
    fondo.inputs["Color"].default_value = (0.25, 0.55, 1.0, 1)
    fondo.inputs["Strength"].default_value = 0.9
    bpy.context.scene.world = mundo


def configurar_render(calidad, usar_gpu, salida, fps):
    ancho, alto, _, muestras = CALIDADES[calidad]
    s = bpy.context.scene
    s.render.engine = "CYCLES"
    s.cycles.samples = muestras
    s.cycles.use_denoising = True
    s.cycles.max_bounces = 4
    s.render.use_persistent_data = True
    s.render.resolution_x = ancho
    s.render.resolution_y = alto
    s.render.resolution_percentage = 100
    s.render.fps = fps
    s.render.image_settings.file_format = "PNG"
    s.render.filepath = os.path.join(os.path.abspath(salida), "")
    s.view_settings.view_transform = "AgX"
    s.view_settings.look = "AgX - Medium High Contrast"
    s.cycles.device = "CPU"
    if usar_gpu:
        prefs = bpy.context.preferences.addons["cycles"].preferences
        for tipo in ("OPTIX", "CUDA", "HIP", "METAL", "ONEAPI"):
            try:
                prefs.compute_device_type = tipo
                prefs.get_devices()
                if any(d.type == tipo for d in prefs.devices):
                    for d in prefs.devices:
                        d.use = d.type == tipo
                    s.cycles.device = "GPU"
                    print(f"[creador] GPU activada: {tipo}")
                    break
            except TypeError:
                continue
        else:
            print("[creador] No se encontró GPU, se usa CPU")


def main():
    a = args()
    est = cargar_estructura(a.estructura)
    with open(a.linea_tiempo, encoding="utf-8") as f:
        lt = json.load(f)
    fps = CALIDADES[a.calidad][2]

    limpiar_escena()
    configurar_render(a.calidad, a.gpu, a.salida, fps)
    crear_luces()

    for i, p in enumerate(est.ESCENARIO):
        crear_pieza(p, 9000 + i)

    # Segmentos de la línea de tiempo: [gancho, paso1..pasoN, final]
    segs = lt["segmentos"]
    indice = 0
    for n, paso in enumerate(est.PASOS):
        seg = segs[n + 1]
        t0, dur = seg["inicio"], seg["duracion"]
        piezas = paso["piezas"]
        # Las piezas entran escalonadas durante el 75% del paso
        ventana = dur * 0.75
        for k, p in enumerate(piezas):
            t = t0 + 0.15 + (ventana * k / max(1, len(piezas)))
            obj, loc = crear_pieza(p, indice)
            animar_pieza(obj, loc, p["anim"], round(t * fps) + 1, fps)
            indice += 1

    total = math.ceil(lt["duracion_total"] * fps)
    s = bpy.context.scene
    s.frame_start, s.frame_end = 1, total
    crear_camara(est.CAMARA, total)
    print(f"[creador] {indice} piezas, {total} frames a {fps} fps")

    os.makedirs(a.salida, exist_ok=True)
    if a.guardar_blend:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(os.path.abspath(a.salida), "..", "escena.blend"))
    if a.frame:
        s.frame_set(a.frame)
        s.render.filepath = os.path.join(os.path.abspath(a.salida), f"prueba_{a.frame:04d}.png")
        bpy.ops.render.render(write_still=True)
    else:
        bpy.ops.render.render(animation=True)


main()
