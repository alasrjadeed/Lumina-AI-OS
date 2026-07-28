#!/bin/bash
# Lumina AI OS — Stop all local services

echo "Stopping Lumina AI OS..."

# Kill backend (port 8000)
if lsof -ti:8000 &>/dev/null; then
    lsof -ti:8000 | xargs kill -9 2>/dev/null
    echo "✓ Backend stopped (port 8000)"
else
    echo "  Backend not running"
fi

# Kill frontend (port 5173)
if lsof -ti:5173 &>/dev/null; then
    lsof -ti:5173 | xargs kill -9 2>/dev/null
    echo "✓ Frontend stopped (port 5173)"
else
    echo "  Frontend not running"
fi

# Kill any remaining uvicorn/vite processes
pkill -f "uvicorn main:app" 2>/dev/null && echo "✓ Uvicorn processes killed" || true
pkill -f "vite" 2>/dev/null && echo "✓ Vite processes killed" || true

# Clean up nohup logs
rm -f /tmp/lumina-backend.log /tmp/lumina-frontend.log 2>/dev/null

echo "Lumina stopped."
