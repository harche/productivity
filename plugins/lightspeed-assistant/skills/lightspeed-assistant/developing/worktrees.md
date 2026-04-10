# Parallel Workspaces (git worktrees)

Work on multiple features simultaneously with isolated branches across
all repos.

## Quick Reference

```bash
hack/worktree.sh sync             # fetch + checkout latest main in all submodules
hack/worktree.sh create <name>    # sync + create .worktrees/<name>/ with all repos
hack/worktree.sh merge <name>     # merge wt/<name> branches into main
hack/worktree.sh remove <name>    # tear down workspace + clean branches
hack/worktree.sh list             # show active workspaces
```

After creating:
```bash
claude --cwd .worktrees/<name>
```

## How It Works

The lightspeed project has multiple repos as git submodules. A single
`git worktree` can only isolate one repo. The script creates worktrees
for the root AND every submodule, assembling them into a single directory.

Each sub-repo gets a `wt/<name>` branch. Changes in the worktree
don't affect the main checkout and vice versa.

## Sync Behavior

Fetches all submodules and fast-forwards to latest remote main:
- **Behind remote:** fast-forwards automatically
- **Ahead of remote (local commits):** skips pull, prints info
- **Diverged from remote:** skips pull, prints warning (resolve manually)

## Merge Behavior

1. Checks each submodule for commits on `wt/<name>` beyond main
2. Skips submodules with no changes
3. Fast-forwards if possible, otherwise creates merge commit
4. Stops on conflicts for manual resolution
5. Updates root repo submodule pointers in a single commit

## Typical Workflow

```bash
hack/worktree.sh create fix-rbac      # create workspace
claude --cwd .worktrees/fix-rbac      # work in it
# ... make changes, commit ...
hack/worktree.sh merge fix-rbac       # integrate back to main
hack/worktree.sh remove fix-rbac      # clean up
```

## Important

- Always `merge` before `remove` — removing deletes `wt/<name>` branches
- Don't delete `.worktrees/` directories manually — use the `remove` command
- Worktrees share the same `.git` object store — lightweight, not full clones
- When merging multiple worktrees that touched the same files, merge one
  at a time and resolve conflicts on subsequent merges

See also: developing/deploying.md (deploying from a worktree)
