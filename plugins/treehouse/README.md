# Treehouse Review

Answer inline review comments you leave in VS Code. Pairs with the **Worktree
Review** VS Code extension, which adds GitHub-style comment threads to any file
or diff in a git worktree and stores them in `<worktree>/.treehouse/comments.json`
(self-gitignored). Agent replies show up live in the VS Code thread.

Like `hunk-review`, but threads persist on disk (survive restarts), follow their
code as lines move, and work on the branch diff vs origin's default branch as
well as uncommitted changes.

## Install and use

```sh
claude plugin install --scope local treehouse@productivity-tools
```

In a worktree open in VS Code:

```text
/treehouse:review        # watch for comments and answer each as it arrives
/treehouse:review stop   # cancel the watcher
```

Or just say "check my comments" for a one-pass answer (the `treehouse-review` skill).

## Requirements

- The Treehouse Review VS Code extension (source: `treehouse/vscode-extension`).
- Python 3 on PATH; scripts use only the standard library; macOS and Linux.
- For the watcher: a host background task that resumes the assistant on exit
  (Claude Code background Bash, or Pi's `bg_run`).

## Scripts

`scripts/comments.py` — read and answer threads:
`list [--all]`, `pending`, `show <id>`, `reply <id> <text|->`, `resolve`, `reopen`,
`add --file F --line N <text>`. Pass `--root` or run inside the worktree.

`scripts/watch_comments.py` — polls every second and exits with a JSON event when
a thread's latest message is from the user and its id is not acknowledged, on
expiry, or after three consecutive read failures. Read-only.

```sh
python3 scripts/watch_comments.py --root "$PWD" --acknowledged-json '[]' --expires-at "$(( $(date +%s) + 3600 ))"
```

Events: `treehouse_user_comments`, `treehouse_watch_expired`, `treehouse_watch_error`,
`treehouse_watch_cancelled`. Exit codes: 0 batch or expiry, 1 read failure, 2 bad
arguments, 130 interrupted.

## Tests

```sh
python3 -m unittest discover -s plugins/treehouse/tests -v
```
