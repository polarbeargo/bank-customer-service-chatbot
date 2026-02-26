#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
BACKEND_PORT=5001
FRONTEND_PORT=3001

kill_port() {
  local port="$1"
  lsof -i ":${port}" -t 2>/dev/null | xargs kill -9 2>/dev/null || true
}

kill_port "$BACKEND_PORT"
kill_port "$FRONTEND_PORT"

# Start backend (port 5001) with venv
cd "$BACKEND_DIR"
if [[ ! -d venv ]]; then
  python3 -m venv venv
fi
source venv/bin/activate
python3 -m pip install -r requirements.txt >/dev/null
PORT="$BACKEND_PORT" python3 app.py >/tmp/chatbot-backend.log 2>&1 &
BACKEND_PID=$!

cleanup() {
  kill "$BACKEND_PID" >/dev/null 2>&1 || true
}
trap cleanup EXIT

# Start frontend
cd "$FRONTEND_DIR"
if [[ ! -d node_modules ]]; then
  npm install --legacy-peer-deps
fi
PORT="$FRONTEND_PORT" REACT_APP_API_URL="http://localhost:${BACKEND_PORT}" npm start
