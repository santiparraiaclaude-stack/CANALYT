"""Une todo: voz + efectos (+ música) y las imágenes en un mp4 vertical."""
import os
import subprocess


def _ff(*args):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *args], check=True)


def pista_audio(escenas, mp3s, ruta_efectos, ruta_wav, musica=None, desfase=0.12):
    """escenas: [{"duracion"}], mp3s: ruta o None por escena (misma longitud)."""
    carpeta = os.path.dirname(ruta_wav)
    partes = []
    for i, (esc, mp3) in enumerate(zip(escenas, mp3s)):
        parte = os.path.join(carpeta, f"_voz_{i:02d}.wav")
        dur = f"{esc['duracion']:.3f}"
        ms = int(desfase * 1000)
        if mp3:
            _ff("-i", mp3, "-af", f"adelay={ms}|{ms},apad=whole_dur={dur}", "-t", dur,
                "-ar", "44100", "-ac", "2", parte)
        else:
            _ff("-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-t", dur, parte)
        partes.append(parte)
    lista = os.path.join(carpeta, "_voz_lista.txt")
    with open(lista, "w") as f:
        f.writelines(f"file '{os.path.abspath(p)}'\n" for p in partes)
    voz_wav = os.path.join(carpeta, "_voz.wav")
    _ff("-f", "concat", "-safe", "0", "-i", lista, "-c", "copy", voz_wav)

    entradas = ["-i", voz_wav, "-i", ruta_efectos]
    filtros = "[0:a]volume=1.0[v];[1:a]volume=0.55,aformat=channel_layouts=stereo[e]"
    mezcla = "[v][e]"
    if musica:
        entradas += ["-stream_loop", "-1", "-i", musica]
        filtros += ";[2:a]volume=0.14[m]"
        mezcla += "[m]"
    n = 3 if musica else 2
    filtros += f";{mezcla}amix=inputs={n}:duration=first:normalize=0,alimiter=limit=0.95[a]"
    _ff(*entradas, "-filter_complex", filtros, "-map", "[a]", "-ar", "44100", ruta_wav)
    for p in partes + [lista, voz_wav]:
        os.remove(p)


def video_final(carpeta_frames, fps, ruta_wav, ruta_mp4):
    _ff("-framerate", str(fps), "-i", os.path.join(carpeta_frames, "%04d.png"),
        "-i", ruta_wav, "-vf", "scale=1080:1920:flags=lanczos",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", ruta_mp4)
