#!/usr/bin/env python3
"""Exit with a JSON batch when a worktree has review threads awaiting the agent."""

import argparse
import json
import math
import os
import sys
import time


def read_threads(root):
    """Return threads from <root>/.treehouse/comments.json ([] if the file does not exist yet)."""
    try:
        with open(os.path.join(root, ".treehouse", "comments.json")) as f:
            payload = json.load(f)
    except FileNotFoundError:
        return []
    if not isinstance(payload, dict) or not isinstance(payload.get("threads", []), list):
        raise ValueError("expected a JSON object containing a threads array")
    return payload.get("threads", [])


def pending(threads, acknowledged):
    """Open threads whose last message is from the user and not yet acknowledged (keyed by that message id)."""
    out = []
    for t in threads:
        comments = t.get("comments") or []
        if t.get("status") == "resolved" or not comments:
            continue
        last = comments[-1]
        if last.get("author") == "agent" or last.get("id") in acknowledged:
            continue
        out.append({"threadId": t.get("id"), "commentId": last.get("id"), "file": t.get("file"),
                    "line": t.get("line"), "outdated": bool(t.get("outdated")), "comments": comments})
    return out


def emit(event, root, **fields):
    print(json.dumps({"event": event, "root": root, **fields}, indent=2), flush=True)


def watch(root, acknowledged, expires_at, interval=1):
    # Fixed wall-clock expiry across re-arms; monotonic timer within this process.
    deadline = time.monotonic() + max(0, expires_at - time.time())
    failures = 0
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            emit("treehouse_watch_expired", root)
            return 0
        try:
            # No fresh baseline: messages added while the assistant was replying stay pending.
            batch = pending(read_threads(root), acknowledged)
            failures = 0
            if batch:
                emit("treehouse_user_comments", root, threads=batch)
                return 0
        except (OSError, ValueError) as error:
            failures += 1
            print(f"{root}: poll failed ({failures}/3): {error}", file=sys.stderr, flush=True)
            if failures >= 3:
                emit("treehouse_watch_error", root, error=str(error),
                     action="Check that .treehouse/comments.json is readable before restarting.")
                return 1
        time.sleep(min(interval, max(0, deadline - time.monotonic())))


def finite_number(value):
    try:
        number = float(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("expected a finite number") from error
    if not math.isfinite(number):
        raise argparse.ArgumentTypeError("expected a finite number")
    return number


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, help="Absolute worktree root (git toplevel)")
    parser.add_argument("--acknowledged-json", default="[]",
                        help="JSON array of user comment IDs already answered or explicitly skipped")
    parser.add_argument("--expires-at", required=True, type=finite_number,
                        help="Fixed review expiry as Unix seconds; reuse this value on every re-arm")
    parser.add_argument("--interval", type=finite_number, default=1, help="Polling interval in seconds (default: 1)")
    args = parser.parse_args(argv)
    if not os.path.isabs(args.root) or not os.path.isdir(args.root):
        parser.error("--root must be an existing absolute directory")
    if args.interval <= 0:
        parser.error("--interval must be greater than zero")
    try:
        acknowledged = json.loads(args.acknowledged_json)
    except ValueError:
        parser.error("--acknowledged-json must be a JSON array of nonempty comment ID strings")
    if not isinstance(acknowledged, list) or any(not isinstance(i, str) or not i for i in acknowledged):
        parser.error("--acknowledged-json must be a JSON array of nonempty comment ID strings")
    args.acknowledged = set(acknowledged)
    return args


def main(argv=None):
    args = parse_args(argv)
    try:
        return watch(args.root, args.acknowledged, args.expires_at, args.interval)
    except KeyboardInterrupt:
        emit("treehouse_watch_cancelled", args.root)
        return 130


if __name__ == "__main__":
    sys.exit(main())
