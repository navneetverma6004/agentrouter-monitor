#!/usr/bin/env python3
"""
AgentRouter uptime monitor.

Sends a minimal (max_tokens=1) request to AgentRouter's Anthropic-compatible
/v1/messages endpoint and reports whether the service is reachable. Only
sends a push notification (via ntfy.sh) when the status CHANGES, so you get
one alert when it goes down and one when it recovers -- not a message every
5 minutes.

Required environment variables (set as GitHub Actions secrets):
  AGENTROUTER_API_KEY  - your AgentRouter API key
  NTFY_TOPIC           - a unique, hard-to-guess topic name for ntfy.sh

Optional:
  AGENTROUTER_MODEL    - defaults to claude-opus-4-6
"""

import json
import os
import time
import urllib.error
import urllib.request

AGENTROUTER_URL = "https://agentrouter.org/v1/messages"
API_KEY = os.environ["AGENTROUTER_API_KEY"]
MODEL = os.environ.get("AGENTROUTER_MODEL", "claude-opus-4-6")
NTFY_TOPIC = os.environ["NTFY_TOPIC"]
STATE_FILE = "state.json"
TIMEOUT = 25


def check_api():
    """Returns (is_up: bool, detail: str)."""
    payload = json.dumps(
        {
            "model": MODEL,
            "max_tokens": 1,
            "messages": [{"role": "user", "content": "ping"}],
        }
    ).encode()

    req = urllib.request.Request(
        AGENTROUTER_URL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}",
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return True, f"HTTP {resp.status}"
    except urllib.error.HTTPError as e:
        # 401/403/429 mean the service itself responded -- it's up, your
        # key or quota is the issue, not an outage. Treat as "up".
        if e.code in (401, 403, 429):
            return True, f"HTTP {e.code} (service responded, check key/quota)"
        return False, f"HTTP {e.code}"
    except urllib.error.URLError as e:
        return False, f"unreachable ({e.reason})"
    except Exception as e:
        return False, f"error ({e})"


def load_state():
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except Exception:
        return {"status": "unknown"}


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)


def notify(title, message, priority="default"):
    url = f"https://ntfy.sh/{NTFY_TOPIC}"
    # HTTP headers are sent as latin-1. Emoji/unicode in a header value
    # crashes urllib unless re-encoded this way (ntfy then reads it back
    # as UTF-8 on their end, so the emoji still displays correctly).
    safe_title = title.encode("utf-8").decode("latin-1")
    req = urllib.request.Request(
        url,
        data=message.encode("utf-8"),
        headers={"Title": safe_title, "Priority": priority},
        method="POST",
    )
    try:
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        print(f"Failed to send notification: {e}")


def main():
    prev = load_state()
    up, detail = check_api()
    now = "up" if up else "down"

    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] status={now} ({detail})")

    if prev.get("status") != now:
        if now == "down":
            notify("🔴 AgentRouter is DOWN", f"Check failed: {detail}", priority="high")
        elif prev.get("status") != "unknown":
            notify("🟢 AgentRouter is back UP", f"Recovered: {detail}", priority="default")

    save_state({"status": now, "last_checked": time.time(), "detail": detail})


if __name__ == "__main__":
    main()
