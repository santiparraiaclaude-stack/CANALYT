"""Produce un video completo de "Constrúyelo tú".

    python3 creador/pipeline.py golden_gate                # vista previa rápida
    python3 creador/pipeline.py golden_gate --calidad alta --gpu
    python3 creador/pipeline.py golden_gate --idiomas es en --musica musica.mp3
    python3 creador/pipeline.py golden_gate --frame 400    # solo una imagen de prueba

Resultado en salida/<estructura>/video_<idioma>.mp4
"""
import argparse
import importlib.util
import json
import os
import shutil
import subprocess
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)

import montar  # noqa: E402
import voz  # noqa: E402

FPS = {"baja": 24, "media": 30, "alta": 30}
DUR_MIN = {"gancho": 3.0, "paso": 3.5, "final": 4.0}
PAUSA = 0.5   # respiro tras cada frase


def buscar_blender():
    for c in (os.environ.get("BLENDER_PATH"), shutil.which("blender"),
              "/Applications/Blender.app/Contents/MacOS/Blender",
              r"C:\Program Files\Blender Foundation\Blender 4.2\blender.exe"):
        if c and os.path.exists(c):
            return c
    sys.exit("No encuentro Blender. Instálalo (setup/) o define BLENDER_PATH.")


def cargar(nombre):
    ruta = os.path.join(AQUI, "estructuras", f"{nombre}.py")
    if not os.path.exists(ruta):
        sys.exit(f"No existe {ruta}")
    spec = importlib.util.spec_from_file_location("estructura", ruta)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod, ruta


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("estructura")
    ap.add_argument("--calidad", default="baja", choices=FPS)
    ap.add_argument("--idiomas", nargs="+", default=["es"])
    ap.add_argument("--gpu", action="store_true")
    ap.add_argument("--musica")
    ap.add_argument("--frame", type=int)
    ap.add_argument("--sin-voz", action="store_true")
    a = ap.parse_args()
    voz.cargar_env()
    montar.FUENTE = os.environ.get("CREADOR_FUENTE", montar.FUENTE)

    est, ruta_est = cargar(a.estructura)
    out = os.path.join(RAIZ, "salida", a.estructura)
    carpeta_voz = os.path.join(out, "voz")
    carpeta_frames = os.path.join(out, f"frames_{a.calidad}")
    os.makedirs(carpeta_voz, exist_ok=True)

    # 1) Segmentos y voz ------------------------------------------------------
    segmentos = [{"tipo": "gancho", "texto": est.GANCHO}]
    segmentos += [{"tipo": "paso", "texto": {k: v for k, v in p.items() if k != "piezas"}}
                  for p in est.PASOS]
    segmentos.append({"tipo": "final", "texto": est.FINAL})

    usar_voz = not a.sin_voz and voz.hay_clave()
    if not usar_voz:
        print("[creador] Sin ELEVENLABS_API_KEY: el video saldrá sin narración.")
    t = 0.0
    for i, s in enumerate(segmentos):
        dur = DUR_MIN[s["tipo"]]
        for idioma in a.idiomas:
            if usar_voz:
                print(f"[creador] Voz {idioma} {i + 1}/{len(segmentos)}")
                d = voz.generar(s["texto"][idioma], idioma,
                                os.path.join(carpeta_voz, f"{idioma}_{i:02d}.mp3"))
                dur = max(dur, d + PAUSA)
        s["inicio"], s["duracion"] = round(t, 3), round(dur, 3)
        t += dur
    lt = {"segmentos": segmentos, "duracion_total": round(t, 3)}
    ruta_lt = os.path.join(out, "linea_tiempo.json")
    with open(ruta_lt, "w", encoding="utf-8") as f:
        json.dump(lt, f, ensure_ascii=False, indent=2)
    print(f"[creador] Duración total: {t:.1f} s")

    # 2) Render 3D ------------------------------------------------------------
    cmd = [buscar_blender(), "-b", "--factory-startup",
           "-P", os.path.join(AQUI, "blender_construir.py"), "--",
           "--estructura", ruta_est, "--linea-tiempo", ruta_lt,
           "--salida", carpeta_frames, "--calidad", a.calidad]
    if a.gpu:
        cmd.append("--gpu")
    if a.frame:
        cmd += ["--frame", str(a.frame)]
    print("[creador] Renderizando con Blender... (puede tardar)")
    subprocess.run(cmd, check=True)
    if a.frame:
        print(f"[creador] Imagen de prueba en {carpeta_frames}/prueba_{a.frame:04d}.png")
        return

    # 3) Montaje por idioma ---------------------------------------------------
    for idioma in a.idiomas:
        ass = os.path.join(out, f"subs_{idioma}.ass")
        wav = os.path.join(out, f"audio_{idioma}.wav")
        mp4 = os.path.join(out, f"video_{idioma}_{a.calidad}.mp4")
        montar.subtitulos_ass(lt, idioma, est.TITULO[idioma], ass)
        montar.pista_audio(lt, idioma, carpeta_voz, wav, a.musica)
        montar.video_final(carpeta_frames, FPS[a.calidad], wav, ass, mp4)
        print(f"[creador] ✅ Video listo: {mp4}")


if __name__ == "__main__":
    main()
