# Hunk Review

A slash command that finds your live [Hunk](https://github.com/hunkdiff/hunk)
session and runs a background watcher so comments you leave in the Hunk UI wake
the assistant, which answers them inline.

The command does not embed Hunk's CLI reference. It runs `hunk skill path` and
reads Hunk's bundled skill, so it stays correct across Hunk upgrades.

## Install and use

```sh
claude plugin install --scope local hunk-review@productivity-tools
```

Open Hunk in the repository you want to discuss, then:

```text
/hunk-review:hunk-review               # match the current repo/worktree
/hunk-review:hunk-review <session-id>  # pick one of several sessions
/hunk-review:hunk-review stop          # cancel the watcher
```

The assistant pins one session, starts the watcher, and yields. Leave a comment
in Hunk; the watcher exits, the assistant wakes, answers at that file/line with
`hunk session comment add`, and re-arms. It never starts a full review or edits
source unless you ask.

## Requirements

- Hunk on PATH with `hunk skill path` and `hunk session comment list --type user --json`
  (0.20.1 or later).
- Python 3 on PATH. The watcher uses only the standard library; macOS and Linux.
- A host background task that resumes the assistant on exit: Claude Code's
  background Bash, or Pi's `bg_run`.

## Watcher script

`scripts/watch_comments.py` polls every two seconds and exits with a JSON event
when unacknowledged user notes appear, on expiry, or after three consecutive
CLI failures. It only reads comments; it never replies or touches the repo.

```sh
python3 scripts/watch_comments.py \
  --session '<session-id>' \
  --acknowledged-json '["noteId-already-answered"]' \
  --expires-at '<unix-timestamp>'
```

Events: `hunk_user_comments`, `hunk_watch_expired`, `hunk_watch_error`,
`hunk_watch_cancelled`. Exit codes: 0 batch or expiry, 1 poll failure,
2 bad arguments, 130 interrupted. Edited notes do not re-trigger; add a new
comment for a follow-up.

## Tests

```sh
python3 -m unittest discover -s plugins/hunk-review/tests -v
```
