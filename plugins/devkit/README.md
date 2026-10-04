# Devkit

Dev toolkit: worktrees, PR/issue explanations, video explainers, review drafts.

- `/devkit:worktree https://github.com/owner/repo/pull/123 [slug]` — create `<repo>/.worktrees/pr-123` (or `pr-123-fixes-loops`, `issue-456-race-condition` with a slug), creating `.worktrees/` if missing. Branch and dir share the full name. Works in any git repo. Re-running is safe.
- `/devkit:explain [this pr | this issue | PR-or-issue-URL-or-number]` — explain a PR or issue in ASD-STE100, from its title, description, comments, review threads, linked PRs/issues and CI, then the code. "this pr" / "this issue" / no argument resolve from the conversation, the `pr-<N>` / `issue-<N>` branch or worktree, or the branch's upstream PR.
- `/devkit:video <topic | this pr | this issue> [output-path]` — 3Blue1Brown-style video explainer: Manim animation + OpenAI TTS narration (`gpt-4o-mini-tts`, voice `marin`, key from macOS keychain `OPENAI_API_KEY`), 1080p60 MP4, ~5–6 min. Gates handover on audio QA (A/V duration match, every clip present and in sync, no dropouts, transcript matches script), then opens it in QuickTime.
- `/devkit:review [this pr | PR-URL-or-number] [focus]` — draft a GitHub pending review in chat first: friendly informal tone, no emojis, minimal body (no PR recap), claims backed by head-SHA permalinks that GitHub renders as snippets, `suggestion` blocks for small fixes, no repeats of existing threads. Posts as PENDING only after you say "post"; never submits.

## Install

```sh
claude plugin install --scope local devkit@productivity-tools
```

Requires `git` and (for worktree GitHub metadata) `gh` via `gh auth login`. `/devkit:video` also needs `manim`, `ffmpeg` and an OpenAI API key.
