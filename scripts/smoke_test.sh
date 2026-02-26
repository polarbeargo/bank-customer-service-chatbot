#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_URL="http://localhost:5001"

health_check() {
  curl -s "${BACKEND_URL}/api/health" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    if data.get('status') != 'healthy':
        sys.exit(1)
except Exception:
    sys.exit(1)
"
}

create_session() {
  curl -s -X POST "${BACKEND_URL}/api/session" -H "Content-Type: application/json" -d '{}' | \
  python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    sid = data.get('session_id')
    if not sid:
        sys.exit(1)
    print(sid)
except Exception:
    sys.exit(1)
"
}

stream_message() {
  local session_id="$1"
  local message="$2"
  local response
  response=$(curl -sN "${BACKEND_URL}/api/chat/${session_id}?message=${message}")
  echo "$response" | grep -q '"done": true'
}

stream_contains() {
  local session_id="$1"
  local message="$2"
  local needle="$3"
  local response full_text
  response=$(curl -sN "${BACKEND_URL}/api/chat/${session_id}?message=${message}")
  # Extract text from JSON chunks and concatenate
  full_text=$(echo "$response" | grep '^data:' | sed 's/^data: //' | python3 -c "
import json, sys
text = ''
for line in sys.stdin:
    try:
        data = json.loads(line)
        if 'text' in data:
            text += data['text']
    except:
        pass
print(text)
")
  echo "$full_text" | grep -qi "$needle"
}

sensitive_requires_verification() {
  local session_id="$1"
  local response
  response=$(curl -sN "${BACKEND_URL}/api/chat/${session_id}?message=what%20is%20my%20account%20balance")
  echo "$response" | grep -qi "For security reasons"
}

sensitive_data_not_returned() {
  local session_id="$1"
  if curl -sN "${BACKEND_URL}/api/chat/${session_id}?message=what%20is%20my%20account%20balance" | grep -qi "TWD 2,500,394"; then
    return 1
  fi
  if curl -sN "${BACKEND_URL}/api/chat/${session_id}?message=what%20is%20my%20loan%20balance" | grep -qi "TWD 19,243,225"; then
    return 1
  fi
  if curl -sN "${BACKEND_URL}/api/chat/${session_id}?message=what%20is%20my%20account%20number" | grep -qi "6102394256679291"; then
    return 1
  fi
  if curl -sN "${BACKEND_URL}/api/chat/${session_id}?message=what%20is%20my%20opening%20branch" | grep -qi "Taipei First Main Branch"; then
    return 1
  fi
}

password_never_returned() {
  local session_id="$1"
  if curl -sN "${BACKEND_URL}/api/chat/${session_id}?message=what%20is%20my%20password" | grep -qi "password"; then
    return 1
  fi
}

verify_tony_stark() {
  local session_id="$1"
  curl -sN "${BACKEND_URL}/api/chat/${session_id}?message=what%20is%20my%20account%20balance" > /dev/null
  stream_contains "$session_id" "Tony%20Stark,%201996/09/10,%20A234763849" "verified"
}

check_account_balance() {
  local session_id="$1"
  curl -sN "${BACKEND_URL}/api/chat/${session_id}?message=what%20is%20my%20account%20balance" > /dev/null
  curl -sN "${BACKEND_URL}/api/chat/${session_id}?message=Tony%20Stark,%201996/09/10,%20A234763849" > /dev/null
  stream_contains "$session_id" "what%20is%20my%20account%20balance" "2,500,394"
}

check_account_number() {
  local session_id="$1"
  curl -sN "${BACKEND_URL}/api/chat/${session_id}?message=what%20is%20my%20account%20number" > /dev/null 2>&1 || true
  curl -sN "${BACKEND_URL}/api/chat/${session_id}?message=Tony%20Stark,%201996/09/10,%20A234763849" > /dev/null 2>&1 || true
  stream_contains "$session_id" "what%20is%20my%20account%20number" "6102394256679291"
}

check_loan_balance() {
  local session_id="$1"
  curl -sN "${BACKEND_URL}/api/chat/${session_id}?message=what%20is%20my%20loan%20balance" > /dev/null 2>&1 || true
  curl -sN "${BACKEND_URL}/api/chat/${session_id}?message=Tony%20Stark,%201996/09/10,%20A234763849" > /dev/null 2>&1 || true
  stream_contains "$session_id" "what%20is%20my%20loan%20balance" "TWD 19,243,225"
}

check_opening_branch() {
  local session_id="$1"
  curl -sN "${BACKEND_URL}/api/chat/${session_id}?message=what%20is%20my%20opening%20branch" > /dev/null 2>&1 || true
  curl -sN "${BACKEND_URL}/api/chat/${session_id}?message=Tony%20Stark,%201996/09/10,%20A234763849" > /dev/null 2>&1 || true
  stream_contains "$session_id" "what%20is%20my%20opening%20branch" "Taipei First Main Branch"
}

echo "[SMOKE] Backend health check"
for i in 1 2 3 4 5; do
  if health_check; then
    break
  fi
  if [ "$i" -eq 5 ]; then
    echo "[SMOKE] Backend health check failed"
    exit 1
  fi
  sleep 2
done

SESSION_ID="$(create_session)"

echo "[SMOKE] Streaming response"
stream_message "$SESSION_ID" "what%20services%20do%20you%20offer"

SESSION_ID="$(create_session)"
echo "[SMOKE] Sensitive query requires verification"
sensitive_requires_verification "$SESSION_ID"

SESSION_ID="$(create_session)"
echo "[SMOKE] Sensitive data not returned before verification"
sensitive_data_not_returned "$SESSION_ID"

SESSION_ID="$(create_session)"
echo "[SMOKE] Password never returned"
password_never_returned "$SESSION_ID"

SESSION_ID="$(create_session)"
echo "[SMOKE] Verify Tony Stark credentials"
verify_tony_stark "$SESSION_ID"

SESSION_ID="$(create_session)"
echo "[SMOKE] Verify account balance"
check_account_balance "$SESSION_ID"

SESSION_ID="$(create_session)"
echo "[SMOKE] Verify account number"
check_account_number "$SESSION_ID"

SESSION_ID="$(create_session)"
echo "[SMOKE] Verify loan balance"
check_loan_balance "$SESSION_ID"

SESSION_ID="$(create_session)"
echo "[SMOKE] Verify opening branch"
check_opening_branch "$SESSION_ID"

echo "[SMOKE] OK"
