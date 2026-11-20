"""Escenarios prefabricados con mucho detalle, listos para usar en una línea.

Cada kit devuelve (piezas, puntos):
  piezas : lista para sumar a ESCENARIO
  puntos : lugares útiles para la historia (dónde poner el celular, la casa de la
           familia, la escotilla...), para colocar cosas y apuntar la cámara.

Usan los modelos de Kenney del catálogo (python3 creador/banco_modelos.py --lista),
buscándolos por palabras clave. Si un modelo no está, ponen una forma básica en su
lugar, así que la escena funciona siempre. Escala: 1 unidad = 1 metro.

    from kits import calle, habitacion, sotano, horizonte
    piezas, p = habitacion((0, 0, 0))
    ESCENARIO = piezas + celular((*p["mesa_noche"][:2], p["mesa_noche"][2]), escala=0.1)
"""
import json
import math
import os
import random

from piezas import arbol, auto, cilindro, cubo, luz, modelo

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_CATALOGO = []


def catalogo():
    if not _CATALOGO:
        ruta = os.path.join(RAIZ, "modelos", "catalogo.json")
        if os.path.exists(ruta):
            with open(ruta, encoding="utf-8") as f:
                _CATALOGO.extend(m["id"] for m in json.load(f))
    return _CATALOGO


def buscar(palabras, packs=None, excluir=()):
    """Ids del catálogo que contienen alguna de las palabras (en orden de preferencia)."""
    out = []
    for palabra in palabras:
        for i in catalogo():
            pack, nombre = i.split("/", 1)
            if packs and not any(p in pack for p in packs):
                continue
            if palabra in nombre and not any(e in nombre for e in excluir) and i not in out:
                out.append(i)
    return out


def _uno(rnd, palabras, packs=None, excluir=()):
    """Un modelo al azar de la PRIMERA palabra que tenga alguno (las demás son de
    respaldo); primero en los packs preferidos y, si no hay, en cualquier pack (así
    sirven también KayKit, Quaternius u otros que descargues)."""
    for grupo in ((packs, None) if packs else (None,)):
        for palabra in palabras:
            ids = buscar([palabra], grupo, excluir)
            if ids:
                return rnd.choice(ids)
    return None


def _rotar(piezas, centro, rumbo):
    """Gira un grupo de piezas alrededor de un centro (en el plano)."""
    if not rumbo:
        return piezas
    a = math.radians(rumbo)
    cx, cy = centro[0], centro[1]
    for p in piezas:
        dx, dy = p["pos"][0] - cx, p["pos"][1] - cy
        p["pos"][0] = cx + dx * math.cos(a) - dy * math.sin(a)
        p["pos"][1] = cy + dx * math.sin(a) + dy * math.cos(a)
        p["rot"] = [p["rot"][0], p["rot"][1], p["rot"][2] + rumbo]
    return piezas


def _punto(local, centro, rumbo):
    a = math.radians(rumbo)
    dx, dy = local[0], local[1]
    return (centro[0] + dx * math.cos(a) - dy * math.sin(a),
            centro[1] + dx * math.sin(a) + dy * math.cos(a), centro[2] + local[2])


def _cil(base, radio, alto, color, **extra):
    """Cilindro apoyado por su BASE (cilindro() recibe el centro)."""
    return cilindro((base[0], base[1], base[2] + alto / 2), radio, alto, color, "ninguna", **extra)


def _mueble(rnd, palabras, pos, largo, color, caja, packs=("furniture",), rumbo=0, excluir=(), alto=None):
    """Un mueble del catálogo o, si no hay, una caja del tamaño indicado.
    Con alto= se escala por su altura (mesas: lo que va encima queda apoyado)."""
    m = _uno(rnd, palabras, packs, excluir)
    if m:
        if alto:
            return [modelo(m, pos, alto=alto, rumbo=rumbo, anim="ninguna")]
        return [modelo(m, pos, largo=largo, rumbo=rumbo, anim="ninguna")]
    return [cubo((pos[0], pos[1], pos[2] + caja[2] / 2), caja, color, "ninguna", (0, 0, rumbo))]


# --- Interiores ----------------------------------------------------------------------

def habitacion(centro=(0, 0, 0), ancho=4.5, fondo=4.2, alto=2.7, rumbo=0, pared="fachada",
               luz_lampara=True, luz_ventana=True, semilla=1):
    """Dormitorio amueblado: cama, mesa de noche con lámpara, armario, escritorio,
    alfombra, cuadro y una ventana con luz de luna. Abierto por el frente (-Y local)
    para que la cámara mire dentro."""
    rnd = random.Random(semilla)
    x0, y0, z0 = centro
    w, d, h = ancho, fondo, alto
    L = []
    L.append(cubo((x0, y0, z0 - 0.05), (w, d, 0.1), "madera", "ninguna"))
    L.append(cubo((x0, y0, z0 + h + 0.05), (w, d, 0.1), pared, "ninguna"))          # techo
    L.append(cubo((x0 - w / 2 - 0.05, y0, z0 + h / 2), (0.1, d, h), pared, "ninguna"))
    L.append(cubo((x0 + w / 2 + 0.05, y0, z0 + h / 2), (0.1, d, h), pared, "ninguna"))
    # pared del fondo con hueco de ventana
    yv, vw, vz0, vz1 = y0 + d / 2 + 0.05, 1.3, 1.0, 2.1
    L.append(cubo((x0 - (w + vw) / 4 - 0.15, yv, z0 + h / 2), ((w - vw) / 2 - 0.3, 0.1, h), pared, "ninguna"))
    L.append(cubo((x0 + (w + vw) / 4 - 0.15, yv, z0 + h / 2), ((w - vw) / 2 + 0.3, 0.1, h), pared, "ninguna"))
    L.append(cubo((x0 - 0.3, yv, z0 + vz0 / 2), (vw, 0.1, vz0), pared, "ninguna"))
    L.append(cubo((x0 - 0.3, yv, z0 + (vz1 + h) / 2), (vw, 0.1, h - vz1), pared, "ninguna"))
    L.append(cubo((x0 - 0.3, yv + 0.02, z0 + (vz0 + vz1) / 2), (vw, 0.04, vz1 - vz0), "vidrio",
                  "ninguna", brillo=0.35 if luz_ventana else 0.0))
    L.append(cubo((x0 - 0.3, yv - 0.06, z0 + (vz0 + vz1) / 2), (0.05, 0.04, vz1 - vz0), "madera", "ninguna"))
    if luz_ventana:
        L.append(luz((x0 - 0.3, yv + 1.5, z0 + 1.7), (0.55, 0.65, 1.0), 120, 1.0, "ninguna"))
    # muebles (posiciones locales respecto al centro)
    cama = (x0 - w / 2 + 1.1, y0 + d / 2 - 1.2, z0)
    mesa = (x0 - w / 2 + 2.35, y0 + d / 2 - 0.35, z0)
    L += _mueble(rnd, ["beddouble", "bedsingle", "bed"], cama, 2.1, "blanco", (1.5, 2.0, 0.55), rumbo=180,
                 excluir=("bunk",))
    # mesa de noche escalada por su ALTURA: así el tope es exacto y lo de encima no flota
    L += _mueble(rnd, ["sidetabledrawers", "sidetable", "nightstand", "cabinetbed"], mesa, 0.55, "madera",
                 (0.6, 0.35, 0.55), alto=0.55)
    tope = (mesa[0], mesa[1], z0 + 0.55)
    L += _mueble(rnd, ["lampsquaretable", "lamproundtable", "lamp"], (tope[0] + 0.2, tope[1] + 0.03, tope[2]),
                 0.2, "farol", (0.18, 0.18, 0.45), excluir=("floor", "wall", "ceiling"), alto=0.45)
    if luz_lampara:
        L.append(luz((tope[0] + 0.2, tope[1] + 0.03, tope[2] + 0.36), (1.0, 0.7, 0.4), 18, 0.15, "ninguna",
                     id="lampara"))
    L += _mueble(rnd, ["wardrobe", "closet", "bookcaseclosed", "bookcase"], (x0 + w / 2 - 0.4, y0 + 0.4, z0),
                 1.4, "madera", (0.6, 1.4, 2.0), rumbo=90)
    L += _mueble(rnd, ["desk", "table"], (x0 + w / 2 - 0.5, y0 - d / 2 + 1.1, z0), 1.3, "madera",
                 (0.7, 1.3, 0.75), rumbo=90, excluir=("side", "coffee", "lamp", "chair"), alto=0.75)
    L += _mueble(rnd, ["chairdesk", "chair"], (x0 + w / 2 - 1.1, y0 - d / 2 + 1.1, z0), 0.6, "negro",
                 (0.5, 0.5, 0.9), rumbo=90, excluir=("lounge",))
    L += _mueble(rnd, ["rugrectangle", "rug"], (x0 - 0.2, y0 - 0.2, z0 + 0.005), 2.2, "rojo",
                 (2.2, 1.5, 0.01))
    L.append(cubo((x0 + w / 2 - 0.02, y0 - 0.8, z0 + 1.6), (0.04, 0.7, 0.5), "dorado", "ninguna"))  # cuadro
    puntos = {"mesa_noche": tope, "cama": (cama[0], cama[1], z0 + 0.6),
              "ventana": (x0 - 0.3, yv, z0 + 1.55), "centro": (x0, y0, z0 + 1.2)}
    if rumbo:
        _rotar(L, centro, rumbo)
        puntos = {k: _punto((v[0] - x0, v[1] - y0, v[2] - z0), centro, rumbo) for k, v in puntos.items()}
    return L, puntos


def sotano(centro=(0, 0, -3), ancho=6.0, fondo=6.0, alto=2.4, escotilla=True, rumbo=0, semilla=2):
    """Sótano: paredes de concreto, escalera, estanterías con cajas, caldera con tubos,
    una bombilla colgando y (opcional) una escotilla en el suelo con luz roja."""
    rnd = random.Random(semilla)
    x0, y0, z0 = centro
    w, d, h = ancho, fondo, alto
    L = [cubo((x0, y0, z0 - 0.05), (w, d, 0.1), "acera", "ninguna"),
         cubo((x0, y0, z0 + h + 0.05), (w, d, 0.1), "acera", "ninguna"),
         cubo((x0 - w / 2 - 0.1, y0, z0 + h / 2), (0.2, d, h), "fachada", "ninguna"),
         cubo((x0 + w / 2 + 0.1, y0, z0 + h / 2), (0.2, d, h), "fachada", "ninguna"),
         cubo((x0, y0 + d / 2 + 0.1, z0 + h / 2), (w, 0.2, h), "fachada", "ninguna")]
    for k in range(10):                                       # escalera que sube
        L.append(cubo((x0 - w / 2 + 0.6, y0 - d / 2 + 0.3 + k * 0.28, z0 + 0.12 + k * 0.24),
                      (1.0, 0.3, 0.24), "madera", "ninguna"))
    for k, yy in enumerate((y0 + d / 2 - 0.35, y0 + 0.6)):    # estanterías con cajas
        xs = x0 + w / 2 - 0.35
        for nivel in range(4):
            L.append(cubo((xs, yy, z0 + 0.3 + nivel * 0.5), (0.6, 1.6, 0.05), "madera", "ninguna"))
            for j in range(rnd.randint(1, 3)):
                caja = _uno(rnd, ["cardboardboxclosed", "cardboardbox", "box"], ("furniture",))
                pos = (xs, yy - 0.5 + j * 0.5, z0 + 0.33 + nivel * 0.5)
                L += ([modelo(caja, pos, largo=0.4, rumbo=rnd.uniform(-15, 15), anim="ninguna")] if caja
                      else [cubo((pos[0], pos[1], pos[2] + 0.15), (0.4, 0.35, 0.3), "arena", "ninguna")])
        for px in (-0.28, 0.28):
            for py in (-0.78, 0.78):
                L.append(cubo((xs + px, yy + py, z0 + 1.0), (0.04, 0.04, 2.0), "acero", "ninguna"))
    cx, cy = x0 + 1.0, y0 + d / 2 - 0.8                       # caldera con tubos
    L.append(_cil((cx, cy, z0), 0.55, 1.7, "naranja_osc"))
    L.append(_cil((cx, cy, z0 + 1.7), 0.1, h - 1.7, "acero"))
    L.append(cubo((cx - 0.56, cy, z0 + 0.6), (0.05, 0.35, 0.25), "negro", "ninguna"))
    L.append(cubo((cx - 0.58, cy, z0 + 0.6), (0.02, 0.25, 0.12), "ventana_calida", "ninguna", brillo=3))
    for k in range(3):
        L.append(cubo((x0, y0 + d / 2 - 0.08, z0 + h - 0.25 - k * 0.18), (w, 0.08, 0.08), "acero", "ninguna"))
    L.append(_cil((x0, y0, z0 + h - 0.4), 0.01, 0.4, "negro"))                      # cable de la bombilla
    L.append(cubo((x0, y0, z0 + h - 0.45), (0.08, 0.08, 0.1), "farol", "ninguna", brillo=5))
    L.append(luz((x0, y0, z0 + h - 0.55), (1.0, 0.72, 0.42), 9, 0.1, "ninguna", id="bombilla"))
    puntos = {"caldera": (cx, cy, z0 + 0.9), "escalera": (x0 - w / 2 + 0.6, y0 - d / 2 + 1.2, z0 + 1.2),
              "centro": (x0, y0, z0 + 1.2)}
    if escotilla:                                             # escotilla entreabierta con luz roja
        ex, ey = cx - 1.4, cy - 0.3
        L.append(cubo((ex, ey, z0 + 0.01), (1.0, 1.0, 0.02), "negro", "ninguna"))
        L.append(cubo((ex, ey, z0 + 0.02), (0.9, 0.9, 0.01), "ventana_roja", "ninguna", brillo=2))
        L.append(cubo((ex + 0.35, ey, z0 + 0.42), (0.9, 0.08, 0.85), "acero", "ninguna", (0, -60, 0),
                      id="tapa", pivote=(ex - 0.1, ey, z0)))
        L.append(luz((ex, ey, z0 + 0.3), (1.0, 0.1, 0.05), 10, 0.3, "ninguna", id="luz_escotilla"))
        puntos["escotilla"] = (ex, ey, z0)
    if rumbo:
        _rotar(L, centro, rumbo)
        puntos = {k: _punto((v[0] - x0, v[1] - y0, v[2] - z0), centro, rumbo) for k, v in puntos.items()}
    return L, puntos


# --- Exteriores ------------------------------------------------------------------------

def calle(y0=0, largo=90, ancho_via=7.0, tipo="suburbana", casas_por_lado=7, autos=8,
          farolas=True, arboles=True, cercas=False, ventanas_encendidas=0.5, giro_casas=0,
          giro_autos=0, packs=None, semilla=3):
    """Calle completa a lo largo del eje Y: asfalto con líneas, aceras, casas (o edificios
    con tipo="comercial") a los dos lados, autos estacionados, árboles, cercas y farolas
    con luz. puntos["casas"] = posiciones de cada casa (para etiquetas como "TU FAMILIA").
    Si las casas salen de espaldas a la calle, prueba giro_casas=180; si los autos salen
    atravesados, giro_autos=90.
    packs: de qué paquetes sacar casas, autos y árboles, p. ej. ("kaykit", "city-builder")
    o ("downtown", "quaternius"). Sin indicarlo, prefiere Kenney y usa el resto si falta."""
    rnd = random.Random(semilla)
    L = [cubo((0, y0, -0.05), (ancho_via, largo, 0.1), "asfalto", "ninguna")]
    for lado in (-1, 1):
        L.append(cubo((lado * (ancho_via / 2 + 1), y0, 0.08), (2.0, largo, 0.16), "acera", "ninguna"))
        L.append(cubo((lado * (ancho_via / 2 + 13), y0, 0.0), (22, largo, 0.1), "pasto_osc", "ninguna"))
    k = -largo / 2 + 1
    while k < largo / 2:
        L.append(cubo((0, y0 + k, 0.005), (0.15, 1.5, 0.01), "amarillo", "ninguna"))
        k += 4
    palabras = (["building-type", "house", "home", "building"] if tipo == "suburbana"
                else ["building-skyscraper", "skyscraper", "building", "low-detail"])
    preferidos = tuple(packs) if packs else None
    packs = preferidos or (("suburban",) if tipo == "suburbana" else ("commercial",))
    paso = largo / casas_por_lado
    casas = []
    for lado in (-1, 1):
        for n in range(casas_por_lado):
            yy = y0 - largo / 2 + paso * (n + 0.5)
            x = lado * (ancho_via / 2 + 2 + (6 if tipo == "suburbana" else 7))
            m = _uno(rnd, palabras, packs)
            rumbo = (90 if lado < 0 else -90) + giro_casas
            if m:
                L.append(modelo(m, (x, yy, 0.1), largo=9 if tipo == "suburbana" else 12, rumbo=rumbo,
                                anim="ninguna"))
            else:
                alto = rnd.uniform(5, 7) if tipo == "suburbana" else rnd.uniform(12, 30)
                L.append(cubo((x, yy, alto / 2), (8, 8, alto), "fachada", "ninguna"))
                L.append(cubo((x, yy, alto + 1), (8.4, 8.4, 2), "ladrillo", "ninguna", (0, 0, 0)))
            casas.append((x, yy, 0))
            if rnd.random() < ventanas_encendidas:             # ventana encendida hacia la calle
                fx = x - lado * 4.05
                for vz in ((1.6,) if tipo == "suburbana" else (2, 5, 8, 11)):
                    L.append(cubo((fx, yy + rnd.uniform(-2, 2), vz), (0.05, 1.2, 1.1),
                                  rnd.choice(["ventana_calida", "ventana_calida", "ventana_roja"]), "ninguna",
                                  brillo=3.5))
                L.append(luz((fx - lado * 0.6, yy, 2.0), (1.0, 0.68, 0.4), 40, 0.5, "ninguna"))
            if cercas:
                cerca = _uno(rnd, ["fence-low", "fence"], ("suburban",))
                fx = lado * (ancho_via / 2 + 2.2)
                for j in (-1, 1):
                    if cerca:
                        L.append(modelo(cerca, (fx, yy + j * 2.8, 0.15), largo=2.2, rumbo=90, anim="ninguna"))
                    else:
                        L.append(cubo((fx, yy + j * 2.8, 0.55), (0.08, 2.2, 0.8), "blanco", "ninguna"))
            if arboles and rnd.random() < 0.7:
                t = _uno(rnd, ["tree"], preferidos or ("nature", "suburban"))
                pos = (lado * (ancho_via / 2 + 4.5), yy + paso / 2, 0.1)
                L += ([modelo(t, pos, alto=rnd.uniform(4, 6.5), rumbo=rnd.uniform(0, 360), anim="ninguna")]
                      if t else arbol(pos, rnd.uniform(1.6, 2.4)))
    if farolas:
        for yy in range(int(y0 - largo / 2 + 6), int(y0 + largo / 2), 16):
            for lado in (-1, 1):
                fx = lado * (ancho_via / 2 + 0.4)
                L.append(_cil((fx, yy, 0), 0.08, 4.6, "acero"))
                L.append(cubo((fx - lado * 0.4, yy, 4.6), (0.9, 0.25, 0.15), "farol", "ninguna", brillo=6))
                L.append(luz((fx - lado * 0.5, yy, 4.4), (1.0, 0.72, 0.42), 160, 0.3, "ninguna",
                             id=f"farola_{yy}_{lado}"))
    modelos_auto = (buscar(["sedan", "suv", "hatchback", "van", "taxi", "car"], preferidos,
                           excluir=("police", "wheel", "card", "carpet", "cart")) if preferidos else [])
    modelos_auto = modelos_auto or (buscar(["sedan", "suv", "hatchback", "van", "taxi"], ("car",),
                                           excluir=("police", "wheel"))
                    or buscar(["sedan", "suv", "hatchback", "taxi", "car"], None,
                              excluir=("police", "wheel", "card", "carpet", "cart")))
    for n in range(autos):
        lado = rnd.choice((-1, 1))
        # estacionados junto a la acera, en fila, sin pisarse
        pos = (lado * (ancho_via / 2 - 1.2), y0 - largo / 2 + 6 + (largo - 12) * (n + rnd.uniform(0.1, 0.6)) / autos,
               0)
        if modelos_auto:   # los modelos importados ya miran a lo largo de Y
            L.append(modelo(rnd.choice(modelos_auto), pos, largo=4.3,
                            rumbo=giro_autos + (0 if lado > 0 else 180), anim="ninguna"))
        else:
            L += auto(pos, rnd.choice(["rojo", "azul", "blanco", "negro"]), 90, "ninguna", escala=3.6)
    return L, {"casas": casas, "inicio": (0, y0 - largo / 2, 1.6), "fin": (0, y0 + largo / 2, 1.6)}


def horizonte(centro=(0, 0, 0), radio=85, n=40, alto=(18, 60), semilla=4):
    """Edificios altos en el horizonte, con cuadrícula de ventanas (algunas encendidas):
    llena el fondo para que nunca se vea vacío. No tapa nada cercano."""
    rnd = random.Random(semilla)
    L = []
    for k in range(n):
        a = 2 * math.pi * k / n + rnd.uniform(-0.03, 0.03)
        r = radio * rnd.uniform(0.9, 1.2)
        x, y = centro[0] + r * math.cos(a), centro[1] + r * math.sin(a)
        h = rnd.uniform(*alto)
        anchura = rnd.uniform(10, 18)
        giro = (0, 0, math.degrees(a))
        L.append(cubo((x, y, h / 2), (anchura, anchura, h), "fachada", "ninguna", giro))
        fx, fy = x - math.cos(a) * (anchura / 2 + 0.05), y - math.sin(a) * (anchura / 2 + 0.05)
        tx, ty = -math.sin(a), math.cos(a)                     # dirección a lo ancho de la fachada
        columnas = int(anchura // 3)
        for fila in range(int((h - 4) // 3.5)):
            for c in range(columnas):
                if rnd.random() > 0.28:
                    continue
                off = (c - (columnas - 1) / 2) * 3
                L.append(cubo((fx + tx * off, fy + ty * off, 3 + fila * 3.5), (0.15, 1.6, 1.8),
                              rnd.choice(["ventana_calida", "ventana_calida", "ventana_roja"]), "ninguna",
                              giro, brillo=2.2))
    return L, {}
