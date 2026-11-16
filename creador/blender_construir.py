"""Anima y renderiza una estructura con Blender (lo llama pipeline.py).

    blender -b --factory-startup -P creador/blender_construir.py -- \
        --estructura creador/estructuras/golden_gate.py \
        --linea-tiempo salida/golden_gate/linea_tiempo_es.json \
        --salida salida/golden_gate/frames_baja_es --calidad baja

Opciones: --gpu, --ver 2.5,10,31 (solo imágenes sueltas en esos segundos),
--guardar-blend (deja escena.blend para abrirla y retocarla a mano).
"""
import argparse
import importlib.util
import json
import math
import os
import random
import sys

import bpy
from mathutils import Euler, Matrix, Vector

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import guion  # noqa: E402
from piezas import COLORES  # noqa: E402

CALIDADES = {
    #          ancho alto  fps muestras
    "boceto": (270, 480, 12, 4),
    "baja":  (360, 640, 24, 6),
    "media": (720, 1280, 30, 16),
    "alta":  (1080, 1920, 30, 32),
}
FUENTES = [
    os.environ.get("CREADOR_FUENTE_ARCHIVO", ""),
    "/System/Library/Fonts/Supplemental/Arial Rounded Bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial Black.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/usr/share/fonts/opentype/inter/Inter-Black.otf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    r"C:\Windows\Fonts\ariblk.ttf",
]
SUAVE = {"suave": ("SINE", "EASE_IN_OUT"), "lineal": ("LINEAR", None),
         "rebote": ("BOUNCE", "EASE_OUT"), "atras": ("BACK", "EASE_OUT"),
         "frena": ("SINE", "EASE_OUT"), "acelera": ("QUAD", "EASE_IN")}
FPS = 24
rnd = random.Random(7)


def args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--estructura", required=True)
    ap.add_argument("--linea-tiempo", required=True)
    ap.add_argument("--salida", required=True)
    ap.add_argument("--calidad", default="baja", choices=CALIDADES)
    ap.add_argument("--gpu", action="store_true")
    ap.add_argument("--ver")
    ap.add_argument("--guardar-blend", action="store_true")
    return ap.parse_args(argv)


def cargar_estructura(ruta):
    spec = importlib.util.spec_from_file_location("estructura", ruta)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def fr(t):
    return int(round(t * FPS)) + 1


# --- Animación: claves --------------------------------------------------------

def fcurves_de(obj):
    """F-curves de un bloque animado, compatible con Blender 4.2 y 5.x."""
    ad = obj.animation_data
    if not ad or not ad.action:
        return []
    try:
        return list(ad.action.fcurves)
    except AttributeError:   # Blender 5: acciones por capas
        from bpy_extras import anim_utils
        cb = anim_utils.action_get_channelbag_for_slot(ad.action, ad.action_slot)
        return list(cb.fcurves) if cb else []


def clave(obj, ruta, frame, suave=None):
    """Inserta una clave; `suave` define cómo se mueve HASTA la clave siguiente."""
    obj.keyframe_insert(ruta, frame=frame)
    if not suave:
        return
    interp, easing = SUAVE[suave]
    for fc in fcurves_de(obj):
        if fc.data_path == ruta:
            for kp in fc.keyframe_points:
                if abs(kp.co.x - frame) < 0.5:
                    kp.interpolation = interp
                    if easing:
                        kp.easing = easing


def visible_entre(obj, f0, f1=None):
    obj.hide_render = True
    obj.keyframe_insert("hide_render", frame=max(0, f0 - 1))
    obj.hide_render = False
    obj.keyframe_insert("hide_render", frame=f0)
    if f1 is not None:
        obj.keyframe_insert("hide_render", frame=f1 - 1)
        obj.hide_render = True
        obj.keyframe_insert("hide_render", frame=f1)


# --- Materiales y mallas ----------------------------------------------------------

_materiales = {}


def _nodos(m):
    if bpy.app.version < (5, 0, 0):
        m.use_nodes = True
    return m.node_tree


def material(nombre):
    if nombre in _materiales:
        return _materiales[nombre]
    m = bpy.data.materials.new(nombre)
    arbol = _nodos(m)
    bsdf = arbol.nodes["Principled BSDF"]
    r, g, b = COLORES.get(nombre, (0.8, 0.0, 0.8))
    bsdf.inputs["Base Color"].default_value = (r, g, b, 1)
    bsdf.inputs["Roughness"].default_value = 0.6
    if nombre == "agua":
        bsdf.inputs["Roughness"].default_value = 0.18
        try:    # olas: relieve con ruido que se mueve
            ruido = arbol.nodes.new("ShaderNodeTexNoise")
            ruido.noise_dimensions = "4D"
            ruido.inputs["Scale"].default_value = 0.35
            ruido.inputs["Detail"].default_value = 3
            rel = arbol.nodes.new("ShaderNodeBump")
            rel.inputs["Strength"].default_value = 0.35
            arbol.links.new(ruido.outputs[0], rel.inputs["Height"])
            arbol.links.new(rel.outputs[0], bsdf.inputs["Normal"])
            w = ruido.inputs["W"]
            w.default_value = 0.0
            w.keyframe_insert("default_value", frame=1)
            w.default_value = 6.0
            w.keyframe_insert("default_value", frame=24 * 120)
            for fc in fcurves_de(arbol):
                for kp in fc.keyframe_points:
                    kp.interpolation = "LINEAR"
        except Exception as e:   # si cambia la API, el agua queda lisa
            print("[creador] agua sin olas:", e)
    _materiales[nombre] = m
    return m


def material_luz(nombre, rgb):
    """Material que no depende de las luces (textos, etiquetas)."""
    clave_m = "luz_" + nombre
    if clave_m in _materiales:
        return _materiales[clave_m]
    m = bpy.data.materials.new(clave_m)
    arbol = _nodos(m)
    for n in list(arbol.nodes):
        arbol.nodes.remove(n)
    salida = arbol.nodes.new("ShaderNodeOutputMaterial")
    em = arbol.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*rgb, 1)
    arbol.links.new(em.outputs[0], salida.inputs[0])
    _materiales[clave_m] = m
    return m


def malla_base(tipo):
    nombre = "_base_" + tipo
    if nombre in bpy.data.meshes:
        return bpy.data.meshes[nombre]
    if tipo == "cubo":
        bpy.ops.mesh.primitive_cube_add(size=1)
    elif tipo == "cilindro":
        bpy.ops.mesh.primitive_cylinder_add(radius=0.5, depth=1, vertices=16)
        bpy.ops.object.shade_smooth()
    elif tipo == "esfera":
        bpy.ops.mesh.primitive_ico_sphere_add(radius=0.5, subdivisions=2)
    elif tipo == "cono":
        bpy.ops.mesh.primitive_cone_add(radius1=0.5, depth=1, vertices=16)
    obj = bpy.context.active_object
    malla = obj.data
    malla.name = nombre
    bpy.data.objects.remove(obj)
    return malla


def enlazar(obj):
    bpy.context.scene.collection.objects.link(obj)
    return obj


def sin_sombra(obj):
    obj.visible_shadow = False
    obj.visible_diffuse = False
    obj.visible_glossy = False
    obj.visible_transmission = False


# --- Piezas y grupos -----------------------------------------------------------------

grupos = {}
_n_pieza = [0]
_n_polvo = [0]


def grupo(nombre, pivote):
    if nombre not in grupos:
        e = enlazar(bpy.data.objects.new("grupo_" + nombre, None))
        e.location = pivote
        grupos[nombre] = {"obj": e, "loc": Vector(pivote), "rot": [0.0, 0.0, 0.0], "esc": 1.0}
    return grupos[nombre]


def crear_pieza(p):
    dx, dy, dz = p["dim"]
    malla = malla_base(p["tipo"]).copy()
    base = 0.5 if p["anim"] == "crecer" else 0.0   # origen en la base
    for v in malla.vertices:
        v.co = Vector((v.co.x * dx, v.co.y * dy, (v.co.z + base) * dz))
    _n_pieza[0] += 1
    obj = enlazar(bpy.data.objects.new(f"pieza_{_n_pieza[0]:04d}", malla))
    malla.materials.append(material(p["color"]))
    if p["tipo"] == "cubo" and min(dx, dy, dz) >= 0.12 and max(dx, dy, dz) < 60:
        bisel = obj.modifiers.new("bisel", "BEVEL")
        bisel.width = min(0.06, 0.2 * min(dx, dy, dz))
        bisel.segments = 1
    rot = Euler([math.radians(a) for a in p["rot"]], "XYZ")
    obj.rotation_euler = rot
    centro = Vector(p["pos"])
    if p["anim"] == "crecer":
        centro = centro - rot.to_matrix() @ Vector((0, 0, dz / 2))
    obj.location = centro
    if p.get("id"):
        g = grupo(p["id"], p.get("pivote", p["pos"]))
        obj.parent = g["obj"]
        obj.matrix_parent_inverse = Matrix.Translation(-Vector(g["obj"].location))
    return obj, centro.copy(), rot


def polvo(pos, tam, f):
    if _n_polvo[0] >= 90:
        return
    for sx in (-1, 1):
        _n_polvo[0] += 1
        m = malla_base("esfera").copy()
        m.materials.append(material("blanco"))
        o = enlazar(bpy.data.objects.new("polvo", m))
        o.visible_shadow = False
        o.location = pos
        o.scale = (0.001,) * 3
        visible_entre(o, f, f + 12)
        clave(o, "location", f, "frena")
        clave(o, "scale", f, "frena")
        o.location = Vector(pos) + Vector((sx * tam * 1.3, rnd.uniform(-1, 1) * tam, tam * 0.5))
        o.scale = (tam,) * 3
        clave(o, "location", f + 5, "lineal")
        clave(o, "scale", f + 5, "lineal")
        o.location = o.location + Vector((sx * tam * 0.5, 0, tam * 0.4))
        o.scale = (0.001,) * 3
        clave(o, "location", f + 11)
        clave(o, "scale", f + 11)


def animar_entrada(obj, loc, rot, p, t):
    anim = p["anim"]
    if anim == "ninguna" or t is None:
        return
    f0 = fr(t)
    f1 = f0 + max(2, round(guion.DUR_ENTRADA[anim] * FPS))
    visible_entre(obj, f0)
    if anim == "caer":
        alto = p.get("altura_caida", 8.0)
        obj.location = loc + Vector((0, 0, alto))
        obj.rotation_euler = Euler((rot.x + math.radians(rnd.uniform(-14, 14)),
                                    rot.y + math.radians(rnd.uniform(-14, 14)), rot.z), "XYZ")
        clave(obj, "location", f0, "rebote")
        clave(obj, "rotation_euler", f0, "frena")
        obj.location = loc
        obj.rotation_euler = rot
        clave(obj, "location", f1)
        clave(obj, "rotation_euler", f0 + max(2, (f1 - f0) // 3))
        tam = max(p["dim"])
        if tam >= 1.5 and not p.get("id"):
            base = loc - Vector((0, 0, p["dim"][2] / 2))
            polvo(base, min(0.9, 0.22 * tam), f0 + round((f1 - f0) * 0.36))
    elif anim == "crecer":
        obj.scale = (1, 1, 0.001)
        clave(obj, "scale", f0, "atras")
        obj.scale = (1, 1, 1)
        clave(obj, "scale", f1)
    elif anim == "subir":
        obj.location = loc - Vector((0, 0, p.get("desde_abajo", 7.0)))
        clave(obj, "location", f0, "atras")
        obj.location = loc
        clave(obj, "location", f1)
    elif anim == "aparecer":
        obj.scale = (0.001,) * 3
        clave(obj, "scale", f0, "atras")
        obj.scale = (1, 1, 1)
        clave(obj, "scale", f1)


def aplicar_accion(a):
    if a["id"] not in grupos:
        print(f"[creador] AVISO: la acción usa un id que no existe: {a['id']}")
        return
    g = grupos[a["id"]]
    o = g["obj"]
    f0, f1 = fr(a["t0"]), max(fr(a["t0"]) + 1, fr(a["t1"]))
    suave = a.get("suave", "lineal" if a.get("hasta_fin") else "suave")

    def poner(frame, s=None):
        o.location = g["loc"]
        o.rotation_euler = Euler(g["rot"], "XYZ")
        o.scale = (g["esc"],) * 3
        for ruta in ("location", "rotation_euler", "scale"):
            clave(o, ruta, frame, s)

    poner(f0, suave)
    if "mover" in a:
        g["loc"] = g["loc"] + Vector(a["mover"])
    if "girar" in a:
        g["rot"] = [g["rot"][i] + math.radians(a["girar"][i]) for i in range(3)]
    if "escala" in a:
        g["esc"] *= a["escala"]
    if a.get("quitar"):
        g["esc"] = 0.001
    poner(f1)


# --- Cámara ------------------------------------------------------------------------

def crear_camara(claves, lente):
    pivote = enlazar(bpy.data.objects.new("pivote", None))
    cam_data = bpy.data.cameras.new("camara")
    cam_data.lens = lente
    cam_data.clip_start = 0.05
    cam = enlazar(bpy.data.objects.new("camara", cam_data))
    cam.parent = pivote
    mira = cam.constraints.new("TRACK_TO")
    mira.target = pivote
    mira.track_axis = "TRACK_NEGATIVE_Z"
    mira.up_axis = "UP_Y"
    for k in claves:
        pose, f = k["pose"], fr(k["t"])
        pivote.location = pose["centro"]
        pivote.rotation_euler = (0, 0, math.radians(pose["angulo"]))
        cam.location = (pose["distancia"], 0, pose["altura"])
        clave(pivote, "location", f, k["tramo"])
        clave(pivote, "rotation_euler", f, k["tramo"])
        clave(cam, "location", f, k["tramo"])
    bpy.context.scene.camera = cam
    return cam


# --- Textos ---------------------------------------------------------------------------

_fuente = []


def fuente():
    if not _fuente:
        _fuente.append(None)
        for f in FUENTES:
            if f and os.path.exists(f):
                _fuente[0] = bpy.data.fonts.load(f)
                break
    return _fuente[0]


def curva_texto(cuerpo, tam, ancho=None, borde=0.0):
    cu = bpy.data.curves.new("txt", "FONT")
    cu.body = cuerpo
    if fuente():
        cu.font = fuente()
    cu.size = tam
    cu.align_x = "CENTER"
    cu.align_y = "CENTER"
    cu.space_line = 1.0
    cu.space_character = 1.06
    if ancho:
        cu.text_boxes[0].width = ancho
        cu.text_boxes[0].x = -ancho / 2
    cu.offset = borde
    return cu


def texto_doble(cuerpo, tam, color, padre, pos, ancho=None, grosor=0.07):
    """Texto con contorno negro. Devuelve [relleno, contorno]."""
    objs = []
    for es_borde in (False, True):
        cu = curva_texto(cuerpo, tam, ancho, tam * grosor if es_borde else 0.0)
        o = enlazar(bpy.data.objects.new("txt", cu))
        cu.materials.append(material_luz("negro", (0, 0, 0)) if es_borde
                            else material_luz(f"c{color}", color))
        o.parent = padre
        o.location = (pos[0], pos[1], pos[2] - (tam * 0.02 if es_borde else 0.0))
        sin_sombra(o)
        objs.append(o)
    return objs


def pop(objs, f0, f1, escala_fin=1.0):
    """Aparece con un saltito en f0 y desaparece en f1."""
    for o in objs:
        visible_entre(o, f0, f1)
        o.scale = (0.55,) * 3
        clave(o, "scale", f0, "atras")
        o.scale = (escala_fin,) * 3
        clave(o, "scale", f0 + 3)


BLANCO, AMARILLO = (1.0, 1.0, 1.0), (1.0, 0.78, 0.0)


def textos_en_camara(cam, plan, lente):
    alto1 = 36.0 / lente          # alto visible a 1 unidad de la cámara (vídeo vertical)
    px = alto1 / 1920.0           # 1 píxel de un vídeo de 1080x1920

    def y_de(frac_desde_arriba):
        return (0.5 - frac_desde_arriba) * alto1

    for w in plan["palabras"]:
        f0, f1 = fr(w["t0"]), max(fr(w["t0"]) + 2, fr(w["t1"]))
        color, tam = (AMARILLO, 112) if w["final"] else (BLANCO, 100)
        if len(w["texto"]) > 11:
            tam *= 11.5 / len(w["texto"])
        pop(texto_doble(w["texto"], tam * px, color, cam, (0, y_de(0.60), -1)), f0, f1)

    if plan["titulo"]:
        t = plan["titulo"]
        objs = texto_doble(t["texto"], 86 * px, AMARILLO, cam, (0, y_de(0.17), -1), grosor=0.045)
        pop(objs, fr(t["t0"]) + 2, fr(t["t1"]))

    for av in plan["avisos"]:
        raiz = enlazar(bpy.data.objects.new("aviso", None))
        raiz.parent = cam
        raiz.location = (0, y_de(0.235), -1)
        raiz.rotation_euler = (0, 0, math.radians(-4))
        tam = 76 * px
        cu = curva_texto(av["texto"], tam)
        cu.materials.append(material_luz(f"c{BLANCO}", BLANCO))
        txt = enlazar(bpy.data.objects.new("aviso_txt", cu))
        txt.parent = raiz
        bpy.context.view_layer.update()
        ancho, alto = txt.dimensions.x, txt.dimensions.y
        caja_m = malla_base("cubo").copy()
        for v in caja_m.vertices:
            v.co = Vector((v.co.x * (ancho + tam * 0.9), v.co.y * (alto + tam * 0.7), v.co.z * tam * 0.02))
        caja_m.materials.append(material_luz("negro", (0, 0, 0)))
        caja = enlazar(bpy.data.objects.new("aviso_caja", caja_m))
        caja.parent = raiz
        caja.location = (0, 0, -tam * 0.05)
        f0, f1 = fr(av["t0"]), fr(av["t1"])
        for o in (txt, caja):
            sin_sombra(o)
            visible_entre(o, f0, f1)
        raiz.scale = (0.3,) * 3
        clave(raiz, "scale", f0, "atras")
        raiz.scale = (1, 1, 1)
        clave(raiz, "scale", f0 + 5)


def etiquetas_3d(cam, plan):
    azul = material_luz("etiqueta", (0.03, 0.22, 0.85))
    for et in plan["etiquetas"]:
        tam = et["tam"]
        alto = et["alto"] if et["alto"] is not None else tam * 3.4
        destino = Vector(et["pos"])
        raiz = enlazar(bpy.data.objects.new("etiqueta", None))
        raiz.location = destino + Vector((0, 0, alto))
        cara = enlazar(bpy.data.objects.new("etiqueta_cara", None))
        cara.parent = raiz
        copia = cara.constraints.new("COPY_ROTATION")
        copia.target = cam
        cu = curva_texto(et["texto"], tam)
        cu.materials.append(material_luz(f"c{BLANCO}", BLANCO))
        txt = enlazar(bpy.data.objects.new("etiqueta_txt", cu))
        txt.parent = cara
        txt.location = (0, 0, tam * 0.06)
        bpy.context.view_layer.update()
        ancho = txt.dimensions.x
        partes = [txt]

        def parte(tipo, dim, pos, padre, rot=(0, 0, 0)):
            m = malla_base(tipo).copy()
            for v in m.vertices:
                v.co = Vector((v.co.x * dim[0], v.co.y * dim[1], v.co.z * dim[2]))
            m.materials.append(azul)
            o = enlazar(bpy.data.objects.new("etiqueta_p", m))
            o.parent = padre
            o.location = pos
            o.rotation_euler = [math.radians(a) for a in rot]
            partes.append(o)

        parte("cubo", (ancho + tam * 0.9, tam * 1.6, tam * 0.05), (0, 0, 0), cara)
        largo = max(0.1, alto - tam * 1.7)
        parte("cilindro", (tam * 0.2, tam * 0.2, largo), (0, 0, -tam * 0.8 - largo / 2), raiz)
        parte("cono", (tam * 0.7, tam * 0.7, tam * 0.8), (0, 0, -alto + tam * 0.5), raiz, (180, 0, 0))
        f0, f1 = fr(et["t0"]), fr(et["t1"])
        for o in partes:
            sin_sombra(o)
            visible_entre(o, f0, f1)
        raiz.scale = (0.001,) * 3
        clave(raiz, "scale", f0, "atras")
        raiz.scale = (1, 1, 1)
        clave(raiz, "scale", f0 + 6)


def confeti(c):
    colores = ["rojo", "amarillo", "azul", "verde", "rosa", "blanco", "turquesa"]
    centro, radio = Vector(c["centro"]), c["radio"]
    f0 = fr(c["t"])
    tam = radio * 0.035
    for i in range(90):
        m = malla_base("cubo").copy()
        for v in m.vertices:
            v.co = Vector((v.co.x * tam, v.co.y * tam * 0.6, v.co.z * tam * 0.12))
        m.materials.append(material(colores[i % len(colores)]))
        o = enlazar(bpy.data.objects.new("confeti", m))
        o.visible_shadow = False
        ang = rnd.uniform(0, 2 * math.pi)
        r = radio * rnd.uniform(0.15, 1.0)
        lado = Vector((math.cos(ang) * r, math.sin(ang) * r, 0))
        fa = f0 + rnd.randint(0, 6)
        visible_entre(o, fa)
        o.location = centro + lado * 0.15
        o.scale = (0.001,) * 3
        clave(o, "location", fa, "frena")
        clave(o, "scale", fa, "lineal")
        clave(o, "rotation_euler", fa, "lineal")
        o.scale = (1, 1, 1)
        clave(o, "scale", fa + 3)
        o.location = centro + lado * 0.8 + Vector((0, 0, radio * rnd.uniform(0.5, 1.0)))
        clave(o, "location", fa + round(0.6 * FPS), "acelera")
        o.location = centro + lado * 1.15 + Vector((0, 0, -radio * rnd.uniform(0.2, 0.5)))
        o.rotation_euler = [rnd.uniform(-12, 12) for _ in range(3)]
        clave(o, "location", fa + round(rnd.uniform(2.4, 3.6) * FPS))
        clave(o, "rotation_euler", fa + round(3.6 * FPS))


# --- Escena, luz y render -----------------------------------------------------------

def crear_luces():
    sol_data = bpy.data.lights.new("sol", "SUN")
    sol_data.energy = 3.2
    sol_data.angle = math.radians(6)
    sol = enlazar(bpy.data.objects.new("sol", sol_data))
    sol.rotation_euler = (math.radians(48), math.radians(8), math.radians(-150))
    mundo = bpy.data.worlds.new("cielo")
    if bpy.app.version < (5, 0, 0):
        mundo.use_nodes = True
    fondo = mundo.node_tree.nodes["Background"]
    fondo.inputs["Color"].default_value = (0.45, 0.72, 1.0, 1)
    fondo.inputs["Strength"].default_value = 1.0
    bpy.context.scene.world = mundo


def configurar_render(calidad, usar_gpu, salida):
    ancho, alto, fps, muestras = CALIDADES[calidad]
    s = bpy.context.scene
    s.render.engine = "CYCLES"
    s.cycles.samples = muestras
    s.cycles.use_denoising = True
    # Filtro antirruido en modo rápido: se ve igual en este estilo y ahorra ~40 %
    for opcion, valor in (("denoising_prefilter", "NONE"), ("denoising_quality", "FAST"),
                          ("denoising_input_passes", "RGB_ALBEDO")):
        try:
            setattr(s.cycles, opcion, valor)
        except (AttributeError, TypeError):
            pass
    s.cycles.max_bounces = 3
    s.render.use_persistent_data = True
    s.render.resolution_x = ancho
    s.render.resolution_y = alto
    s.render.resolution_percentage = 100
    s.render.fps = fps
    s.render.image_settings.file_format = "PNG"
    s.render.filepath = os.path.join(os.path.abspath(salida), "")
    try:
        s.view_settings.view_transform = "Standard"
        s.view_settings.look = "None"
    except TypeError:
        pass
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
                    try:
                        s.cycles.denoising_use_gpu = True
                    except (AttributeError, TypeError):
                        pass
                    print(f"[creador] GPU activada: {tipo}")
                    break
            except TypeError:
                continue
        else:
            print("[creador] No se encontró GPU, se usa CPU")


def main():
    global FPS
    a = args()
    est = cargar_estructura(a.estructura)
    with open(a.linea_tiempo, encoding="utf-8") as f:
        lt = json.load(f)
    FPS = CALIDADES[a.calidad][2]
    plan = guion.planificar(est, lt, lt["idioma"])

    bpy.ops.wm.read_factory_settings(use_empty=True)
    configurar_render(a.calidad, a.gpu, a.salida)
    crear_luces()

    for item in plan["piezas"]:
        obj, loc, rot = crear_pieza(item["p"])
        animar_entrada(obj, loc, rot, item["p"], item["t"])
    for acc in sorted(plan["acciones"], key=lambda x: x["t0"]):
        aplicar_accion(acc)

    lente = getattr(est, "CAMARA", {}).get("lente", 24)
    cam = crear_camara(plan["camara"], lente)
    textos_en_camara(cam, plan, lente)
    etiquetas_3d(cam, plan)
    if plan["confeti"]:
        confeti(plan["confeti"])

    total = math.ceil(plan["total"] * FPS)
    s = bpy.context.scene
    s.frame_start, s.frame_end = 1, total
    print(f"[creador] {_n_pieza[0]} piezas, {total} frames a {FPS} fps")

    os.makedirs(a.salida, exist_ok=True)
    if a.guardar_blend:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(os.path.abspath(a.salida), "..", "escena.blend"))
    if a.ver:
        for seg in a.ver.split(","):
            f = min(total, fr(float(seg)))
            s.frame_set(f)
            s.render.filepath = os.path.join(os.path.abspath(a.salida), f"ver_{float(seg):06.2f}.png")
            bpy.ops.render.render(write_still=True)
    else:
        bpy.ops.render.render(animation=True)


main()
