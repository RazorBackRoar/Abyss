#!/bin/zsh
# Build Abyss using the canonical universal-build.sh
# This script delegates to .razorcore/universal-build.sh to ensure consistent
# uv toolchain, PyInstaller settings, ad-hoc signing, and locked DMG layout.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
RAZORCORE_DIR="$SCRIPT_DIR/../.razorcore"

exec bash "$RAZORCORE_DIR/universal-build.sh" "Abyss" "$@"
