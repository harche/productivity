#!/usr/bin/env python3
"""
IBKR session keepalive — calls /tickle periodically to prevent session timeout.

Usage:
    python3 keepalive.py              # tickle every 4 minutes (default)
    python3 keepalive.py --interval 3 # tickle every 3 minutes
    python3 keepalive.py --once       # single tickle, then exit
"""

from __future__ import annotations

import argparse
import sys
import time
from datetime import datetime

# Allow running from the scripts directory
sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))

from ibkr_client import api_post, api_get


def tickle() -> dict:
    """Call /tickle and return the response."""
    return api_post("/tickle")


def check_auth() -> dict:
    """Check authentication status."""
    return api_get("/iserver/auth/status")


def run(interval_minutes: float, once: bool) -> None:
    # Initial check
    try:
        status = check_auth()
    except Exception as e:
        sys.exit(f"ERROR: Cannot reach gateway — {e}")

    if not status.get("authenticated"):
        sys.exit(
            "ERROR: Not authenticated. Log in at https://localhost:5000 "
            "or run: python3 start_gateway.py"
        )

    if once:
        resp = tickle()
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"[{ts}] Tickle OK — session: {resp.get('session', 'N/A')}")
        return

    print(f"Keepalive started — tickling every {interval_minutes} min. Ctrl+C to stop.")

    consecutive_failures = 0
    max_failures = 3

    while True:
        try:
            resp = tickle()
            ts = datetime.now().strftime("%H:%M:%S")
            print(f"[{ts}] Tickle OK — session: {resp.get('session', 'N/A')}")
            consecutive_failures = 0
            time.sleep(interval_minutes * 60)
        except KeyboardInterrupt:
            print("\nStopped.")
            break
        except Exception:
            consecutive_failures += 1
            ts = datetime.now().strftime("%H:%M:%S")
            if consecutive_failures >= max_failures:
                print(f"[{ts}] Gateway unreachable after {max_failures} attempts. Exiting.")
                break
            print(f"[{ts}] Gateway unreachable ({consecutive_failures}/{max_failures}). Retrying in 30s...")
            time.sleep(30)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="IBKR session keepalive")
    parser.add_argument(
        "--interval", type=float, default=4,
        help="Minutes between tickles (default: 4)",
    )
    parser.add_argument(
        "--once", action="store_true",
        help="Single tickle then exit",
    )
    args = parser.parse_args()
    run(args.interval, args.once)
