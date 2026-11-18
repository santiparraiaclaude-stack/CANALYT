"""Efectos de sonido del video.

Recibe la lista de sonidos del plan ([{"tipo", "t"}]) y escribe un WAV mono.
Tipos: golpe, pop, subida, paso, splash, crash, alerta, tada, latido, goteo,
susurro, estatica y ambiente (fondo en bucle: AMBIENTE en la estructura).

Si hay grabaciones reales en sonidos/<tipo>/ (las baja creador/banco_sonidos.py
desde Openverse, o pones las tuyas), se usan esas, variando entre ellas. Si no,
el sonido se sintetiza.
"""
import array
import math
import os
import random
import subprocess
import wave

BANCO = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sonidos")
LARGO_MAX = {"golpe": 1.2, "pop": 0.5, "subida": 0.9, "paso": 1.4, "splash": 2.5,
             "crash": 2.5, "alerta": 1.2, "tada": 3.0, "latido": 3.0, "goteo": 0.8,
             "susurro": 3.0, "estatica": 2.0, "ambiente": 60.0}
_cache = {}


def _archivos(tipo):
    carpeta = os.path.join(BANCO, tipo)
    if not os.path.isdir(carpeta):
        return []
    return sorted(os.path.join(carpeta, f) for f in os.listdir(carpeta)
                  if f.lower().endswith((".wav", ".mp3", ".ogg", ".flac")))


def _grabacion(ruta, tipo):
    """Lee un archivo con ffmpeg, quita el silencio inicial, recorta y normaliza."""
    if ruta in _cache:
        return _cache[ruta]
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", ruta, "-ac", "1", "-ar", str(FREC),
                        "-f", "f32le", "-"], capture_output=True)
    datos = array.array("f")
    datos.frombytes(r.stdout[: len(r.stdout) // 4 * 4])
    pico = max((abs(v) for v in datos), default=0.0)
    if pico < 1e-4:
        _cache[ruta] = None
        return None
    umbral = pico * 0.08
    inicio = next((i for i, v in enumerate(datos) if abs(v) > umbral), 0)
    inicio = max(0, inicio - int(0.004 * FREC))
    largo = int(LARGO_MAX.get(tipo, 2.0) * FREC)
    trozo = datos[inicio:inicio + largo]
    cola = min(len(trozo), int(0.06 * FREC))     # se apaga suave si se recortó
    for k in range(cola):
        trozo[len(trozo) - cola + k] *= 1 - k / cola
    _cache[ruta] = [v / pico for v in trozo]
    return _cache[ruta]

FREC = 44100
ESPERA = {"golpe": 0.07, "pop": 0.05, "subida": 0.09}   # separación mínima entre iguales
VOLUMEN = {"golpe": 0.50, "pop": 0.22, "subida": 0.16, "paso": 0.30, "splash": 0.45,
           "crash": 0.60, "alerta": 0.30, "tada": 0.40, "latido": 0.55, "goteo": 0.30,
           "susurro": 0.35, "estatica": 0.30, "ambiente": 0.22}


def _golpe(rnd):
    n = int(0.2 * FREC)
    out, fase = [], 0.0
    for i in range(n):
        t = i / FREC
        fase += 2 * math.pi * (55 + 75 * math.exp(-t * 28)) / FREC
        clic = rnd.uniform(-1, 1) * math.exp(-t * 320) * 0.5
        out.append(math.sin(fase) * math.exp(-t * 20) + clic)
    return out


def _pop(rnd):
    n = int(0.07 * FREC)
    base = rnd.choice([520, 587, 660, 784])
    out, fase = [], 0.0
    for i in range(n):
        t = i / FREC
        fase += 2 * math.pi * (base + 500 * t / 0.07) / FREC
        out.append(math.sin(fase) * math.exp(-t * 55))
    return out


def _ruido(rnd, dur, corte0, corte1, forma):
    """Ruido con filtro pasa-bajos que cambia de corte0 a corte1 (0..1)."""
    n = int(dur * FREC)
    out, y = [], 0.0
    for i in range(n):
        x = i / n
        a = corte0 + (corte1 - corte0) * x
        y += a * (rnd.uniform(-1, 1) - y)
        out.append(y * forma(x))
    return out


def _subida(rnd):
    return _ruido(rnd, 0.3, 0.02, 0.25, lambda x: math.sin(math.pi * x) ** 2 * 2.5)


def _paso(rnd):
    return _ruido(rnd, 0.4, 0.3, 0.03, lambda x: math.sin(math.pi * x) ** 1.5 * 2.0)


def _splash(rnd):
    return _ruido(rnd, 0.7, 0.6, 0.08, lambda x: math.exp(-x * 5) * (1 - math.exp(-x * 60)) * 1.6)


def _crash(rnd):
    r = _ruido(rnd, 0.5, 0.5, 0.1, lambda x: math.exp(-x * 7) * 1.5)
    g = _golpe(rnd)
    return [a + (g[i] if i < len(g) else 0.0) for i, a in enumerate(r)]


def _alerta(rnd):
    out = []
    for frec in (392, 311):
        n = int(0.13 * FREC)
        for i in range(n):
            t = i / FREC
            s = math.sin(2 * math.pi * frec * t)
            s = 0.6 * s + 0.4 * (1 if s > 0 else -1) * 0.5
            out.append(s * min(1, i / 200) * min(1, (n - i) / 400))
    return out


def _tada(rnd):
    notas = [(523, 0.0), (659, 0.09), (784, 0.18), (1047, 0.27), (1319, 0.36)]
    n = int(1.4 * FREC)
    out = [0.0] * n
    for frec, ini in notas:
        i0 = int(ini * FREC)
        for i in range(i0, n):
            t = (i - i0) / FREC
            out[i] += (math.sin(2 * math.pi * frec * t) + 0.3 * math.sin(4 * math.pi * frec * t)) \
                * math.exp(-t * 3.5) * min(1, t * 200) * 0.35
    return out


def _latido(rnd):
    out = []
    for golpe in (0.0, 0.28):
        n0 = int(golpe * FREC) - len(out)
        out += [0.0] * max(0, n0)
        fase = 0.0
        for i in range(int(0.18 * FREC)):
            t = i / FREC
            fase += 2 * math.pi * (48 + 30 * math.exp(-t * 30)) / FREC
            out.append(math.sin(fase) * math.exp(-t * 22) * (1.0 if golpe == 0 else 0.7))
    return out


def _goteo(rnd):
    n = int(0.25 * FREC)
    out, fase = [], 0.0
    for i in range(n):
        t = i / FREC
        fase += 2 * math.pi * (900 + 1400 * math.exp(-t * 60)) / FREC
        out.append(math.sin(fase) * math.exp(-t * 28))
    return out


def _susurro(rnd):
    return _ruido(rnd, 1.6, 0.35, 0.25, lambda x: (math.sin(math.pi * x) ** 2) * (0.6 + 0.4 * math.sin(x * 40)))


def _estatica(rnd):
    return _ruido(rnd, 1.0, 0.95, 0.9, lambda x: 0.7 * (1 - x * 0.3) * (0.5 + 0.5 * (rnd.random() > 0.4)))


def _ambiente(rnd):
    """Zumbido grave y oscuro (se repite en bucle bajo todo el video)."""
    n = int(8.0 * FREC)
    out, y = [], 0.0
    for i in range(n):
        t = i / FREC
        y += 0.02 * (rnd.uniform(-1, 1) - y)
        tono = 0.5 * math.sin(2 * math.pi * 55 * t) + 0.3 * math.sin(2 * math.pi * 82.5 * t + math.sin(t * 0.7))
        out.append((tono * (0.6 + 0.4 * math.sin(2 * math.pi * t / 8.0)) + y * 2.0) * 0.6)
    return out


# Las grabaciones vienen normalizadas a pico 1: se ajustan para que suenen parecido
REAL_GANANCIA = {"golpe": 0.55, "pop": 0.5, "subida": 0.45, "paso": 0.45, "splash": 0.4,
                 "crash": 0.4, "alerta": 0.4, "tada": 0.5, "latido": 0.6, "goteo": 0.5,
                 "susurro": 0.5, "estatica": 0.4, "ambiente": 0.5}

GENERADORES = {"golpe": _golpe, "pop": _pop, "subida": _subida, "paso": _paso,
               "splash": _splash, "crash": _crash, "alerta": _alerta, "tada": _tada,
               "latido": _latido, "goteo": _goteo, "susurro": _susurro, "estatica": _estatica,
               "ambiente": _ambiente}


def _fondo(tipo, rnd, n, pista):
    """Sonido de ambiente en bucle bajo todo el video, con entrada y salida suaves."""
    reales = _archivos(tipo)
    muestras = _grabacion(rnd.choice(reales), tipo) if reales else None
    vol = VOLUMEN.get(tipo, 0.2) * (REAL_GANANCIA.get(tipo, 0.5) if muestras else 1.0)
    if not muestras:
        muestras = GENERADORES.get(tipo, _ambiente)(rnd)
    largo = len(muestras)
    cruce = min(int(0.5 * FREC), largo // 4)
    entrada, salida = int(1.5 * FREC), int(2.0 * FREC)
    for i in range(n):
        k = i % largo
        v = muestras[k]
        if k < cruce and i >= largo:                       # disimula la costura del bucle
            v = v * (k / cruce) + muestras[largo - cruce + k] * (1 - k / cruce)
        env = min(1.0, i / entrada, (n - i) / salida)
        pista[i] += v * vol * max(0.0, env)


def generar(sonidos, duracion, ruta_wav, ambiente=None):
    rnd = random.Random(3)
    n = int(duracion * FREC) + FREC
    pista = array.array("f", bytes(4 * n))
    if ambiente:
        _fondo(ambiente, rnd, n, pista)
    ultimo = {}
    for s in sorted(sonidos, key=lambda x: x["t"]):
        tipo, t = s["tipo"], s["t"]
        if tipo not in GENERADORES or t < 0:
            continue
        if t - ultimo.get(tipo, -9) < ESPERA.get(tipo, 0.0):
            continue
        ultimo[tipo] = t
        vol = VOLUMEN[tipo] * rnd.uniform(0.8, 1.0)
        i0 = int(t * FREC)
        muestras = None
        reales = _archivos(tipo)
        if reales:
            muestras = _grabacion(rnd.choice(reales), tipo)
            vol *= REAL_GANANCIA.get(tipo, 0.8)
        if muestras is None:
            muestras = GENERADORES[tipo](rnd)
        for i, v in enumerate(muestras):
            if i0 + i < n:
                pista[i0 + i] += v * vol
    salida = array.array("h", (int(max(-1.0, min(1.0, v)) * 32000) for v in pista))
    with wave.open(ruta_wav, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(FREC)
        w.writeframes(salida.tobytes())
