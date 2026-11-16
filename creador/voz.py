"""Genera la narración con ElevenLabs (sin dependencias extra).

Necesita la variable de entorno ELEVENLABS_API_KEY (o un archivo .env en la
raíz del repo). Si no hay clave, devuelve None y el video sale sin voz.
"""
import json
import os
import subprocess
import urllib.error
import urllib.request

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Voces multilingües de la biblioteca pública de ElevenLabs. Puedes poner
# las tuyas en .env (ELEVENLABS_VOZ_ES / ELEVENLABS_VOZ_EN).
VOCES_POR_DEFECTO = {
    "es": "pNInz6obpgDQGcFmaJgB",   # Adam
    "en": "pNInz6obpgDQGcFmaJgB",
}
MODELO = "eleven_multilingual_v2"


def cargar_env():
    ruta = os.path.join(RAIZ, ".env")
    if not os.path.exists(ruta):
        return
    with open(ruta, encoding="utf-8") as f:
        for linea in f:
            linea = linea.strip()
            if linea and not linea.startswith("#") and "=" in linea:
                k, v = linea.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"'))


def hay_clave():
    cargar_env()
    return bool(os.environ.get("ELEVENLABS_API_KEY"))


def duracion_audio(ruta):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", ruta],
        capture_output=True, text=True, check=True)
    return float(out.stdout.strip())


def generar(texto, idioma, ruta_mp3):
    """Genera un mp3. Devuelve su duración en segundos, o None si no hay clave."""
    if not hay_clave():
        return None
    if os.path.exists(ruta_mp3) and os.path.getsize(ruta_mp3) > 0:
        return duracion_audio(ruta_mp3)   # ya generado: no gastar créditos otra vez
    voz = os.environ.get(f"ELEVENLABS_VOZ_{idioma.upper()}", VOCES_POR_DEFECTO.get(idioma))
    url = (f"https://api.elevenlabs.io/v1/text-to-speech/{voz}"
           "?output_format=mp3_44100_128")
    cuerpo = json.dumps({
        "text": texto,
        "model_id": MODELO,
        "voice_settings": {"stability": 0.45, "similarity_boost": 0.8,
                           "style": 0.35, "use_speaker_boost": True},
    }).encode()
    req = urllib.request.Request(url, data=cuerpo, method="POST", headers={
        "xi-api-key": os.environ["ELEVENLABS_API_KEY"],
        "Content-Type": "application/json",
        "Accept": "audio/mpeg",
    })
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            datos = r.read()
    except urllib.error.HTTPError as e:
        raise SystemExit(f"ElevenLabs respondió {e.code}: {e.read().decode()[:300]}")
    os.makedirs(os.path.dirname(ruta_mp3), exist_ok=True)
    with open(ruta_mp3, "wb") as f:
        f.write(datos)
    return duracion_audio(ruta_mp3)
