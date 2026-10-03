# Devkit

Dev toolkit: worktrees, inline review, dynamic workflows, PR/issue explanations.

- `/devkit:worktree https://github.com/owner/repo/pull/123 [slug]` — create `<repo>/.worktrees/pr-123` (or `pr-123-fixes-loops`, `issue-456-race-condition` with a slug), creating `.worktrees/` if missing. Branch and dir share the full name. Works in any git repo. Re-running is safe.
- `/devkit:code-comments [clean | <path>]` — answer inline `AQ` source comments with `AA` replies directly below. Same markers and idempotency as `code-comments:code-comments`.
- `/devkit:workflow <task>` — author and run a dynamic workflow to explore the task from all angles. Sequential workflows per phase (understand → design → implement → review) so the user stays in the loop. Token cost is not a constraint; lean toward orchestrating + adversarial verify unless trivial or already verified.
- `/devkit:explain [this pr | this issue | PR-or-issue-URL-or-number]` — explain a PR or issue in ASD-STE100, from its title, description, comments, review threads, linked PRs/issues and CI, then the code. "this pr" / "this issue" / no argument resolve from the conversation, the `pr-<N>` / `issue-<N>` branch or worktree, or the branch's upstream PR.

## Install

```sh
claude plugin install --scope local devkit@productivity-tools
```

Requires `git` and (for worktree GitHub metadata) `gh` via `gh auth login`.
