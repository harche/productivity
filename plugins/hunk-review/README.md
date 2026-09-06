# Hunk Review

One slash command for interactive Hunk reviews, inline questions, and automatic
comment watching. No skill and no separate watch command.

## Install and use

From the registered productivity marketplace:

```sh
claude plugin install --scope local hunk-review@productivity-tools
```

Open Hunk yourself in the repository you want to discuss, then invoke the
`hunk-review` command. Claude Code namespaces it by plugin:

```text
/hunk-review:hunk-review
/hunk-review:hunk-review <session-id>
/hunk-review:hunk-review stop
```

The command selects and pins a live Hunk session, answers outstanding inline
questions, and starts watching. Multiple matching sessions require a choice; it
never silently switches sessions. A full code review or source edits happen only
when requested.

## Requirements

- Hunk on PATH with the session CLI, including `comment list --type user --json`
  (the copied guide is from Hunk 0.20.1).
- Python 3 on PATH; the watcher uses only the standard library and works on macOS
  and Linux.
- A host background task tool whose terminal notification resumes the assistant.
  The command documents Pi's `bg_run` protocol. Other hosts must provide an
  equivalent notifying background-shell task; without one, automatic watching
  is unavailable, but normal inline interaction still works.

## Bundled watcher

`commands/hunk-review.md` contains the Hunk CLI guide and watch/reply/re-arm
instructions. `scripts/watch_comments.py` contains the implementation, so the
model runs it rather than generating Python on every turn:

```sh
python3 /absolute/plugin/path/scripts/watch_comments.py \
  --session '<session-id>' \
  --acknowledged-json '["user:already-answered-id"]' \
  --expires-at '<unix-timestamp>'
```

The assistant sets an expiry once (one hour by default), then reuses it and the
acknowledged IDs on every launch. Pass `[]` when no notes have been acknowledged.
The script polls every two seconds and exits with a JSON batch when it sees
unacknowledged user notes. That exit triggers the host notification. After
replying, the assistant re-arms the same script; it does not baseline away notes
added while replying. Only one watcher runs per conversation/session pair.

The script never sends replies, starts an LLM, or writes to the repository. It
exits on expiry or after three consecutive CLI failures. Stopping the review
cancels the task and prevents re-arming. Edited notes with an already acknowledged
ID do not wake the watcher; add a new comment for a follow-up question.

Exit codes: `0` for a detected batch or expiry (inspect the JSON `event`), `1` for
polling failure, `2` for invalid arguments, and `130` for keyboard interruption.
Host-initiated cancellation may instead be reported by the background task tool.

## Tests

From the marketplace root:

```sh
python3 -m unittest discover -s plugins/hunk-review/tests -v
```

Tests mock the Hunk CLI and clock; they do not control a live review session.
