"""Piezas básicas para describir una construcción paso a paso.

Este módulo es Python puro (no importa Blender), así que las estructuras
se pueden escribir y probar sin abrir Blender.

Cada pieza es un diccionario:
    tipo   : "cubo" | "cilindro"
    pos    : centro de la pieza (x, y, z) en metros de escena
    dim    : tamaño total (ancho_x, fondo_y, alto_z)
    rot    : rotación en grados (x, y, z)
    color  : nombre de un color de COLORES
    anim   : cómo entra en escena:
               "caer"     -> cae desde arriba y rebota
               "crecer"   -> crece desde su base (ideal para torres, columnas)
               "aparecer" -> aparece con un "pop" (ideal para cables, detalles)
               "ninguna"  -> está desde el inicio (escenario)
"""
import math

# Paleta del canal: colores saturados que se leen bien en el móvil.
COLORES = {
    "naranja":   (0.85, 0.20, 0.05),   # "International Orange" del Golden Gate
    "naranja_osc": (0.55, 0.12, 0.03),
    "concreto":  (0.62, 0.60, 0.56),
    "asfalto":   (0.08, 0.08, 0.09),
    "amarillo":  (0.95, 0.75, 0.05),
    "blanco":    (0.92, 0.92, 0.92),
    "agua":      (0.03, 0.22, 0.38),
    "pasto":     (0.18, 0.42, 0.12),
    "roca":      (0.35, 0.28, 0.20),
    "acero":     (0.45, 0.47, 0.50),
    "rojo":      (0.75, 0.05, 0.05),
    "azul":      (0.05, 0.25, 0.75),
    "verde":     (0.10, 0.55, 0.20),
    "vidrio":    (0.35, 0.55, 0.70),
    "dorado":    (0.85, 0.62, 0.15),
    "arena":     (0.80, 0.68, 0.45),
}


def cubo(pos, dim, color="concreto", anim="caer", rot=(0, 0, 0)):
    return {"tipo": "cubo", "pos": list(pos), "dim": list(dim),
            "rot": list(rot), "color": color, "anim": anim}


def cilindro(pos, radio, alto, color="acero", anim="crecer", rot=(0, 0, 0)):
    return {"tipo": "cilindro", "pos": list(pos), "dim": [radio * 2, radio * 2, alto],
            "rot": list(rot), "color": color, "anim": anim}


def segmento(p1, p2, radio=0.1, color="acero", anim="aparecer", tipo="cilindro"):
    """Pieza recta que une p1 con p2 (cables, vigas inclinadas, tirantes)."""
    dx, dy, dz = (p2[i] - p1[i] for i in range(3))
    largo = math.sqrt(dx * dx + dy * dy + dz * dz)
    centro = [(p1[i] + p2[i]) / 2 for i in range(3)]
    ux, uy, uz = dx / largo, dy / largo, dz / largo
    # Rotación Euler XYZ que lleva el eje Z local a la dirección (ux, uy, uz)
    rx = -math.degrees(math.asin(max(-1.0, min(1.0, uy))))
    ry = math.degrees(math.atan2(ux, uz))
    dim = [radio * 2, radio * 2, largo]
    return {"tipo": tipo, "pos": centro, "dim": dim, "rot": [rx, ry, 0],
            "color": color, "anim": anim}


def parabola(x0, z0, x1, z1, z_min=None, n=12):
    """Puntos (x, z) de una curva tipo cable colgante entre dos apoyos.

    Si se da z_min, la curva baja hasta esa altura en el punto medio
    (vano central de un puente colgante). Si no, es una curva suave
    entre ambos extremos (vanos laterales).
    """
    pts = []
    for i in range(n + 1):
        t = i / n
        x = x0 + (x1 - x0) * t
        recta = z0 + (z1 - z0) * t
        if z_min is not None:
            medio = (z0 + z1) / 2
            flecha = medio - z_min
            z = recta - 4 * flecha * t * (1 - t)
        else:
            flecha = abs(z1 - z0) * 0.12
            z = recta - 4 * flecha * t * (1 - t)
        pts.append((x, z))
    return pts


def cadena(puntos3d, radio=0.1, color="acero", anim="aparecer"):
    """Une una lista de puntos con segmentos (un cable hecho de tramos)."""
    return [segmento(puntos3d[i], puntos3d[i + 1], radio, color, anim)
            for i in range(len(puntos3d) - 1)]


def reflejar_x(piezas):
    """Copia piezas reflejadas en el eje X (para estructuras simétricas)."""
    out = []
    for p in piezas:
        q = dict(p)
        q["pos"] = [-p["pos"][0], p["pos"][1], p["pos"][2]]
        q["rot"] = [p["rot"][0], -p["rot"][1], -p["rot"][2]]
        out.append(q)
    return out
