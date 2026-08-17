# Fleet: Conductor + Worker Claude Sessions Across Worktrees

Orchestrate N independent work items (across one or many repos) by running a fleet of autonomous Claude Code sessions, one per task worktree, each in its own tmux window — conducted and babysat from the current session. Extends `worktrees.md` (one workspace per PR/issue) to many task-named workspaces at once.

Use when a planning/audit phase produced a list of independent work items (parity gaps, per-KEP features, a bug list). Versus built-in subagents, tmux workers are **user-joinable, persistent, per-worktree sessions**: the user can attach to any window and steer, and each keeps its own resumable history (`claude --continue` in the worktree only sees that worktree's sessions).

## Fleet Setup

- Worktrees are task-named: `git worktree add .worktrees/<task> -b wt/<task> origin/main` — base on **freshly-fetched `origin/main`**, never `HEAD` (checkouts are often on feature branches). Multiple worktrees per repo is fine.
- Never touch existing checkouts or `.worktrees/` entries you didn't create this session.
- Windows go **in the current tmux session**, named `<repo-short>-<task>` (e.g. `tpu-seamless-upgrades`) when the fleet spans repos. Check for name collisions with existing windows BEFORE creating: `tmux rename-window -t "$S:name"` errors ambiguously ("can't find window") when two windows share a name — move then rename immediately, or use unique names from the start.

## Handoff Briefs (`CLAUDE.local.md`) — the highest-leverage piece

Write one per worktree. It is auto-loaded when any Claude session starts there, so pickup needs zero prompting. Required sections:

1. **Task + branch + push remote** ("Branch `wt/<task>` (tracks origin/main). Push to fork remote `<name>`, PR against `<upstream>` main.")
2. **The gap/bug with file:line evidence** — claims the worker can verify, not vibes.
3. **Reference implementations as absolute paths into sibling repos** — workers read them directly; this is what makes cross-repo porting work.
4. **Suggested approach** (numbered), **test expectations**, **repo-specific gotchas** (e.g. "this driver only supports all-chips-on-node claims").
5. **Cross-links to paired worktrees** ("same fix in `<repo>/.worktrees/<task>`; keep semantics identical, cross-link PRs").

Then add `CLAUDE.local.md` to each repo's `.git/info/exclude` (NOT `.gitignore`) — local-only, shared by all that repo's worktrees, can never be committed.

## Launch Protocol

```bash
S=$(tmux display-message -p '#{session_name}')
tmux send-keys -t "$S:<win>" 'claude --dangerously-skip-permissions --name <win>' Enter
```

- **Always name the session at launch** (`--name`), and make the name identical to the tmux window and worktree name (`tpu-seamless-upgrades`). Named sessions are addressable by name from any other Claude session (`ListAgents` / `SendMessage`) and resumable with `claude --resume <name>` — no UUID hunting. For a session already running unnamed, `/rename <name>` inside it does the same. Auto-generated names (`native-resources-75`, `kubernetes-9d`) are not stable across restarts; explicit names are.

- The folder-trust dialog needs **Enter** to confirm — pressing "1"/"y" alone does nothing (a common "it's stuck" report). Trust persists per directory.
- Verify launch: `#{pane_current_command}` flips from `zsh` to the claude binary (shows as a version string like `2.1.232`, not "claude").
- To exit a running session: two `C-c` **back-to-back** (spaced sends miss the "press ctrl-c again" window).
- Kick-off prompt template (send text and `Enter` as separate `send-keys` calls, small sleep between):

> Read CLAUDE.local.md in this directory and begin the task it describes. Work autonomously: implement, add tests, run them, and commit to the current wt/ branch as you go. Do NOT push, open PRs, or file issues — leave those for my review. If the note says design-first, write the proposal draft to a local PROPOSAL.md instead of coding.

The no-push/no-PR/no-issue guardrail is what makes a large autonomous fleet safe; the conductor (or user) reviews and pushes.

## Talking to Workers — message, don't scrape

- **Claude Code workers**: use `SendMessage` to the session name (append the `[ref]` only if the send errors asking to disambiguate). Ask for a status/summary/handoff and it arrives as a `<cross-session-message>` — complete, structured, no terminal parsing. This is how a conductor gets context out of a worker (e.g. "summarize what you set up, key files, and what the user asked for") — far more reliable than `capture-pane`.
- **tmux is for liveness and steering only**: `#{pane_current_command}` (`zsh` = exited/crashed, version string/`node` = running), the done-heuristic markers below, and sending prompts. Never treat a scraped pane as the full record — TUIs collapse tool output ("`… 11 input + 39 output lines hidden`"), word-wrap tables mid-token, and emit no completion signal.
- **Prompts go through a file**: `tmux send-keys ... "claude ... \"\$(cat prompt.txt)\""`. Typing a long prompt inline breaks on embedded quotes — a `"<request>/<subrequest>"` inside the prompt turned into a shell redirect and the launch silently failed with `no such file or directory: request`.

## Non-Claude Workers (Cursor `agent`, etc.) — report to a file

Non-Claude agents can't be messaged, so scraping is the only channel unless you give them one. Keep them **interactive in a tmux pane** (the user wants to step in and steer directly — don't push them into `-p`/JSON mode), and make the **report file the source of truth**:

- Launch: `agent --yolo --model <model> "$(cat prompt.txt)"` (Cursor CLI; `--yolo` = run everything; `agent --list-models` for IDs, e.g. `cursor-grok-4.6-high`). Same pane-liveness check applies (`node` running / `zsh` exited).
- Append this boilerplate to every non-Claude prompt:

> Write your report to `.agent-reports/<name>.md` in this worktree. Line 1 is `STATUS: RUNNING|DONE|FAILED|BLOCKED` plus a timestamp — update it as you go, not only at the end. Append a section after each major step with the exact commands and the relevant output (pass/fail lines, checks) — I cannot see your terminal. If you need a decision, set `STATUS: BLOCKED`, write the question, and stop.

- Reader: `head -1 .agent-reports/<name>.md` is the done signal; the body has evidence the pane would have hidden. Add `.agent-reports/` to the repo's `.git/info/exclude` — like `CLAUDE.local.md`, it must never land in a PR (workers also leave scratch manifests behind; check `git status` before pushing).
- Same guardrails as Claude workers: no push, no commits unless asked, say what infrastructure (kind clusters) was left running.

## Recovery After a Reboot

tmux-resurrect restores panes and cwds, not processes; every Claude/agent process is gone. To bring the fleet back:

- Which panes had what: the resurrect save (`~/.local/share/tmux/resurrect/last`) keeps each pane's title — Claude sets it to `✳ <session title>` — and cwd. Titles persist after a session exits, so confirm liveness by transcript mtime: sessions alive at the crash all have `~/.claude/projects/<encoded-cwd>/<id>.jsonl` last written at the reboot minute.
- Relaunch per pane with `claude --dangerously-skip-permissions --resume <name-or-id>` via `send-keys`. Named sessions make this a one-liner per window; unnamed ones need the cwd → newest transcript lookup.
- **Large sessions prompt "Resume from summary (recommended) / Resume full session as-is".** "Resume from summary" is not read-only: it runs `/compact` and writes the summary into the transcript, so every later `--resume` silently loads the compacted state. To keep full history pick option 2 (Down, Enter). If summary was chosen by mistake, exit, cut the transcript back to just before the `/compact` user entry (back it up first), and relaunch — the prompt reappears.
- Verify with `/context` in the pane: a full resume shows the real message-token count (hundreds of k for long sessions); a summarized one shows a few k.

## Babysitting Loop

Run a `/loop` (10m is a good cadence) from the conductor. Per tick, per window:

- **Done heuristic — all three required**: pane lacks `esc to interrupt` AND `git log origin/main..HEAD` shows commits AND clean tree. Idle alone is a false positive: a session waiting on its own background subagents looks idle.
- **One-shot action injection** (e.g. send `/code-review` when done): record window IDs in a scratchpad state file so re-fires never double-send.
- Failure modes actually observed:
  - **Stuck "waiting for the final notification"**: session idles forever expecting a task notification that already arrived. Nudge: "Your background task has already finished — no further notification is coming. Retrieve its output and proceed as planned."
  - **Usage-limit stall**: pane shows `You've hit your session limit · resets <time>`. Work-in-progress (dirty tree) is intact; after reset, send "continue where you left off — finish and commit".
  - **Queued user prompts in composers**: the user steers windows directly; a queued prompt may duplicate another window's task. Flag the conflict in the status report; never clear the user's input.
- Status digests: `tmux capture-pane -p -S -120 -t "$S:<win>" | grep -v '^\s*$'` — panes narrower than the conductor's assumption wrap the status line, so match markers (`esc to interrupt`) anywhere in the pane, not on the last line.

## Shell Gotchas (cost real debugging time)

- The Bash tool may run **zsh**: unquoted `$VAR` does NOT word-split (loop over literal lists), and `path` is a special array tied to `$PATH` — assigning `path=$(...)` destroys PATH mid-script. Use `wtdir`, never `path`.
- `chmod -R u+w` before removing built worktrees (Go module caches are read-only) — same as worktrees.md.

## Wrap-up

- Final report: per-branch table (commits, verification state), open decisions parked in specific windows, leftover infrastructure (e2e kind clusters a worker left running — workers should say so; make them tear down or list it).
- Push per branch after review: `git push <fork-remote> wt/<task>`; open paired PRs cross-linked.
- Cleanup: kill fleet windows, `git worktree remove` + `git branch -D wt/<task>` (worktrees.md Cleanup section applies). Deleting a branch a worker committed to is recoverable via reflog for ~2 weeks — mention that when tearing down abandoned work.
