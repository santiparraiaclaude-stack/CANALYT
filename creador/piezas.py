"""Piezas básicas para describir una escena 3D.

Python puro (no importa Blender): las estructuras se pueden escribir y
revisar sin abrir Blender.

Cada pieza es un diccionario:
    tipo   : "cubo" | "cilindro" | "esfera" | "cono" | "modelo" (ver modelo())
    pos    : centro de la pieza (x, y, z)
    dim    : tamaño total (ancho_x, fondo_y, alto_z)
    rot    : rotación en grados (x, y, z)
    color  : nombre de un color de COLORES
    anim   : cómo entra en escena:
               "caer"     -> cae desde arriba girando y rebota
               "crecer"   -> crece desde su base (torres, columnas, tirantes)
               "subir"    -> sube desde abajo (piezas que se izan)
               "aparecer" -> aparece con un "pop" (cables, detalles)
               "ninguna"  -> está desde el inicio (escenario)
    id     : (opcional) nombre de grupo, para moverla después con acciones
    pivote : (opcional) punto alrededor del que gira su grupo
    t      : (opcional) momento de entrada dentro de la escena, de 0 a 1
"""
import math

# Paleta del canal: colores vivos que se leen bien en el móvil.
COLORES = {
    "naranja":     (0.90, 0.22, 0.04),
    "naranja_osc": (0.60, 0.13, 0.03),
    "concreto":    (0.70, 0.68, 0.63),
    "asfalto":     (0.07, 0.07, 0.08),
    "amarillo":    (1.00, 0.72, 0.03),
    "blanco":      (0.95, 0.95, 0.95),
    "agua":        (0.02, 0.30, 0.55),
    "pasto":       (0.25, 0.55, 0.12),
    "pasto_osc":   (0.13, 0.38, 0.10),
    "roca":        (0.42, 0.34, 0.25),
    "acero":       (0.50, 0.53, 0.57),
    "rojo":        (0.85, 0.06, 0.05),
    "azul":        (0.05, 0.25, 0.80),
    "azul_osc":    (0.04, 0.10, 0.28),
    "verde":       (0.08, 0.55, 0.22),
    "rosa":        (0.95, 0.30, 0.50),
    "morado":      (0.40, 0.20, 0.75),
    "turquesa":    (0.05, 0.60, 0.60),
    "vidrio":      (0.35, 0.60, 0.80),
    "dorado":      (0.90, 0.65, 0.15),
    "arena":       (0.85, 0.72, 0.48),
    "madera":      (0.45, 0.27, 0.12),
    "negro":       (0.02, 0.02, 0.02),
    "piel":        (0.90, 0.62, 0.45),
}

COLORES_AUTO = ["rojo", "azul", "blanco", "verde", "amarillo", "rosa",
                "turquesa", "morado", "naranja", "negro"]


def _pieza(tipo, pos, dim, color, anim, rot, extra):
    p = {"tipo": tipo, "pos": list(pos), "dim": list(dim), "rot": list(rot),
         "color": color, "anim": anim}
    p.update({k: v for k, v in extra.items() if v is not None})
    return p


def cubo(pos, dim, color="concreto", anim="caer", rot=(0, 0, 0), **extra):
    return _pieza("cubo", pos, dim, color, anim, rot, extra)


def cilindro(pos, radio, alto, color="acero", anim="crecer", rot=(0, 0, 0), **extra):
    return _pieza("cilindro", pos, (radio * 2, radio * 2, alto), color, anim, rot, extra)


def esfera(pos, dim, color="blanco", anim="aparecer", rot=(0, 0, 0), **extra):
    if isinstance(dim, (int, float)):
        dim = (dim, dim, dim)
    return _pieza("esfera", pos, dim, color, anim, rot, extra)


def cono(pos, radio, alto, color="rojo", anim="aparecer", rot=(0, 0, 0), **extra):
    return _pieza("cono", pos, (radio * 2, radio * 2, alto), color, anim, rot, extra)


def segmento(p1, p2, radio=0.1, color="acero", anim="aparecer", tipo="cilindro", **extra):
    """Pieza recta de p1 a p2 (cables, vigas inclinadas, tirantes).

    Con anim="crecer", crece desde p1 hacia p2.
    """
    dx, dy, dz = (p2[i] - p1[i] for i in range(3))
    largo = math.sqrt(dx * dx + dy * dy + dz * dz)
    centro = [(p1[i] + p2[i]) / 2 for i in range(3)]
    ux, uy, uz = dx / largo, dy / largo, dz / largo
    # Rotación Euler XYZ que lleva el eje Z local a la dirección (ux, uy, uz)
    rx = -math.degrees(math.asin(max(-1.0, min(1.0, uy))))
    ry = math.degrees(math.atan2(ux, uz))
    return _pieza(tipo, centro, (radio * 2, radio * 2, largo), color, anim, (rx, ry, 0), extra)


def parabola(x0, z0, x1, z1, z_min=None, n=12):
    """Puntos (x, z) de una curva tipo cable colgante entre dos apoyos."""
    pts = []
    for i in range(n + 1):
        t = i / n
        x = x0 + (x1 - x0) * t
        recta = z0 + (z1 - z0) * t
        if z_min is not None:
            flecha = (z0 + z1) / 2 - z_min
        else:
            flecha = abs(z1 - z0) * 0.12
        pts.append((x, recta - 4 * flecha * t * (1 - t)))
    return pts


def cadena(puntos3d, radio=0.1, color="acero", anim="aparecer", **extra):
    """Une una lista de puntos con segmentos (un cable hecho de tramos)."""
    return [segmento(puntos3d[i], puntos3d[i + 1], radio, color, anim, **extra)
            for i in range(len(puntos3d) - 1)]


def grupo(nombre, piezas, pivote=None):
    """Marca piezas como un grupo que luego se puede mover, girar o quitar."""
    for p in piezas:
        p["id"] = nombre
        if pivote is not None:
            p["pivote"] = list(pivote)
    return piezas


def con(piezas, **campos):
    """Pone los mismos campos (anim, t, color...) a varias piezas."""
    for p in piezas:
        p.update(campos)
    return piezas


def modelo(id_modelo, pos, largo=None, alto=None, escala=1.0, rumbo=0, anim="caer", **extra):
    """Un modelo 3D descargado (ver `python3 creador/banco_modelos.py --lista`).

    pos   : punto del suelo bajo el modelo (centro de su base)
    largo : tamaño de su lado más largo en la escena (o alto: su altura); si no, escala
    rumbo : giro en grados alrededor del eje vertical
    """
    p = {"tipo": "modelo", "modelo": id_modelo, "pos": list(pos), "dim": [0, 0, 0],
         "rot": [0, 0, rumbo], "color": None, "anim": anim, "escala": escala}
    if largo:
        p["largo"] = largo
    if alto:
        p["alto"] = alto
    p.update({k: v for k, v in extra.items() if v is not None})
    return p


# --- Objetos prefabricados ---------------------------------------------------

def auto(pos, color="rojo", rumbo=0, anim="aparecer", escala=1.0, **extra):
    """Auto low-poly. pos = punto del suelo bajo el auto. rumbo en grados (0 = +X)."""
    x, y, z = pos
    e = escala
    r = (0, 0, rumbo)
    return [
        cubo((x, y, z + 0.22 * e), (1.15 * e, 0.6 * e, 0.3 * e), color, anim, r, **extra),
        _girado(cubo((x - 0.08 * e, y, z + 0.5 * e), (0.6 * e, 0.52 * e, 0.28 * e),
                     "azul_osc", anim, r, **extra), (x, y), rumbo),
    ]


def camion(pos, color="blanco", rumbo=0, anim="aparecer", escala=1.0, **extra):
    x, y, z = pos
    e = escala
    r = (0, 0, rumbo)
    return [
        _girado(cubo((x - 0.35 * e, y, z + 0.55 * e), (1.7 * e, 0.7 * e, 0.9 * e),
                     color, anim, r, **extra), (x, y), rumbo),
        _girado(cubo((x + 0.85 * e, y, z + 0.4 * e), (0.6 * e, 0.66 * e, 0.6 * e),
                     "rojo", anim, r, **extra), (x, y), rumbo),
    ]


def barco(pos, rumbo=0, anim="aparecer", escala=1.0, color="rojo", **extra):
    """Barco de carga. pos = punto sobre el agua."""
    x, y, z = pos
    e = escala
    r = (0, 0, rumbo)
    piezas = [
        cubo((x, y, z + 0.45 * e), (5.0 * e, 1.6 * e, 0.9 * e), color, anim, r, **extra),
        cubo((x - 1.6 * e, y, z + 1.4 * e), (1.0 * e, 1.2 * e, 1.0 * e), "blanco", anim, r, **extra),
        cubo((x + 0.6 * e, y, z + 1.15 * e), (2.4 * e, 1.2 * e, 0.5 * e), "amarillo", anim, r, **extra),
        cubo((x + 0.6 * e, y, z + 1.6 * e), (1.6 * e, 1.2 * e, 0.4 * e), "azul", anim, r, **extra),
    ]
    return [_girado(p, (x, y), rumbo) for p in piezas]


def nube(pos, escala=1.0, **extra):
    x, y, z = pos
    e = escala
    return [
        esfera((x, y, z), (5 * e, 3 * e, 1.6 * e), "blanco", "ninguna", **extra),
        esfera((x + 2.2 * e, y + 0.4 * e, z - 0.2 * e), (3.5 * e, 2.4 * e, 1.2 * e), "blanco", "ninguna", **extra),
        esfera((x - 2.0 * e, y - 0.3 * e, z - 0.25 * e), (3.2 * e, 2.2 * e, 1.1 * e), "blanco", "ninguna", **extra),
    ]


def arbol(pos, escala=1.0, anim="ninguna", **extra):
    x, y, z = pos
    e = escala
    return [
        cilindro((x, y, z + 0.4 * e), 0.12 * e, 0.8 * e, "madera", anim, **extra),
        esfera((x, y, z + 1.2 * e), (1.1 * e, 1.1 * e, 1.2 * e), "pasto_osc", anim, **extra),
    ]


def equis(pos, tam=1.5, anim="aparecer", **extra):
    """Una X roja para marcar que algo salió mal."""
    return [
        cubo(pos, (tam, tam * 0.2, tam * 0.2), "rojo", anim, (0, 45, 0), **extra),
        cubo(pos, (tam, tam * 0.2, tam * 0.2), "rojo", anim, (0, -45, 0), **extra),
    ]


def _girado(p, centro_xy, rumbo):
    """Gira la posición de una pieza alrededor de un centro (para prefabricados)."""
    if not rumbo:
        return p
    a = math.radians(rumbo)
    dx, dy = p["pos"][0] - centro_xy[0], p["pos"][1] - centro_xy[1]
    p["pos"][0] = centro_xy[0] + dx * math.cos(a) - dy * math.sin(a)
    p["pos"][1] = centro_xy[1] + dx * math.sin(a) + dy * math.cos(a)
    return p


def reflejar_x(piezas):
    """Copia piezas reflejadas en el eje X (para estructuras simétricas)."""
    out = []
    for p in piezas:
        q = dict(p)
        q["pos"] = [-p["pos"][0], p["pos"][1], p["pos"][2]]
        q["rot"] = [p["rot"][0], -p["rot"][1], -p["rot"][2]]
        if "pivote" in p:
            q["pivote"] = [-p["pivote"][0], p["pivote"][1], p["pivote"][2]]
        out.append(q)
    return out
