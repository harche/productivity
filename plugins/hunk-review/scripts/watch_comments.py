#!/usr/bin/env python3
"""Exit with a JSON batch when a pinned Hunk session has unacknowledged notes."""

import argparse
import json
import math
import subprocess
import sys
import time


def read_comments(session, timeout):
    result = subprocess.run(
        ["hunk", "session", "comment", "list", session, "--type", "user", "--json"],
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if result.returncode != 0:
        raise ValueError(
            result.stderr.strip() or result.stdout.strip()
            or f"hunk exited with code {result.returncode}"
        )
    payload = json.loads(result.stdout)
    if not isinstance(payload, dict) or not isinstance(payload.get("comments"), list):
        raise ValueError("expected a JSON object containing a comments array")
    comments = payload["comments"]
    if any(
        not isinstance(note, dict)
        or not isinstance(note.get("noteId"), str)
        or not note["noteId"]
        for note in comments
    ):
        raise ValueError("expected each comment to have a nonempty string noteId")
    # Replies must never wake the watcher, even if the CLI returns mixed sources.
    return [note for note in comments if note.get("source") == "user"]


def emit(event, session, **fields):
    print(json.dumps({"event": event, "sessionId": session, **fields}, indent=2), flush=True)


def watch(session, acknowledged, expires_at, interval=2):
    # Keep the original wall-clock expiry across re-arms, but use a monotonic
    # timer within this process so clock adjustments cannot prolong a poll loop.
    deadline = time.monotonic() + max(0, expires_at - time.time())
    failures = 0
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            emit("hunk_watch_expired", session)
            return 0
        try:
            comments = read_comments(session, timeout=min(10, remaining))
            # Do not snapshot a new baseline: notes added while the assistant
            # was replying must remain pending on the next launch.
            pending = [note for note in comments if note["noteId"] not in acknowledged]
            failures = 0
            if pending:
                emit("hunk_user_comments", session, comments=pending)
                return 0
        except (OSError, subprocess.SubprocessError, ValueError) as error:
            failures += 1
            print(
                f"Hunk session {session}: poll failed ({failures}/3): {error}",
                file=sys.stderr, flush=True,
            )
            if failures >= 3:
                emit(
                    "hunk_watch_error", session,
                    error=str(error),
                    action="Check that the selected Hunk session and daemon are reachable before restarting.",
                )
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
    parser.add_argument("--session", required=True, help="Exact Hunk session ID (not a repo selector)")
    parser.add_argument(
        "--acknowledged-json", default="[]",
        help="JSON array of user note IDs already answered or explicitly skipped",
    )
    parser.add_argument(
        "--expires-at", required=True, type=finite_number,
        help="Fixed review expiry as Unix seconds; reuse this value on every re-arm",
    )
    parser.add_argument("--interval", type=finite_number, default=2, help="Polling interval in seconds (default: 2)")
    args = parser.parse_args(argv)
    if not args.session.strip() or args.session.startswith("-"):
        parser.error("--session must be a nonempty session ID, not an option")
    if args.interval <= 0:
        parser.error("--interval must be greater than zero")
    try:
        acknowledged = json.loads(args.acknowledged_json)
    except ValueError:
        parser.error("--acknowledged-json must be a JSON array of nonempty note ID strings")
    if not isinstance(acknowledged, list) or any(
        not isinstance(note_id, str) or not note_id for note_id in acknowledged
    ):
        parser.error("--acknowledged-json must be a JSON array of nonempty note ID strings")
    args.acknowledged = set(acknowledged)
    return args


def main(argv=None):
    args = parse_args(argv)
    try:
        return watch(args.session, args.acknowledged, args.expires_at, args.interval)
    except KeyboardInterrupt:
        emit("hunk_watch_cancelled", args.session)
        return 130


if __name__ == "__main__":
    sys.exit(main())
