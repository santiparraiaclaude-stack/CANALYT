# Modelos 3D

1. Descarga packs gratis (CC0) y deja los .zip en `modelos/descargas/`:
   - https://kenney.nl/assets/car-kit (autos, camiones)
   - https://kenney.nl/assets/city-kit-roads (carreteras, puentes)
   - https://kenney.nl/assets/city-kit-industrial (fábricas, tanques)
   - https://kenney.nl/assets/city-kit-commercial (edificios)
   - https://kenney.nl/assets/nature-kit (árboles, rocas)
   - https://kenney.nl/assets/mini-characters (personajes)
   - https://kenney.nl/assets/train-kit (trenes)
   - https://kenney.nl/assets/city-kit-suburban (casas y calles: historias)
   - https://kenney.nl/assets/furniture-kit (muebles e interiores: historias)

   Más detalle (también gratis y CC0; se preparan igual):
   - https://kaylousberg.itch.io/city-builder-bits (KayKit: ciudad con edificios,
     calles, semáforos, farolas, autos y árboles; elige "Download" con precio 0)
   - https://quaternius.com/packs/downtowncitymegakit.html (Quaternius: más de 300
     piezas para manzanas tipo Nueva York)
   - https://quaternius.itch.io/quaternius-lowpoly-bundle (todos los packs de
     Quaternius: casas, interiores, autos, personajes animados...)
   En cada página: Download -> "Continue without donating" (o dona si quieres).
2. Ejecuta `python3 creador/banco_modelos.py --revisar`: trae de Descargas solo los zip
   de paquetes 3D, los prepara y te dice qué paquetes recomendados te faltan, con enlace.
3. Para ver qué hay: `python3 creador/banco_modelos.py --lista` (o `--lista truck`).

Los modelos no se suben a git.
