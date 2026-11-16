"""¿Cómo se hace un puente colgante? (el Golden Gate, San Francisco, 1937)

Historia de problema -> solución. Escala: 1 unidad ~ 30 m, estilizada para
que se lea en vertical. Datos comprobados: torres de 227 m, 600 000 remaches
por torre, 27 572 alambres por cable (casi 1 m de grosor), seis carriles.
"""
from piezas import (arbol, auto, barco, cadena, cilindro, con, cubo, equis,
                    esfera, grupo, nube, parabola, segmento, COLORES_AUTO)

TITULO = {"es": "¿CÓMO SE HACE UN\nPUENTE COLGANTE?", "en": "HOW DO YOU BUILD A\nSUSPENSION BRIDGE?"}
CAMARA = {"lente": 24}

ORILLA = 21        # el agua va de x = -21 a x = 21
Z = 5.8            # altura de la carretera
TX = 10            # torres en x = ±10
TOPE = 20          # altura de las torres
CY = 1.9           # los cables van en y = ±1.9
ANCLA = 24.5


def _cable_central(y):
    return [(x, y, z) for x, z in parabola(-TX, TOPE - 0.3, TX, TOPE - 0.3, z_min=Z + 1.6, n=16)]


def _cable_lateral(lado, y):
    pts = parabola(lado * ANCLA, Z + 2.0, lado * TX, TOPE - 0.3, n=6)
    return [(x, y, z) for x, z in pts]


def _altura_cable(x):
    for y in (CY,):
        pts = _cable_lateral(-1, y) + _cable_central(y)[1:] + _cable_lateral(1, y)[::-1][1:]
    for (x0, _, z0), (x1, _, z1) in zip(pts, pts[1:]):
        if x0 <= x <= x1:
            return z0 + (z1 - z0) * (x - x0) / (x1 - x0)
    return Z


# --- Escenario ---------------------------------------------------------------
def _escenario():
    p = [cubo((0, 0, -0.5), (170, 170, 1), "agua", "ninguna")]
    for lado in (-1, 1):
        p += [
            cubo((lado * 48, 0, 2.8), (54, 110, 5.6), "roca", "ninguna"),
            cubo((lado * 48, 0, 5.7), (54, 110, 0.25), "pasto", "ninguna"),
            cubo((lado * 48, 0, 5.86), (54, 3.8, 0.08), "asfalto", "ninguna"),
            esfera((lado * 50, 30, 6), (30, 26, 10), "pasto_osc", "ninguna"),
            esfera((lado * 58, -22, 6), (26, 22, 7), "pasto_osc", "ninguna"),
        ]
        x = ORILLA + 1.5
        while x < 70:
            p.append(cubo((lado * x, 0, 5.91), (0.8, 0.1, 0.02), "amarillo", "ninguna"))
            x += 1.8
        for ax, ay, e in ((26, 7, 1.3), (31, -9, 1.6), (37, 12, 1.2), (29, 16, 1.5),
                          (42, -14, 1.4), (34, -18, 1.2), (25, -6, 1.1)):
            p += arbol((lado * ax, ay, 5.8), e)
    p += grupo("nubes", nube((-30, 45, 30), 1.6) + nube((15, 60, 34), 2.0) + nube((48, 38, 28), 1.4))
    # Autos esperando en la orilla izquierda (cruzarán al final) y en la derecha
    fila = []
    for i in range(9):
        fila += auto((-ORILLA - 2.2 - i * 1.9, -0.9, 5.9), COLORES_AUTO[i % 10], 0, "ninguna")
    p += grupo("autos_d", fila, (0, 0, 0))
    fila = []
    for i in range(6):
        fila += auto((ORILLA + 3 + i * 2.6, 0.9, 5.9), COLORES_AUTO[(i + 4) % 10], 180, "ninguna")
    p += grupo("autos_i", fila, (0, 0, 0))
    # El ferry: así se cruzaba antes
    ferry = [cubo((-13, 9, 0.35), (4.2, 2.2, 0.7), "blanco", "ninguna"),
             cubo((-14.3, 9, 1.1), (1.2, 1.8, 0.9), "azul", "ninguna")]
    ferry += auto((-12.4, 9, 0.7), "rojo", 0, "ninguna")
    p += grupo("ferry", ferry, (-13, 9, 0))
    return p


ESCENARIO = _escenario()


# --- Piezas de cada escena -------------------------------------------------------
def _vigas():
    return (grupo("viga_i", [cubo((-ORILLA / 2, 0, Z), (ORILLA, 3.4, 0.5), "concreto", "caer", t=0.04)],
                  (-ORILLA, 0, Z))
            + grupo("viga_d", [cubo((ORILLA / 2, 0, Z), (ORILLA, 3.4, 0.5), "concreto", "caer", t=0.12)],
                    (ORILLA, 0, Z)))


def _pilares():
    p = [cilindro((x, 0, Z / 2 - 0.2), 0.9, Z - 0.4, "concreto", "crecer") for x in (-14, -7, 0, 7, 14)]
    p += [cubo((x, 0, Z), (7, 3.4, 0.5), "concreto", "caer") for x in (-17.5, -10.5, -3.5, 3.5, 10.5, 17.5)]
    p = grupo("pilares", p, (0, 0, 0))
    p += grupo("barco", barco((7, 27, 0), -90, "aparecer", 1.3, t=0.33, mudo=True), (7, 27, 0))
    p += grupo("x1", equis((7, 4.6, 8.5), 3.2, t=0.66), (7, 4.6, 8.5))
    return p


def _cimientos():
    p = []
    for x in (-TX, TX):
        p += [cubo((x - 2.7, 0, 0.6), (0.5, 7.6, 1.8), "concreto", "crecer"),
              cubo((x + 2.7, 0, 0.6), (0.5, 7.6, 1.8), "concreto", "crecer"),
              cubo((x, -3.55, 0.6), (4.9, 0.5, 1.8), "concreto", "crecer"),
              cubo((x, 3.55, 0.6), (4.9, 0.5, 1.8), "concreto", "crecer"),
              cubo((x, 0, 0.75), (3.6, 5.6, 1.5), "concreto", "caer", altura_caida=6)]
    return p


NIVELES = [(1.5, 4.9), (4.9, 8.3), (8.3, 11.5), (11.5, 14.5), (14.5, 17.4), (17.4, TOPE)]
ANCHOS = [1.3, 1.2, 1.1, 1.0, 0.9, 0.8]


def _torres():
    p = []
    for (z0, z1), ancho in zip(NIVELES, ANCHOS):
        for x, nombre in ((-TX, "torre_i"), (TX, "torre_d")):
            nivel = [cubo((x, y, (z0 + z1) / 2), (ancho, 0.9, z1 - z0), "naranja", "caer", altura_caida=7)
                     for y in (-CY, CY)]
            if z1 > Z + 2:
                nivel.append(cubo((x, 0, z1 - 0.35), (ancho * 0.8, CY * 2, 0.6), "naranja", "aparecer"))
            p += grupo(nombre, nivel, (x, 0, 1.5))
    return p


def _cables_centrales():
    p = []
    mitades = {}
    for y in (-CY, CY):
        tramos = cadena(_cable_central(y), 0.17, "naranja", "aparecer")
        mitades[y] = (grupo("torre_i", tramos[:8], (-TX, 0, 1.5)),
                      grupo("torre_d", tramos[8:][::-1], (TX, 0, 1.5)))
    for k in range(8):          # de las torres hacia el centro, los dos cables a la vez
        for y in (-CY, CY):
            p += [mitades[y][0][k], mitades[y][1][k]]
    return p


def _anclajes():
    p = [cubo((-ANCLA, 0, Z + 1.0), (3.6, 5.6, 2.0), "concreto", "caer", t=0.48),
         cubo((ANCLA, 0, Z + 1.0), (3.6, 5.6, 2.0), "concreto", "caer", t=0.54)]
    for k in range(6):
        for lado in (-1, 1):
            for y in (-CY, CY):
                p.append(cadena(_cable_lateral(lado, y), 0.17, "naranja", "aparecer")[k])
    return p


def _tablero():
    xs = [x * 1.5 for x in range(-13, 14) if abs(abs(x * 1.5) - TX) > 0.9]
    tirantes = []
    for k, x in enumerate(sorted(xs, key=lambda v: abs(abs(v) - TX))):
        for y in (-CY, CY):
            tirantes.append(segmento((x, y, _altura_cable(x)), (x, y, Z + 0.2), 0.05,
                                     "naranja_osc", "crecer", t=0.03 + 0.36 * k / len(xs)))
    centros = sorted([-20 + 2 * i for i in range(21)], key=lambda v: abs(abs(v) - TX))
    tramos = [cubo((x, 0, Z), (2.03, CY * 2 + 0.5, 0.55), "naranja", "subir", desde_abajo=6.5)
              for x in centros]
    return tirantes + grupo("tablero", tramos, (0, 0, Z))


def _armadura():
    p = []
    for y in (-CY - 0.1, CY + 0.1):
        p.append(cubo((0, y, Z - 1.0), (42, 0.2, 0.2), "naranja_osc", "aparecer", t=0.56))
        x = -21.0
        while x < 20.5:
            p.append(segmento((x, y, Z - 0.3), (x + 1.0, y, Z - 1.0), 0.07, "naranja_osc", "aparecer", tipo="cubo"))
            p.append(segmento((x + 1.0, y, Z - 1.0), (x + 2.0, y, Z - 0.3), 0.07, "naranja_osc", "aparecer", tipo="cubo"))
            x += 2.0
    return grupo("tablero", p, (0, 0, Z))


def _calzada():
    p = [cubo((x, 0, Z + 0.3), (2.03, CY * 2 - 0.5, 0.08), "asfalto", "aparecer")
         for x in [-20 + 2 * i for i in range(21)]]
    x = -20.5
    while x < 21:
        p.append(cubo((x, 0, Z + 0.35), (0.8, 0.1, 0.02), "amarillo", "aparecer", mudo=True))
        x += 1.8
    return p


W = {"centro": (0, 0, 10), "distancia": 40, "altura": 18, "angulo": 212}

ESCENAS = [
    {   # 0 — gancho
        "es": "¿Cómo cruzas más de un kilómetro de mar abierto, con olas, niebla y barcos pasando?",
        "en": "How do you cross a mile of open sea, with waves, fog and ships passing through?",
        "camara": {"centro": (-8, 0, 2), "distancia": 38, "altura": 27, "angulo": 197},
        "deriva": 8,
        "acciones": [
            {"id": "ferry", "t": 0.0, "dur": 16, "mover": (27, 0, 0), "suave": "lineal"},
            {"id": "nubes", "t": 0.0, "hasta_fin": True, "velocidad": (0.5, 0, 0)},
        ],
    },
    {   # 1 — la viga
        "es": "Fácil: pones una viga enorme de orilla a orilla. Pero es tan larga que se dobla con su propio peso... y adiós.",
        "en": "Easy: you lay one huge beam from shore to shore. But it's so long it bends under its own weight... and it's gone.",
        "camara": {"centro": (-3, 0, 2), "distancia": 34, "altura": 22, "angulo": 210},
        "piezas": _vigas(),
        "acciones": [
            {"id": "viga_i", "t": 0.48, "durf": 0.13, "girar": (0, 14, 0)},
            {"id": "viga_d", "t": 0.48, "durf": 0.13, "girar": (0, -14, 0)},
            {"id": "viga_i", "t": 0.66, "durf": 0.13, "girar": (0, 60, 0), "mover": (0, 0, -3),
             "suave": "acelera", "sonido": "splash", "sonido_en": 0.8},
            {"id": "viga_d", "t": 0.66, "durf": 0.13, "girar": (0, -60, 0), "mover": (0, 0, -3), "suave": "acelera"},
            {"id": "viga_i", "t": 0.86, "durf": 0.1, "mover": (0, 0, -14), "quitar": True},
            {"id": "viga_d", "t": 0.86, "durf": 0.1, "mover": (0, 0, -14), "quitar": True},
        ],
        "avisos": [{"es": "¡SE DOBLA!", "en": "IT BENDS!", "t": (0.5, 0.97)}],
    },
    {   # 2 — los pilares
        "es": "Entonces le pones pilares. Pero aquí el mar tiene cien metros de fondo... y los barcos ya no pueden pasar.",
        "en": "So you add pillars. But the sea here is three hundred feet deep... and now ships can't get through.",
        "camara": {"centro": (4, 3, 1), "distancia": 34, "altura": 25, "angulo": 300},
        "piezas": _pilares(),
        "ventana": (0.02, 0.28),
        "acciones": [
            {"id": "barco", "t": 0.36, "durf": 0.28, "mover": (0, -21.3, 0), "suave": "lineal",
             "sonido": "crash", "sonido_en": 1.0},
            {"id": "barco", "t": 0.64, "durf": 0.06, "mover": (0, 1.3, 0), "girar": (0, 0, 9), "suave": "frena"},
            {"id": "pilares", "t": 0.9, "durf": 0.08, "quitar": True},
            {"id": "barco", "t": 0.9, "durf": 0.08, "quitar": True},
            {"id": "x1", "t": 0.9, "durf": 0.08, "quitar": True},
        ],
        "avisos": [{"es": "¡CUIDADO!", "en": "WATCH OUT!", "t": (0.6, 0.93)}],
        "etiquetas": [{"es": "100 M DE FONDO", "en": "300 FT DEEP", "pos": (-3.5, -5, 0.2), "t": (0.34, 0.6)}],
    },
    {   # 3 — cimientos
        "es": "La solución: solo dos torres gigantes y el centro libre. Para cada una levantas un muro en pleno mar, lo vacías como una piscina y adentro pones los cimientos.",
        "en": "The fix: just two giant towers, with the middle left open. For each one you build a wall out at sea, drain it like a pool, and lay the foundation inside.",
        "camara": {"centro": (-TX, 0, -1), "distancia": 15, "altura": 14, "angulo": 235},
        "camara_fin": {"centro": (0, 0, -1), "distancia": 32, "altura": 26, "angulo": 250},
        "ventana": (0.14, 0.85),
        "piezas": _cimientos(),
    },
    {   # 4 — torres
        "es": "Encima apilas acero, bloque sobre bloque, hasta los 227 metros. Cada torre lleva 600 mil remaches.",
        "en": "On top you stack steel, block on block, up to 746 feet. Each tower holds 600,000 rivets.",
        "camara": {"centro": (-TX, 0, 4), "distancia": 20, "altura": 9, "angulo": 222},
        "camara_fin": {"centro": (-2, 0, 6), "distancia": 38, "altura": 20, "angulo": 212},
        "ventana": (0.03, 0.8),
        "piezas": _torres(),
        "etiquetas": [{"es": "227 M", "en": "746 FT", "pos": (-TX, 0, TOPE), "t": (0.8, 1.0), "alto": 4}],
    },
    {   # 5 — cables
        "es": "Luego tiendes dos cables de torre a torre. Cada uno lleva 27 mil alambres de acero y mide casi un metro de grueso.",
        "en": "Then you string two cables from tower to tower. Each one packs 27,000 steel wires and is three feet thick.",
        "camara": {"centro": (0, 0, 8), "distancia": 36, "altura": 18, "angulo": 216},
        "ventana": (0.05, 0.5),
        "piezas": _cables_centrales(),
        "etiquetas": [{"es": "27 572 ALAMBRES", "en": "27,572 WIRES", "pos": (0, -CY, Z + 1.8), "t": (0.55, 1.0), "alto": 6}],
    },
    {   # 6 — anclajes
        "es": "Pero su peso jala las torres hacia adentro. Así que amarras cada cable a un bloque de concreto gigante en la orilla: los anclajes.",
        "en": "But their weight pulls the towers inward. So you tie each cable to a giant concrete block on shore: the anchorages.",
        "ventana": (0.66, 0.92),
        "piezas": _anclajes(),
        "acciones": [
            {"id": "torre_i", "t": 0.06, "durf": 0.14, "girar": (0, 6, 0)},
            {"id": "torre_d", "t": 0.06, "durf": 0.14, "girar": (0, -6, 0)},
            {"id": "torre_i", "t": 0.6, "durf": 0.08, "girar": (0, -6, 0), "suave": "atras"},
            {"id": "torre_d", "t": 0.6, "durf": 0.08, "girar": (0, 6, 0), "suave": "atras"},
        ],
        "avisos": [{"es": "¡SE CIERRAN!", "en": "THEY LEAN IN!", "t": (0.08, 0.45)}],
        "camara": {"centro": (0, 0, 6), "distancia": 33, "altura": 14, "angulo": 262},
        "etiquetas": [{"es": "ANCLAJE", "en": "ANCHORAGE", "pos": (-ANCLA, 0, Z + 2.1), "t": (0.62, 1.0)}],
        "camara_fin": {"centro": (-21, 0, 6), "distancia": 26, "altura": 15, "angulo": 240},
    },
    {   # 7 — tirantes y tablero
        "es": "De los cables cuelgas tirantes, y de los tirantes, la carretera. La montas desde las torres hacia los dos lados a la vez, para que todo quede en equilibrio.",
        "en": "From the cables you hang suspenders, and from those, the road. You build it out from the towers in both directions at once, so everything stays balanced.",
        "camara": {"centro": (0, 0, 5), "distancia": 36, "altura": 20, "angulo": 214},
        "camara_fin": {"centro": (0, 0, 4), "distancia": 30, "altura": 16, "angulo": 228},
        "ventana": (0.42, 0.9),
        "piezas": _tablero(),
    },
    {   # 8 — el viento
        "es": "Pero con viento fuerte, la carretera se retuerce como una cinta. Entonces le atornillas una armadura de acero por debajo, y queda firme.",
        "en": "But in strong wind, the road twists like a ribbon. So you bolt a steel truss underneath, and it holds firm.",
        "camara": {"centro": (3, 0, 4), "distancia": 22, "altura": 10, "angulo": 197},
        "camara_fin": {"centro": (3, 0, 3.5), "distancia": 13, "altura": 3, "angulo": 258},
        "corte": True,
        "ventana": (0.58, 0.9),
        "piezas": _armadura(),
        "acciones": [
            {"id": "tablero", "t": 0.05, "durf": 0.07, "girar": (7, 0, 0), "sonido": "paso"},
            {"id": "tablero", "t": 0.12, "durf": 0.09, "girar": (-14, 0, 0), "sonido": "paso"},
            {"id": "tablero", "t": 0.21, "durf": 0.09, "girar": (13, 0, 0), "sonido": "paso"},
            {"id": "tablero", "t": 0.30, "durf": 0.09, "girar": (-10, 0, 0)},
            {"id": "tablero", "t": 0.39, "durf": 0.08, "girar": (4, 0, 0)},
        ],
        "avisos": [{"es": "¡EL VIENTO!", "en": "THE WIND!", "t": (0.05, 0.48)}],
        "etiquetas": [{"es": "ARMADURA", "en": "TRUSS", "pos": (3, -CY - 0.2, Z - 0.4), "t": (0.7, 1.0), "alto": 3.2}],
    },
    {   # 9 — calzada y autos
        "es": "Asfalto, seis carriles y su famoso color naranja, elegido para verse entre la niebla. ¡Y por fin pasan los autos!",
        "en": "Asphalt, six lanes, and its famous orange, chosen to stand out in the fog. And at last, the cars roll through!",
        "camara": {"centro": (0, 0, 5), "distancia": 16, "altura": 9, "angulo": 238},
        "camara_fin": {"centro": (2, 0, 5), "distancia": 19, "altura": 10, "angulo": 226},
        "corte": True,
        "ventana": (0.03, 0.5),
        "piezas": _calzada(),
        "acciones": [
            {"id": "autos_d", "t": 0.62, "hasta_fin": True, "velocidad": (5, 0, 0)},
            {"id": "autos_i", "t": 0.62, "hasta_fin": True, "velocidad": (-5, 0, 0)},
        ],
    },
    {   # 10 — final
        "es": "¡Bien! Has construido el Golden Gate. ¿Qué construimos mañana?",
        "en": "Nice! You just built the Golden Gate. What should we build next?",
        "final": True,
        "camara": dict(W),
        "deriva": 30,
        "piezas": grupo("barco2", barco((3, 26, 0), -90, "aparecer", 1.3, t=0.0, mudo=True), (3, 26, 0)),
        "acciones": [{"id": "barco2", "t": 0.02, "hasta_fin": True, "velocidad": (0, -7, 0)}],
        "confeti": (0, 0, 13),
    },
]
