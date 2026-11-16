---
description: Lee las estadísticas de los videos publicados y actualiza la fórmula del canal
---

Analiza qué videos funcionaron y deja las conclusiones listas para los próximos.

1. Ejecuta `python3 creador/publicar.py metricas` para traer las estadísticas
   actuales de cada video en cada red.
2. Lee `canal/metricas.json` (números, y en TikTok la curva de retención segundo a
   segundo), `canal/publicaciones.json` (tema, tipo de gancho, duración, número de
   escenas y palabras de cada video) y el guion de cada video en
   `creador/estructuras/<nombre>.py`.
3. Pide el análisis al agente `investigador`, pasándole esos datos. Debe comparar:
   - qué **temas** y qué **tipo de gancho** tuvieron más vistas y más compartidos;
   - en qué **segundo se va la gente** (retención) y qué estaba pasando en el guion
     en ese momento: frase larga, escena lenta, dato confuso;
   - si los videos **más cortos o más largos** retienen mejor;
   - diferencias entre redes (algo que funcione en TikTok y no en YouTube).
   Con menos de 5 videos publicados o menos de 3 días de datos, que diga con
   claridad que es pronto para sacar conclusiones y se limite a observaciones.
4. Actualiza `canal/aprendizajes.md`: reescribe "Qué repetir" y "Qué evitar" con
   reglas concretas y accionables (máximo 8 en cada una, cada una con el dato que la
   respalda) y añade una entrada con fecha en "Historial de análisis".
5. Pide al `investigador` 5 ideas nuevas que apliquen lo aprendido y añádelas a
   `ideas.md`.
6. Resume al usuario en pocas líneas: los 3 mejores videos y por qué, qué vamos a
   cambiar, y las ideas nuevas.

No inventes causas: si un resultado puede ser casualidad (pocos datos), dilo así.
