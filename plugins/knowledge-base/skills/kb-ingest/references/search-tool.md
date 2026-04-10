# Default Search Tool

When initializing a new KB, create `tools/search` with this script and `chmod +x` it.

```python
#!/usr/bin/env python3
"""Search the knowledge base wiki and raw sources.

Usage:
    tools/search <query> [--raw] [--all] [--context N]

Examples:
    tools/search gomaxprocs              # search wiki articles
    tools/search "stop-the-world" --raw  # search raw sources too
    tools/search crio --context 3        # show 3 lines of context
    tools/search "customer.*512" --all   # regex, search everything
"""

import argparse
import os
import re
import sys
from pathlib import Path


def find_kb_root():
    """Walk up from script location to find KB root (has AGENTS.md)."""
    d = Path(__file__).resolve().parent.parent
    if (d / "AGENTS.md").exists():
        return d
    # fallback: cwd
    d = Path.cwd()
    while d != d.parent:
        if (d / "AGENTS.md").exists():
            return d
        d = d.parent
    print("Error: could not find KB root (no AGENTS.md found)", file=sys.stderr)
    sys.exit(1)


def search_files(root, dirs, pattern, context_lines):
    """Search markdown files in given directories for a pattern."""
    results = []
    for d in dirs:
        dirpath = root / d
        if not dirpath.exists():
            continue
        for fp in sorted(dirpath.rglob("*.md")):
            if fp.name.startswith("_") and fp.name != "_index.md":
                continue
            try:
                lines = fp.read_text().splitlines()
            except Exception:
                continue
            for i, line in enumerate(lines):
                if pattern.search(line):
                    rel = fp.relative_to(root)
                    start = max(0, i - context_lines)
                    end = min(len(lines), i + context_lines + 1)
                    ctx = []
                    for j in range(start, end):
                        prefix = ">" if j == i else " "
                        ctx.append(f"  {prefix} {j+1:4d} | {lines[j]}")
                    results.append((str(rel), i + 1, ctx))
    return results


def main():
    parser = argparse.ArgumentParser(description="Search the knowledge base")
    parser.add_argument("query", help="Search query (regex supported)")
    parser.add_argument("--raw", action="store_true", help="Also search raw/ sources")
    parser.add_argument("--all", action="store_true", help="Search wiki/, raw/, and outputs/")
    parser.add_argument("--context", "-C", type=int, default=1, help="Lines of context (default: 1)")
    parser.add_argument("--ignore-case", "-i", action="store_true", help="Case-insensitive search")
    args = parser.parse_args()

    root = find_kb_root()

    flags = re.IGNORECASE if args.ignore_case else 0
    try:
        pattern = re.compile(args.query, flags)
    except re.error as e:
        print(f"Invalid regex: {e}", file=sys.stderr)
        sys.exit(1)

    dirs = ["wiki"]
    if args.raw or args.all:
        dirs.append("raw")
    if args.all:
        dirs.append("outputs")

    results = search_files(root, dirs, pattern, args.context)

    if not results:
        print(f"No matches for '{args.query}' in {', '.join(dirs)}/")
        sys.exit(0)

    print(f"{len(results)} match(es) for '{args.query}':\n")
    current_file = None
    for filepath, lineno, ctx_lines in results:
        if filepath != current_file:
            if current_file is not None:
                print()
            print(f"\033[1m{filepath}\033[0m")
            current_file = filepath
        for cl in ctx_lines:
            # highlight the match line
            if cl.startswith("  >"):
                print(f"\033[33m{cl}\033[0m")
            else:
                print(cl)
        print()


if __name__ == "__main__":
    main()
```
