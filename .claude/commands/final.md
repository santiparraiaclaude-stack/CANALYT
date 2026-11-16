---
description: Render final en alta calidad de un video ya aprobado, con textos para publicar
argument-hint: <nombre de la estructura, p. ej. golden_gate>
---

Haz la versión para publicar de: **$ARGUMENTS**

Si no se indica nombre, usa la estructura modificada más recientemente en
`creador/estructuras/` y confirma con el usuario cuál es antes de empezar.

1. Comprueba que existe `creador/estructuras/<nombre>.py`.
2. Lanza **en segundo plano** (tarda más de una hora; `caffeinate` evita que el Mac
   se duerma):
   `caffeinate -dims python3 creador/pipeline.py <nombre> --calidad alta --gpu`
3. Avisa al usuario de que ya está en marcha, de que puede seguir usando el Mac pero
   debe dejarlo enchufado y sin cerrar la terminal, y de cuánto falta aproximadamente
   (mira cuántas imágenes hay en `salida/<nombre>/frames_alta_es/` frente al total
   que imprime el comando).
4. Mientras se renderiza, escribe `salida/<nombre>/publicar.json` con este formato:
   `{"titulo": "...", "descripcion": "...", "hashtags": ["...", "..."],
   "comentario": "...", "tema": "...", "gancho": "..."}`
   - `titulo`: menos de 60 caracteres, con gancho. `descripcion`: 1–2 frases.
   - `hashtags`: 3 a 5, sin el símbolo #. `comentario`: una pregunta para fijar.
   - `tema`: una palabra (puentes, túneles, presas...). `gancho`: el tipo de gancho
     usado (pregunta, reto, dato sorprendente, error famoso...). Estos dos sirven
     para analizar después qué funciona, así que sé consistente con los anteriores
     (mira `canal/publicaciones.json`).
5. Cuando termine el render, abre el video con `open salida/<nombre>/video_es_alta.mp4`.
6. **Ponlo en el calendario.** Ejecuta `python3 creador/publicar.py agendar <nombre>`
   (añade `--fecha "AAAA-MM-DD HH:MM"` si el usuario pidió una fecha concreta).
   Reserva el siguiente hueco libre y escribe `salida/<nombre>/publicar.md` con los
   textos listos para copiar en cada red. Ábrelo con `open salida/<nombre>/publicar.md`.
7. Dile al usuario, en pocas líneas: qué día y a qué hora le toca subirlo, que los
   textos para copiar están en ese archivo, que marque el video como contenido hecho
   con IA, y que cuando lo suba te lo diga (o escriba `/calendario`) para marcarlo.

Si el render falla o se interrumpe, explica qué pasó en una frase y vuelve a lanzarlo.
