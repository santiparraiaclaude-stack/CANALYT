---
description: Crea un video nuevo a partir de una idea y enseña el boceto para aprobarlo
argument-hint: <idea del video, p. ej. "cómo se hace un túnel bajo el mar">
---

El usuario quiere un video nuevo del canal sobre: **$ARGUMENTS**

Si no hay idea (argumento vacío), busca en la web 5 temas en tendencia que encajen
con el canal, preséntalos con su gancho en una línea y pregunta cuál quiere. No sigas
hasta que elija.

Sigue estos pasos en orden. Eres tú quien conduce; el usuario no es técnico, así que
háblale en español sencillo y no le pidas que ejecute comandos.

1. **Guion y escena (delégalo al agente `creador`).** Pásale la idea y pídele que
   siga su flujo completo hasta dejar creado y comprobado
   `creador/estructuras/<nombre>.py`: investigar, guion problema → solución con datos
   verificados, escena 3D, y revisar el encuadre con `--ver` hasta que todas las
   escenas se vean bien. Dile que **no** renderice el video y que te devuelva: el
   nombre de la estructura, el guion en español escena por escena y las fuentes de
   los datos.
2. **Enséñale el guion al usuario** en una lista corta (una línea por escena) y sigue
   sin esperar respuesta, salvo que el agente haya dejado dudas.
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
6. Cuando lo apruebe, dile que escriba **`/final <nombre>`** (o hazlo tú si te lo
   pide directamente) y recuérdale que el render final tarda más de una hora.

Reglas: no gastes voz de ElevenLabs sin necesidad (cada cambio de texto regenera solo
esa frase); no hagas el render en alta hasta que el usuario apruebe el boceto; si un
comando falla, lee el error y arréglalo tú antes de molestar al usuario.
