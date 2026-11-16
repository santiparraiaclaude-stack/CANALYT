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
4. Mientras se renderiza, escribe `salida/<nombre>/publicar.md` con, para TikTok,
   Instagram Reels y YouTube Shorts: título (menos de 60 caracteres, con gancho),
   descripción de 1–2 frases, 3–5 hashtags, y un comentario para fijar que haga una
   pregunta. Recuerda marcar el video como contenido generado con IA al subirlo.
5. Cuando termine, abre el video con `open salida/<nombre>/video_es_alta.mp4`,
   enseña los textos de `publicar.md` y dile dónde está el archivo.

Si el render falla o se interrumpe, explica qué pasó en una frase y vuelve a lanzarlo.
