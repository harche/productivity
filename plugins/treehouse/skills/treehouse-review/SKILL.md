---
name: treehouse-review
description: Answer the user's inline review comments left in VS Code via the Treehouse Review extension (stored in .treehouse/comments.json in the worktree). Use when the user says "check my comments", "address my review", "I left notes in VS Code", "reply to my comments", or similar. For a live back-and-forth with a background watcher, the user runs /treehouse:review instead.
---

# Treehouse Review comments (one pass)

The user leaves line comments in VS Code; answer them with the bundled CLI.
Never edit `.treehouse/comments.json` by hand.

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/comments.py" pending
```

If `CLAUDE_PLUGIN_ROOT` is unset, the script is at `../../scripts/comments.py`
relative to this file.

For each thread printed (with code context):

- Question → answer it.
- Change request → make the change, then reply with what you changed.
- Unclear → reply with a clarifying question instead of guessing.
- Reply: `comments.py reply <id> '<text>'` (Markdown; `-` reads stdin). Ids accept unique prefixes.

Do not resolve or delete threads unless the user asks. Other commands: `list [--all]`,
`show <id>`, `add --file F --line N '<text>'` (start a thread to flag something for the user).
Line numbers refer to the current working-tree file.

Finish with a one-line summary per thread in chat. If the user wants ongoing
back-and-forth, suggest `/treehouse:review`.
