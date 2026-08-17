#!/usr/bin/env bash
# Starts SentinelChain AI locally: backend (FastAPI) + frontend (Vite).
# Usage: ./scripts/dev.sh
set -e

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND="$ROOT/backend"
FRONTEND="$ROOT/frontend"

if [ ! -d "$BACKEND/.venv" ]; then
  echo "Creating backend virtual environment..."
  python3 -m venv "$BACKEND/.venv"
  "$BACKEND/.venv/bin/pip" install -r "$BACKEND/requirements.txt"
fi

if [ ! -d "$FRONTEND/node_modules" ]; then
  echo "Installing frontend dependencies..."
  (cd "$FRONTEND" && npm install)
fi

(cd "$BACKEND" && ./.venv/bin/uvicorn app.main:app --reload --port 8000) &
BACKEND_PID=$!

(cd "$FRONTEND" && npm run dev) &
FRONTEND_PID=$!

echo "Backend:  http://localhost:8000/docs"
echo "Frontend: http://localhost:5173"

trap "kill $BACKEND_PID $FRONTEND_PID" EXIT
wait
