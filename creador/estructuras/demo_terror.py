"""Plantilla de historia de terror interactiva: «El edificio que se apaga».

Formato: narración en segunda persona, suspenso que sube, y al final el espectador
elige A o B en los comentarios para la parte 2. Escena nocturna low-poly: calle con
niebla, farolas, edificios con ventanas encendidas que se apagan una a una.
"""
import random

from piezas import auto, con, cubo, grupo, luz

TITULO = {"es": "PARTE 1\nLAS LUCES SE APAGAN", "en": "PART 1\nTHE LIGHTS GO OUT"}
TEMA = "terror"
ESTILO = "terror"
AMBIENTE = "ambiente"
CAMARA = {"lente": 28}

rnd = random.Random(13)


def edificio(x, y, ancho, pisos, lado, nombre):
    """Fachada con ventanas. lado = 1 mira hacia -X... (la calle va por el eje Y)."""
    fondo = 6
    alto = pisos * 3.0 + 1
    p = [cubo((x + lado * fondo / 2, y, alto / 2), (fondo, ancho, alto), "fachada", "ninguna")]
    ventanas_on, ventanas_off = [], []
    for piso in range(pisos):
        for k in range(int(ancho // 2.6)):
            vy = y - ancho / 2 + 1.5 + k * 2.6
            vz = 2.2 + piso * 3.0
            encendida = rnd.random() < 0.6
            pieza = cubo((x - lado * 0.02, vy, vz), (0.1, 1.3, 1.6),
                         "ventana_roja" if rnd.random() < 0.5 else "ventana_calida", "ninguna",
                         brillo=4.0 if encendida else 0.0)
            (ventanas_on if encendida else ventanas_off).append(pieza)
            p.append(cubo((x - lado * 0.06, vy, vz - 0.95), (0.25, 1.6, 0.12), "acera", "ninguna"))
    p += grupo(nombre, ventanas_on, (x, y, 0))
    return p + ventanas_off


def _escenario():
    p = [cubo((0, 0, -0.1), (16, 140, 0.2), "asfalto", "ninguna")]
    for lado in (-1, 1):
        p.append(cubo((lado * 7, 0, 0.1), (2, 140, 0.3), "acera", "ninguna"))
    y = -55
    n = 0
    while y < 55:
        ancho = rnd.choice([8, 10, 12])
        for lado in (-1, 1):
            p += edificio(lado * 8, y + ancho / 2, ancho, rnd.choice([4, 5, 6, 7]), lado, f"luces_{n}")
            n += 1
        y += ancho + 0.6
    for yy in range(-50, 55, 14):
        for lado in (-1, 1):
            p.append(cubo((lado * 6.3, yy, 2.4), (0.15, 0.15, 4.8), "acero", "ninguna"))
            p.append(cubo((lado * 5.9, yy, 4.8), (0.9, 0.3, 0.2), "farol", "ninguna", brillo=6.0))
            p.append(luz((lado * 5.8, yy, 4.5), (1.0, 0.7, 0.4), 140, 0.3, "ninguna", id=f"farola_{yy}_{lado}"))
    p += auto((2.5, -12, 0), "rojo", 90, "ninguna")
    p += auto((-2.5, 18, 0), "blanco", 90, "ninguna")
    # habitación con el celular (se ve en la escena 4)
    p.append(cubo((0, 80, 0.5), (8, 8, 1), "madera", "ninguna"))
    p.append(cubo((0, 80, 1.05), (0.9, 1.7, 0.08), "negro", "ninguna"))
    p += grupo("pantalla", [cubo((0, 80, 1.1), (0.8, 1.55, 0.02), "pantalla", "ninguna", brillo=1.6),
                            luz((0, 80, 1.6), (1.0, 0.2, 0.15), 25, 0.4, "ninguna")], (0, 80, 1.1))
    return p


ESCENARIO = _escenario()
CALLE = {"centro": (0, 6, 3), "distancia": 18, "altura": 0.6, "angulo": 268}

ESCENAS = [
    {
        "es": "Son las tres y diecisiete. Tu celular vibra con un mensaje sin remitente: «No enciendas ninguna luz».",
        "en": "It's three seventeen. Your phone buzzes with a message from no one: 'Don't turn on any lights.'",
        "camara": {"centro": (0, 80, 1.1), "distancia": 3.2, "altura": 2.6, "angulo": 250},
        "camara_fin": {"centro": (0, 80, 1.1), "distancia": 2.2, "altura": 2.0, "angulo": 262},
        "sonidos": [{"tipo": "estatica", "t": 0.1}, {"tipo": "latido", "t": 0.7}],
    },
    {
        "es": "Te asomas a la ventana. En todo el barrio hay luces encendidas... y empiezan a apagarse, una por una.",
        "en": "You look out the window. The whole block is lit... and the lights start going out, one by one.",
        "camara": dict(CALLE),
        "corte": True,
        "camara_fin": {"centro": (0, 10, 6), "distancia": 20, "altura": 3, "angulo": 270},
        "acciones": [{"id": f"luces_{n}", "t": 0.45 + 0.03 * n, "dur": 0.15, "quitar": True,
                      "sonido": "goteo" if n % 3 == 0 else None} for n in range(14)],
    },
    {
        "es": "Las farolas también. La oscuridad avanza por la calle, directo hacia tu edificio.",
        "en": "The streetlights too. The darkness moves down the street, straight toward your building.",
        "camara": {"centro": (0, 0, 4), "distancia": 26, "altura": 9, "angulo": 268},
        "acciones": [{"id": f"farola_{yy}_{lado}", "t": 0.1 + 0.05 * k, "dur": 0.1, "quitar": True}
                     for k, (yy, lado) in enumerate((yy, lado) for yy in reversed(range(-50, 55, 14))
                                                    for lado in (-1, 1))],
        "avisos": [{"es": "SE ACERCA", "en": "IT'S COMING", "t": (0.55, 0.95)}],
        "sonidos": [{"tipo": "latido", "t": 0.5}, {"tipo": "latido", "t": 0.75}],
    },
    {
        "es": "Solo queda una luz encendida en toda la calle: la pantalla de tu celular. Y algo afuera la acaba de ver.",
        "en": "Only one light is left on the whole street: your phone screen. And something outside just saw it.",
        "camara": {"centro": (0, 80, 1.1), "distancia": 2.6, "altura": 1.2, "angulo": 300},
        "corte": True,
        "sonidos": [{"tipo": "susurro", "t": 0.6}, {"tipo": "golpe", "t": 0.9}],
    },
    {
        "es": "¿Qué haces? A: apagas el celular y te quedas a oscuras. B: lo usas de linterna y sales a ver.",
        "en": "What do you do? A: turn off your phone and stay in the dark. B: use it as a flashlight and go look.",
        "final": True,
        "camara": {"centro": (0, 80, 1.1), "distancia": 3.6, "altura": 3.2, "angulo": 270},
        "opciones": {"es": ["A) Apagas el celular", "B) Sales con la linterna"],
                     "en": ["A) Turn off your phone", "B) Go out with the light"]},
        "opciones_t": 0.15,
        "celebrar": False,
    },
]
