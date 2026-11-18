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
    ap.add_argument("--estilo", default="maqueta")
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
    for hijo in obj.children_recursive:
        _visible(hijo, f0, f1)
    _visible(obj, f0, f1)


def _visible(obj, f0, f1=None):
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


def material(nombre, brillo=0.0):
    """Material de un color de COLORES. brillo > 0 lo hace emitir luz (ventanas, pantallas)."""
    if brillo:
        clave_m = f"{nombre}@{brillo}"
        if clave_m not in _materiales:
            m = material(nombre).copy()
            m.name = clave_m
            b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
            r, g, bl = COLORES.get(nombre, (1, 1, 1))
            em = _entrada(b, "Emission Color", "Emission")
            if em:
                em.default_value = (r, g, bl, 1)
            fuerza = _entrada(b, "Emission Strength")
            if fuerza:
                fuerza.default_value = brillo
            _materiales[clave_m] = m
        return _materiales[clave_m]
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


# --- Modelos 3D descargados (creador/banco_modelos.py) ---------------------------

_biblioteca = {}
_catalogo = []


def catalogo_modelos():
    if not _catalogo:
        ruta = os.path.join(os.path.dirname(AQUI), "modelos", "catalogo.json")
        if os.path.exists(ruta):
            with open(ruta, encoding="utf-8") as f:
                _catalogo.extend(json.load(f))
    return _catalogo


def importar(id_modelo):
    """Importa un modelo una sola vez y lo guarda oculto para hacer copias."""
    if id_modelo in _biblioteca:
        return _biblioteca[id_modelo]
    item = next((m for m in catalogo_modelos() if m["id"] == id_modelo), None)
    if item is None:
        print(f"[creador] AVISO: no existe el modelo «{id_modelo}» "
              "(mira python3 creador/banco_modelos.py --lista)")
        _biblioteca[id_modelo] = None
        return None
    ruta = os.path.join(os.path.dirname(AQUI), item["archivo"])
    antes = set(bpy.data.objects)
    ext = os.path.splitext(ruta)[1].lower()
    try:
        if ext in (".glb", ".gltf"):
            bpy.ops.import_scene.gltf(filepath=ruta)
        elif ext == ".fbx":
            bpy.ops.import_scene.fbx(filepath=ruta)
        else:
            bpy.ops.wm.obj_import(filepath=ruta)
    except Exception as e:
        print(f"[creador] AVISO: no pude importar {ruta}: {e}")
        _biblioteca[id_modelo] = None
        return None
    nuevos = [o for o in bpy.data.objects if o not in antes]
    bpy.context.view_layer.update()
    mallas = [(o.data, o.matrix_world.copy(), [m for m in o.data.materials])
              for o in nuevos if o.type == "MESH"]
    puntos = [mw @ Vector(v.co) for datos, mw, _ in mallas for v in datos.vertices]
    for o in nuevos:
        bpy.data.objects.remove(o)
    if not puntos:
        _biblioteca[id_modelo] = None
        return None
    mn = Vector((min(p.x for p in puntos), min(p.y for p in puntos), min(p.z for p in puntos)))
    mx = Vector((max(p.x for p in puntos), max(p.y for p in puntos), max(p.z for p in puntos)))
    _biblioteca[id_modelo] = {"mallas": mallas, "min": mn, "max": mx}
    return _biblioteca[id_modelo]


def crear_modelo(p):
    lib = importar(p["modelo"])
    raiz = enlazar(bpy.data.objects.new(f"modelo_{_n_pieza[0]:04d}", None))
    if lib is None:     # sin modelo: queda vacío y la escena sigue funcionando
        return raiz, (1, 1, 1)
    tam = lib["max"] - lib["min"]
    if p.get("largo"):
        esc = p["largo"] / max(tam.x, tam.y, 1e-6)
    elif p.get("alto"):
        esc = p["alto"] / max(tam.z, 1e-6)
    else:
        esc = p.get("escala", 1.0)
    base = Vector(((lib["min"].x + lib["max"].x) / 2, (lib["min"].y + lib["max"].y) / 2, lib["min"].z))
    for datos, mw, _ in lib["mallas"]:
        hijo = enlazar(bpy.data.objects.new(raiz.name + "_p", datos))
        hijo.parent = raiz
        hijo.matrix_parent_inverse = Matrix.Identity(4)
        hijo.matrix_basis = Matrix.Translation(-base) @ mw
    raiz.scale = (esc, esc, esc)
    return raiz, (tam.x * esc, tam.y * esc, tam.z * esc)


def crear_luz(p):
    datos = bpy.data.lights.new("luz", p.get("clase", "POINT"))
    datos.energy = p.get("potencia", 50)
    datos.color = tuple(p.get("rgb", (1.0, 0.8, 0.6)))
    datos.shadow_soft_size = p.get("radio", 0.2)
    if datos.type == "SPOT":
        datos.spot_size = math.radians(p.get("apertura", 60))
    _n_pieza[0] += 1
    obj = enlazar(bpy.data.objects.new(f"luz_{_n_pieza[0]:04d}", datos))
    rot = Euler([math.radians(a) for a in p["rot"]], "XYZ")
    obj.rotation_euler = rot
    obj.location = Vector(p["pos"])
    if p.get("id"):
        g = grupo(p["id"], p.get("pivote", p["pos"]))
        obj.parent = g["obj"]
        obj.matrix_parent_inverse = Matrix.Translation(-Vector(g["obj"].location))
    return obj, Vector(p["pos"]), rot


def crear_pieza(p):
    if p["tipo"] == "luz":
        return crear_luz(p)
    if p["tipo"] == "modelo":
        _n_pieza[0] += 1
        obj, dims = crear_modelo(p)
        p["dim"] = list(dims)
        rot = Euler([math.radians(a) for a in p["rot"]], "XYZ")
        obj.rotation_euler = rot
        centro = Vector(p["pos"])          # en los modelos, pos = punto del suelo bajo el modelo
        obj.location = centro
        if p.get("id"):
            g = grupo(p["id"], p.get("pivote", p["pos"]))
            obj.parent = g["obj"]
            obj.matrix_parent_inverse = Matrix.Translation(-Vector(g["obj"].location))
        return obj, centro.copy(), rot
    dx, dy, dz = p["dim"]
    malla = malla_base(p["tipo"]).copy()
    base = 0.5 if p["anim"] == "crecer" else 0.0   # origen en la base
    for v in malla.vertices:
        v.co = Vector((v.co.x * dx, v.co.y * dy, (v.co.z + base) * dz))
    _n_pieza[0] += 1
    obj = enlazar(bpy.data.objects.new(f"pieza_{_n_pieza[0]:04d}", malla))
    malla.materials.append(material(p["color"], p.get("brillo", 0.0)))
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
    base_esc = Vector(obj.scale)
    anim = p["anim"]
    if anim == "ninguna" or t is None:
        return
    if p["tipo"] == "luz":      # una luz solo se enciende
        visible_entre(obj, fr(t))
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
            base = loc if p["tipo"] == "modelo" else loc - Vector((0, 0, p["dim"][2] / 2))
            polvo(base, min(0.9, 0.22 * tam), f0 + round((f1 - f0) * 0.36))
    elif anim == "crecer":
        obj.scale = (base_esc.x, base_esc.y, base_esc.z * 0.001)
        clave(obj, "scale", f0, "atras")
        obj.scale = base_esc
        clave(obj, "scale", f1)
    elif anim == "subir":
        obj.location = loc - Vector((0, 0, p.get("desde_abajo", 7.0)))
        clave(obj, "location", f0, "atras")
        obj.location = loc
        clave(obj, "location", f1)
    elif anim == "aparecer":
        obj.scale = base_esc * 0.001
        clave(obj, "scale", f0, "atras")
        obj.scale = base_esc
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


def caja_plana(ancho, alto, rgb, padre, pos, nombre="txt_caja"):
    m = malla_base("cubo").copy()
    for v in m.vertices:
        v.co = Vector((v.co.x * ancho, v.co.y * alto, v.co.z * 0.0005))
    m.materials.append(material_luz(f"c{rgb}", rgb))
    o = enlazar(bpy.data.objects.new(nombre, m))
    o.parent = padre
    o.location = pos
    sin_sombra(o)
    return o


def subtitulos_karaoke(cam, plan, px, y_de, conf):
    """La frase completa en gris; la palabra que suena, en blanco dentro de un recuadro."""
    gris = tuple(conf.get("color_frase", (0.62, 0.66, 0.72)))
    tam = conf.get("tam", 66) * px
    ancho_max = 880 * px
    por_frase = conf.get("palabras_por_frase", 4)
    y0 = y_de(conf.get("altura", 0.23))
    escenas = {}
    for w in plan["palabras"]:
        w = dict(w, palabra=w.get("crudo") or w["texto"])
        escenas.setdefault(w["escena"], []).append(w)
    for lista in escenas.values():
        frases, actual = [], []
        for w in lista:
            actual.append(w)
            fin_frase = w["palabra"][-1:] in ".?!:;," or len(actual) >= por_frase
            if fin_frase:
                frases.append(actual)
                actual = []
        if actual:
            frases.append(actual)
        for k, frase in enumerate(frases):
            t0 = frase[0]["t0"]
            t1 = frases[k + 1][0]["t0"] if k + 1 < len(frases) else frase[-1]["t1"] + 0.35
            # medir cada palabra y repartir en líneas centradas
            medidas = []
            for w in frase:
                cu = curva_texto(w["palabra"], tam)
                o = enlazar(bpy.data.objects.new("txt_medida", cu))
                bpy.context.view_layer.update()
                medidas.append(o.dimensions.x)
                bpy.data.objects.remove(o)
            espacio = tam * 0.3
            lineas, linea, ancho = [], [], 0.0
            for w, a in zip(frase, medidas):
                if linea and ancho + espacio + a > ancho_max:
                    lineas.append((linea, ancho))
                    linea, ancho = [], 0.0
                ancho += (espacio if linea else 0) + a
                linea.append((w, a))
            lineas.append((linea, ancho))
            for n, (linea, ancho) in enumerate(lineas):
                x = -ancho / 2
                y = y0 - n * tam * 1.35
                for i, (w, a) in enumerate(linea):
                    cx = x + a / 2
                    fondo = texto_doble(w["palabra"], tam, gris, cam, (cx, y, -1), grosor=0.03)
                    for o in fondo:
                        visible_entre(o, fr(t0), fr(t1))
                    sig = linea[i + 1][0]["t0"] if i + 1 < len(linea) else w["t1"] + 0.15
                    w0, w1 = fr(w["t0"]), max(fr(w["t0"]) + 2, fr(min(sig, t1)))
                    activa = texto_doble(w["palabra"], tam, BLANCO, cam, (cx, y, -0.999), grosor=0.05)
                    marco = caja_plana(a + tam * 0.45, tam * 1.15, (1, 1, 1), cam, (cx, y + tam * 0.02, -1.001))
                    interior = caja_plana(a + tam * 0.33, tam * 1.03, (0.03, 0.04, 0.07), cam, (cx, y + tam * 0.02, -1.0005))
                    for o in activa + [marco, interior]:
                        visible_entre(o, w0, w1)
                    x += a + espacio


def textos_en_camara(cam, plan, lente, conf=None):
    conf = conf or {}
    alto1 = 36.0 / lente          # alto visible a 1 unidad de la cámara (vídeo vertical)
    px = alto1 / 1920.0           # 1 píxel de un vídeo de 1080x1920

    def y_de(frac_desde_arriba):
        return (0.5 - frac_desde_arriba) * alto1

    if conf.get("marca"):         # tu @usuario, discreto, todo el video
        objs = texto_doble(conf["marca"], 34 * px, (0.85, 0.87, 0.9), cam, (0, y_de(0.62), -1.002), grosor=0.04)
        for o in objs:
            visible_entre(o, 1)

    for op in plan.get("opciones", []):     # pantalla final "¿qué harías?"
        n = len(op["items"])
        for k, item in enumerate(op["items"]):
            y = y_de(0.40 + k * 0.13 - (n - 2) * 0.05)
            f0 = fr(op["t0"]) + k * 6
            caja = caja_plana(860 * px, 150 * px, (0.06, 0.06, 0.08), cam, (0, y, -1.001), "aviso_op")
            borde = caja_plana(876 * px, 166 * px, tuple(conf.get("color_opciones", (0.9, 0.12, 0.1))), cam,
                               (0, y, -1.0015), "aviso_op")
            txt = texto_doble(item, 58 * px, BLANCO, cam, (0, y - 10 * px, -0.999), ancho=800 * px, grosor=0.04)
            pop([caja, borde] + txt, f0, fr(op["t1"]))

    if conf.get("subtitulos") == "karaoke":
        subtitulos_karaoke(cam, plan, px, y_de, conf.get("karaoke", {}))
        plan = dict(plan, palabras=[])

    for w in plan["palabras"]:
        f0, f1 = fr(w["t0"]), max(fr(w["t0"]) + 2, fr(w["t1"]))
        color, tam = (AMARILLO, 112) if w["final"] else (BLANCO, 100)
        if len(w["texto"]) > 11:
            tam *= 11.5 / len(w["texto"])
        pop(texto_doble(w["texto"], tam * px, color, cam, (0, y_de(0.60), -1)), f0, f1)

    if plan["titulo"]:
        t = plan["titulo"]
        color_t = tuple(conf.get("color_titulo", AMARILLO))
        objs = texto_doble(t["texto"], 86 * px, color_t, cam, (0, y_de(conf.get("titulo_altura", 0.17)), -1),
                           grosor=0.045)
        pop(objs, fr(t["t0"]) + 2, fr(t["t1"]))

    for av in plan["avisos"]:
        raiz = enlazar(bpy.data.objects.new("aviso", None))
        raiz.parent = cam
        raiz.location = (0, y_de(conf.get("aviso_altura", 0.235)), -1)
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


MARGEN_X = 0.05            # margen lateral (fracción del ancho)
ZONA_Y = (0.30, 0.86)      # franja vertical segura (0 = abajo, 1 = arriba)


def _en_pantalla(cam, punto, lente):
    """Posición en pantalla (0..1, 0..1) y tamaño visible (ancho, alto) a esa distancia."""
    from bpy_extras.object_utils import world_to_camera_view
    s = bpy.context.scene
    nx, ny, z = world_to_camera_view(s, cam, Vector(punto))
    alto_v = max(0.01, z) * 36.0 / lente
    return nx, ny, alto_v * s.render.resolution_x / s.render.resolution_y, alto_v, z


def _ajuste(valores, minimo, maximo):
    """Desplazamiento que mete en [minimo, maximo] lo mejor posible todos los valores."""
    falta = max(0.0, max(minimo - v for v in valores))    # hay que subir al menos esto
    sobra = max(0.0, max(v - maximo for v in valores))    # hay que bajar al menos esto
    return (falta - sobra) if not (falta and sobra) else (falta - sobra) / 2


def etiquetas_3d(cam, plan, lente):
    """Etiquetas con flecha. Se recolocan solas para no salirse de la pantalla."""
    azul = material_luz("etiqueta", (0.03, 0.22, 0.85))
    s = bpy.context.scene
    avisos = []
    for et in plan["etiquetas"]:
        tam = et["tam"]
        alto = et["alto"] if et["alto"] is not None else tam * 3.4
        destino = Vector(et["pos"])
        f0, f1 = fr(et["t0"]), max(fr(et["t0"]) + 8, fr(et["t1"]))
        raiz = enlazar(bpy.data.objects.new("etiqueta", None))
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
        medio_ancho = (txt.dimensions.x + tam * 0.9) / 2
        medio_alto = tam * 0.8

        # --- Encajar en pantalla: se mira dónde cae durante todo el rato que se ve ---
        pos = destino + Vector((0, 0, alto))
        escala = 1.0
        for _ in range(3):
            xs, ys, datos = [], [], []
            for f in sorted({f0 + 6, (f0 + f1) // 2, f1 - 2}):
                s.frame_set(f)
                bpy.context.view_layer.update()
                nx, ny, ancho_v, alto_v, z = _en_pantalla(cam, pos, lente)
                xs.append(nx)
                ys.append(ny)
                datos.append((ancho_v, alto_v, cam.matrix_world.copy()))
            ancho_v = sum(d[0] for d in datos) / len(datos)
            alto_v = sum(d[1] for d in datos) / len(datos)
            mw = datos[len(datos) // 2][2]
            escala = min(escala, (1 - 2 * MARGEN_X) * 0.98 * ancho_v / (2 * medio_ancho * escala) * escala)
            hw, hh = medio_ancho * escala / ancho_v, medio_alto * escala / alto_v
            dx = _ajuste(xs, MARGEN_X + hw, 1 - MARGEN_X - hw)
            dy = _ajuste(ys, ZONA_Y[0] + hh, ZONA_Y[1] - hh)
            if abs(dx) < 0.004 and abs(dy) < 0.004:
                break
            derecha, arriba = mw.col[0].xyz.normalized(), mw.col[1].xyz.normalized()
            pos = pos + derecha * (dx * ancho_v) + arriba * (dy * alto_v)
        fuera = [f for f, x, y in zip((f0 + 6, (f0 + f1) // 2, f1 - 2), xs, ys)
                 if not (hw <= x + 0.02 and x - 0.02 <= 1 - hw and 0.2 <= y <= 0.93)]
        if fuera:
            avisos.append(f"la etiqueta «{et['texto']}» no cabe del todo en pantalla "
                          f"(segundos {et['t0']:.1f}-{et['t1']:.1f}): acerca la cámara a ese punto "
                          "o acorta el rato que se muestra")
        s.frame_set((f0 + f1) // 2)
        bpy.context.view_layer.update()
        nx, ny, _, _, z = _en_pantalla(cam, destino, lente)
        if not (0.03 <= nx <= 0.97 and 0.1 <= ny <= 0.95 and z > 0):
            avisos.append(f"la etiqueta «{et['texto']}» señala un punto que la cámara no ve")

        raiz.location = pos
        partes = [txt]

        def parte(tipo, dim, padre, loc, quat=None):
            m = malla_base(tipo).copy()
            for v in m.vertices:
                v.co = Vector((v.co.x * dim[0], v.co.y * dim[1], v.co.z * dim[2]))
            m.materials.append(azul)
            o = enlazar(bpy.data.objects.new("etiqueta_p", m))
            o.parent = padre
            o.location = loc
            if quat is not None:
                o.rotation_mode = "QUATERNION"
                o.rotation_quaternion = quat
            partes.append(o)
            return o

        parte("cubo", (medio_ancho * 2, medio_alto * 2, tam * 0.05), cara, (0, 0, 0))
        # Flecha: de debajo del cartel hasta el punto señalado (puede ir inclinada)
        t = tam * escala
        hacia = destino - pos
        largo_total = hacia.length
        direccion = hacia.normalized()
        giro = direccion.to_track_quat("Z", "Y")
        ini, punta = medio_alto * escala * 1.05, t * 0.8
        largo = max(0.05, largo_total - ini - punta - t * 0.15)
        flecha = [parte("cilindro", (t * 0.2, t * 0.2, largo), None, pos + direccion * (ini + largo / 2), giro),
                  parte("cono", (t * 0.7, t * 0.7, punta), None,
                        pos + direccion * (ini + largo + punta / 2), giro)]
        for o in partes:
            sin_sombra(o)
            visible_entre(o, f0, f1)
        for o, fin in [(raiz, escala)] + [(o, 1.0) for o in flecha]:
            o.scale = (0.001,) * 3
            clave(o, "scale", f0, "atras")
            o.scale = (fin,) * 3
            clave(o, "scale", f0 + 6)
    s.frame_set(1)
    return avisos


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


# --- Estilos visuales -----------------------------------------------------------------

RUTA_ESTILOS = os.path.join(os.path.dirname(AQUI), "canal", "estilos.json")


def cargar_estilos():
    if os.path.exists(RUTA_ESTILOS):
        with open(RUTA_ESTILOS, encoding="utf-8") as f:
            return json.load(f).get("estilos", {})
    return {"maqueta": {}}


SIN_CONTORNO = ("txt", "aviso", "etiqueta", "confeti", "polvo")


def _bsdf(m):
    if not m or not m.node_tree or m.name.startswith("luz_"):
        return None
    return next((n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)


def _entrada(nodo, *nombres):
    for n in nombres:
        if n in nodo.inputs:
            return nodo.inputs[n]
    return None


def contorno(color, grosor_1080):
    s = bpy.context.scene
    s.render.use_freestyle = True
    s.render.line_thickness_mode = "ABSOLUTE"
    grosor = grosor_1080 * s.render.resolution_x / 1080
    capa = bpy.context.view_layer
    capa.use_freestyle = True
    ajustes = capa.freestyle_settings
    linea = ajustes.linesets[0] if len(ajustes.linesets) else ajustes.linesets.new("contorno")
    linea.select_by_visibility = True
    linea.select_by_edge_types = True
    linea.select_silhouette = True
    linea.select_border = True
    linea.select_crease = True
    sin = bpy.data.collections.new("sin_contorno")
    s.collection.children.link(sin)
    for o in s.objects:
        if o.name.startswith(SIN_CONTORNO):
            sin.objects.link(o)
    linea.select_by_collection = True
    linea.collection = sin
    linea.collection_negation = "EXCLUSIVE"
    if linea.linestyle is None:
        linea.linestyle = bpy.data.linestyles.new("contorno")
    linea.linestyle.color = color
    linea.linestyle.thickness = grosor


def niebla(conf):
    """Niebla según la distancia a la cámara (pase de niebla + composición)."""
    s = bpy.context.scene
    bpy.context.view_layer.use_pass_mist = True
    s.world.mist_settings.start = conf.get("inicio", 4)
    s.world.mist_settings.depth = conf.get("distancia", 40)
    color = (*conf.get("color", (0.05, 0.07, 0.12)), 1)
    fuerza = conf.get("fuerza", 0.85)
    if hasattr(s, "compositing_node_group"):          # Blender 5
        arbol = bpy.data.node_groups.new("niebla", "CompositorNodeTree")
        arbol.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
        s.compositing_node_group = arbol
        capas = arbol.nodes.new("CompositorNodeRLayers")
        mult = arbol.nodes.new("ShaderNodeMath")
        mezcla = arbol.nodes.new("ShaderNodeMix")
        mezcla.data_type = "RGBA"
        salida = arbol.nodes.new("NodeGroupOutput")
        ent_f, ent_a, ent_b, sal = mezcla.inputs["Factor"], mezcla.inputs["A"], mezcla.inputs["B"], mezcla.outputs["Result"]
    else:                                              # Blender 4
        s.use_nodes = True
        arbol = s.node_tree
        for n in list(arbol.nodes):
            arbol.nodes.remove(n)
        capas = arbol.nodes.new("CompositorNodeRLayers")
        mult = arbol.nodes.new("CompositorNodeMath")
        mezcla = arbol.nodes.new("CompositorNodeMixRGB")
        salida = arbol.nodes.new("CompositorNodeComposite")
        ent_f, ent_a, ent_b, sal = mezcla.inputs[0], mezcla.inputs[1], mezcla.inputs[2], mezcla.outputs[0]
    try:
        s.render.compositor_device = "CPU"
    except (AttributeError, TypeError):
        pass
    mult.operation = "MULTIPLY"
    mult.inputs[1].default_value = fuerza
    arbol.links.new(capas.outputs["Mist"], mult.inputs[0])
    arbol.links.new(mult.outputs[0], ent_f)
    arbol.links.new(capas.outputs["Image"], ent_a)
    ent_b.default_value = color
    arbol.links.new(sal, salida.inputs[0])


def aplicar_estilo(nombre):
    """Aplica un estilo de canal/estilos.json. Ajustes posibles (todos opcionales):

    materiales: rugosidad, brillo, mezcla {color, cantidad} (tiñe todos los colores),
                color_fijo (todo de un color), color_agua
    contorno:   color, grosor (líneas tipo cómic; grosor en píxeles a 1080 de ancho)
    cielo:      color, fuerza
    sol:        energia, angulo (grados; más = sombras más suaves), color
    """
    estilos = cargar_estilos()
    if not nombre or nombre not in estilos:
        if nombre and nombre != "maqueta":
            print(f"[creador] AVISO: estilo «{nombre}» no existe; uso maqueta. Hay: {', '.join(estilos)}")
        return
    e = estilos[nombre]
    s = bpy.context.scene
    sol = bpy.data.objects.get("sol")
    fondo = s.world.node_tree.nodes["Background"]
    mat = e.get("materiales", {})
    for m in bpy.data.materials:
        b = _bsdf(m)
        if not b:
            continue
        rug = _entrada(b, "Roughness")
        brillo = _entrada(b, "Specular IOR Level", "Specular")
        color = _entrada(b, "Base Color")
        if "rugosidad" in mat and rug:
            rug.default_value = mat["rugosidad"]
        if "brillo" in mat and brillo:
            brillo.default_value = mat["brillo"]
        if "color_fijo" in mat and color:
            for enlace in list(color.links):
                m.node_tree.links.remove(enlace)
            fijo = mat.get("color_agua", mat["color_fijo"]) if m.name == "agua" else mat["color_fijo"]
            color.default_value = (*fijo, 1)
        elif "mezcla" in mat and color and not color.is_linked:
            c, t, k = color.default_value, mat["mezcla"]["color"], mat["mezcla"]["cantidad"]
            color.default_value = tuple(c[i] * (1 - k) + t[i] * k for i in range(3)) + (1,)
    if "contorno" in e:
        contorno(tuple(e["contorno"].get("color", (0, 0, 0))), e["contorno"].get("grosor", 3.0))
    cielo = e.get("cielo", {})
    if "color" in cielo:
        fondo.inputs["Color"].default_value = (*cielo["color"], 1)
    if "fuerza" in cielo:
        fondo.inputs["Strength"].default_value = cielo["fuerza"]
    if "niebla" in e:
        niebla(e["niebla"])
    luz = e.get("sol", {})
    if sol:
        if "energia" in luz:
            sol.data.energy = luz["energia"]
        if "angulo" in luz:
            sol.data.angle = math.radians(luz["angulo"])
        if "color" in luz:
            sol.data.color = tuple(luz["color"])
    print(f"[creador] Estilo: {nombre}")


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
    textos_en_camara(cam, plan, lente, cargar_estilos().get(a.estilo, {}))
    for aviso in etiquetas_3d(cam, plan, lente):
        print("[creador] AVISO:", aviso)
    if plan["confeti"]:
        confeti(plan["confeti"])

    aplicar_estilo(a.estilo)

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
