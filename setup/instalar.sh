#!/usr/bin/env bash
# Instala lo necesario para "creador" en Linux o macOS.
#   bash setup/instalar.sh
set -euo pipefail
BLENDER_VER="4.2.3"

if [[ "$(uname)" == "Darwin" ]]; then
  command -v brew >/dev/null || { echo "Instala Homebrew primero: https://brew.sh"; exit 1; }
  brew install ffmpeg python@3.12
  if [[ ! -d /Applications/Blender.app ]]; then
    brew install --cask blender@lts || brew install --cask blender
  fi
  echo "Blender: /Applications/Blender.app/Contents/MacOS/Blender"
else
  sudo apt-get update
  sudo apt-get install -y ffmpeg python3 curl xz-utils libxi6 libxkbcommon0 libxrender1 libsm6 libgl1
  if ! command -v blender >/dev/null; then
    echo "Descargando Blender ${BLENDER_VER} LTS..."
    curl -L -o /tmp/blender.tar.xz \
      "https://download.blender.org/release/Blender${BLENDER_VER%.*}/blender-${BLENDER_VER}-linux-x64.tar.xz"
    sudo tar -xf /tmp/blender.tar.xz -C /opt
    sudo ln -sf "/opt/blender-${BLENDER_VER}-linux-x64/blender" /usr/local/bin/blender
    rm /tmp/blender.tar.xz
  fi
fi

[[ -f .env ]] || cp .env.example .env
echo
if [[ -x /Applications/Blender.app/Contents/MacOS/Blender ]]; then
  /Applications/Blender.app/Contents/MacOS/Blender --version | head -1
else
  blender --version | head -1 || true
fi
ffmpeg -version | head -1
echo "✅ Listo. Pon tu clave de ElevenLabs en el archivo .env y prueba:"
echo "   python3 creador/pipeline.py golden_gate --gpu"
