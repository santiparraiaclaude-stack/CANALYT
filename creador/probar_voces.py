"""Escucha varias voces de tu cuenta de ElevenLabs y elige la del canal.

    python3 creador/probar_voces.py                  # genera una muestra de cada voz
    python3 creador/probar_voces.py --elegir Nombre  # la guarda en .env
    python3 creador/probar_voces.py --idioma en ...  # lo mismo para inglés

Las muestras quedan en salida/voces/. Cada muestra gasta unos 150 caracteres
de tu cuota. Para tener más voces (por ejemplo, con acento latino), entra a
elevenlabs.io -> Voices -> Voice Library, añade las que te gusten a "My Voices"
y vuelve a ejecutar este script.
"""
import argparse
import os
import re
import subprocess
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)
import voz  # noqa: E402

MUESTRA = {
    "es": "¿Cómo cruzas un kilómetro de mar abierto? Fácil: pones una viga enorme "
          "de orilla a orilla. Pero se dobla con su propio peso... y adiós.",
    "en": "How do you cross a mile of open sea? Easy: you lay a huge beam from "
          "shore to shore. But it bends under its own weight... and it's gone.",
}
# Voces de fábrica, por si la clave no tiene permiso para listar las de la cuenta
DE_FABRICA = {
    "Daniel": "onwK4e9ZLuTAKqWW03F9", "Brian": "nPczCjzI2devNBz1zQrb",
    "George": "JBFqnCBsd6RMkjVDRZzb", "Liam": "TX3LPaxmHKxFdv7VOQHJ",
    "Will": "bIHbv24MWmeRgasZH3fP", "Eric": "cjVigY5qzO86Huf0OWal",
    "Chris": "iP95p4xoKVk53GoZ742B", "Charlie": "IKne3meq5aSn9XLyUdCD",
    "Matilda": "XrExE9yKIg1WjnnlVkGX", "Sarah": "EXAVITQu4vr4xnSDxMaL",
}


def voces_disponibles():
    try:
        datos = voz.pedir("/voices")
        voces = {}
        for v in datos.get("voices", []):
            nombre = re.sub(r"[^A-Za-z0-9áéíóúñÁÉÍÓÚÑ]+", "_", v["name"].split(" - ")[0]).strip("_")
            # primero las tuyas (clonadas o añadidas de la biblioteca), luego las de fábrica
            voces[nombre] = (v["voice_id"], v.get("category") != "premade")
        orden = sorted(voces, key=lambda n: (not voces[n][1], n))
        return {n: voces[n][0] for n in orden}
    except RuntimeError as e:
        print("No pude listar las voces de tu cuenta (uso las de fábrica):", str(e)[:120])
        return dict(DE_FABRICA)


def guardar_en_env(variable, valor):
    ruta = os.path.join(RAIZ, ".env")
    lineas = open(ruta, encoding="utf-8").read().splitlines() if os.path.exists(ruta) else []
    lineas = [l for l in lineas if not l.startswith(variable + "=")]
    lineas.append(f"{variable}={valor}")
    with open(ruta, "w", encoding="utf-8") as f:
        f.write("\n".join(lineas) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--idioma", default="es", choices=["es", "en"])
    ap.add_argument("--elegir")
    ap.add_argument("--max", type=int, default=10)
    a = ap.parse_args()
    if not voz.hay_clave():
        sys.exit("Falta ELEVENLABS_API_KEY en el archivo .env")
    voces = voces_disponibles()

    if a.elegir:
        coincide = [n for n in voces if n.lower() == a.elegir.lower()]
        if not coincide:
            sys.exit(f"No encuentro la voz '{a.elegir}'. Disponibles: {', '.join(voces)}")
        guardar_en_env(f"ELEVENLABS_VOZ_{a.idioma.upper()}", voces[coincide[0]])
        print(f"✅ Voz '{coincide[0]}' guardada para {a.idioma}. El próximo video ya la usa.")
        return

    carpeta = os.path.join(RAIZ, "salida", "voces")
    os.makedirs(carpeta, exist_ok=True)
    cfg = voz.config(a.idioma)
    for nombre, vid in list(voces.items())[:a.max]:
        ruta = os.path.join(carpeta, f"{a.idioma}_{nombre}.mp3")
        if not os.path.exists(ruta):
            try:
                audio = voz.pedir(f"/text-to-speech/{vid}?output_format=mp3_44100_128",
                                  {"text": MUESTRA[a.idioma], "model_id": cfg["modelo"],
                                   "voice_settings": voz.ajustes_voz(cfg["velocidad"])}, binario=True)
            except RuntimeError as e:
                print(f"  ✗ {nombre}: {str(e)[:110]}")
                continue
            with open(ruta, "wb") as f:
                f.write(audio)
        print(f"  ✓ {nombre}")
    print(f"\nMuestras en: {carpeta}")
    print("Escúchalas y elige con:  python3 creador/probar_voces.py --elegir NOMBRE")
    if sys.platform == "darwin":
        subprocess.run(["open", carpeta])


if __name__ == "__main__":
    main()
