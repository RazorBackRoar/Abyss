#!/bin/zsh
set -euo pipefail

APP_NAME="Abyss"
ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON_BIN="/opt/homebrew/bin/python3.14"
VENV_PYTHON="$ROOT_DIR/.venv/bin/python"

cd "$ROOT_DIR"

if [[ ! -x "$PYTHON_BIN" ]]; then
  echo "ERROR: Python 3.14 not found at $PYTHON_BIN"
  echo "Install Python 3.14 or edit PYTHON_BIN in build_app.zsh."
  exit 1
fi

echo "Using Python:"
"$PYTHON_BIN" --version

"$PYTHON_BIN" -m venv .venv --upgrade

"$VENV_PYTHON" --version
"$VENV_PYTHON" -m pip install --upgrade pip setuptools wheel
"$VENV_PYTHON" -m pip install -r requirements.txt

rm -rf build dist

"$VENV_PYTHON" -m PyInstaller --clean --noconfirm Abyss.spec

if [[ ! -d "dist/${APP_NAME}.app" ]]; then
  echo "ERROR: dist/${APP_NAME}.app was not created"
  exit 1
fi

codesign --force --deep --sign - "dist/${APP_NAME}.app"

echo ""
echo "Built:"
echo "$ROOT_DIR/dist/${APP_NAME}.app"
