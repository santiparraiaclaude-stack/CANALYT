---
description: Muestra qué videos toca subir y cuándo; marca los que ya se subieron
argument-hint: [opcional: "ya subí golden_gate" + enlaces]
---

$ARGUMENTS

1. Si el usuario dice que ya subió algún video, márcalo:
   `python3 creador/publicar.py subido <nombre>` y, si te dio enlaces, añade
   `--tiktok URL --instagram URL --youtube URL --facebook URL` (los que tenga).
2. Ejecuta `python3 creador/publicar.py calendario` y enséñale el resultado tal cual.
3. Si hay alguno ATRASADO, recuérdaselo y ofrece cambiarle la fecha
   (`python3 creador/publicar.py agendar <nombre> --fecha "AAAA-MM-DD HH:MM"`).
4. Si quedan menos de 3 videos pendientes, sugiérele hacer más con `/video`.
