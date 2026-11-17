---
description: Crea, cambia o asigna estilos visuales (por tema/nicho o para todo el canal)
argument-hint: <qué quieres, p. ej. "para los videos de tecnología quiero un estilo neón">
---

El usuario quiere: **$ARGUMENTS**

Los estilos viven en `canal/estilos.json`:
- `defecto`: el estilo de los videos cuyo tema no tiene uno asignado.
- `por_tema`: tema o nicho → estilo (en minúsculas, p. ej. `"tecnologia": "plano"`).
  El tema de cada video es `TEMA = "..."` en su `creador/estructuras/<nombre>.py`.
- `estilos`: cada estilo con sus ajustes. Lee la documentación de la función
  `aplicar_estilo` en `creador/blender_construir.py` para ver todos los ajustes posibles
  (materiales, contorno, cielo, sol) y copia la forma de los estilos que ya existen.

Según lo que pida:

1. **Ver los estilos:** enséñale la lista con su descripción y qué tema usa cada uno.
2. **Asignar un estilo a un tema o a todo el canal:** cambia `por_tema` o `defecto`.
3. **Crear un estilo nuevo** a partir de su descripción ("neón", "atardecer",
   "blanco y negro", "como acuarela"...): añádelo a `estilos` con un nombre corto en
   minúsculas y una `descripcion`. Tradúcelo a los ajustes que existen; si algo no se
   puede hacer con ellos (por ejemplo, texturas de acuarela), dilo claramente y
   propón lo más parecido.
4. **Enséñaselo:** renderiza una imagen de prueba con un video existente, por ejemplo
   `python3 creador/pipeline.py golden_gate --sin-voz --estilo <nombre> --ver 60`, y
   ábrela con `open salida/golden_gate/frames_baja_es/ver_060.00.png`. Pregunta si le
   gusta y ajusta hasta que diga que sí.
5. **Confirma en una línea** qué quedó: qué estilo usa cada tema y cuál es el de
   por defecto. Recuérdale que los videos ya renderizados no cambian; los nuevos sí.

No borres un estilo que esté asignado a un tema sin preguntar.
