# Dev Environment Setup

Clone all lightspeed repos and initialize a parent project with git submodules.

## GitHub Organization

All repos are in **[NotAKubeKlaw](https://github.com/NotAKubeKlaw)**.

## Quick Setup

From your project directory:

```bash
git init
git submodule add https://github.com/NotAKubeKlaw/lightspeed-operator.git
git submodule add https://github.com/NotAKubeKlaw/lightspeed-agent.git
git submodule add https://github.com/NotAKubeKlaw/lightspeed-console.git
git submodule add https://github.com/NotAKubeKlaw/lightspeed-skills.git
git commit -m "Add lightspeed submodules"
```

## Core Repos (submodules)

| Repo | Required | Purpose |
|------|----------|---------|
| `lightspeed-operator` | Yes | Operator: CRDs, reconciler, deploy scripts |
| `lightspeed-agent` | Yes | Agent: LLM integration, chat API |
| `lightspeed-console` | Yes | Console plugin: proposal UI |
| `lightspeed-skills` | Yes | Per-profile skills OCI images |

## Optional Repos

| Repo | Purpose |
|------|---------|
| `lightspeed-gitops-demo` | ArgoCD-managed workloads for testing proposals |

Clone the demo repo separately if needed — it's a standalone deployment target,
not a build dependency:

```bash
git submodule add https://github.com/NotAKubeKlaw/lightspeed-gitops-demo.git
```

## Cloning on a New Machine

If the parent repo already exists with submodules configured:

```bash
git clone --recurse-submodules <parent-repo-url>
```

Or after a regular clone:

```bash
git submodule update --init --recursive
```

## Verifying Setup

After setup, the directory structure should be:

```
lightspeed-tachyon/
  lightspeed-operator/   # Go operator
  lightspeed-agent/      # TypeScript agent
  lightspeed-console/    # React console plugin
  lightspeed-skills/     # Skills images
  hack/                  # worktree.sh lives here (in operator)
```

## Next Steps

- **Build and deploy:** See deploying.md
- **Parallel workspaces:** See worktrees.md
- **Codebase orientation:** See codebase.md
