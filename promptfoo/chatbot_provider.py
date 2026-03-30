#!/usr/bin/env python3
"""Promptfoo Python provider for the bank customer service chatbot backend."""

from __future__ import annotations

import json
import os
import sys
import urllib.parse
import urllib.request

BASE_URL = os.getenv("PROMPTFOO_CHATBOT_BASE_URL", "http://localhost:5001")
TIMEOUT_SECONDS = float(os.getenv("PROMPTFOO_HTTP_TIMEOUT", "20"))


def _read_json_response(request: urllib.request.Request) -> dict:
    with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
        payload = response.read().decode("utf-8", errors="replace")
    return json.loads(payload)


def _create_session() -> str:
    request = urllib.request.Request(
        url=f"{BASE_URL}/api/session",
        data=b"{}",
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    data = _read_json_response(request)
    session_id = data.get("session_id")
    if not session_id:
        raise RuntimeError("Session creation failed: missing session_id")
    return session_id


def _chat(session_id: str, user_message: str) -> str:
    query = urllib.parse.urlencode({"message": user_message})
    request = urllib.request.Request(
        url=f"{BASE_URL}/api/chat/{session_id}?{query}",
        headers={"Accept": "text/event-stream"},
        method="GET",
    )

    chunks: list[str] = []
    with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
        for raw_line in response:
            line = raw_line.decode("utf-8", errors="replace").strip()
            if not line.startswith("data: "):
                continue

            raw_json = line[6:]
            try:
                item = json.loads(raw_json)
            except json.JSONDecodeError:
                continue

            text = item.get("text")
            if isinstance(text, str):
                chunks.append(text)

            if item.get("done") is True:
                break

    return "".join(chunks).strip()


def call_api(prompt: str, options: dict, context: dict) -> dict:
    """Promptfoo provider entrypoint."""
    try:
        session_id = _create_session()
        output = _chat(session_id, prompt)
        return {"output": output}
    except Exception as exc:  # pragma: no cover
        return {"output": "", "error": str(exc)}


def main() -> int:
    if len(sys.argv) < 2:
        print("", end="")
        return 0

    prompt = sys.argv[1]

    result = call_api(prompt, {}, {})
    if result.get("error"):
        print(f"Promptfoo provider error: {result['error']}", file=sys.stderr)
        return 1
    print(result.get("output", ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
