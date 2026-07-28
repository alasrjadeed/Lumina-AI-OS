#!/bin/bash
# Lumina AI OS — Local Development Launcher
# Starts backend (FastAPI) and frontend (React/Vite) with one command
# Usage: bash start.sh

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"
VENV_DIR="$(dirname "$SCRIPT_DIR")/venv"

echo "╔══════════════════════════════════════════╗"
echo "║        Lumina AI OS — Local Start        ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# Check prerequisites
if [ ! -f ".env" ]; then
    echo "⚠  No .env found. Copying from .env.example..."
    cp .env.example .env
    echo "   Edit .env to add your API keys, then re-run."
    exit 1
fi

# Create data directory
mkdir -p data

# ── Backend ──
echo "→ Starting Backend (FastAPI on :8000)..."
PYTHON=""
if [ -f "$VENV_DIR/bin/python" ]; then
    PYTHON="$VENV_DIR/bin/python"
elif command -v python3 &>/dev/null; then
    PYTHON="python3"
else
    echo "✗ Python not found. Install Python 3.12+ or create venv at $VENV_DIR"
    exit 1
fi

lsof -ti:8000 | xargs kill -9 2>/dev/null || true
nohup "$PYTHON" -m uvicorn main:app --host 0.0.0.0 --port 8000 > /tmp/lumina-backend.log 2>&1 &
BACKEND_PID=$!
echo "   Backend PID: $BACKEND_PID (log: /tmp/lumina-backend.log)"

# Wait for backend
echo -n "   Waiting for backend..."
for i in {1..15}; do
    if curl -s http://localhost:8000/ >/dev/null 2>&1; then
        echo " ready!"
        break
    fi
    echo -n "."
    sleep 1
done

# ── Frontend ──
echo "→ Starting Frontend (React/Vite on :5173)..."
if [ -d "lumina-ui/node_modules" ] && [ -f "lumina-ui/package.json" ]; then
    cd lumina-ui
    lsof -ti:5173 | xargs kill -9 2>/dev/null || true
    nohup npx vite --host 0.0.0.0 > /tmp/lumina-frontend.log 2>&1 &
    FRONTEND_PID=$!
    cd ..
    echo "   Frontend PID: $FRONTEND_PID (log: /tmp/lumina-frontend.log)"
else
    echo "   ⚠  lumina-ui/node_modules not found. Run: cd lumina-ui && npm install"
fi

# ── Summary ──
echo ""
echo "╔══════════════════════════════════════════╗"
echo "║           Lumina is running!             ║"
echo "╠══════════════════════════════════════════╣"
echo "║  Dashboard:  http://localhost:5173       ║"
echo "║  API Docs:   http://localhost:8000/docs  ║"
echo "║  Health:     http://localhost:8000/system/health ║"
echo "╠══════════════════════════════════════════╣"
echo "║  Stop:       bash stop.sh                ║"
echo "║  Backend log: /tmp/lumina-backend.log    ║"
echo "║  Frontend log:/tmp/lumina-frontend.log   ║"
echo "╚══════════════════════════════════════════╝"
