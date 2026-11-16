---
description: Analiza las estadísticas de los videos publicados y actualiza la fórmula del canal
argument-hint: [opcional: números o rutas de capturas de las estadísticas]
---

Analiza qué videos funcionaron y deja las conclusiones listas para los próximos.

$ARGUMENTS

## 1. Reúne los números

Mira `canal/publicaciones.json` para saber qué videos están marcados como subidos.
Para cada uno hacen falta, por red (TikTok, Instagram, YouTube, Facebook): vistas,
likes, comentarios, compartidos y, donde exista, **retención** (porcentaje que lo ve
entero, tiempo medio de visualización y el segundo donde más gente se va).

Consíguelos por este orden:
- **Lo que el usuario te haya pasado** en este mensaje: números escritos, o capturas
  de pantalla de las estadísticas (léelas con Read; también puede dejarlas en
  `canal/capturas/`).
- **Si tienes herramientas de navegador (Claude in Chrome)**, pregunta si quiere que
  las leas tú de YouTube Studio, las analíticas de TikTok y Meta Business Suite, y
  hazlo solo si dice que sí. Solo lectura: no cambies nada en esas páginas.
- **Si hay `UPLOAD_POST_API_KEY` en `.env`**: `python3 creador/publicar.py metricas`.
- Si no tienes nada de lo anterior, **pídeselo al usuario** con instrucciones exactas
  de dónde hacer la captura en cada red, y para aquí hasta que las mande.

Guarda lo reunido en `canal/metricas.json` con esta forma (añade, no borres lo
anterior; `historial` guarda un registro por fecha para ver la evolución):

```json
{"<nombre>": {"titulo": "...", "fecha": "AAAA-MM-DDTHH:MM:00", "redes": {
  "tiktok": {"metricas": {"views": 0, "likes": 0, "comments": 0, "shares": 0,
             "full_video_watched_rate": 0.0, "average_time_watched": 0.0,
             "segundo_mayor_caida": 0},
             "historial": {"AAAA-MM-DD": {"views": 0, "likes": 0}}}}}}
```

Anota solo lo que de verdad aparezca en los datos; no rellenes huecos con estimaciones.

## 2. Analiza (agente `investigador`)

Pásale `canal/metricas.json`, `canal/publicaciones.json` (tema, tipo de gancho,
duración, escenas y palabras de cada video) y el guion de cada video
(`creador/estructuras/<nombre>.py`). Debe comparar:
- qué **temas** y qué **tipo de gancho** tuvieron más vistas y más compartidos;
- en qué **segundo se va la gente** y qué pasaba en el guion en ese momento;
- si los videos **más cortos o más largos** retienen mejor;
- diferencias entre redes.

Con menos de 5 videos o menos de 3 días de datos, que diga claramente que es pronto
para conclusiones y se limite a observaciones.

## 3. Deja la fórmula escrita

Actualiza `canal/aprendizajes.md`: reescribe "Qué repetir" y "Qué evitar" con reglas
concretas (máximo 8 en cada una, cada una con el dato que la respalda) y añade una
entrada con fecha en "Historial de análisis". Pide al `investigador` 5 ideas nuevas
que apliquen lo aprendido y añádelas a `ideas.md`.

## 4. Cuéntaselo al usuario

En pocas líneas: los mejores videos y por qué, qué vamos a cambiar y las ideas
nuevas. No inventes causas: si algo puede ser casualidad por pocos datos, dilo.
