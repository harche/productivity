#!/usr/bin/env python3
"""Read and answer review threads left in VS Code by the Treehouse Review extension.

Threads live in <git toplevel>/.treehouse/comments.json. Run from inside the worktree or pass --root.

  comments.py list [--all] [--json]       open threads (--all includes resolved)
  comments.py pending [--json]            open threads whose last message is from the user
  comments.py show <id>                   one thread with code context
  comments.py reply <id> <text|->         reply as the agent ("-" reads stdin)
  comments.py resolve <id> | reopen <id>
  comments.py add --file F --line N <text|->   start a thread as the agent
"""

import argparse
import datetime
import json
import os
import random
import string
import subprocess
import sys
import time


def git_root(start=None):
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"], cwd=start, text=True, stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return os.path.abspath(start or os.getcwd())


def store_path(root):
    return os.path.join(root, ".treehouse", "comments.json")


def load(root):
    try:
        with open(store_path(root)) as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {"version": 1, "threads": []}
    data.setdefault("threads", [])
    return data


def save(root, data):
    directory = os.path.dirname(store_path(root))
    os.makedirs(directory, exist_ok=True)
    ignore = os.path.join(directory, ".gitignore")
    if not os.path.exists(ignore):
        with open(ignore, "w") as f:
            f.write("*\n")
    tmp = f"{store_path(root)}.{os.getpid()}.tmp"
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")
    os.replace(tmp, store_path(root))


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def new_id(prefix):
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=4))
    return prefix + format(int(time.time() * 1000), "x") + suffix


def is_open(thread):
    return thread.get("status") != "resolved"


def awaiting_agent(thread):
    return is_open(thread) and bool(thread["comments"]) and thread["comments"][-1]["author"] != "agent"


def find(data, thread_id):
    hits = [t for t in data["threads"] if t["id"] == thread_id] or [
        t for t in data["threads"] if t["id"].startswith(thread_id)
    ]
    if len(hits) != 1:
        sys.exit(f"treehouse-comments: {'no' if not hits else 'ambiguous'} thread matching {thread_id!r}")
    return hits[0]


def file_lines(root, rel):
    try:
        with open(os.path.join(root, rel)) as f:
            return f.read().splitlines()
    except OSError:
        return None


def text_arg(value):
    return sys.stdin.read().strip() if value == "-" else value


def show(root, thread, context=3):
    flags = [thread.get("status", "open")]
    if thread.get("outdated"):
        flags.append("outdated")
    if awaiting_agent(thread):
        flags.append("awaiting agent")
    print(f"[{thread['id']}] {thread['file']}:{thread['line']}  ({', '.join(flags)})")
    lines = file_lines(root, thread["file"])
    if lines is not None:
        i = thread["line"] - 1
        for n in range(max(0, i - context), min(len(lines), i + context + 1)):
            print(f"  {'>' if n == i else ' '} {n + 1:5} | {lines[n]}")
    elif thread.get("anchor"):
        print(f"  > (file missing) | {thread['anchor'].get('text', '')}")
    for c in thread["comments"]:
        who = "agent" if c["author"] == "agent" else "user"
        print(f"  {who:>5}: " + c["body"].replace("\n", "\n         "))
    print()


def output(root, threads, as_json):
    if as_json:
        json.dump(threads, sys.stdout, indent=2)
        print()
    elif not threads:
        print("no threads")
    else:
        for t in threads:
            show(root, t)


def main(argv=None):
    parser = argparse.ArgumentParser(prog="comments.py", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", help="worktree root (default: git toplevel of the current directory)")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("list"); p.add_argument("--all", action="store_true"); p.add_argument("--json", action="store_true")
    p = sub.add_parser("pending"); p.add_argument("--json", action="store_true")
    p = sub.add_parser("show"); p.add_argument("id")
    p = sub.add_parser("reply"); p.add_argument("id"); p.add_argument("text"); p.add_argument("--resolve", action="store_true")
    p = sub.add_parser("resolve"); p.add_argument("id")
    p = sub.add_parser("reopen"); p.add_argument("id")
    p = sub.add_parser("add"); p.add_argument("--file", required=True); p.add_argument("--line", type=int, required=True); p.add_argument("text")
    args = parser.parse_args(argv)
    root = git_root(args.root)

    if args.cmd == "list":
        output(root, [t for t in load(root)["threads"] if args.all or is_open(t)], args.json)
    elif args.cmd == "pending":
        output(root, [t for t in load(root)["threads"] if awaiting_agent(t)], args.json)
    elif args.cmd == "show":
        show(root, find(load(root), args.id), context=6)
    elif args.cmd in ("reply", "resolve", "reopen"):
        data = load(root)
        thread = find(data, args.id)
        if args.cmd == "reply":
            thread["comments"].append({"id": new_id("c"), "author": "agent", "name": "Agent",
                                       "body": text_arg(args.text), "createdAt": now()})
        if args.cmd == "resolve" or getattr(args, "resolve", False):
            thread["status"] = "resolved"
        elif args.cmd == "reopen":
            thread["status"] = "open"
        save(root, data)
        print(f"{args.cmd}: {thread['id']}")
    elif args.cmd == "add":
        rel = os.path.relpath(os.path.abspath(args.file), root) if os.path.isabs(args.file) or os.path.exists(args.file) else args.file
        lines = file_lines(root, rel) or []
        i = args.line - 1
        anchor = {"text": lines[i] if 0 <= i < len(lines) else "",
                  "before": lines[max(0, i - 2):max(0, i)], "after": lines[i + 1:i + 3]}
        data = load(root)
        thread = {"id": new_id("t"), "file": rel, "line": args.line, "anchor": anchor, "status": "open", "createdAt": now(),
                  "comments": [{"id": new_id("c"), "author": "agent", "name": "Agent",
                                "body": text_arg(args.text), "createdAt": now()}]}
        data["threads"].append(thread)
        save(root, data)
        print(f"added: {thread['id']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
