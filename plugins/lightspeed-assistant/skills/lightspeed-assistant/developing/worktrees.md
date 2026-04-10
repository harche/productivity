# Parallel Workspaces (git worktrees)

Work on multiple features simultaneously with isolated branches across
all repos using `lightspeed-operator/hack/worktree.sh`.

## Commands

```
lightspeed-operator/hack/worktree.sh sync                  — fetch + checkout main in all submodules
lightspeed-operator/hack/worktree.sh create <name> [base]  — sync + create parallel workspace
lightspeed-operator/hack/worktree.sh pull <name>           — sync main + merge into all worktree branches
lightspeed-operator/hack/worktree.sh merge <name>          — merge worktree branches into main + update root
lightspeed-operator/hack/worktree.sh remove <name>         — tear down workspace
lightspeed-operator/hack/worktree.sh list                  — show active workspaces
```

## Typical Flow

```bash
# 1. Create a workspace (syncs all submodules first)
lightspeed-operator/hack/worktree.sh create fix-rbac

# 2. Work in the workspace
claude --cwd .worktrees/fix-rbac

# 3. Pull latest main into your workspace (if main moved ahead)
lightspeed-operator/hack/worktree.sh pull fix-rbac

# 4. Merge workspace branches back into main
lightspeed-operator/hack/worktree.sh merge fix-rbac

# 5. Clean up
lightspeed-operator/hack/worktree.sh remove fix-rbac
```

## What Each Command Does

### sync

Fetches all remotes, initializes submodules, and fast-forwards each
submodule's tracked branch (from `.gitmodules`, defaults to `main`).
Never rebases or creates merge commits — if a submodule has diverged
from its remote, it warns and skips.

### create \<name\> [base]

1. Runs `sync` first to ensure everything is up to date
2. Creates a root worktree at `.worktrees/<name>` on branch `wt/<name>`
3. Creates a worktree for each submodule inside the workspace, also on `wt/<name>`

The optional `base` argument sets the starting point (defaults to HEAD).

### pull \<name\>

1. Runs `sync` to update main branches
2. Merges each submodule's tracked branch into its `wt/<name>` branch
3. Updates root worktree submodule pointers

Stops on conflict — resolve it in the submodule, then re-run `pull`.

### merge \<name\>

1. Merges the root repo's `wt/<name>` into its current branch
2. Merges each submodule's `wt/<name>` into its tracked branch
   (fast-forward when possible, merge commit otherwise)
3. Syncs with remote worktree branches (handles agent-pushed commits)
4. Reconciles submodule pointers — catches cases where the root
   fast-forwarded a pointer but the submodule's main fell behind
5. Commits updated submodule pointers in the root repo

### remove \<name\>

Removes all submodule worktrees, the root worktree, and deletes all
`wt/<name>` branches. Always merge before removing — removing does not
preserve unmerged changes.

### list

Shows all active workspaces with each submodule's current branch.

## Branch Naming

All worktree branches use the `wt/<name>` convention. The deploy
scripts in `hack/` auto-detect this via `lib.sh` — when
`WORKSPACE_ROOT` is inside `.worktrees/<name>/`, images are tagged
`wt-<name>` instead of `latest`. Multiple workspaces can deploy to
the same cluster without clobbering each other's images.

## Important

- Always `merge` before `remove` — removing the worktree does not merge changes
- Don't delete `.worktrees/` directories manually — use `lightspeed-operator/hack/worktree.sh remove`
- Worktrees share the same `.git` object store — they're lightweight, not full clones
- `pull` stops on the first conflict — resolve and re-run
- `merge` handles remote worktree branches (agent-pushed commits are synced before merge)

See also: developing/deploying.md (deploying from a worktree)
