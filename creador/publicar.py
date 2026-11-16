"""Programa las publicaciones del canal y recoge sus estadísticas (Upload-Post).

    python3 creador/publicar.py estado                 # ¿está todo conectado?
    python3 creador/publicar.py programar golden_gate  # sube el video y lo programa
    python3 creador/publicar.py metricas               # actualiza las estadísticas

Configuración en .env:
    UPLOAD_POST_API_KEY=...        clave de app.upload-post.com -> API Keys
    UPLOAD_POST_PERFIL=...         nombre del perfil creado en Upload-Post
    CANAL_ZONA=America/Bogota      zona horaria de las publicaciones
    CANAL_HORAS=18:30              horas de publicación, separadas por comas
    CANAL_REDES=tiktok,instagram,youtube,facebook

Cada video necesita salida/<nombre>/publicar.json (lo escribe el comando /final):
    {"titulo": "...", "descripcion": "...", "hashtags": ["ingenieria", ...],
     "comentario": "¿Qué construimos mañana?", "tema": "puentes", "gancho": "pregunta"}

El registro de lo publicado queda en canal/publicaciones.json y las
estadísticas en canal/metricas.json.
"""
import argparse
import datetime as dt
import json
import os
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from zoneinfo import ZoneInfo

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)
import voz  # noqa: E402  (solo para leer el .env)

API = os.environ.get("UPLOAD_POST_URL", "https://api.upload-post.com/api")
CANAL = os.path.join(RAIZ, "canal")
REGISTRO = os.path.join(CANAL, "publicaciones.json")
METRICAS = os.path.join(CANAL, "metricas.json")


def cfg():
    voz.cargar_env()
    return {
        "clave": os.environ.get("UPLOAD_POST_API_KEY", ""),
        "perfil": os.environ.get("UPLOAD_POST_PERFIL", ""),
        "zona": os.environ.get("CANAL_ZONA", "America/Bogota"),
        "horas": [h.strip() for h in os.environ.get("CANAL_HORAS", "18:30").split(",") if h.strip()],
        "redes": [r.strip() for r in os.environ.get(
            "CANAL_REDES", "tiktok,instagram,youtube,facebook").split(",") if r.strip()],
    }


def leer(ruta, defecto):
    if os.path.exists(ruta):
        with open(ruta, encoding="utf-8") as f:
            return json.load(f)
    return defecto


def guardar(ruta, datos):
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=1)


def pedir(ruta, **params):
    c = cfg()
    url = API + ruta + ("?" + urllib.parse.urlencode(params) if params else "")
    req = urllib.request.Request(url, headers={"Authorization": "Apikey " + c["clave"]})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Upload-Post respondió {e.code}: {e.read().decode()[:300]}")


def exigir_config():
    c = cfg()
    if not c["clave"]:
        sys.exit("Falta UPLOAD_POST_API_KEY en .env (créala en app.upload-post.com -> API Keys).")
    if not c["perfil"]:
        sys.exit("Falta UPLOAD_POST_PERFIL en .env. Ejecuta: python3 creador/publicar.py estado")
    return c


# --- estado -------------------------------------------------------------------

def estado(_a):
    c = cfg()
    if not c["clave"]:
        sys.exit("Falta UPLOAD_POST_API_KEY en .env (créala en app.upload-post.com -> API Keys).")
    perfiles = pedir("/uploadposts/users").get("profiles", [])
    if not perfiles:
        sys.exit("Tu cuenta de Upload-Post no tiene perfiles. Crea uno en app.upload-post.com "
                 "(Manage Users) y conecta ahí tus redes.")
    print("Perfiles en Upload-Post:")
    for p in perfiles:
        cuentas = p.get("social_accounts") or {}
        conectadas = [red for red, dato in cuentas.items() if dato]
        marca = "  <- el del canal" if p.get("username") == c["perfil"] else ""
        print(f"  - {p.get('username')}: {', '.join(conectadas) or 'sin redes conectadas'}{marca}")
        if p.get("username") == c["perfil"]:
            faltan = [r for r in c["redes"] if r not in conectadas]
            if faltan:
                print(f"    ⚠️  Faltan por conectar: {', '.join(faltan)}")
    if not c["perfil"]:
        print("\nElige uno y añade al .env:  UPLOAD_POST_PERFIL=<nombre del perfil>")
        return
    if "facebook" in c["redes"]:
        try:
            paginas = pedir("/uploadposts/facebook/pages", profile=c["perfil"]).get("pages", [])
            for pg in paginas:
                print(f"  Página de Facebook: {pg.get('name')} (id {pg.get('id')})")
            if not paginas:
                print("  ⚠️  No hay ninguna página de Facebook conectada.")
        except RuntimeError as e:
            print("  ⚠️  No pude leer las páginas de Facebook:", str(e)[:150])
    print(f"\nHorario: todos los días a las {', '.join(c['horas'])} ({c['zona']})")


# --- programar ------------------------------------------------------------------

def siguiente_hueco(c, registro):
    """Primera hora libre del horario del canal, después de lo ya programado."""
    zona = ZoneInfo(c["zona"])
    ocupadas = {r["fecha"] for r in registro}
    desde = dt.datetime.now(zona) + dt.timedelta(minutes=30)
    dia = desde.date()
    for _ in range(400):
        for hora in sorted(c["horas"]):
            h, m = (int(x) for x in hora.split(":"))
            momento = dt.datetime(dia.year, dia.month, dia.day, h, m, tzinfo=zona)
            texto = momento.strftime("%Y-%m-%dT%H:%M:00")
            if momento > desde and texto not in ocupadas:
                return texto
        dia += dt.timedelta(days=1)
    raise RuntimeError("No encontré hueco libre")


def datos_del_video(nombre):
    """Lo que hace falta saber del video para analizarlo después."""
    out = {}
    lt = leer(os.path.join(RAIZ, "salida", nombre, "linea_tiempo_es.json"), None)
    if lt:
        out["duracion"] = lt["duracion_total"]
        out["escenas"] = len(lt["escenas"])
        out["palabras"] = sum(len(e.get("palabras", [])) for e in lt["escenas"])
        out["duracion_gancho"] = lt["escenas"][0]["duracion"]
        out["texto_gancho"] = " ".join(p[0] for p in lt["escenas"][0].get("palabras", []))
    return out


def programar(a):
    c = exigir_config()
    carpeta = os.path.join(RAIZ, "salida", a.nombre)
    video = a.video or os.path.join(carpeta, "video_es_alta.mp4")
    if not os.path.exists(video):
        sys.exit(f"No encuentro {video}. Haz primero el render final (/final {a.nombre}).")
    textos = leer(os.path.join(carpeta, "publicar.json"), None)
    if not textos:
        sys.exit(f"Falta {carpeta}/publicar.json con título, descripción y hashtags.")

    registro = leer(REGISTRO, [])
    if any(r["nombre"] == a.nombre for r in registro) and not a.repetir:
        sys.exit(f"'{a.nombre}' ya está programado. Usa --repetir si de verdad quieres subirlo otra vez.")
    fecha = a.fecha.replace(" ", "T") + (":00" if len(a.fecha) == 16 else "") if a.fecha \
        else siguiente_hueco(c, registro)
    redes = a.redes or c["redes"]

    etiquetas = " ".join("#" + h.lstrip("#") for h in textos.get("hashtags", []))
    pie = f"{textos['titulo']}\n\n{textos.get('descripcion', '')}\n\n{etiquetas}".strip()
    id_externo = f"{a.nombre}-{fecha[:10]}"
    campos = [
        ("user", c["perfil"]), ("title", textos["titulo"][:100]), ("description", pie),
        ("scheduled_date", fecha), ("timezone", c["zona"]), ("external_id", id_externo),
        ("is_ai_generated", "true"),
        ("tiktok_title", pie[:2200]), ("instagram_title", pie[:2200]), ("facebook_title", pie),
        ("youtube_title", (textos["titulo"][:90] + " #shorts")), ("youtube_description", pie),
        ("privacyStatus", "public"), ("selfDeclaredMadeForKids", "false"), ("categoryId", "28"),
        ("media_type", "REELS"), ("facebook_media_type", "REELS"), ("facebook_is_ai_generated", "true"),
    ]
    campos += [("platform[]", r) for r in redes]
    campos += [("tags[]", h.lstrip("#")) for h in textos.get("hashtags", [])]
    if textos.get("comentario"):
        campos.append(("first_comment", textos["comentario"]))
    if "facebook" in redes:
        pagina = os.environ.get("FACEBOOK_PAGE_ID")
        if not pagina:
            paginas = pedir("/uploadposts/facebook/pages", profile=c["perfil"]).get("pages", [])
            if not paginas:
                sys.exit("No hay página de Facebook conectada en Upload-Post (o quita facebook de CANAL_REDES).")
            pagina = paginas[0]["id"]
        campos.append(("facebook_page_id", str(pagina)))

    print(f"Programando '{textos['titulo']}'")
    print(f"  Fecha: {fecha} ({c['zona']})   Redes: {', '.join(redes)}")
    if a.simular:
        print("  (simulación: no se ha subido nada)")
        return

    # curl sube el archivo sin cargarlo en memoria; la clave va por la entrada
    # estándar para que no aparezca en la lista de procesos.
    cmd = ["curl", "-sS", "--config", "-", "-X", "POST", API + "/upload", "-F", f"video=@{video}"]
    for k, v in campos:
        cmd += ["--form-string", f"{k}={v}"]
    r = subprocess.run(cmd, input=f'header = "Authorization: Apikey {c["clave"]}"\n',
                       capture_output=True, text=True)
    try:
        resp = json.loads(r.stdout)
    except json.JSONDecodeError:
        sys.exit(f"Upload-Post no respondió como se esperaba: {(r.stdout or r.stderr)[:400]}")
    if not resp.get("success"):
        sys.exit(f"❌ Upload-Post rechazó la publicación: {json.dumps(resp, ensure_ascii=False)[:500]}")

    registro.append({"nombre": a.nombre, "fecha": fecha, "zona": c["zona"], "redes": redes,
                     "id_externo": id_externo, "job_id": resp.get("job_id"),
                     "request_id": resp.get("request_id"), "titulo": textos["titulo"],
                     "tema": textos.get("tema"), "gancho": textos.get("gancho"),
                     **datos_del_video(a.nombre)})
    guardar(REGISTRO, registro)
    print(f"✅ Programado para el {fecha}. Puedes verlo en app.upload-post.com (calendario).")


# --- métricas ----------------------------------------------------------------------

def metricas(_a):
    c = exigir_config()
    registro = leer(REGISTRO, [])
    datos = leer(METRICAS, {})
    ahora = dt.datetime.now(ZoneInfo(c["zona"]))
    hoy = ahora.strftime("%Y-%m-%d")
    for r in registro:
        momento = dt.datetime.fromisoformat(r["fecha"]).replace(tzinfo=ZoneInfo(r.get("zona", c["zona"])))
        if momento > ahora:
            continue
        try:
            filas = pedir("/uploadposts/history", external_id=r["id_externo"], limit=20).get("history", [])
        except RuntimeError as e:
            print(f"  {r['nombre']}: {str(e)[:150]}")
            continue
        video = datos.setdefault(r["nombre"], {"titulo": r["titulo"], "fecha": r["fecha"], "redes": {}})
        for fila in filas:
            red = fila.get("platform")
            if not fila.get("success"):
                video["redes"].setdefault(red, {})["error"] = fila.get("error_message")
                continue
            pid = fila.get("platform_post_id")
            pid = pid[0] if isinstance(pid, list) and pid else pid
            if not pid:
                continue
            entrada = video["redes"].setdefault(red, {})
            entrada.update({"url": fila.get("post_url"), "post_id": pid})
            try:
                resp = pedir("/uploadposts/post-analytics", platform_post_id=pid, platform=red, user=c["perfil"])
                m = (resp.get("platforms", {}).get(red, {}) or {})
                if m.get("post_metrics"):
                    entrada["metricas"] = m["post_metrics"]
                    entrada.setdefault("historial", {})[hoy] = {
                        k: v for k, v in m["post_metrics"].items() if isinstance(v, (int, float))}
                elif m.get("post_metrics_error"):
                    entrada["error"] = m["post_metrics_error"]
            except RuntimeError as e:
                entrada["error"] = str(e)[:200]
    guardar(METRICAS, datos)

    print(f"{'Video':<26}{'Red':<11}{'Vistas':>9}{'Likes':>8}{'Coment.':>9}{'Compart.':>10}{'Vio todo':>10}")
    for nombre, video in datos.items():
        for red, e in sorted(video["redes"].items()):
            m = e.get("metricas") or {}
            completo = m.get("full_video_watched_rate")
            print(f"{nombre[:25]:<26}{red:<11}{m.get('views', '-'):>9}{m.get('likes', '-'):>8}"
                  f"{m.get('comments', '-'):>9}{m.get('shares', '-'):>10}"
                  f"{(f'{completo * 100:.0f} %' if isinstance(completo, (int, float)) else '-'):>10}")
    if not datos:
        print("(todavía no hay videos publicados)")
    print(f"\nDatos completos en {METRICAS}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="orden", required=True)
    sub.add_parser("estado").set_defaults(f=estado)
    p = sub.add_parser("programar")
    p.add_argument("nombre")
    p.add_argument("--fecha", help='"2026-11-20 18:30" (si no, el siguiente hueco libre)')
    p.add_argument("--redes", nargs="+")
    p.add_argument("--video", help="otro archivo de video (por defecto, el de calidad alta)")
    p.add_argument("--repetir", action="store_true")
    p.add_argument("--simular", action="store_true", help="muestra lo que haría sin subir nada")
    p.set_defaults(f=programar)
    sub.add_parser("metricas").set_defaults(f=metricas)
    a = ap.parse_args()
    try:
        a.f(a)
    except RuntimeError as e:
        sys.exit("❌ " + str(e))


if __name__ == "__main__":
    main()
