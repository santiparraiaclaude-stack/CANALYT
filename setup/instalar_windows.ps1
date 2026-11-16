# Instala lo necesario para "creador" en Windows 10/11.
# Abre PowerShell en la carpeta del proyecto y ejecuta:
#   powershell -ExecutionPolicy Bypass -File setup\instalar_windows.ps1
winget install --id BlenderFoundation.Blender -e
winget install --id Gyan.FFmpeg -e
winget install --id Python.Python.3.12 -e
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
Write-Host ""
Write-Host "Listo. Cierra y vuelve a abrir la terminal para que se carguen los programas."
Write-Host "Si Blender no se encuentra, en .env pon: BLENDER_PATH=C:\Program Files\Blender Foundation\Blender 4.2\blender.exe"
Write-Host "Prueba con:  python creador\pipeline.py golden_gate"
