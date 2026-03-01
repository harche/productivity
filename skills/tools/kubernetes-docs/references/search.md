# Kubernetes Docs — Search & Read Reference

All commands use the `gh` CLI. See the [github](../../github/SKILL.md) skill for general `gh` usage.

## Discovering Available Versions

Kubernetes docs are versioned via **git branches** (`release-X.Y`), not directories.

```bash
# List recent release branches
gh api repos/kubernetes/website/branches --paginate --jq '.[].name' \
  | grep "^release-" | sort -V | tail -5

# Get the latest release branch into a variable
VERSION=$(gh api repos/kubernetes/website/branches --paginate --jq '.[].name' \
  | grep "^release-" | sort -V | tail -1)
```

## Navigating the Doc Tree

Since there is no index file, navigate by listing directories:

```bash
# List top-level sections
gh api "repos/kubernetes/website/contents/content/en/docs?ref=$VERSION" \
  --jq '.[] | select(.type=="dir") | .name'

# List contents of a section
gh api "repos/kubernetes/website/contents/content/en/docs/concepts?ref=$VERSION" \
  --jq '.[] | "\(.type)\t\(.name)"'

# List contents of a subsection
gh api "repos/kubernetes/website/contents/content/en/docs/concepts/workloads?ref=$VERSION" \
  --jq '.[] | "\(.type)\t\(.name)"'

# Drill deeper
gh api "repos/kubernetes/website/contents/content/en/docs/concepts/workloads/pods?ref=$VERSION" \
  --jq '.[] | "\(.type)\t\(.name)"'
```

## Reading Documentation Files

```bash
# Read a file (always include raw content header)
gh api "repos/kubernetes/website/contents/content/en/docs/{path}?ref=$VERSION" \
  -H "Accept: application/vnd.github.raw+json"
```

### Common Paths

```bash
# Concepts
gh api "repos/kubernetes/website/contents/content/en/docs/concepts/workloads/pods/_index.md?ref=release-1.34" \
  -H "Accept: application/vnd.github.raw+json"

gh api "repos/kubernetes/website/contents/content/en/docs/concepts/workloads/pods/pod-lifecycle.md?ref=release-1.34" \
  -H "Accept: application/vnd.github.raw+json"

gh api "repos/kubernetes/website/contents/content/en/docs/concepts/services-networking/service.md?ref=release-1.34" \
  -H "Accept: application/vnd.github.raw+json"

gh api "repos/kubernetes/website/contents/content/en/docs/concepts/services-networking/ingress.md?ref=release-1.34" \
  -H "Accept: application/vnd.github.raw+json"

gh api "repos/kubernetes/website/contents/content/en/docs/concepts/storage/persistent-volumes.md?ref=release-1.34" \
  -H "Accept: application/vnd.github.raw+json"

gh api "repos/kubernetes/website/contents/content/en/docs/concepts/scheduling-eviction/_index.md?ref=release-1.34" \
  -H "Accept: application/vnd.github.raw+json"

# Tasks
gh api "repos/kubernetes/website/contents/content/en/docs/tasks/configure-pod-container?ref=release-1.34" \
  --jq '.[] | .name'

gh api "repos/kubernetes/website/contents/content/en/docs/tasks/debug?ref=release-1.34" \
  --jq '.[] | "\(.type)\t\(.name)"'

gh api "repos/kubernetes/website/contents/content/en/docs/tasks/administer-cluster?ref=release-1.34" \
  --jq '.[] | .name' | head -20

# Reference (RBAC, API, kubectl)
gh api "repos/kubernetes/website/contents/content/en/docs/reference/access-authn-authz?ref=release-1.34" \
  --jq '.[] | .name'

gh api "repos/kubernetes/website/contents/content/en/docs/reference/kubectl?ref=release-1.34" \
  --jq '.[] | .name'

# Tutorials
gh api "repos/kubernetes/website/contents/content/en/docs/tutorials/stateful-application?ref=release-1.34" \
  --jq '.[] | .name'

# Setup / Installation
gh api "repos/kubernetes/website/contents/content/en/docs/setup/production-environment?ref=release-1.34" \
  --jq '.[] | "\(.type)\t\(.name)"'
```

## Searching for Topics

Without an index file, find relevant docs by listing directories and scanning filenames:

```bash
# Search for files matching a keyword in a section (recursive with GitHub search API)
gh api "search/code?q=repo:kubernetes/website+path:content/en/docs+filename:network" \
  --jq '.items[:10] | .[] | .path'

# Or simply list and grep filenames in a section
gh api "repos/kubernetes/website/contents/content/en/docs/concepts/services-networking?ref=$VERSION" \
  --jq '.[].name'

gh api "repos/kubernetes/website/contents/content/en/docs/tasks?ref=$VERSION" \
  --jq '.[].name' | grep -i "network\|dns\|ingress"
```

## Section Guide

| Section | Path | Description |
|---------|------|-------------|
| **Concepts** | `concepts/` | Core k8s concepts: workloads, networking, storage, security |
| **Tasks** | `tasks/` | Step-by-step how-tos: configure pods, debug, administer cluster |
| **Tutorials** | `tutorials/` | Guided walkthroughs: basics, stateful/stateless apps |
| **Reference** | `reference/` | API reference, kubectl commands, RBAC, config |
| **Setup** | `setup/` | Cluster installation and configuration |
| **Contribute** | `contribute/` | Contributing to Kubernetes docs |

### Key Subsections

| Topic | Path |
|-------|------|
| Pods | `concepts/workloads/pods/` |
| Deployments | `concepts/workloads/controllers/` |
| Services | `concepts/services-networking/service.md` |
| Ingress | `concepts/services-networking/ingress.md` |
| Network Policies | `concepts/services-networking/network-policies.md` |
| Persistent Volumes | `concepts/storage/persistent-volumes.md` |
| ConfigMaps/Secrets | `concepts/configuration/` |
| RBAC | `reference/access-authn-authz/` |
| Scheduling | `concepts/scheduling-eviction/` |
| Security | `concepts/security/` |
| Debugging | `tasks/debug/` |
| kubectl reference | `reference/kubectl/` |

## Tips

- **Start with directory listings**: No index file exists, so list directories to find files. The tree is well-organized and filenames are descriptive.
- **Use `_index.md` for overviews**: Each section/subsection has an `_index.md` that provides the overview — start there.
- **Hugo shortcodes**: Docs contain Hugo template tags like `{{< glossary_tooltip >}}` or `{{< note >}}`. Ignore these when reading content.
- **Version via `ref`**: Always include `?ref=$VERSION` (or `?ref=release-1.34`) in API calls to target a specific Kubernetes version.
- **`main` branch**: Tracks the next upcoming release. Use release branches for stable docs.
- **Large sections**: `tasks/administer-cluster/` and `reference/` are very large. List contents first to find the specific file you need.
- **Rate limits**: `gh` uses your authenticated GitHub token for higher API rate limits.
