# Developing

Orientation for developers building the LightspeedProposal system.

> **Legacy boundary:** The operator has legacy code (appserver/, OLSConfig
> controller). The proposal system lives in `internal/controller/proposal/`
> and `api/v1alpha1/*proposal*|*workflow*|*agent*|*llmprovider*_types.go`.
> Stay in these areas.

## Topics

|setup.md — Dev environment setup: clone repos, init submodules (developer)
|codebase.md — Repo map, key files, what's legacy vs new (developer)
|reconciler.md — Phase handlers, callAgent flow, retry, escalation (developer)
|deploying.md — hack/ scripts for build, push, deploy iteration (developer)
|worktrees.md — Parallel workspaces across all repos (developer)

## Deploy References

|references/clusters.md — Registry URLs, push auth, skopeo commands
|references/components.md — Per-component build/push/rollout details + troubleshooting
