# Deploying and Iterating

All deploy scripts live in `lightspeed-operator/hack/`. Run from the
operator directory.

> **Confirm before deploying.** Every script below builds and pushes images
> or restarts deployments. Ask the user for confirmation before running.

## First-Time Deploy

```bash
KUBECONFIG=/path/to/kubeconfig bash lightspeed-operator/hack/deploy-operator.sh
```

Sets up registry, CRDs, namespace, kustomize, builds and pushes all images.

## Fast Iteration (redeploy single component)

```bash
cd lightspeed-operator
KUBECONFIG=... bash hack/redeploy-operator.sh      # operator binary
KUBECONFIG=... bash hack/redeploy-agent.sh          # agent + skills
KUBECONFIG=... bash hack/redeploy-skills.sh         # skills images + agent restart
KUBECONFIG=... bash hack/redeploy-console.sh        # console plugin
KUBECONFIG=... bash hack/redeploy-all.sh            # everything
```

All scripts accept `--skip-build` to reuse existing local images.

## Worktree-Safe Image Tags

Scripts auto-detect git worktrees and tag images as `wt-<name>`
(e.g., `lightspeed-operator:wt-acs-integration`). Main repo uses `:latest`.
Multiple worktrees can deploy to the same cluster without clobbering.

## What Each Script Does

| Script | Builds | Pushes | Restarts |
|--------|--------|--------|----------|
| `redeploy-operator.sh` | operator binary | operator image | operator deployment |
| `redeploy-agent.sh` | agent container | agent image | agent pods |
| `redeploy-skills.sh` | 5 skills images | all skills images | agent pods |
| `redeploy-console.sh` | console plugin | console image | console deployment |
| `redeploy-all.sh` | everything | everything | everything |

## Adapter Skills Images

Each adapter in `examples/adapters/` has its own `Containerfile.skills`
and `deploy.sh` that builds and pushes the skills image. For example:

```bash
KUBECONFIG=... bash examples/adapters/alertmanager/deploy.sh
```

This builds the adapter binary, skills image, and deploys everything.

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Image push auth error | Token expired: `oc create token builder -n openshift-lightspeed --duration=10m` |
| ImagePullBackOff | Image not at correct registry path. Check `oc get istag -n openshift-lightspeed` |
| Operator CrashLoop after CRD changes | Run `make manifests`, reapply CRDs, then redeploy |
| Console placeholder image | Operator set `__REPLACE_LIGHTSPEED_CONSOLE_PLUGIN__`. Patch deployment manually |
| Agent not picking up new image | Delete SandboxClaim, operator recreates it |

See also: references/clusters.md (registry details), references/components.md (per-component details)
