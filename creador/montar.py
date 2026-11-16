"""Monta el video final: frames + voz + subtítulos (+ música opcional)."""
import os
import subprocess

FUENTE = os.environ.get("CREADOR_FUENTE", "Inter Black")


def _t(seg):
    h = int(seg // 3600)
    m = int(seg % 3600 // 60)
    s = seg % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def _escapar(texto):
    return texto.replace("\\", "").replace("{", "(").replace("}", ")").replace("\n", "\\N")


def subtitulos_ass(lt, idioma, titulo, ruta):
    cab = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Titulo,{FUENTE},92,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,1,0,0,0,100,100,0,0,1,7,4,8,60,60,230,1
Style: Texto,{FUENTE},66,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,1,0,0,0,100,100,0,0,1,6,3,2,80,80,330,1
Style: Paso,{FUENTE},50,&H0000D7FF,&H00FFFFFF,&H00000000,&H64000000,1,0,0,0,100,100,2,0,1,5,2,8,60,60,160,1
Style: Final,{FUENTE},84,&H0000D7FF,&H00FFFFFF,&H00000000,&H64000000,1,0,0,0,100,100,0,0,1,7,4,5,70,70,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    pop = r"{\fad(120,120)\fscx70\fscy70\t(0,180,\fscx105\fscy105)\t(180,280,\fscx100\fscy100)}"
    lineas = []
    segs = lt["segmentos"]
    n_pasos = len(segs) - 2
    paso_txt = "PASO" if idioma == "es" else "STEP"
    for i, s in enumerate(segs):
        ini, fin = s["inicio"], s["inicio"] + s["duracion"]
        texto = _escapar(s["texto"][idioma])
        if s["tipo"] == "gancho":
            lineas.append(f"Dialogue: 1,{_t(ini)},{_t(fin)},Titulo,,0,0,0,,{pop}{_escapar(titulo)}")
            lineas.append(f"Dialogue: 0,{_t(ini + 0.3)},{_t(fin)},Texto,,0,0,0,,{pop}{texto}")
        elif s["tipo"] == "paso":
            lineas.append(f"Dialogue: 1,{_t(ini)},{_t(fin)},Paso,,0,0,0,,{pop}{paso_txt} {i}/{n_pasos}")
            lineas.append(f"Dialogue: 0,{_t(ini)},{_t(fin)},Texto,,0,0,0,,{pop}{texto}")
        else:
            lineas.append(f"Dialogue: 0,{_t(ini)},{_t(fin + 0.5)},Final,,0,0,0,,{pop}{texto}")
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(cab + "\n".join(lineas) + "\n")


def pista_audio(lt, idioma, carpeta_voz, ruta_wav, musica=None):
    """Une las voces de cada segmento respetando la línea de tiempo."""
    partes = []
    for i, s in enumerate(lt["segmentos"]):
        mp3 = os.path.join(carpeta_voz, f"{idioma}_{i:02d}.mp3")
        parte = os.path.join(carpeta_voz, f"_{idioma}_{i:02d}.wav")
        dur = f"{s['duracion']:.3f}"
        if os.path.exists(mp3):
            cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", mp3,
                   "-af", f"adelay=150|150,apad=whole_dur={dur}", "-t", dur,
                   "-ar", "44100", "-ac", "2", parte]
        else:
            cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi",
                   "-i", "anullsrc=r=44100:cl=stereo", "-t", dur, parte]
        subprocess.run(cmd, check=True)
        partes.append(parte)
    lista = os.path.join(carpeta_voz, f"_{idioma}_lista.txt")
    with open(lista, "w") as f:
        f.writelines(f"file '{os.path.abspath(p)}'\n" for p in partes)
    voz_wav = ruta_wav if not musica else ruta_wav + ".voz.wav"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
                    "-i", lista, "-c", "copy", voz_wav], check=True)
    if musica:
        subprocess.run([
            "ffmpeg", "-y", "-loglevel", "error", "-i", voz_wav, "-stream_loop", "-1", "-i", musica,
            "-filter_complex",
            "[1:a]volume=0.18[m];[0:a][m]amix=inputs=2:duration=first:dropout_transition=0[a]",
            "-map", "[a]", ruta_wav], check=True)


def ffmpeg_tiene_libass():
    if os.environ.get("CREADOR_SIN_LIBASS"):
        return False
    out = subprocess.run(["ffmpeg", "-hide_banner", "-filters"],
                         capture_output=True, text=True).stdout
    return any(l.split()[1:2] == ["ass"] for l in out.splitlines() if l.strip())


def textos_en_pantalla(lt, idioma, titulo):
    """Lista de (texto, estilo, inicio, fin): lo mismo que los subtítulos .ass."""
    segs = lt["segmentos"]
    n_pasos = len(segs) - 2
    paso_txt = "PASO" if idioma == "es" else "STEP"
    out = []
    for i, s in enumerate(segs):
        ini, fin = s["inicio"], s["inicio"] + s["duracion"]
        texto = s["texto"][idioma]
        if s["tipo"] == "gancho":
            out.append((titulo, "titulo", ini, fin))
            out.append((texto, "texto", ini + 0.3, fin))
        elif s["tipo"] == "paso":
            out.append((f"{paso_txt} {i}/{n_pasos}", "paso", ini, fin))
            out.append((texto, "texto", ini, fin))
        else:
            out.append((texto, "final", ini, fin + 0.5))
    return out


def video_final(carpeta_frames, fps, ruta_wav, ruta_ass, ruta_mp4,
                lt=None, idioma="es", titulo="", blender=None):
    entrada = ["-framerate", str(fps), "-i", os.path.join(carpeta_frames, "%04d.png"),
               "-i", ruta_wav]
    salida = ["-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
              "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", ruta_mp4]

    if ffmpeg_tiene_libass():
        filtro = f"scale=1080:1920:flags=lanczos,ass='{ruta_ass}'"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *entrada, "-vf", filtro, *salida],
                       check=True)
        return

    # Plan B: textos dibujados con Blender y superpuestos con overlay
    print("[creador] ffmpeg sin libass: dibujando los textos con Blender")
    carpeta = os.path.join(os.path.dirname(ruta_mp4), f"textos_{idioma}")
    os.makedirs(carpeta, exist_ok=True)
    textos = textos_en_pantalla(lt, idioma, titulo)
    trabajos = [{"texto": t, "estilo": e, "archivo": os.path.join(carpeta, f"{k:02d}.png")}
                for k, (t, e, _, _) in enumerate(textos)]
    ruta_json = os.path.join(carpeta, "textos.json")
    import json
    with open(ruta_json, "w", encoding="utf-8") as f:
        json.dump(trabajos, f, ensure_ascii=False)
    aqui = os.path.dirname(os.path.abspath(__file__))
    subprocess.run([blender, "-b", "--factory-startup",
                    "-P", os.path.join(aqui, "blender_textos.py"), "--", ruta_json],
                   check=True, stdout=subprocess.DEVNULL)

    for t in trabajos:
        entrada += ["-loop", "1", "-framerate", str(fps), "-i", t["archivo"]]
    cadena = ["[0:v]scale=1080:1920:flags=lanczos[v0]"]
    for k, (_, _, ini, fin) in enumerate(textos):
        cadena.append(f"[v{k}][{k + 2}:v]overlay=0:0:shortest=1:"
                      f"enable='between(t,{ini:.3f},{fin:.3f})'[v{k + 1}]")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *entrada,
                    "-filter_complex", ";".join(cadena), "-map", f"[v{len(textos)}]",
                    "-map", "1:a", *salida], check=True)
