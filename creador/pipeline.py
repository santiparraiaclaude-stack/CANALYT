"""Produce un video completo de "Constrúyelo tú".

    python3 creador/pipeline.py golden_gate --ver 2 10 30      # imágenes sueltas (segundos)
    python3 creador/pipeline.py golden_gate --gpu              # vista previa rápida
    python3 creador/pipeline.py golden_gate --calidad alta --gpu
    python3 creador/pipeline.py golden_gate --idiomas es en --musica musica.mp3

Resultado: salida/<estructura>/video_<idioma>_<calidad>.mp4

Si solo cambias la música o los sonidos, no se vuelve a renderizar: las
imágenes se reutilizan mientras no cambien el guion, la voz ni la escena.
"""
import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)

import guion  # noqa: E402
import montar  # noqa: E402
import sonido  # noqa: E402
import voz  # noqa: E402

FPS = {"boceto": 12, "baja": 24, "media": 30, "alta": 30}
PAUSA = 0.35          # respiro tras cada frase
DUR_MINIMA = 2.2


def buscar_blender():
    for c in (os.environ.get("BLENDER_PATH"), shutil.which("blender"),
              "/Applications/Blender.app/Contents/MacOS/Blender",
              r"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe",
              r"C:\Program Files\Blender Foundation\Blender 4.2\blender.exe"):
        if c and os.path.exists(c):
            return c
    sys.exit("No encuentro Blender. Instálalo (setup/) o define BLENDER_PATH en .env")


def cargar(nombre):
    ruta = os.path.join(AQUI, "estructuras", f"{nombre}.py")
    if not os.path.exists(ruta):
        sys.exit(f"No existe {ruta}")
    spec = importlib.util.spec_from_file_location("estructura", ruta)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod, ruta


def huella_render(ruta_est, lt, calidad):
    h = hashlib.sha1()
    for ruta in (ruta_est, os.path.join(AQUI, "piezas.py"), os.path.join(AQUI, "guion.py"),
                 os.path.join(AQUI, "blender_construir.py")):
        with open(ruta, "rb") as f:
            h.update(f.read())
    h.update(json.dumps(lt, sort_keys=True).encode())
    h.update(calidad.encode())
    return h.hexdigest()


# Nuestros tipos de sonido -> los de la skill Real SFX (references/typed-cues.md)
TIPOS_REAL_SFX = {"golpe": ("hit", 0.8), "pop": ("pop", 0.7), "subida": ("whoosh", 0.5),
                  "paso": ("wipe", 0.9), "splash": ("water", 1.0), "crash": ("hit", 1.2),
                  "alerta": ("error", 0.8), "tada": ("success", 1.0)}


def escribir_cues(sonidos, ruta):
    """Lista de eventos de sonido con su segundo exacto, en el formato de Real SFX."""
    cues, ultimo = [], {}
    for s in sorted(sonidos, key=lambda x: x["t"]):
        tipo, g = TIPOS_REAL_SFX.get(s["tipo"], (None, 1.0))
        if not tipo or s["t"] - ultimo.get(tipo, -9) < 0.12:
            continue
        ultimo[tipo] = s["t"]
        cue = {"t": round(s["t"], 3), "type": tipo, "g": g}
        if tipo == "whoosh":
            cue["len"] = 0.4
        cues.append(cue)
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump({"cues": cues}, f, indent=1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("estructura")
    ap.add_argument("--calidad", default="baja", choices=FPS)
    ap.add_argument("--idiomas", nargs="+", default=["es"])
    ap.add_argument("--gpu", action="store_true")
    ap.add_argument("--musica")
    ap.add_argument("--ver", nargs="+", type=float, metavar="SEG",
                    help="renderiza solo imágenes sueltas en esos segundos")
    ap.add_argument("--sin-voz", action="store_true")
    ap.add_argument("--guardar-blend", action="store_true")
    ap.add_argument("--estilo", help="maqueta, caricatura, arcilla o plano (si no, el ESTILO de la estructura)")
    ap.add_argument("--sin-efectos", action="store_true",
                    help="solo voz (y música): para ponerle los efectos con otra herramienta (Real SFX)")
    a = ap.parse_args()
    voz.cargar_env()
    if a.sin_voz:
        os.environ["ELEVENLABS_API_KEY"] = ""

    est, ruta_est = cargar(a.estructura)
    estilo = a.estilo or getattr(est, "ESTILO", "maqueta")
    print(f"[creador] Estilo visual: {estilo}")
    out = os.path.join(RAIZ, "salida", a.estructura)
    os.makedirs(out, exist_ok=True)
    if not voz.hay_clave():
        print("[creador] Sin clave de ElevenLabs: el video saldrá sin narración.")

    for idioma in a.idiomas:
        # 1) Voz y línea de tiempo --------------------------------------------
        escenas, mp3s, t = [], [], 0.0
        textos = guion.textos_de(est, idioma)
        for i, texto in enumerate(textos):
            if voz.hay_clave():
                print(f"[creador] Voz {idioma} {i + 1}/{len(textos)}")
            mp3, dur, palabras = voz.generar(texto, idioma, os.path.join(out, "voz"))
            dur = max(DUR_MINIMA, dur + voz.DESFASE + PAUSA)
            if est.ESCENAS[i].get("final"):
                dur = max(dur, 5.0)
            escenas.append({"inicio": round(t, 3), "duracion": round(dur, 3), "palabras": palabras})
            mp3s.append(mp3)
            t += dur
        lt = {"idioma": idioma, "escenas": escenas, "duracion_total": round(t, 3)}
        ruta_lt = os.path.join(out, f"linea_tiempo_{idioma}.json")
        with open(ruta_lt, "w", encoding="utf-8") as f:
            json.dump(lt, f, ensure_ascii=False, indent=1)
        print(f"[creador] Duración ({idioma}): {t:.1f} s")

        # 2) Render 3D ----------------------------------------------------------
        frames = os.path.join(out, f"frames_{a.calidad}_{idioma}")
        cmd = [buscar_blender(), "-b", "--factory-startup",
               "-P", os.path.join(AQUI, "blender_construir.py"), "--",
               "--estructura", ruta_est, "--linea-tiempo", ruta_lt,
               "--salida", frames, "--calidad", a.calidad, "--estilo", estilo]
        if a.gpu:
            cmd.append("--gpu")
        if a.guardar_blend:
            cmd.append("--guardar-blend")
        if a.ver:
            cmd += ["--ver", ",".join(str(s) for s in a.ver)]
            subprocess.run(cmd, check=True)
            print(f"[creador] Imágenes de prueba en {frames}/ (ver_*.png)")
            continue
        huella = huella_render(ruta_est, lt, a.calidad + estilo)
        marca = os.path.join(frames, "huella.txt")
        hecho = os.path.exists(marca) and open(marca).read() == huella
        if hecho:
            print("[creador] La escena no cambió: reutilizo las imágenes ya renderizadas")
        else:
            if os.path.isdir(frames):
                shutil.rmtree(frames)
            print("[creador] Renderizando con Blender... (puede tardar)")
            subprocess.run(cmd, check=True)
            with open(marca, "w") as f:
                f.write(huella)

        # 3) Sonido y montaje ---------------------------------------------------
        plan = guion.planificar(est, lt, idioma)
        efectos = os.path.join(out, f"_efectos_{idioma}.wav")
        sonido.generar([] if a.sin_efectos else plan["sonidos"], lt["duracion_total"], efectos)
        escribir_cues(plan["sonidos"], os.path.join(out, f"cues_{idioma}.json"))
        wav = os.path.join(out, f"audio_{idioma}.wav")
        montar.pista_audio(escenas, mp3s, efectos, wav, a.musica, voz.DESFASE)
        mp4 = os.path.join(out, f"video_{idioma}_{a.calidad}.mp4")
        montar.video_final(frames, FPS[a.calidad], wav, mp4)
        os.remove(efectos)
        print(f"[creador] ✅ Video listo: {mp4}")


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as e:
        texto = str(e)
        if "paid_plan_required" in texto:
            sys.exit("\n❌ ElevenLabs: esa voz es de la biblioteca y el plan gratis no deja usarla "
                     "desde aquí.\n   Opciones: (1) pasar al plan Starter en elevenlabs.io -> Subscription, o\n"
                     "   (2) usar una voz de fábrica: python3 creador/probar_voces.py")
        if "voice_not_found" in texto:
            sys.exit("\n❌ ElevenLabs no encuentra esa voz. Añádela a 'My Voices' en elevenlabs.io "
                     "o elige otra con: python3 creador/probar_voces.py")
        if "quota_exceeded" in texto:
            sys.exit("\n❌ Se acabaron los caracteres de tu plan de ElevenLabs este mes.")
        sys.exit("\n❌ " + texto)
