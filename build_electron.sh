#!/usr/bin/env bash
# build_electron.sh — One-click build: Flask binary + Electron .app
set -euo pipefail
cd "$(dirname "$0")"

echo "═══════════════════════════════════════════"
echo "  Audio Transcriber — Electron Build"
echo "═══════════════════════════════════════════"

# ── Step 1: Build React frontend ──────────────────────────────
echo ""
echo "▶ Step 1/4: Building React frontend..."
cd frontend
npm install --silent
npm run build
cd ..
echo "  ✔ Frontend built → static/"

# ── Step 2: Bundle Flask with PyInstaller ─────────────────────
echo ""
echo "▶ Step 2/4: Bundling Flask backend with PyInstaller..."

# Activate virtualenv if present
if [ -d ".venv" ]; then
  source .venv/bin/activate
fi

# Build Flask as a one-folder bundle (goes into flask_dist/)
pyinstaller build_app.spec --clean --noconfirm --distpath flask_dist 2>&1 | tail -5
echo "  ✔ Flask binary → flask_dist/Audio Transcriber/"

# ── Step 3: Install Electron dependencies ─────────────────────
echo ""
echo "▶ Step 3/4: Installing Electron dependencies..."
cd electron
npm install --silent
cd ..
echo "  ✔ Electron dependencies installed"

# ── Step 4: Build Electron .app ───────────────────────────────
echo ""
echo "▶ Step 4/4: Building Electron .app..."
cd electron
npx electron-builder --mac dir 2>&1 | tail -10
cd ..
echo "  ✔ Electron app built"

# ── Done ──────────────────────────────────────────────────────
echo ""
echo "═══════════════════════════════════════════"
APP_PATH="electron/dist/mac/Audio Transcriber.app"
if [ -d "$APP_PATH" ] || [ -d "electron/dist/mac-arm64/Audio Transcriber.app" ]; then
  echo "  ✅ BUILD SUCCESSFUL"
  echo ""
  echo "  To launch:"
  echo "    open \"$APP_PATH\""
  echo ""
  echo "  To build DMG:"
  echo "    cd electron && npm run build:dmg"
else
  echo "  ❌ BUILD FAILED — check output above"
fi
echo "═══════════════════════════════════════════"
