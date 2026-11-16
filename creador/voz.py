"""Narración con ElevenLabs, con el tiempo exacto de cada palabra.

Configuración en .env (en la raíz del proyecto):
    ELEVENLABS_API_KEY=...
    ELEVENLABS_VOZ_ES=<id de la voz>      (elige una con creador/probar_voces.py)
    ELEVENLABS_VOZ_EN=<id de la voz>
    ELEVENLABS_VELOCIDAD=1.08             (0.7 a 1.2)
    ELEVENLABS_MODELO=eleven_multilingual_v2

Sin clave, el video sale sin voz y los tiempos se calculan por estimación.
"""
import base64
import hashlib
import json
import os
import subprocess
import urllib.error
import urllib.request

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API = "https://api.elevenlabs.io/v1"
VOZ_POR_DEFECTO = "onwK4e9ZLuTAKqWW03F9"     # Daniel (voz de fábrica de ElevenLabs)
DESFASE = 0.12                               # silencio antes de cada frase


def cargar_env():
    ruta = os.path.join(RAIZ, ".env")
    if not os.path.exists(ruta):
        return
    with open(ruta, encoding="utf-8") as f:
        for linea in f:
            linea = linea.strip()
            if linea and not linea.startswith("#") and "=" in linea:
                k, v = linea.split("=", 1)
                if v.strip().strip('"'):
                    os.environ.setdefault(k.strip(), v.strip().strip('"'))


def clave_api():
    cargar_env()
    k = os.environ.get("ELEVENLABS_API_KEY", "")
    return k if k and k != "TU_CLAVE" else ""


def hay_clave():
    return bool(clave_api())


def config(idioma):
    cargar_env()
    return {
        "voz": os.environ.get(f"ELEVENLABS_VOZ_{idioma.upper()}") or VOZ_POR_DEFECTO,
        "modelo": os.environ.get("ELEVENLABS_MODELO", "eleven_multilingual_v2"),
        "velocidad": float(os.environ.get("ELEVENLABS_VELOCIDAD", "1.08")),
    }


def pedir(ruta, cuerpo=None, binario=False):
    """Llamada a la API de ElevenLabs. Devuelve JSON (o bytes si binario)."""
    req = urllib.request.Request(
        API + ruta, method="POST" if cuerpo is not None else "GET",
        data=json.dumps(cuerpo).encode() if cuerpo is not None else None,
        headers={"xi-api-key": clave_api(), "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            datos = r.read()
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"ElevenLabs respondió {e.code}: {e.read().decode()[:400]}")
    return datos if binario else json.loads(datos)


def ajustes_voz(velocidad):
    return {"stability": 0.4, "similarity_boost": 0.8, "style": 0.45,
            "use_speaker_boost": True, "speed": velocidad}


def duracion_audio(ruta):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", ruta], capture_output=True, text=True, check=True)
    return float(out.stdout.strip())


def limpiar(palabra):
    """Cómo se ve la palabra en pantalla (sin comas ni puntos sueltos)."""
    p = palabra.strip().strip(",.;:…\"“”()").replace("...", "")
    for i, c in enumerate(p):
        if c.isalpha():
            return p[:i] + c.upper() + p[i + 1:]
    return p


def _palabras_de_alineacion(al):
    car = al["characters"]
    ini = al["character_start_times_seconds"]
    fin = al["character_end_times_seconds"]
    out, actual, t0, t1 = [], "", None, None
    for c, a, b in zip(car, ini, fin):
        if c.isspace():
            if actual:
                out.append([actual, t0, t1])
            actual, t0 = "", None
        else:
            if t0 is None:
                t0 = a
            actual += c
            t1 = b
    if actual:
        out.append([actual, t0, t1])
    return out


def estimar(texto, velocidad=1.08):
    """Sin voz real: duración y tiempos aproximados para poder previsualizar."""
    palabras = texto.split()
    pesos = [len(p) + 2 + (4 if p[-1] in ",.;:?!" else 0) for p in palabras]
    dur = sum(pesos) * 0.062 / velocidad
    out, t = [], 0.0
    for p, w in zip(palabras, pesos):
        d = dur * w / sum(pesos)
        out.append([p, t, t + d * 0.9])
        t += d
    return dur, out


def generar(texto, idioma, carpeta):
    """Devuelve (ruta_mp3 o None, duración, palabras) para una frase.

    palabras = [[texto_en_pantalla, inicio, fin], ...] en segundos desde el
    principio del segmento. Se guarda en caché: solo se vuelve a pagar si
    cambia el texto, la voz, el modelo o la velocidad.
    """
    cfg = config(idioma)
    if not hay_clave():
        dur, pal = estimar(texto, cfg["velocidad"])
    else:
        huella = hashlib.sha1(json.dumps([texto, cfg], sort_keys=True).encode()).hexdigest()[:12]
        mp3 = os.path.join(carpeta, f"{idioma}_{huella}.mp3")
        meta = mp3[:-4] + ".json"
        if not (os.path.exists(mp3) and os.path.exists(meta)):
            os.makedirs(carpeta, exist_ok=True)
            cuerpo = {"text": texto, "model_id": cfg["modelo"],
                      "voice_settings": ajustes_voz(cfg["velocidad"])}
            r = pedir(f"/text-to-speech/{cfg['voz']}/with-timestamps?output_format=mp3_44100_128", cuerpo)
            with open(mp3, "wb") as f:
                f.write(base64.b64decode(r["audio_base64"]))
            with open(meta, "w", encoding="utf-8") as f:
                json.dump(r.get("alignment") or {}, f)
        dur = duracion_audio(mp3)
        with open(meta, encoding="utf-8") as f:
            al = json.load(f)
        try:
            pal = _palabras_de_alineacion(al)
        except (KeyError, TypeError):
            pal = []
        if not pal:   # sin tiempos: se reparten según el largo de cada palabra
            _, pal = estimar(texto)
            factor = dur / max(0.01, pal[-1][2])
            pal = [[p, a * factor, b * factor] for p, a, b in pal]
        return mp3, dur, _para_pantalla(pal)
    return None, dur, _para_pantalla(pal)


def _para_pantalla(pal):
    out = []
    for p, a, b in pal:
        txt = limpiar(p)
        if txt:
            out.append([txt, round(a + DESFASE, 3), round(b + DESFASE, 3)])
    return out
