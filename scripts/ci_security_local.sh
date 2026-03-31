#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if ! command -v uv >/dev/null 2>&1; then
  echo "[ERROR] uv is not installed or not in PATH."
  exit 1
fi

echo "[CI-LOCAL] Setting up backend venv with uv"
if [[ ! -d backend/.venv ]]; then
  uv venv backend/.venv
fi
uv pip install --python backend/.venv/bin/python -r backend/requirements.txt

echo "[CI-LOCAL] Running backend tests"
(
  cd backend
  uv run --python .venv/bin/python test_chatbot.py
) | tee backend-test-output.txt
grep -q "Failed: 0" backend-test-output.txt

echo "[CI-LOCAL] Starting backend API on :5001"
( cd backend && PORT=5001 uv run --python .venv/bin/python app.py ) > backend-ci-local.log 2>&1 &
BACKEND_PID=$!

cleanup() {
  kill "$BACKEND_PID" >/dev/null 2>&1 || true
}
trap cleanup EXIT

echo "[CI-LOCAL] Waiting for backend health"
for i in $(seq 1 60); do
  if curl -fsS "http://localhost:5001/api/health" >/dev/null; then
    break
  fi
  sleep 1
done

curl -fsS "http://localhost:5001/api/health" >/dev/null

echo "[CI-LOCAL] Running Promptfoo eval"
PROMPTFOO_CHATBOT_BASE_URL="http://localhost:5001" \
PROMPTFOO_HTTP_TIMEOUT="20" \
  npx promptfoo eval -c promptfoo/promptfooconfig.yaml

if [[ "${RUN_REDTEAM:-0}" == "1" ]]; then
  echo "[CI-LOCAL] Running Promptfoo red-team (throttled: ~40 cases, concurrency=1)"
  PROMPTFOO_CHATBOT_BASE_URL="http://localhost:5001" \
  PROMPTFOO_HTTP_TIMEOUT="30" \
    npx promptfoo redteam run \
      --config promptfoo/redteam-local.yaml \
      --max-concurrency 1
else
  echo "[CI-LOCAL] Skipping Promptfoo red-team (set RUN_REDTEAM=1 to enable)"
fi

echo "[CI-LOCAL] Security dry-run completed successfully"
