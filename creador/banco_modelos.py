"""Prepara los modelos 3D descargados (Kenney, Quaternius, etc.) para usarlos en los videos.

1. Descarga los packs que quieras (zip) y déjalos en  modelos/descargas/
2. Ejecuta:   python3 creador/banco_modelos.py
3. Mira qué hay:   python3 creador/banco_modelos.py --lista [texto]

Saca de cada zip los modelos (.glb preferido; si no, .gltf, .fbx u .obj), los deja en
modelos/<pack>/ y escribe modelos/catalogo.json, que leen los agentes para elegir
qué usar. En una escena se usan así:  modelo("car-kit/truck", pos=(0, 0, 0), largo=4)

Packs recomendados (gratis, CC0: se pueden usar en videos monetizados):
  kenney.nl/assets/car-kit              autos, camiones, ambulancia...
  kenney.nl/assets/city-kit-roads       carreteras, puentes, señales
  kenney.nl/assets/city-kit-industrial  fábricas, tanques, chimeneas
  kenney.nl/assets/city-kit-commercial  edificios y tiendas
  kenney.nl/assets/nature-kit           árboles, rocas, terreno
  kenney.nl/assets/mini-characters      personajes pequeños
  kenney.nl/assets/train-kit            trenes y vías
  kaylousberg.itch.io/city-builder-bits ciudad completa estilo KayKit (CC0)
  quaternius.com/packs/downtowncitymegakit.html  manzanas de ciudad (CC0)
  quaternius.com                        personajes, vehículos, edificios (CC0)
"""
import argparse
import json
import os
import re
import shutil
import sys
import zipfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELOS = os.path.join(RAIZ, "modelos")
DESCARGAS = os.path.join(MODELOS, "descargas")
CATALOGO = os.path.join(MODELOS, "catalogo.json")
PREFERENCIA = [".glb", ".gltf", ".fbx", ".obj"]
AUXILIARES = (".bin", ".png", ".jpg", ".jpeg", ".mtl", ".tga")


def nombre_pack(zip_o_carpeta):
    base = os.path.splitext(os.path.basename(zip_o_carpeta))[0]
    base = re.sub(r"^kenney[_ -]", "", base, flags=re.I)
    base = re.sub(r"\s*\(\d+\)$", "", base)                      # copias "(1)" del navegador
    base = re.sub(r"[_ -]v?\d+([._-]\d+)*$", "", base)          # versiones "_2.0", "-2-1", "20"
    return re.sub(r"[^a-z0-9]+", "-", base.lower()).strip("-") or "pack"


def limpiar(nombre):
    return re.sub(r"[^a-z0-9]+", "-", nombre.lower()).strip("-")


def extraer(zip_ruta):
    pack = nombre_pack(zip_ruta)
    destino = os.path.join(MODELOS, pack)
    with zipfile.ZipFile(zip_ruta) as z:
        nombres = [n for n in z.namelist() if not n.endswith("/") and "__MACOSX" not in n]
        # por modelo, el mejor formato disponible
        mejores = {}
        for n in nombres:
            base, ext = os.path.splitext(os.path.basename(n))
            ext = ext.lower()
            if ext in PREFERENCIA:
                clave = limpiar(base)
                actual = mejores.get(clave)
                if actual is None or PREFERENCIA.index(ext) < PREFERENCIA.index(os.path.splitext(actual)[1].lower()):
                    mejores[clave] = n
        if not mejores:
            print(f"  {os.path.basename(zip_ruta)}: no tiene modelos 3D (¿es un pack 2D?)")
            return pack, 0
        carpetas = {os.path.dirname(n) for n in mejores.values()}
        os.makedirs(destino, exist_ok=True)
        for clave, n in mejores.items():
            ext = os.path.splitext(n)[1].lower()
            with z.open(n) as src, open(os.path.join(destino, clave + ext), "wb") as dst:
                shutil.copyfileobj(src, dst)
        # texturas y .bin que acompañan a .gltf / .obj / .fbx (misma carpeta o "Textures")
        for n in nombres:
            if n.lower().endswith(AUXILIARES) and (os.path.dirname(n) in carpetas
                                                   or "textures" in n.lower()):
                ruta = os.path.join(destino, os.path.basename(n))
                if not os.path.exists(ruta):
                    with z.open(n) as src, open(ruta, "wb") as dst:
                        shutil.copyfileobj(src, dst)
    return pack, len(mejores)


def catalogar():
    items = []
    for pack in sorted(os.listdir(MODELOS)):
        carpeta = os.path.join(MODELOS, pack)
        if pack == "descargas" or not os.path.isdir(carpeta):
            continue
        for f in sorted(os.listdir(carpeta)):
            base, ext = os.path.splitext(f)
            if ext.lower() in PREFERENCIA:
                items.append({"id": f"{pack}/{base}", "pack": pack,
                              "archivo": os.path.relpath(os.path.join(carpeta, f), RAIZ)})
    with open(CATALOGO, "w", encoding="utf-8") as fh:
        json.dump(items, fh, ensure_ascii=False, indent=1)
    return items


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--lista", nargs="?", const="", metavar="TEXTO",
                    help="muestra el catálogo (opcional: filtra por texto, p. ej. truck)")
    a = ap.parse_args()
    os.makedirs(DESCARGAS, exist_ok=True)

    if a.lista is not None:
        items = catalogar()
        filtro = a.lista.lower()
        elegidos = [i for i in items if filtro in i["id"]]
        packs = {}
        for i in elegidos:
            packs.setdefault(i["pack"], []).append(i["id"].split("/", 1)[1])
        for pack, nombres in packs.items():
            print(f"{pack} ({len(nombres)}): {', '.join(nombres)}")
        print(f"\n{len(elegidos)} modelos" + (f" con '{a.lista}'" if a.lista else ""))
        return

    zips = sorted(f for f in os.listdir(DESCARGAS) if f.lower().endswith(".zip"))
    if not zips:
        print(f"No hay ningún .zip en {DESCARGAS}\n")
        print(__doc__.split("Packs recomendados")[1].join(["Packs recomendados", ""]))
        sys.exit(1)
    for z in zips:
        try:
            pack, n = extraer(os.path.join(DESCARGAS, z))
            if n:
                print(f"  ✓ {pack}: {n} modelos")
        except zipfile.BadZipFile:
            print(f"  ✗ {z}: el zip está dañado o incompleto; vuelve a descargarlo")
    items = catalogar()
    print(f"\nListo: {len(items)} modelos en el catálogo ({CATALOGO})")
    print("Para verlos:  python3 creador/banco_modelos.py --lista")


if __name__ == "__main__":
    main()
