#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
BACKEND_PORT=5001
FRONTEND_PORT=3001
BACKEND_PYTHON=""
USE_UV="${USE_UV:-0}"

kill_port() {
  local port="$1"
  lsof -i ":${port}" -t 2>/dev/null | xargs kill -9 2>/dev/null || true
}

kill_port "$BACKEND_PORT"
kill_port "$FRONTEND_PORT"

# Start backend (port 5001) with venv
cd "$BACKEND_DIR"

if [[ "$USE_UV" == "1" ]] && ! command -v uv >/dev/null 2>&1; then
  echo "[ERROR] USE_UV=1 but 'uv' is not installed or not in PATH."
  exit 1
fi

if command -v uv >/dev/null 2>&1; then
  if [[ ! -d .venv ]]; then
    uv venv .venv
  fi
  uv pip install --python .venv/bin/python -r requirements.txt >/dev/null
  BACKEND_PYTHON=".venv/bin/python"
else
  if [[ ! -d venv ]]; then
    python3 -m venv venv
  fi
  source venv/bin/activate
  python3 -m pip install -r requirements.txt >/dev/null
  BACKEND_PYTHON="python3"
fi

PORT="$BACKEND_PORT" "$BACKEND_PYTHON" app.py >/tmp/chatbot-backend.log 2>&1 &
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
