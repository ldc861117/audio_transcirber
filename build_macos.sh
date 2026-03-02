#!/bin/bash
set -e

# ── macOS App Build Script ──
# Builds the Audio Transcriber as a native macOS .app bundle

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "═══════════════════════════════════════════════"
echo "  🔨 Building Audio Transcriber macOS App"
echo "═══════════════════════════════════════════════"

# Step 1: Build frontend
echo ""
echo "📦 Step 1/3: Building React frontend..."
cd frontend
npm install --silent
npm run build
cd ..
echo "✅ Frontend built to static/"

# Step 2: Verify static assets
if [ ! -f "static/index.html" ]; then
    echo "❌ Error: static/index.html not found after build!"
    exit 1
fi
echo "✅ static/index.html verified"

# Step 3: Activate venv and run PyInstaller
echo ""
echo "🏗️  Step 2/3: Running PyInstaller..."
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

pyinstaller build_app.spec --clean --noconfirm

# Step 4: Verify output
echo ""
echo "🔍 Step 3/3: Verifying build..."
APP_PATH="dist/Audio Transcriber.app"
if [ -d "$APP_PATH" ]; then
    APP_SIZE=$(du -sh "$APP_PATH" | cut -f1)
    echo "✅ Build successful!"
    echo ""
    echo "═══════════════════════════════════════════════"
    echo "  📱 App:  dist/Audio Transcriber.app"
    echo "  📏 Size: $APP_SIZE"
    echo ""
    echo "  To test:  open \"dist/Audio Transcriber.app\""
    echo "═══════════════════════════════════════════════"
else
    echo "❌ Build failed! App not found at: $APP_PATH"
    exit 1
fi
