---
description: Crea un video nuevo a partir de una idea y enseña el boceto para aprobarlo
argument-hint: <idea del video, p. ej. "cómo se hace un túnel bajo el mar">
---

El usuario quiere un video nuevo del canal sobre: **$ARGUMENTS**

Si no hay idea (argumento vacío), toma las 5 primeras de "Pendientes" en `ideas.md`
(si hay menos, pide más al agente `investigador`), preséntalas con su gancho en una
línea y pregunta cuál quiere. No sigas hasta que elija.

Sigue estos pasos en orden. Eres tú quien conduce; el usuario no es técnico, así que
háblale en español sencillo y no le pidas que ejecute comandos.

1. **Guion (agente `investigador`, usa Opus).** Pásale la idea y pídele el guion
   completo como cadena de pruebas (haces algo → ¿y si...? → consecuencia →
   arreglo), con datos verificados, escena por escena.
2. **Enséñale el guion al usuario** en una lista corta, una línea por vuelta con su
   forma "haces X → ¿y si Y? → pasa Z → lo arreglas con W", y pregúntale si le gusta
   o quiere cambiar alguna prueba. Espera su respuesta antes de animar: cambiar el
   guion después cuesta otro render.
   **Animación (agente `creador`, usa Fable).** Pásale el guion entero y pídele que
   deje creado y comprobado `creador/estructuras/<nombre>.py`, revisando el encuadre
   con `--ver` hasta que todas las escenas, avisos y etiquetas se vean completos.
   Dile que **no** renderice el video y que te devuelva el nombre de la estructura.
3. **Boceto.** Ejecuta, desde la raíz del proyecto:
   `python3 creador/pipeline.py <nombre> --calidad boceto --gpu`
   (tarda pocos minutos; si supera el límite de tiempo, lánzalo en segundo plano y
   espera a que termine).
   Si en la salida aparece alguna línea `[creador] AVISO:` (un texto que no cabe o
   señala algo que no se ve), corrige la escena y repite el boceto antes de enseñarlo.
4. **Ábrelo** con `open salida/<nombre>/video_es_boceto.mp4` y dile al usuario que es
   un borrador (se ve borroso y a saltos) para revisar voz, historia y movimiento.
5. **PARA y pregunta:** "¿Qué cambiamos?" Ofrece ejemplos: textos, ritmo, una escena
   que no se entiende, cámaras. Aplica los cambios que pida (tú mismo si son
   pequeños; con el agente `creador` si hay que rehacer escenas), vuelve a generar
   el boceto y vuelve a preguntar. Repite hasta que diga que está bien.
   Al aprobarlo, mueve la idea a "Hechos" en `ideas.md`.
6. Cuando lo apruebe, dile que escriba **`/final <nombre>`** (o hazlo tú si te lo
   pide directamente) y recuérdale que el render final tarda más de una hora.

Reglas: no gastes voz de ElevenLabs sin necesidad (cada cambio de texto regenera solo
esa frase); no hagas el render en alta hasta que el usuario apruebe el boceto; si un
comando falla, lee el error y arréglalo tú antes de molestar al usuario.
