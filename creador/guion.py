"""Convierte una estructura (lista de ESCENAS) en un plan con tiempos exactos.

Python puro: lo usan Blender (para animar) y sonido.py (para los efectos).

Una estructura define:

    TITULO   = {"es": "...", "en": "..."}      pregunta que se ve al principio
    AMBIENTE = "ambiente"                      (opcional) sonido de fondo todo el video
    CAMARA   = {"lente": 24}
    ESCENARIO = [piezas con anim="ninguna"]
    ESCENAS  = [escena, escena, ...]

Cada escena es un momento de la historia:

    {
      "es": "Texto que dice la voz", "en": "...",
      "camara": {"centro": (x, y, z), "distancia": d, "altura": h, "angulo": a},
      "camara_fin": {...},          # opcional: la cámara viaja hasta aquí
      "corte": True,                # opcional: salta de golpe a esta cámara
      "deriva": 6,                  # grados que gira despacio durante la escena
      "piezas": [...],              # lo que se construye
      "ventana": (0.05, 0.7),       # tramo de la escena en que entran las piezas
      "acciones": [                 # mover / girar / quitar grupos (por "id")
          {"id": "viga", "t": 0.5, "dur": 0.6, "mover": (0, 0, -8),
           "girar": (0, 30, 0), "quitar": False, "hasta_fin": False,
           "velocidad": (5, 0, 0),   # con hasta_fin: avanza a esa velocidad
           "durf": 0.1,              # duración como fracción de la escena
           "suave": "suave" | "lineal" | "rebote", "sonido": "splash"},
      ],
      "avisos": [{"es": "¡SE DOBLA!", "en": "...", "t": (0.5, 0.95)}],
      "etiquetas": [{"es": "ANCLAJE", "en": "...", "pos": (x, y, z), "t": (0.3, 1)}],
      "sonidos": [{"tipo": "crash", "t": 0.6}],
      "final": True,                # última escena: confeti y texto destacado
      "celebrar": False,            # final sin confeti ni fanfarria (historias, terror)
      "opciones": {"es": ["A) ...", "B) ..."], "en": [...]},  # pantalla "¿qué harías?"
      "opciones_t": 0.2,            # cuándo aparecen las opciones dentro de la escena
    }

Todos los "t" son fracciones de la escena (0 = empieza, 1 = termina), porque
la duración real la marca la voz.
"""

DUR_ENTRADA = {"caer": 0.55, "crecer": 0.7, "subir": 0.6, "aparecer": 0.3}
TRANSICION_CAMARA = 1.0     # segundos que tarda en viajar a la nueva toma
SONIDO_ENTRADA = {"caer": ("golpe", 0.2), "crecer": ("subida", 0.0),
                  "subir": ("subida", 0.0), "aparecer": ("pop", 0.0)}


def planificar(est, lt, idioma):
    """lt = {"escenas": [{"inicio", "duracion", "palabras"}], "duracion_total"}."""
    total = lt["duracion_total"]
    plan = {"piezas": [], "acciones": [], "camara": [], "palabras": [], "opciones": [],
            "ambiente": getattr(est, "AMBIENTE", None),
            "avisos": [], "etiquetas": [], "sonidos": [], "confeti": None,
            "titulo": None, "total": total}

    for p in est.ESCENARIO:
        plan["piezas"].append({"p": p, "t": None})

    pose = None
    for i, (esc, seg) in enumerate(zip(est.ESCENAS, lt["escenas"])):
        T, D = seg["inicio"], seg["duracion"]

        # --- Piezas ---
        piezas = esc.get("piezas", [])
        autos = [p for p in piezas if "t" not in p and p["anim"] != "ninguna"]
        w0, w1 = esc.get("ventana", (0.05, 0.7))
        k = 0
        for p in piezas:
            if p["anim"] == "ninguna":
                t = None
            elif "t" in p:
                t = T + D * p["t"]
            else:
                t = T + D * (w0 + (w1 - w0) * k / max(1, len(autos)))
                k += 1
            plan["piezas"].append({"p": p, "t": t})
            if t is not None and not p.get("mudo"):
                tipo, desfase = SONIDO_ENTRADA[p["anim"]]
                plan["sonidos"].append({"tipo": tipo, "t": t + desfase})

        # --- Acciones ---
        for a in esc.get("acciones", []):
            t0 = T + D * a.get("t", 0.0)
            if a.get("hasta_fin"):
                t1 = total
            elif "durf" in a:
                t1 = t0 + D * a["durf"]
            else:
                t1 = t0 + a.get("dur", 0.6)
            a = dict(a)
            if "velocidad" in a:      # unidades por segundo -> desplazamiento total
                a["mover"] = [v * (t1 - t0) for v in a["velocidad"]]
            plan["acciones"].append({**a, "t0": t0, "t1": t1})
            if a.get("sonido"):
                plan["sonidos"].append({"tipo": a["sonido"], "t": t0 + a.get("sonido_en", 0.0) * (t1 - t0)})

        # --- Cámara ---
        nueva = esc.get("camara")
        fin_esc = T + D - 0.05
        if nueva or pose is None:
            destino = dict(pose or {}, **(nueva or {}))
            if pose is None:
                plan["camara"].append({"t": 0.0, "pose": destino, "tramo": "lineal"})
            elif esc.get("corte"):
                plan["camara"].append({"t": T, "pose": destino, "tramo": "lineal"})
                plan["sonidos"].append({"tipo": "paso", "t": T})
            else:
                # la clave anterior (fin de la escena previa) inicia un tramo suave
                plan["camara"][-1]["tramo"] = "suave"
                plan["camara"].append({"t": T + min(TRANSICION_CAMARA, 0.35 * D),
                                       "pose": destino, "tramo": "lineal"})
            pose = destino
        fin = dict(pose, **esc.get("camara_fin", {}))
        if "camara_fin" not in esc:
            fin["angulo"] = pose["angulo"] + esc.get("deriva", 6)
        plan["camara"].append({"t": fin_esc, "pose": fin, "tramo": "lineal"})
        pose = fin

        # --- Textos ---
        for item in seg.get("palabras", []):
            palabra, a, b = item[:3]
            crudo = item[3] if len(item) > 3 else palabra
            plan["palabras"].append({"texto": palabra, "crudo": crudo, "t0": T + a, "t1": T + b,
                                     "final": bool(esc.get("final")), "escena": i})
        if i == 0 and getattr(est, "TITULO", None):
            plan["titulo"] = {"texto": est.TITULO[idioma], "t0": 0.0, "t1": T + D}
        for av in esc.get("avisos", []):
            f0, f1 = av.get("t", (0.3, 0.95))
            plan["avisos"].append({"texto": av[idioma], "t0": T + D * f0, "t1": T + D * f1})
            plan["sonidos"].append({"tipo": av.get("sonido", "alerta"), "t": T + D * f0})
        for et in esc.get("etiquetas", []):
            f0, f1 = et.get("t", (0.3, 1.0))
            plan["etiquetas"].append({
                "texto": et[idioma], "pos": et["pos"], "alto": et.get("alto"),
                "tam": et.get("tam", 0.045 * pose["distancia"]),
                "t0": T + D * f0, "t1": T + D * f1})
            plan["sonidos"].append({"tipo": "pop", "t": T + D * f0})
        for s in esc.get("sonidos", []):
            plan["sonidos"].append({"tipo": s["tipo"], "t": T + D * s["t"]})

        if esc.get("opciones"):
            f0 = esc.get("opciones_t", 0.2)
            plan["opciones"].append({"items": esc["opciones"][idioma], "t0": T + D * f0, "t1": T + D + 0.6})
            plan["sonidos"].append({"tipo": "golpe", "t": T + D * f0})

        if esc.get("final") and esc.get("celebrar", True):
            plan["confeti"] = {"t": T + 0.15, "centro": esc.get("confeti", pose["centro"]),
                               "radio": pose["distancia"] * 0.35}
            plan["sonidos"].append({"tipo": "tada", "t": T + 0.1})

    # Las palabras no se pisan: cada una dura hasta que empieza la siguiente
    pal = plan["palabras"]
    for a, b in zip(pal, pal[1:]):
        if b["t0"] - a["t1"] < 0.25:
            a["t1"] = b["t0"]
    plan["sonidos"].sort(key=lambda s: s["t"])
    return plan


def textos_de(est, idioma):
    return [esc[idioma] for esc in est.ESCENAS]
