---
description: Create a git worktree in .worktrees for a GitHub PR or issue
argument-hint: "<PR-or-issue-URL-or-number> [slug] [repo-path]"
---

# Worktree setup

REQUEST: $ARGUMENTS

Create a git worktree under `.worktrees/` for the given PR or issue. Works in any git repo. Create `.worktrees/` if missing.

## 1. Resolve target repo

- If REQUEST contains an existing local directory that is inside a git repo, use its toplevel:
  `git -C <path> rev-parse --show-toplevel`
- Otherwise use cwd's toplevel: `git rev-parse --show-toplevel`
- Fail with the repo path and `git status` hint if not a git repo.
- Run all subsequent `git` commands with `-C <root>`.

## 2. Parse REQUEST

Extract type, number, and optional descriptor slug. Accept:

- `https://github.com/owner/repo/pull/123` → PR 123
- `https://github.com/owner/repo/issues/123` → issue 123
- `123`, `#123`, `pr-123`, `pr 123`, `pull 123` → PR 123
- `issue 123`, `issue-123` → issue 123
- Suffixed forms carry the slug: `pr-123-fixes-loops` → PR 123 + slug `fixes-loops`; `issue-456-race-condition` → issue 456 + slug `race-condition`
- A trailing bare token is also a slug: `https://.../pull/123 fixes-loops` or `123 fixes-loops` → same as above
- Optional existing local `repo-path` token (see section 1).

Slug rules: kebab-case (`a-z0-9` + hyphens), no slashes, no leading/trailing hyphen (e.g. `fixes-loops`, `race-condition`). A bare slug token gets prefixed automatically; a fully-suffixed `pr-<N>-<slug>` / `issue-<N>-<slug>` token is used as-is.

If type is ambiguous (bare `123`), try `gh pr view 123` first, fall back to issue. If neither resolves and no URL type hint exists, ask the user.

Branch and worktree dir share one full name (`<FULL>`):

- PR → `pr-<N>` or `pr-<N>-<slug>`, path `<root>/.worktrees/<FULL>`
- Issue → `issue-<N>` or `issue-<N>-<slug>`, path `<root>/.worktrees/<FULL>`

## 3. Preflight (idempotent)

```bash
mkdir -p <root>/.worktrees
git -C <root> worktree list
git -C <root> branch --list 'pr-<N>*' 'issue-<N>*'
```

- If the target path is already a registered worktree, report its path, branch, and `git -C <path> log --oneline -3`. Stop.
- If the path exists on disk but is not registered, stop and tell the user to move or remove it. Never delete unregistered directories.
- If the branch exists but has no worktree, reuse it (section 4 fetch uses `-f` only in this case).

## 4. Fetch / create branch

Prefer `gh` for metadata when available; fall back to plain `git fetch` for PR refs. `gh` auth is via `gh auth login`, no manual tokens.

**PR (`<FULL>` = `pr-<N>` or `pr-<N>-<slug>`):**

```bash
gh pr view <N> --json title,headRefName,headRefOid,baseRefName,url
git -C <root> fetch origin pull/<N>/head:<FULL>
# branch exists, no worktree: update with -f
git -C <root> fetch origin pull/<N>/head:<FULL> -f
```

**Issue (`<FULL>` = `issue-<N>` or `issue-<N>-<slug>`):**

```bash
gh issue view <N> --json title,url
# resolve base: gh default branch, else origin/HEAD, else master/main
gh repo view --json defaultBranchRef -q .defaultBranchRef.name
git -C <root> symbolic-ref refs/remotes/origin/HEAD
git -C <root> fetch origin <base>
git -C <root> branch <FULL> origin/<base>
```

If `gh` is missing or the repo is not GitHub-hosted, skip metadata and use `git fetch` (PR) or the local default branch (issue). Report what was skipped.

## 5. Add worktree

```bash
git -C <root> worktree add <root>/.worktrees/<FULL> <FULL>
```

Examples: `<root>/.worktrees/pr-123` / branch `pr-123`; `<root>/.worktrees/pr-123-fixes-loops` / branch `pr-123-fixes-loops`; `<root>/.worktrees/issue-456-race-condition` / branch `issue-456-race-condition`.

## 6. Verify and report

```bash
git -C <root> worktree list
git -C <worktree-path> log --oneline -3
git -C <worktree-path> status --short --branch
```

Report one line each: path, branch (+ base for issues, PR title/url when known), and the update command (`git -C <root> fetch origin pull/<N>/head:<FULL> -f` for PRs).
