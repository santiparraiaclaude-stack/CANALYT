---
description: Crea una historia interactiva (terror, misterio...) en partes, con votación A/B al final
argument-hint: <idea de la historia, o "parte 2 de <nombre>" con la opción ganadora>
---

El usuario quiere una historia interactiva: **$ARGUMENTS**

Es un formato distinto al de construcción y conviene publicarlo en **otra cuenta**
(díselo la primera vez si no lo sabe). Usa `creador/estructuras/demo_terror.py` como
plantilla: escenario nocturno, luces (`luz(...)`), piezas que brillan (`brillo=`),
`ESTILO = "terror"`, `TEMA = "terror"`, `AMBIENTE = "ambiente"` y una escena final con
`"opciones"` y `"celebrar": False`.

## 1. Guion (agente `investigador`)

Pídele una historia con esta forma (segunda persona, presente, frases cortas):

- **Gancho (0–5 s):** una situación concreta y rara que pase *ahora*, con un detalle
  preciso ("Son las 3:17. Tu celular vibra: «No enciendas ninguna luz»").
- **3 a 5 escenas de escalada:** cada una añade una pista nueva y más miedo; nada se
  explica del todo. Un detalle sensorial por escena (un sonido, una luz, un olor).
- **El momento límite:** la amenaza descubre al protagonista o se queda a un paso.
- **La decisión:** "¿Qué haces? A: ... B: ..." Dos opciones concretas, las dos
  tentadoras y las dos arriesgadas. La voz las lee; en pantalla salen como tarjetas.
- Entre 120 y 190 palabras en total (45–75 s). Sin sangre ni violencia explícita: el
  miedo viene de lo que no se ve. Nada que imite noticias reales ni alertas oficiales
  de verdad (organismos, logos, números de emergencia reales).
- Título corto tipo "PARTE 1\nNOMBRE DE LA HISTORIA".
- Para cada escena: texto de voz, qué se ve (lugar, cámara, luz), sonidos (`latido`,
  `goteo`, `susurro`, `estatica`, `golpe`) y avisos si los hay ("SE ACERCA").

**Si es una continuación** ("parte 2 de X, ganó la B"): lee la estructura de la parte
anterior, continúa desde la opción ganadora, reutiliza escenario y personajes, y
termina con una decisión nueva. La primera frase resume en una línea lo anterior.

Enséñale el guion al usuario (una línea por escena) y espera su visto bueno.

## 2. Escena (agente `creador`)

Pásale el guion aprobado. Recuérdale: escenas nocturnas con niebla, ventanas y
pantallas con `brillo`, farolas y lámparas con `luz(...)`, cámaras bajas y cercanas
(como si fueras tú quien mira), luces que se apagan con acciones `quitar`, y nada
de confeti. Que revise el encuadre con `--ver` (subtítulos, avisos y tarjetas A/B
completos y legibles) y no renderice el video.

## 3. Boceto, cambios y final

Igual que en `/video`: `python3 creador/pipeline.py <nombre> --calidad boceto --gpu`,
ábrelo, pregunta qué cambiar y repite. Cuando lo apruebe, `/final <nombre>`.

En `publicar.json` usa `"tema": "terror"` y en la descripción invita a votar:
"¿Qué harías: A o B? Comenta tu voto y sígueme para la parte 2".
