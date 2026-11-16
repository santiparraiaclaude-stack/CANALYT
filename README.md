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

## 2. Elegir la voz

```bash
python3 creador/probar_voces.py
```

Genera una muestra de cada voz de tu cuenta de ElevenLabs en `salida/voces/`.
Escúchalas y quédate con una:

```bash
python3 creador/probar_voces.py --elegir NOMBRE
```

Para más voces (por ejemplo con acento latino), añádelas en elevenlabs.io →
Voices → Voice Library → "Add to My Voices" y vuelve a ejecutar el script.
La velocidad se cambia en `.env` con `ELEVENLABS_VELOCIDAD=1.08`.

## 3. Hacer un video

```bash
# Imágenes sueltas (en esos segundos) para revisar el encuadre
python3 creador/pipeline.py golden_gate --ver 3 20 60

# Borrador rápido para ver el movimiento
python3 creador/pipeline.py golden_gate --calidad boceto --gpu

# Versión para publicar (1080x1920)
python3 creador/pipeline.py golden_gate --calidad alta --gpu
```

Opciones: `--idiomas es en`, `--musica cancion.mp3`, `--sin-voz`.
Los videos quedan en `salida/golden_gate/`.

## 4. El agente `creador`

Está en `.claude/agents/creador.md`. Para tenerlo en todos tus proyectos:

```bash
mkdir -p ~/.claude/agents && cp .claude/agents/creador.md ~/.claude/agents/
```

Desde Claude Code, en esta carpeta, pídele cosas como:

- *"creador, dame 10 ideas de videos que estén en tendencia"*
- *"creador, haz el video de cómo se hace un túnel bajo el mar"*

## Estructura del proyecto

```
.claude/agents/creador.md     el agente
creador/
  piezas.py                   piezas 3D, prefabricados (autos, barcos...) y colores
  guion.py                    convierte las escenas en una línea de tiempo
  estructuras/golden_gate.py  un archivo por video (plantilla)
  blender_construir.py        animación y render en Blender
  voz.py                      narración con ElevenLabs (tiempos por palabra)
  probar_voces.py             muestras para elegir la voz
  sonido.py                   efectos de sonido
  montar.py                   mezcla de audio y mp4 final
  pipeline.py                 lo une todo
setup/                        instaladores
```
