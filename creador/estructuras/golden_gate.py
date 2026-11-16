"""Construye el Golden Gate (San Francisco, 1937).

Escala aproximada: 1 unidad de escena ~ 30 m reales. No es un plano de
ingeniería: es una maqueta estilizada que se lee bien en un vertical 9:16.
"""
from piezas import cubo, cilindro, segmento, parabola, cadena

TITULO = {"es": "CONSTRUYE EL GOLDEN GATE", "en": "BUILD THE GOLDEN GATE"}

# Gancho (primeros segundos): solo se ve el escenario vacío.
GANCHO = {
    "es": "Hoy vas a construir el puente más famoso del mundo.",
    "en": "Today you're building the most famous bridge in the world.",
}

FINAL = {
    "es": "¡Bien! Has construido el Golden Gate. ¿Qué construimos mañana?",
    "en": "Nice! You just built the Golden Gate. What should we build next?",
}

CAMARA = {
    "centro": (-1, 0, 9),      # punto al que mira la cámara
    "distancia": 38,           # radio de la órbita
    "altura": 9,               # altura sobre el centro
    "angulo_inicio": 228,      # grados (0 = mirando desde +X)
    "angulo_fin": 246,
    "lente": 24,               # mm (menor = más gran angular)
}

# --- Medidas de la maqueta -------------------------------------------------
TORRE_X = 10          # torres en x = ±10
TABLERO_Z = 6         # altura de la calzada sobre el agua
TORRE_TOPE = 20
CABLE_Y = 1.7         # separación de los cables (a cada lado)
ANCLA_X = 23
ORILLA_X = 21


def _cable_pts(y):
    """Puntos 3D de un cable principal completo (lateral, central, lateral)."""
    pts = []
    pts += parabola(-ANCLA_X, TABLERO_Z + 1, -TORRE_X, TORRE_TOPE - 0.3, n=6)
    pts += parabola(-TORRE_X, TORRE_TOPE - 0.3, TORRE_X, TORRE_TOPE - 0.3,
                    z_min=TABLERO_Z + 1.2, n=16)[1:]
    pts += parabola(TORRE_X, TORRE_TOPE - 0.3, ANCLA_X, TABLERO_Z + 1, n=6)[1:]
    return [(x, y, z) for x, z in pts]


def _altura_cable(x):
    """Altura del cable principal sobre una x dada (para los tirantes)."""
    pts = _cable_pts(0)
    for (x0, _, z0), (x1, _, z1) in zip(pts, pts[1:]):
        if x0 <= x <= x1:
            t = (x - x0) / (x1 - x0)
            return z0 + (z1 - z0) * t
    return TABLERO_Z


# --- Escenario (visible desde el principio) ---------------------------------
ESCENARIO = [
    cubo((0, 0, -0.5), (140, 140, 1), "agua", "ninguna"),
    # Acantilados de cada orilla
    cubo((-34, 0, 2.6), (26, 40, 6.2), "roca", "ninguna"),
    cubo((34, 0, 2.6), (26, 40, 6.2), "roca", "ninguna"),
    cubo((-34, 0, 5.85), (26, 40, 0.3), "pasto", "ninguna"),
    cubo((34, 0, 5.85), (26, 40, 0.3), "pasto", "ninguna"),
]


def _paso_cimientos():
    p = []
    for x in (-TORRE_X, TORRE_X):
        p.append(cubo((x, 0, 0.4), (3.2, 6.0, 1.6), "concreto", "crecer"))
    for x in (-ANCLA_X, ANCLA_X):
        p.append(cubo((x, 0, 6.6), (3.0, 5.0, 1.6), "concreto", "caer"))
    return p


def _paso_torres():
    p = []
    for x in (-TORRE_X, TORRE_X):
        base = 1.2
        alto = TORRE_TOPE - base
        for y in (-CABLE_Y, CABLE_Y):
            p.append(cubo((x, y, base + alto / 2), (1.0, 0.9, alto), "naranja", "crecer"))
        # Vigas horizontales entre las dos patas (más arriba = más tarde)
        for z in (TABLERO_Z - 1.2, 11.5, 15.5, TORRE_TOPE - 0.6):
            p.append(cubo((x, 0, z), (0.8, CABLE_Y * 2, 0.7), "naranja", "aparecer"))
    return p


def _paso_cables():
    p = []
    for y in (-CABLE_Y, CABLE_Y):
        p += cadena(_cable_pts(y), radio=0.16, color="naranja", anim="aparecer")
    return p


def _paso_tirantes():
    p = []
    x = -ANCLA_X + 2.0
    while x < ANCLA_X - 1.5:
        if abs(abs(x) - TORRE_X) > 0.8:
            z_top = _altura_cable(x)
            if z_top - TABLERO_Z > 0.6:
                for y in (-CABLE_Y, CABLE_Y):
                    p.append(segmento((x, y, TABLERO_Z + 0.25), (x, y, z_top),
                                      radio=0.05, color="naranja_osc", anim="crecer"))
        x += 1.25
    return p


def _tramos_tablero():
    xs = []
    x = -ORILLA_X
    while x < ORILLA_X:
        xs.append(x + 1.0)
        x += 2.0
    # Como en 1936: desde las torres hacia afuera, para equilibrar el peso
    xs.sort(key=lambda v: min(abs(v - TORRE_X), abs(v + TORRE_X)))
    return xs


def _paso_tablero():
    return [cubo((x, 0, TABLERO_Z), (2.02, CABLE_Y * 2 + 0.6, 0.55), "naranja", "caer")
            for x in _tramos_tablero()]


def _paso_calzada():
    p = []
    for x in sorted(_tramos_tablero()):
        p.append(cubo((x, 0, TABLERO_Z + 0.33), (2.02, CABLE_Y * 2 - 0.2, 0.12), "asfalto", "aparecer"))
    x = -ORILLA_X + 0.5
    while x < ORILLA_X:
        p.append(cubo((x, 0, TABLERO_Z + 0.41), (0.7, 0.08, 0.03), "amarillo", "aparecer"))
        x += 1.5
    # Autos
    autos = [(-15, -0.7, "rojo"), (-6, 0.7, "azul"), (3, -0.7, "blanco"),
             (12, 0.7, "verde"), (17, -0.7, "amarillo")]
    for x, y, c in autos:
        p.append(cubo((x, y, TABLERO_Z + 0.65), (1.1, 0.55, 0.4), c, "caer"))
    return p


# Cada paso = lo que se construye + lo que dice la voz durante ese paso.
PASOS = [
    {
        "es": "Primero, los cimientos: bloques de concreto en el mar y anclajes gigantes en cada orilla.",
        "en": "First, the foundations: concrete blocks in the sea and huge anchors on each shore.",
        "piezas": _paso_cimientos(),
    },
    {
        "es": "Ahora levanta las torres: 227 metros de acero, más altas que un edificio de 60 pisos.",
        "en": "Now raise the towers: 746 feet of steel, taller than a 60-story building.",
        "piezas": _paso_torres(),
    },
    {
        "es": "Pasa los cables principales. Cada uno tiene más de 27 mil alambres de acero.",
        "en": "String the main cables. Each one holds more than 27,000 steel wires.",
        "piezas": _paso_cables(),
    },
    {
        "es": "Cuelga los tirantes verticales: ellos van a sostener todo el peso.",
        "en": "Hang the vertical suspenders: they will carry all the weight.",
        "piezas": _paso_tirantes(),
    },
    {
        "es": "Coloca el tablero desde las torres hacia afuera, para que el peso quede equilibrado.",
        "en": "Place the deck from the towers outward, so the weight stays balanced.",
        "piezas": _paso_tablero(),
    },
    {
        "es": "Asfalto, líneas... y abre el paso a los autos.",
        "en": "Asphalt, road lines... and open it to traffic.",
        "piezas": _paso_calzada(),
    },
]
