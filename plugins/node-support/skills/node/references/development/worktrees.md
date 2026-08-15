# Worktrees: Parallel Multi-Repo Workspaces

Create isolated workspaces using `git worktree` with a `wt/<name>` branch under `.worktrees/<name>/`. When submodules are present, each one gets its own worktree and branch inside the workspace.

For running a whole fleet of autonomous Claude sessions across many task worktrees at once (conductor + workers pattern), see `fleet.md`.

## Repo Resolution

When given a GitHub PR or issue URL, resolve the local repo before creating a worktree.

**Parse the URL** to extract `<owner>`, `<repo>`, type (`pull`/`issues`), and number. For example, `github.com/kubernetes-sigs/dra-driver-nvidia-gpu/pull/1243` → owner=`kubernetes-sigs`, repo=`dra-driver-nvidia-gpu`, type=`pull`, number=`1243`.

**Find or clone the repo:**

```bash
OWNER="<owner>"
REPO="<repo>"
REMOTE_URL="git@github.com:$OWNER/$REPO.git"

# 1. Check if pwd is already the repo
CURRENT_REMOTE=$(git remote get-url origin 2>/dev/null)
if echo "$CURRENT_REMOTE" | grep -qE "[:/]$OWNER/$REPO(\.git)?$"; then
  REPO_DIR="$(pwd)"

# 2. Check if <repo>/ subdirectory exists with matching remote
elif [ -d "$REPO" ] && echo "$(git -C "$REPO" remote get-url origin 2>/dev/null)" | grep -qE "[:/]$OWNER/$REPO(\.git)?$"; then
  REPO_DIR="$(pwd)/$REPO"

# 3. Clone into pwd (full clone — history is useful even for reviews)
else
  git clone "$REMOTE_URL"
  REPO_DIR="$(pwd)/$REPO"
fi

cd "$REPO_DIR"
```

**For the user's own PRs (fork remote):** If the PR author matches the authenticated user (`gh api user --jq '.login'`), and the PR head repo differs from the base repo, add the fork as a remote so the user can push back:

```bash
PR_AUTHOR=$(gh pr view <number> --repo "$OWNER/$REPO" --json author --jq '.author.login')
GH_USER=$(gh api user --jq '.login')
if [ "$PR_AUTHOR" = "$GH_USER" ]; then
  FORK_OWNER=$(gh pr view <number> --repo "$OWNER/$REPO" --json headRepositoryOwner --jq '.headRepositoryOwner.login')
  if [ "$FORK_OWNER" != "$OWNER" ]; then
    git remote add "$FORK_OWNER" "git@github.com:$FORK_OWNER/$REPO.git" 2>/dev/null
    git fetch --quiet "$FORK_OWNER"
  fi
fi
```

After resolution, proceed with the Create flow below.

## Create a Workspace

```bash
# Sync submodules first
git fetch --quiet origin
git submodule update --init --quiet
git submodule foreach --quiet 'git fetch --quiet origin; git checkout main --quiet 2>/dev/null; git merge --ff-only origin/main --quiet 2>/dev/null || true'

# Create root worktree
git worktree add .worktrees/<name> -b wt/<name> HEAD

# Create submodule worktrees
git submodule foreach --quiet 'git worktree add "$toplevel/.worktrees/<name>/$sm_path" -b "wt/<name>" HEAD'

cd .worktrees/<name>/
```

After the worktree is created, create a tmux window for it:

```bash
# Detect current tmux session (skip if not in tmux)
SESSION=$(tmux display-message -p '#{session_name}' 2>/dev/null)

# Create window named after the worktree, starting in the worktree directory
[ -n "$SESSION" ] && tmux new-window -t "$SESSION" -n "<name>" -c "$(pwd)/.worktrees/<name>/"
```

## Merge Back

```bash
# For each submodule: merge wt/<name> into main
git submodule foreach --quiet '
  git checkout main --quiet
  git merge --ff-only wt/<name> --quiet 2>/dev/null || git merge wt/<name> --no-edit --quiet
'

# Merge root
git checkout main
git merge --ff-only wt/<name> --quiet 2>/dev/null || git merge wt/<name> --no-edit --quiet

# Update submodule pointers
git add -A && git diff --cached --quiet || git commit -m "Merge workspace <name>"
```

## Remove

```bash
# Kill the tmux window (skip if not in tmux)
SESSION=$(tmux display-message -p '#{session_name}' 2>/dev/null)
[ -n "$SESSION" ] && tmux kill-window -t "$SESSION:=<name>" 2>/dev/null

# Remove worktree and branch
git submodule foreach --quiet 'git worktree remove --force "$toplevel/.worktrees/<name>/$sm_path" 2>/dev/null; git branch -D "wt/<name>" 2>/dev/null'
git worktree remove --force .worktrees/<name>
git branch -D wt/<name>
```

## Cleanup Merged/Closed

Garbage-collect worktrees whose PRs are merged or issues are closed. Works in two modes: single-repo (when pwd is inside a repo) and multi-repo (when pwd is a project folder containing multiple cloned repos).

```bash
SESSION=$(tmux display-message -p '#{session_name}' 2>/dev/null)

cleanup_repo() {
  local repo_dir="$1"
  local REPO
  REPO=$(git -C "$repo_dir" remote get-url origin | sed -E 's|.*[:/]([^/]+/[^/]+?)(\.git)?$|\1|')
  echo "==> Checking $REPO ($repo_dir)"

  # Check each pr-* worktree
  for wt in "$repo_dir"/.worktrees/pr-*; do
    [ -d "$wt" ] || continue
    pr=$(basename "$wt" | sed 's/^pr-//')
    state=$(gh pr view "$pr" --repo "$REPO" --json state --jq '.state' 2>/dev/null)
    if [ "$state" = "MERGED" ] || [ "$state" = "CLOSED" ]; then
      echo "  Removing pr-$pr ($state)"
      [ -n "$SESSION" ] && tmux kill-window -t "$SESSION:=pr-$pr" 2>/dev/null
      chmod -R u+w "$wt" 2>/dev/null
      git -C "$repo_dir" worktree remove --force "$wt" 2>/dev/null || rm -rf "$wt"
      git -C "$repo_dir" branch -D "wt/pr-$pr" 2>/dev/null
    fi
  done

  # Check each issue-* worktree
  for wt in "$repo_dir"/.worktrees/issue-*; do
    [ -d "$wt" ] || continue
    issue=$(basename "$wt" | sed 's/^issue-//')
    state=$(gh issue view "$issue" --repo "$REPO" --json state --jq '.state' 2>/dev/null)
    if [ "$state" = "CLOSED" ]; then
      echo "  Removing issue-$issue ($state)"
      [ -n "$SESSION" ] && tmux kill-window -t "$SESSION:=issue-$issue" 2>/dev/null
      chmod -R u+w "$wt" 2>/dev/null
      git -C "$repo_dir" worktree remove --force "$wt" 2>/dev/null || rm -rf "$wt"
      git -C "$repo_dir" branch -D "wt/issue-$issue" 2>/dev/null
    fi
  done
}

# Single-repo: pwd is inside a git repo
if git rev-parse --git-dir >/dev/null 2>&1; then
  cleanup_repo "$(git rev-parse --show-toplevel)"

# Multi-repo: pwd is a project folder containing cloned repos
else
  for repo_dir in */; do
    [ -d "$repo_dir/.git" ] || continue
    [ -d "$repo_dir/.worktrees" ] || continue
    cleanup_repo "$repo_dir"
  done
fi
```

## Non-Obvious Details

- **Repo resolution uses pwd** — repos are cloned into the current directory. This works whether you're in `~/repos` for standalone repos or in `~/Projects/my-project/` for multi-repo projects. No fixed base path is assumed.
- **Full clone always** — never shallow-clone. History is useful even for reviews.
- **Fork remote only for user's own PRs** — for third-party PRs, `git fetch origin pull/N/head` works without adding remotes. Only add the fork as a remote when the user authored the PR and needs to push.
- **Branch prefix is `wt/`** — every workspace creates `wt/<name>` branches in the root and all submodules. Don't manually create branches with this prefix.
- **Always sync submodules before branching** — fetch and fast-forward all submodules to their tracked branch so your workspace starts from the latest remote state.
- **Remote agent pushes** — if an agent pushed commits to `origin/wt/<name>`, fetch and merge them before merging into main: `git fetch origin; git merge origin/wt/<name>`.
- **Reconcile submodule pointers after merge** — ensure each submodule's main matches the commit the root repo expects. Prevents pointer drift.
- **Only fast-forward during sync** — never rebase or create merge commits during sync. If a submodule has diverged, warn and skip.
- **Tmux window name = worktree name** — always name windows `pr-NNNNN` or `issue-NNNNN` to match the worktree directory. This makes automated cleanup possible.
- **Tmux session = current session** — detected via `tmux display-message`. Works for any repo (kubernetes, cri-o, runc, etc.) since the session is determined by where the agent is running, not hardcoded.
- **Skip tmux if not in tmux** — all tmux commands are guarded by `[ -n "$SESSION" ]`. Worktree operations work standalone.
- **chmod before rm for Go module caches** — `_output/local/go/cache/mod/` contains read-only files. Always `chmod -R u+w` before removing a worktree that may have been built.
