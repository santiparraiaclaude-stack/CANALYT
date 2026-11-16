# CANALYT: "Constrúyelo tú"

Canal de animación 3D para **YouTube Shorts, Instagram Reels y TikTok**: en cada
video el espectador "construye" una estructura famosa pieza por pieza, y al final
aparece *"¡Bien! Has construido el ___"*.

Todo se produce con herramientas baratas o gratis:

| Parte | Herramienta | Costo |
|---|---|---|
| Animación 3D | Blender 4.2 LTS (con scripts de Python) | Gratis |
| Voz | ElevenLabs | Plan Starter (uso comercial) |
| Montaje y subtítulos | ffmpeg | Gratis |
| Ideas, guiones y código | Claude, con el agente `creador` | Tu plan de Claude |

## 1. Instalación

**Linux / macOS**
```bash
bash setup/instalar.sh
```

**Windows (PowerShell)**
```powershell
powershell -ExecutionPolicy Bypass -File setup\instalar_windows.ps1
```

Después, abre `.env` y pega tu clave de ElevenLabs en `ELEVENLABS_API_KEY=`.
La clave está en elevenlabs.io → Profile → API Keys.

## 2. Hacer un video

```bash
# Imagen de prueba para revisar el encuadre (segundos)
python3 creador/pipeline.py golden_gate --frame 600

# Vista previa rápida 360x640 (minutos)
python3 creador/pipeline.py golden_gate

# Versión final 1080x1920 en dos idiomas, con tarjeta gráfica y música
python3 creador/pipeline.py golden_gate --calidad alta --gpu --idiomas es en --musica musica.mp3
```

Los videos quedan en `salida/golden_gate/`.

## 3. El agente `creador`

Está en `.claude/agents/creador.md`. Desde Claude Code, en esta carpeta, pídele cosas como:

- *"creador, dame 10 ideas de estructuras que estén en tendencia esta semana"*
- *"creador, haz el video de la Torre Eiffel"*
- *"creador, renderiza golden_gate en alta calidad en español e inglés"*

El agente busca datos reales, escribe el guion, crea `creador/estructuras/<nombre>.py`,
revisa el encuadre, renderiza y te deja el título, la descripción y los hashtags.

## Estructura del proyecto

```
.claude/agents/creador.md     el agente
creador/
  piezas.py                   piezas 3D básicas y paleta de colores
  estructuras/golden_gate.py  un archivo por video (plantilla)
  blender_construir.py        animación y render en Blender
  voz.py                      narración con ElevenLabs
  montar.py                   subtítulos, audio y mp4 final
  pipeline.py                 lo une todo
setup/                        instaladores
```
