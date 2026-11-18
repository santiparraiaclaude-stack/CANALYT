"""Descarga un banco de efectos de sonido REALES y gratis (CC0) desde Openverse.

    python3 creador/banco_sonidos.py              # baja ~6 sonidos de cada tipo
    python3 creador/banco_sonidos.py --por-tipo 10
    python3 creador/banco_sonidos.py --lista      # qué hay en el banco

Los guarda en sonidos/<tipo>/ y sonido.py los usa automáticamente en vez de los
sintetizados. Si un tipo no tiene archivos, se sintetiza como antes.

Openverse no pide registro. Solo se bajan sonidos con licencia CC0 (dominio
público: se pueden usar en videos monetizados sin dar crédito); aun así se
guarda quién los hizo en sonidos/creditos.csv por si alguna red lo pide.

También puedes poner tus propios archivos (.wav, .mp3, .ogg, .flac) en esas
carpetas: se usan igual.
"""
import argparse
import csv
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BANCO = os.path.join(RAIZ, "sonidos")
API = "https://api.openverse.org/v1/audio/"
AGENTE = "constru-yelo-tu-canal/1.0 (banco de efectos)"

# tipo de sonido del canal -> búsquedas en Openverse y duración aceptable (s)
TIPOS = {
    "golpe":  (["wood impact thud", "heavy impact hit", "block drop thud"], 0.15, 2.5),
    "pop":    (["ui pop", "bubble pop", "cartoon pop"], 0.04, 0.8),
    "subida": (["short whoosh", "swish", "fast swoosh"], 0.15, 1.5),
    "paso":   (["transition whoosh", "swoosh transition", "air whoosh"], 0.3, 2.0),
    "splash": (["water splash", "splash into water", "big splash"], 0.4, 4.0),
    "crash":  (["metal crash", "crash impact", "collision crash"], 0.3, 4.0),
    "alerta": (["alert beep", "warning alarm short", "error buzzer"], 0.15, 2.0),
    "tada":   (["success fanfare", "tada", "level complete jingle"], 0.6, 4.0),
    # terror / suspenso
    "ambiente": (["dark ambient drone", "horror ambience", "eerie atmosphere"], 8.0, 90.0),
    "latido":   (["heartbeat", "heart beat slow"], 0.5, 8.0),
    "goteo":    (["water drip", "faucet drip", "drop of water"], 0.1, 3.0),
    "susurro":  (["whisper", "creepy whisper"], 0.5, 6.0),
    "estatica": (["radio static", "tv static noise"], 0.4, 5.0),
}


def buscar(consulta, max_resultados=20):   # más de 20 exige registrarse
    params = urllib.parse.urlencode({"q": consulta, "license": "cc0", "page_size": max_resultados,
                                     "extension": "mp3,wav,ogg,flac"})
    req = urllib.request.Request(f"{API}?{params}", headers={"User-Agent": AGENTE})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read()).get("results", [])


def bajar(url, ruta, intentos=2):
    for i in range(intentos):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": AGENTE})
            with urllib.request.urlopen(req, timeout=20) as r:
                datos = r.read()
            if len(datos) < 1000:
                raise ValueError("archivo vacío")
            with open(ruta, "wb") as f:
                f.write(datos)
            return True
        except (urllib.error.URLError, ValueError, TimeoutError):
            time.sleep(1.0)
    return False


def valido(ruta):
    """Comprueba que ffmpeg lo puede leer."""
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=nw=1:nk=1", ruta], capture_output=True, text=True)
    try:
        return float(r.stdout.strip()) > 0.02
    except ValueError:
        return False


def archivos(tipo):
    carpeta = os.path.join(BANCO, tipo)
    if not os.path.isdir(carpeta):
        return []
    return sorted(os.path.join(carpeta, f) for f in os.listdir(carpeta)
                  if f.lower().endswith((".wav", ".mp3", ".ogg", ".flac")))


def lista():
    total = 0
    for tipo in TIPOS:
        n = len(archivos(tipo))
        total += n
        print(f"  {tipo:<8} {n:>3} sonidos reales" + ("" if n else "  (se sintetiza)"))
    print(f"Total: {total} en {BANCO}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--por-tipo", type=int, default=6)
    ap.add_argument("--tipos", nargs="+", choices=list(TIPOS))
    ap.add_argument("--lista", action="store_true")
    a = ap.parse_args()
    if a.lista:
        lista()
        return

    creditos_ruta = os.path.join(BANCO, "creditos.csv")
    os.makedirs(BANCO, exist_ok=True)
    vistos = set()
    if os.path.exists(creditos_ruta):
        with open(creditos_ruta, encoding="utf-8") as f:
            vistos = {fila["id"] for fila in csv.DictReader(f)}
    nuevo = not os.path.exists(creditos_ruta)
    with open(creditos_ruta, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if nuevo:
            w.writerow(["id", "tipo", "archivo", "titulo", "autor", "licencia", "fuente", "pagina"])
        for tipo in a.tipos or TIPOS:
            consultas, dmin, dmax = TIPOS[tipo]
            carpeta = os.path.join(BANCO, tipo)
            os.makedirs(carpeta, exist_ok=True)
            falta = a.por_tipo - len(archivos(tipo))
            print(f"{tipo}: ", end="", flush=True)
            for consulta in consultas:
                if falta <= 0:
                    break
                try:
                    resultados = buscar(consulta)
                except (urllib.error.URLError, TimeoutError) as e:
                    print(f"(búsqueda '{consulta}' falló: {e}) ", end="")
                    continue
                fallos = 0
                for r in resultados:
                    if falta <= 0 or fallos >= 4:   # el servidor está rechazando: otra búsqueda
                        break
                    dur = (r.get("duration") or 0) / 1000
                    if r["id"] in vistos or r.get("license") != "cc0" or not (dmin <= dur <= dmax):
                        continue
                    ext = (r.get("filetype") or "mp3").lower()
                    ruta = os.path.join(carpeta, f"{r['id'][:8]}.{ext}")
                    time.sleep(0.5)              # sin prisas: no saturar el servidor
                    if not bajar(r["url"], ruta) or not valido(ruta):
                        if os.path.exists(ruta):
                            os.remove(ruta)
                        fallos += 1
                        print("x", end="", flush=True)
                        continue
                    fallos = 0
                    vistos.add(r["id"])
                    w.writerow([r["id"], tipo, os.path.relpath(ruta, RAIZ), r.get("title"),
                                r.get("creator"), "CC0", r.get("source"), r.get("foreign_landing_url")])
                    f.flush()
                    falta -= 1
                    print("·", end="", flush=True)
            print(f" {len(archivos(tipo))}")
            f.flush()
    print()
    lista()


if __name__ == "__main__":
    main()
