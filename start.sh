#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

if [ ! -d "backend/.venv" ]; then
  echo "[setup] creating Python virtual environment"
  python3 -m venv backend/.venv
fi

source backend/.venv/bin/activate
echo "[setup] installing backend dependencies"
pip install --quiet -r backend/requirements.txt

if [ ! -f "backend/.env" ]; then
  echo "[setup] creating backend/.env from example"
  cp backend/.env.example backend/.env
fi

echo "[setup] installing frontend dependencies"
if [ ! -d "frontend/node_modules" ]; then
  (cd frontend && npm install)
fi

cleanup() {
  kill "${BACKEND_PID:-}" "${FRONTEND_PID:-}" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo "[run] starting backend at http://127.0.0.1:8000"
(cd backend && uvicorn app.main:app --host 127.0.0.1 --port 8000) &
BACKEND_PID=$!

echo "[run] starting frontend at http://127.0.0.1:5173"
(cd frontend && npm run dev) &
FRONTEND_PID=$!

wait "$BACKEND_PID" "$FRONTEND_PID"
