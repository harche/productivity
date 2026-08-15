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
tmux send-keys -t "$S:<win>" 'claude --dangerously-skip-permissions' Enter
```

- The folder-trust dialog needs **Enter** to confirm — pressing "1"/"y" alone does nothing (a common "it's stuck" report). Trust persists per directory.
- Verify launch: `#{pane_current_command}` flips from `zsh` to the claude binary (shows as a version string like `2.1.232`, not "claude").
- To exit a running session: two `C-c` **back-to-back** (spaced sends miss the "press ctrl-c again" window).
- Kick-off prompt template (send text and `Enter` as separate `send-keys` calls, small sleep between):

> Read CLAUDE.local.md in this directory and begin the task it describes. Work autonomously: implement, add tests, run them, and commit to the current wt/ branch as you go. Do NOT push, open PRs, or file issues — leave those for my review. If the note says design-first, write the proposal draft to a local PROPOSAL.md instead of coding.

The no-push/no-PR/no-issue guardrail is what makes a large autonomous fleet safe; the conductor (or user) reviews and pushes.

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
